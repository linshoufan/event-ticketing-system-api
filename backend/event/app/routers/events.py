from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from typing import Optional
from ..core.database import get_db
from ..core.dependencies import role_required
from ..core.response import success, paginated
from ..schemas.event import (
    EventCreate, EventUpdate, EventResponse, 
    PaginatedEventResponse, BatchUpdateSchema,
    SingleEventResponse, BatchCreateSchema, BatchQuerySchema,
    BatchDeleteSchema
)
from ..services.event_service import DuplicateEventNameError, EventService
from ..repositories.event_repository import EventRepository

router = APIRouter(prefix="/v1/events", tags=["events"])

def get_event_service(db: Session = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
):
    try:
        db_event = service.create_event(event_in)
    except DuplicateEventNameError:
        raise HTTPException(
            status_code=409,
            detail={"code": "EVENT_NAME_ALREADY_EXISTS", "message": "Event name already exists"},
        )
    return success({
        "eventId": db_event.event_id,
        "isDraft": db_event.is_draft,
        "createdAt": db_event.created_at
    })

@router.get("", response_model=PaginatedEventResponse, include_in_schema=False)
@router.get("/", response_model=PaginatedEventResponse)
def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    startDate: Optional[datetime] = Query(None, alias="startDate"),
    endDate: Optional[datetime] = Query(None, alias="endDate"),
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("employee", "welfare_member", "hr")) # 加入權限檢查
):
    try:
        events, total = service.get_filtered_events(
            page, limit, keyword, category, status, startDate, endDate
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "BAD_REQUEST", "message": str(e)})
    return paginated(events, page, limit, total)

@router.get("/{eventId}", response_model=SingleEventResponse)
def get_event_details(
    eventId: str, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("employee", "welfare_member", "hr")) # 加入權限檢查
):
    db_event = service.get_event(eventId)
    if not db_event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return success(db_event)

@router.patch("/{eventId}", response_model=dict)
def update_event(
    eventId: str, 
    update_data: EventUpdate, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
):
    db_event = service.update_event(eventId, update_data)
    if not db_event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return success({
        "updated": True,
        "updatedAt": db_event.updated_at
    })

@router.patch("", response_model=dict, status_code=status.HTTP_207_MULTI_STATUS, include_in_schema=False)
@router.patch("/", response_model=dict, status_code=status.HTTP_207_MULTI_STATUS)
def batch_update_events(
    batch_in: BatchUpdateSchema, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
):
    result = service.batch_update(batch_in.updates)
    return success(result)

@router.post("/batch", response_model=dict, status_code=status.HTTP_201_CREATED)
def batch_create_events(
    batch_in: BatchCreateSchema,
    response: Response,
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
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
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("employee", "welfare_member", "hr"))
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
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
):
    result = service.batch_delete(batch_in.eventIds)
    if result["failed"]:
        response.status_code = status.HTTP_207_MULTI_STATUS
    return success(result)

@router.delete("/{eventId}", response_model=dict)
def delete_event(
    eventId: str, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member"))
):
    delete_result = service.delete_event(eventId)
    if delete_result == "not_found":
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    if delete_result == "not_deletable":
        raise HTTPException(status_code=409, detail={"code": "EVENT_NOT_DELETABLE", "message": "Event is not deletable"})
    return success({"deleted": True})
