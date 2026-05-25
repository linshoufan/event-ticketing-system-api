import hashlib
import hmac
import math
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import CheckinRequest

VALID_STATUSES = {"used", "unused", "invalid"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def calculate_status(ticket: Ticket, now: datetime | None = None) -> str:
    current = now or _utcnow()
    start = _as_aware(ticket.event.event_start_time)
    end = _as_aware(ticket.event.event_end_time)
    if current < start or current > end:
        return "invalid"
    if ticket.checked_in_at is not None:
        return "used"
    return "unused"


def checkin_available(ticket: Ticket, now: datetime | None = None) -> bool:
    return calculate_status(ticket, now=now) == "unused"


def validate_status_filter(value: str | None) -> None:
    if value is not None and value not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATUS", "message": "Invalid ticket status"},
        )


def get_ticket(ticket_id: str, db: Session) -> Ticket:
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TICKET_NOT_FOUND", "message": "Ticket not found"},
        )
    return ticket


def list_user_tickets(user_id: str, ticket_status: str | None, db: Session) -> list[Ticket]:
    validate_status_filter(ticket_status)
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    if ticket_status is None:
        return tickets
    return [ticket for ticket in tickets if calculate_status(ticket) == ticket_status]


def ensure_ticket_readable(ticket: Ticket, current_user: User) -> None:
    if current_user.role == "welfare_member":
        return
    if current_user.role == "employee" and ticket.user_id == current_user.user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
    )


def build_qr_payload(ticket: Ticket) -> str:
    raw = f"{ticket.ticket_id}:{ticket.event_id}:{ticket.user_id}"
    signature = hmac.new(settings.jwt_secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()[:12]
    return f"{raw}:sig_{signature}"


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def check_in(ticket_id: str, body: CheckinRequest, current_user: User, db: Session) -> Ticket:
    ticket = get_ticket(ticket_id=ticket_id, db=db)
    if ticket.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
        )

    now = _utcnow()
    ticket_status = calculate_status(ticket, now=now)
    if ticket_status == "used":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TICKET_INVALID", "message": "Ticket is used or invalid"},
        )
    if ticket_status == "invalid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_EVENT_TIME", "message": "Check-in only available during event time"},
        )

    distance = _distance_meters(
        body.latitude,
        body.longitude,
        ticket.event.latitude,
        ticket.event.longitude,
    )
    if distance > ticket.event.checkin_radius_meters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OUT_OF_RANGE", "message": "User is not within event location"},
        )

    ticket.checked_in_at = now
    ticket.updated_at = now
    db.commit()
    db.refresh(ticket)
    return ticket

