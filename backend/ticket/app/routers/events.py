from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import role_required, CurrentUser
from app.core.external import get_event_client, EventClient
from app.core.response import paginated
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository

router = APIRouter(prefix="/events")

def get_ticket_service(db: Session = Depends(get_db), event_client: EventClient = Depends(get_event_client)) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo, event_client)

@router.get("/{eventId}/tickets")
def get_event_tickets(
    eventId: str,
    status: str = Query(None, regex="^(used|unused|invalid)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(role_required("welfare_member", "hr")),
    service: TicketService = Depends(get_ticket_service)
):
    """View all tickets for a specific event (Admin only)."""
    result = service.get_event_tickets(eventId, status, page, limit)
    return paginated(
        data={"summary": result["summary"], "tickets": result["tickets"]},
        page=page,
        limit=limit,
        total=result["total"]
    )
