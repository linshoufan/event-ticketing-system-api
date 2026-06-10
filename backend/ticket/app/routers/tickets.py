from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import role_required, CurrentUser
from app.core.external import get_event_client, EventClient, get_account_client, AccountClient
from app.core.response import success
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCheckin

router = APIRouter(prefix="/tickets")


def get_ticket_service(
    db: Annotated[Session, Depends(get_db)],
    event_client: Annotated[EventClient, Depends(get_event_client)],
    account_client: Annotated[AccountClient, Depends(get_account_client)],
) -> TicketService:
    repo = TicketRepository(db)
    return TicketService(repo, event_client, account_client)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
TicketUserDep = Annotated[
    CurrentUser,
    Depends(role_required("employee", "welfare_member", "hr")),
]


@router.get("")
def get_my_tickets(
    current_user: TicketUserDep,
    service: TicketServiceDep,
    status: Annotated[str | None, Query(pattern="^(used|unused|invalid)$")] = None,
):
    """Retrieve my ticket list."""
    tickets = service.get_user_tickets(current_user.user_id, status)
    return success(tickets)


@router.get("/{ticketId}")
def get_ticket_detail(
    ticket_id: Annotated[str, Path(alias="ticketId")],
    current_user: TicketUserDep,
    service: TicketServiceDep,
):
    """Get single ticket details."""
    is_welfare = current_user.role == "welfare_member"
    ticket = service.get_ticket_detail(ticket_id, current_user.user_id if not is_welfare else None)
    return success(ticket)


@router.post("/{ticketId}/checkin")
def checkin(
    ticket_id: Annotated[str, Path(alias="ticketId")],
    current_user: TicketUserDep,
    service: TicketServiceDep,
    checkin_data: Annotated[Any, Body()] = None,
):
    """Perform check-in with geofencing."""
    if current_user.role == "welfare_member":
        result = service.checkin_by_welfare(ticket_id)
    else:
        try:
            parsed_checkin = TicketCheckin.model_validate(checkin_data)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc

        result = service.checkin(
            ticket_id,
            current_user.user_id,
            parsed_checkin.latitude,
            parsed_checkin.longitude,
        )
    return success(result)
