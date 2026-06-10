from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import verify_internal_key
from ..core.response import success
from ..repositories.event_repository import EventRepository
from ..schemas.event import SingleEventResponse
from ..services.event_service import EventService

router = APIRouter(
    prefix="/v1/internal/events",
    tags=["internal-events"],
    dependencies=[Depends(verify_internal_key)],
)

EVENT_NOT_FOUND_MESSAGE = "Event not found"
EVENT_NOT_FOUND_RESPONSES = {404: {"description": EVENT_NOT_FOUND_MESSAGE}}


def _service(db: Annotated[Session, Depends(get_db)]) -> EventService:
    return EventService(EventRepository(db))


EventServiceDep = Annotated[EventService, Depends(_service)]


@router.get(
    "/{eventId}",
    response_model=SingleEventResponse,
    responses=EVENT_NOT_FOUND_RESPONSES,
)
def get_event_internal(
    event_id: Annotated[str, Path(alias="eventId")],
    service: EventServiceDep,
):
    """供其他微服務（Transaction）以 X-Internal-Key 讀取活動詳情。回傳格式與公開 GET 相同。"""
    db_event = service.get_event(event_id)
    if not db_event:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": EVENT_NOT_FOUND_MESSAGE},
        )
    return success(db_event)
