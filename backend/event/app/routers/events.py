from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from ..core.database import get_db
from ..core.dependencies import role_required
from ..core.response import success, paginated
from ..schemas.event import (
    EventCreate, EventUpdate, EventResponse, 
    PaginatedEventResponse, BatchUpdateSchema,
    SingleEventResponse
)
from ..services.event_service import EventService
from ..repositories.event_repository import EventRepository

router = APIRouter(prefix="/v1/events", tags=["events"])

def get_event_service(db: Session = Depends(get_db)) -> EventService:
    repo = EventRepository(db)
    return EventService(repo)

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member", "hr"))
):
    db_event = service.create_event(event_in)
    return success({
        "eventId": db_event.event_id,
        "isDraft": db_event.is_draft,
        "createdAt": db_event.created_at
    })

@router.get("/", response_model=PaginatedEventResponse)
def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[int] = None,
    service: EventService = Depends(get_event_service)
):
    events, total = service.get_filtered_events(
        page, limit, keyword, category, status
    )
    return paginated(events, page, limit, total)

@router.get("/{eventId}", response_model=SingleEventResponse)
def get_event_details(eventId: str, service: EventService = Depends(get_event_service)):
    db_event = service.get_event(eventId)
    if not db_event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return success(db_event)

@router.patch("/{eventId}", response_model=dict)
def update_event(
    eventId: str, 
    update_data: EventUpdate, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member", "hr"))
):
    db_event = service.update_event(eventId, update_data)
    if not db_event:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return success({
        "updated": True,
        "updatedAt": db_event.updated_at
    })

@router.patch("/", response_model=dict, status_code=status.HTTP_207_MULTI_STATUS)
def batch_update_events(
    batch_in: BatchUpdateSchema, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member", "hr"))
):
    result = service.batch_update(batch_in.updates)
    return success(result)

@router.delete("/{eventId}", response_model=dict)
def delete_event(
    eventId: str, 
    service: EventService = Depends(get_event_service),
    _ = Depends(role_required("welfare_member", "hr"))
):
    success_deleted = service.delete_event(eventId)
    if not success_deleted:
        raise HTTPException(status_code=404, detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"})
    return success({"deleted": True})
