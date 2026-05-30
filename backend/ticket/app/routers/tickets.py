from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import role_required, CurrentUser
from app.core.external import get_event_client, EventClient
from app.core.response import success
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCheckin

router = APIRouter(prefix="/tickets")

def get_ticket_service(db: Session = Depends(get_db), event_client: EventClient = Depends(get_event_client)) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo, event_client)

@router.get("")
def get_my_tickets(
    status: str = Query(None, regex="^(used|unused|invalid)$"),
    current_user: CurrentUser = Depends(role_required("employee", "welfare_member", "hr")),
    service: TicketService = Depends(get_ticket_service)
):
    """Retrieve my ticket list."""
    tickets = service.get_user_tickets(current_user.user_id, status)
    return success(tickets)

@router.get("/{ticketId}")
def get_ticket_detail(
    ticketId: str,
    current_user: CurrentUser = Depends(role_required("employee", "welfare_member", "hr")),
    service: TicketService = Depends(get_ticket_service)
):
    """Get single ticket details."""
    is_welfare = current_user.role == "welfare_member"
    ticket = service.get_ticket_detail(ticketId, current_user.user_id if not is_welfare else None)
    return success(ticket)

@router.post("/{ticketId}/checkin")
def checkin(
    ticketId: str,
    checkin_data: TicketCheckin,
    current_user: CurrentUser = Depends(role_required("employee")),
    service: TicketService = Depends(get_ticket_service)
):
    """Perform check-in with geofencing."""
    result = service.checkin(ticketId, current_user.user_id, checkin_data.latitude, checkin_data.longitude)
    return success(result)
