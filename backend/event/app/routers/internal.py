from fastapi import APIRouter, Depends, HTTPException
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


def _service(db: Session = Depends(get_db)) -> EventService:
    return EventService(EventRepository(db))


@router.get("/{eventId}", response_model=SingleEventResponse)
def get_event_internal(eventId: str, service: EventService = Depends(_service)):
    """供其他微服務（Transaction）以 X-Internal-Key 讀取活動詳情。回傳格式與公開 GET 相同。"""
    db_event = service.get_event(eventId)
    if not db_event:
        raise HTTPException(
            status_code=404,
            detail={"code": "EVENT_NOT_FOUND", "message": "Event not found"},
        )
    return success(db_event)