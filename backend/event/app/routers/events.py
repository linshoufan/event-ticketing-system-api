from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import CurrentUser, role_required
from ..core.external import TicketClient, get_ticket_client
from ..core.response import success, paginated
from ..core.external import TransactionClient, get_transaction_client
from ..schemas.event import (
    EventCreate, EventUpdate, EventResponse, 
    PaginatedEventResponse, BatchUpdateSchema,
    SingleEventResponse, BatchCreateSchema, BatchQuerySchema,
    BatchDeleteSchema
)
from ..services.event_service import DuplicateEventNameError, EventService
from ..repositories.event_repository import EventRepository

router = APIRouter(prefix="/v1/events", tags=["events"])

EVENT_NOT_FOUND_MESSAGE = "Event not found"
EVENT_NAME_ALREADY_EXISTS_MESSAGE = "Event name already exists"


def get_event_service(
    db: Annotated[Session, Depends(get_db)],
    ticket_client: Annotated[TicketClient, Depends(get_ticket_client)],
    transaction_client: Annotated[TransactionClient, Depends(get_transaction_client)],
) -> EventService:
    repo = EventRepository(db)
    return EventService(repo, ticket_client, transaction_client) 


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
WelfareMemberDep = Annotated[CurrentUser, Depends(role_required("welfare_member"))]
EmployeeEventReaderDep = Annotated[
    CurrentUser,
    Depends(role_required("employee", "welfare_member", "hr")),
]


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": EVENT_NAME_ALREADY_EXISTS_MESSAGE}},
    include_in_schema=False,
)
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": EVENT_NAME_ALREADY_EXISTS_MESSAGE}},
)
def create_event(
    event_in: EventCreate, 
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    try:
        db_event = service.create_event(event_in)
        now = datetime.now(timezone.utc)
        updated = service.update_statuses(now)

        if any(updated.values()):
            print(f"[scheduler] Updated event statuses: {updated['registering']} registering, {updated['closed']} closed, {updated['ended']} ended.")

    except DuplicateEventNameError:
        raise HTTPException(
            status_code=409,
            detail={"code": "EVENT_NAME_ALREADY_EXISTS", "message": EVENT_NAME_ALREADY_EXISTS_MESSAGE},
        )
    return success({
        "eventId": db_event.event_id,
        "isDraft": db_event.is_draft,
        "createdAt": db_event.created_at
    })


@router.get(
    "",
    response_model=PaginatedEventResponse,
    responses={400: {"description": "Bad request"}},
    include_in_schema=False,
)
@router.get("/", response_model=PaginatedEventResponse, responses={400: {"description": "Bad request"}})
def get_events(
    service: EventServiceDep,
    _current_user: EmployeeEventReaderDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 20,
    keyword: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query(alias="startDate")] = None,
    end_date: Annotated[datetime | None, Query(alias="endDate")] = None,
):
    try:
        events, total = service.get_filtered_events(
            page, limit, keyword, category, status, start_date, end_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "BAD_REQUEST", "message": str(e)})
    return paginated(events, page, limit, total)


@router.get(
    "/{eventId}",
    response_model=SingleEventResponse,
    responses={404: {"description": EVENT_NOT_FOUND_MESSAGE}},
)
def get_event_details(
    event_id: Annotated[str, Path(alias="eventId")],
    service: EventServiceDep,
    _current_user: EmployeeEventReaderDep,
):
    db_event = service.get_event(event_id)
    if not db_event:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": EVENT_NOT_FOUND_MESSAGE},
        )
    return success(db_event)


@router.patch("/{eventId}", response_model=dict, responses={404: {"description": EVENT_NOT_FOUND_MESSAGE}})
def update_event(
    event_id: Annotated[str, Path(alias="eventId")],
    update_data: EventUpdate,
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    db_event = service.update_event(event_id, update_data)
    if not db_event:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": EVENT_NOT_FOUND_MESSAGE},
        )

    now = datetime.now(timezone.utc)
    updated = service.update_statuses(now)
    if any(updated.values()):
        print(f"[scheduler] Updated event statuses: {updated['registering']} registering, {updated['closed']} closed, {updated['ended']} ended.")

    return success({
        "updated": True,
        "updatedAt": db_event.updated_at
    })

@router.patch("", response_model=dict, status_code=status.HTTP_207_MULTI_STATUS, include_in_schema=False)
@router.patch("/", response_model=dict, status_code=status.HTTP_207_MULTI_STATUS)
def batch_update_events(
    batch_in: BatchUpdateSchema, 
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    result = service.batch_update(batch_in.updates)
    return success(result)

@router.post("/batch", response_model=dict, status_code=status.HTTP_201_CREATED)
def batch_create_events(
    batch_in: BatchCreateSchema,
    response: Response,
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    result = service.batch_create(batch_in.events)
    if result["failed"] and result["succeeded"]:
        response.status_code = status.HTTP_207_MULTI_STATUS
    elif result["failed"]:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return success(result)

@router.post("/batch/query", response_model=dict)
def batch_query_events(
    batch_in: BatchQuerySchema,
    service: EventServiceDep,
    _current_user: EmployeeEventReaderDep,
):
    result = service.batch_query(batch_in.eventIds)
    result["found"] = [
        EventResponse.model_validate(event).model_dump(by_alias=True)
        for event in result["found"]
    ]
    return success(result)

@router.delete("/batch", response_model=dict)
def batch_delete_events(
    batch_in: BatchDeleteSchema,
    response: Response,
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    result = service.batch_delete(batch_in.eventIds)
    if result["failed"]:
        response.status_code = status.HTTP_207_MULTI_STATUS
    return success(result)

@router.delete(
    "/{eventId}",
    response_model=dict,
    responses={
        404: {"description": EVENT_NOT_FOUND_MESSAGE},
        409: {"description": "Event is not deletable"},
        502: {"description": "Related resource cleanup failed"},
    },
)
def delete_event(
    event_id: Annotated[str, Path(alias="eventId")],
    service: EventServiceDep,
    _current_user: WelfareMemberDep,
):
    delete_result = service.delete_event(event_id)
    if delete_result == "not_found":
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": EVENT_NOT_FOUND_MESSAGE},
        )
    if delete_result == "ticket_cleanup_failed":
        raise HTTPException(
            status_code=502,
            detail={"code": "TICKET_CLEANUP_FAILED", "message": "Failed to delete related tickets"},
        )
    if delete_result == "transaction_cleanup_failed":
        raise HTTPException(
            status_code=502,
            detail={"code": "TRANSACTION_CLEANUP_FAILED", "message": "Failed to delete related registrations"},
        )
    if delete_result == "not_deletable":
        raise HTTPException(status_code=409, detail={"code": "EVENT_NOT_DELETABLE", "message": "Event is not deletable"})
    return success({"deleted": True})
