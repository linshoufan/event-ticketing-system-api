import math
from datetime import datetime, timezone
from typing import List, Optional

from app.models.ticket import Ticket
from app.repositories.ticket_repository import TicketRepository
from app.core.external import EventClient, EventInfo
from fastapi import HTTPException, status

class TicketService:
    def __init__(self, repository: TicketRepository, event_client: EventClient):
        self.repo = repository
        self.event_client = event_client

    def create_ticket(self, user_id: str, event_id: str, transaction_id: str) -> Ticket:
        # Check if ticket already exists for this transaction
        existing = self.repo.get_by_transaction_id(transaction_id)
        if existing:
            return existing
        
        # Check if active ticket already exists for user and event
        active_ticket = self.repo.get_active_ticket(user_id, event_id)
        if active_ticket:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "TICKET_ALREADY_EXISTS", 
                    "message": "User already has an active ticket for this event", 
                    "ticketId": active_ticket.ticket_id
                }
            )

        new_ticket = Ticket(
            user_id=user_id,
            event_id=event_id,
            transaction_id=transaction_id,
            status="unused"
        )
        return self.repo.create(new_ticket)

    def void_ticket(self, ticket_id: str) -> bool:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            return True # Idempotent
        
        if ticket.status == "used":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_USED", "message": "Ticket is already checked in"}
            )
        
        self.repo.delete(ticket)
        return True

    def get_unused_tickets_for_ended_event(self, event_id: str) -> List[str]:
        event = self.event_client.get_event(event_id)
        now = datetime.now(timezone.utc)
        if event.event_end_time > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "EVENT_NOT_ENDED", "message": "Event has not ended yet"}
            )
        
        # We can query unused tickets through repo
        # Note: we filter by event_id and status='unused'
        # To be strict, we'd add this method to repo, but using user filter for now as proxy
        # Better: add to repo if it's a common query
        tickets = self.repo.db.query(Ticket).filter(
            Ticket.event_id == event_id,
            Ticket.status == "unused"
        ).all()
        return [t.ticket_id for t in tickets]

    def get_user_tickets(self, user_id: str, status_filter: str = None) -> List[dict]:
        tickets = self.repo.get_user_tickets(user_id, status_filter)
        result = []
        now = datetime.now(timezone.utc)
        
        for t in tickets:
            try:
                event = self.event_client.get_event(t.event_id)
                checkin_available = event.event_start_time <= now <= event.event_end_time and t.status == "unused"
                
                display_status = t.status
                if t.status == "unused":
                    if now < event.event_start_time or now > event.event_end_time:
                        display_status = "invalid"

                result.append({
                    "ticketId": t.ticket_id,
                    "eventId": t.event_id,
                    "eventName": event.name,
                    "eventStartTime": event.event_start_time.isoformat(),
                    "eventLocation": event.location,
                    "status": display_status,
                    "checkinAvailable": checkin_available
                })
            except Exception:
                result.append({
                    "ticketId": t.ticket_id,
                    "eventId": t.event_id,
                    "status": t.status,
                    "checkinAvailable": False
                })
        
        return result

    def get_ticket_detail(self, ticket_id: str, current_user_id: str = None, is_internal: bool = False) -> dict:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail={"code": "TICKET_NOT_FOUND", "message": "Ticket not found"})
        
        if not is_internal and current_user_id and ticket.user_id != current_user_id:
             raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

        try:
            event = self.event_client.get_event(ticket.event_id)
            now = datetime.now(timezone.utc)
            checkin_available = event.event_start_time <= now <= event.event_end_time and ticket.status == "unused"

            display_status = ticket.status
            if ticket.status == "unused":
                if now < event.event_start_time or now > event.event_end_time:
                    display_status = "invalid"

            return {
                "ticketId": ticket.ticket_id,
                "userId": ticket.user_id,
                "eventId": ticket.event_id,
                "eventName": event.name,
                "eventStartTime": event.event_start_time.isoformat(),
                "eventEndTime": event.event_end_time.isoformat(),
                "eventLocation": event.location,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "checkinRadiusMeters": event.checkin_radius_meters,
                "status": display_status,
                "checkinAvailable": checkin_available,
                "qrPayload": f"{ticket.ticket_id}:{ticket.event_id}:{ticket.user_id}:sig_mock"
            }
        except Exception as e:
            # If Event Service is unreachable, return basic information
            return {
                "ticketId": ticket.ticket_id,
                "userId": ticket.user_id,
                "eventId": ticket.event_id,
                "eventName": "Unknown Event (Event Service Offline)",
                "status": ticket.status,
                "checkinAvailable": False,
                "qrPayload": f"{ticket.ticket_id}:{ticket.event_id}:{ticket.user_id}:sig_mock"
            }

    def checkin(self, ticket_id: str, user_id: str, lat: float, lon: float) -> dict:
        ticket = self.repo.get_by_id(ticket_id)
        if not ticket or ticket.user_id != user_id:
             raise HTTPException(status_code=404, detail={"code": "TICKET_NOT_FOUND", "message": "Ticket not found"})
        
        if ticket.status != "unused":
             raise HTTPException(status_code=400, detail={"code": "TICKET_INVALID", "message": "Ticket is used or invalid"})
        
        event = self.event_client.get_event(ticket.event_id)
        now = datetime.now(timezone.utc)
        
        if not (event.event_start_time <= now <= event.event_end_time):
            raise HTTPException(status_code=400, detail={"code": "NOT_EVENT_TIME", "message": "Check-in only available during event time"})
        
        # Geofencing
        event_lat = float(event.latitude)
        event_lon = float(event.longitude)
        radius = float(event.checkin_radius_meters)
        
        distance = self._calculate_distance(lat, lon, event_lat, event_lon)
        if distance > radius:
             raise HTTPException(status_code=400, detail={"code": "OUT_OF_RANGE", "message": "User is not within event location"})
        
        ticket.status = "used"
        ticket.checked_in_at = now
        self.repo.save()
        
        return {"checkedIn": True, "checkedInAt": now.isoformat()}

    def get_event_tickets(self, event_id: str, status_filter: str = None, page: int = 1, limit: int = 50) -> dict:
        tickets = self.repo.get_event_tickets(event_id, status_filter, page, limit)
        total = self.repo.count_event_tickets(event_id, status_filter)
        summary = self.repo.get_event_summary(event_id)
        
        return {
            "summary": summary,
            "tickets": [{"ticketId": t.ticket_id, "userId": t.user_id, "status": t.status} for t in tickets],
            "total": total
        }

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        # Haversine formula
        R = 6371000  # Radius of the earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) * math.sin(dphi / 2) + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(dlambda / 2) * math.sin(dlambda / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
