from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import role_required, CurrentUser
from app.core.external import get_event_client, EventClient, get_account_client, AccountClient
from app.core.response import paginated
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository

router = APIRouter(prefix="/events")


def get_ticket_service(
    db: Annotated[Session, Depends(get_db)],
    event_client: Annotated[EventClient, Depends(get_event_client)],
    account_client: Annotated[AccountClient, Depends(get_account_client)],
) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo, event_client, account_client)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
TicketStaffDep = Annotated[CurrentUser, Depends(role_required("welfare_member", "hr"))]


@router.get("/{eventId}/tickets")
def get_event_tickets(
    event_id: Annotated[str, Path(alias="eventId")],
    _current_user: TicketStaffDep,
    service: TicketServiceDep,
    status: Annotated[str | None, Query(pattern="^(used|unused|invalid)$")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """View all tickets for a specific event (Admin only)."""
    result = service.get_event_tickets(event_id, status, page, limit)
    return paginated(
        data={"summary": result["summary"], "tickets": result["tickets"]},
        page=page,
        limit=limit,
        total=result["total"]
    )
