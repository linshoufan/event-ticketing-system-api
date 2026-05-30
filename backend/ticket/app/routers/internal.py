from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import verify_internal_key
from app.core.external import get_event_client, EventClient
from app.core.response import success
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreateInternal

router = APIRouter(prefix="/internal/tickets", dependencies=[Depends(verify_internal_key)])

def get_ticket_service(db: Session = Depends(get_db), event_client: EventClient = Depends(get_event_client)) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo, event_client)

@router.post("", status_code=status.HTTP_201_CREATED)
def issue_ticket(
    data: TicketCreateInternal,
    service: TicketService = Depends(get_ticket_service)
):
    ticket = service.create_ticket(data.userId, data.eventId, data.transactionId)
    return success(ticket.to_dict())

@router.delete("/{ticket_id}")
def void_ticket(
    ticket_id: str,
    service: TicketService = Depends(get_ticket_service)
):
    service.void_ticket(ticket_id)
    return success({"ticketId": ticket_id, "voided": True})

@router.get("/no-show")
def get_no_show_tickets(
    eventId: str = Query(..., alias="eventId"),
    service: TicketService = Depends(get_ticket_service)
):
    ticket_ids = service.get_unused_tickets_for_ended_event(eventId)
    return success({"eventId": eventId, "ticketIds": ticket_ids})
