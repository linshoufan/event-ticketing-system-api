from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, role_required
from app.core.response import success
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import (
    CheckedInResponse,
    CheckinRequest,
    TicketDetailResponse,
    TicketListItemResponse,
)
from app.services import ticket_service

router = APIRouter()


def _to_list_item(ticket: Ticket) -> dict:
    return TicketListItemResponse(
        ticketId=ticket.ticket_id,
        eventId=ticket.event_id,
        eventName=ticket.event.name,
        eventStartTime=ticket.event.event_start_time,
        eventLocation=ticket.event.location,
        status=ticket_service.calculate_status(ticket),
        checkinAvailable=ticket_service.checkin_available(ticket),
    ).model_dump()


def _to_detail(ticket: Ticket) -> dict:
    return TicketDetailResponse(
        ticketId=ticket.ticket_id,
        userId=ticket.user_id,
        eventId=ticket.event_id,
        eventName=ticket.event.name,
        eventStartTime=ticket.event.event_start_time,
        eventEndTime=ticket.event.event_end_time,
        eventLocation=ticket.event.location,
        latitude=ticket.event.latitude,
        longitude=ticket.event.longitude,
        checkinRadiusMeters=ticket.event.checkin_radius_meters,
        status=ticket_service.calculate_status(ticket),
        checkinAvailable=ticket_service.checkin_available(ticket),
        qrPayload=ticket_service.build_qr_payload(ticket),
    ).model_dump()


@router.get("/tickets", response_model=dict)
def list_my_tickets(
    status: str | None = None,
    current_user: User = Depends(role_required("employee")),
    db: Session = Depends(get_db),
):
    tickets = ticket_service.list_user_tickets(
        user_id=current_user.user_id,
        ticket_status=status,
        db=db,
    )
    return success([_to_list_item(ticket) for ticket in tickets])


@router.get("/tickets/{ticket_id}", response_model=dict)
def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = ticket_service.get_ticket(ticket_id=ticket_id, db=db)
    ticket_service.ensure_ticket_readable(ticket=ticket, current_user=current_user)
    return success(_to_detail(ticket))


@router.post("/tickets/{ticket_id}/checkin", response_model=dict)
def check_in(
    ticket_id: str,
    body: CheckinRequest,
    current_user: User = Depends(role_required("employee")),
    db: Session = Depends(get_db),
):
    ticket = ticket_service.check_in(
        ticket_id=ticket_id,
        body=body,
        current_user=current_user,
        db=db,
    )
    return success(
        CheckedInResponse(
            checkedIn=True,
            checkedInAt=ticket.checked_in_at,
        ).model_dump()
    )
