import uuid
from datetime import datetime
from typing import List, Tuple, Optional, Any
from ..models.event import Event
from ..schemas.event import EventCreate, EventUpdate, BatchUpdateItem
from ..repositories.event_repository import EventRepository

class EventService:
    # 欄位映射：Pydantic (camelCase) -> SQLAlchemy Attribute (snake_case)
    COLUMN_MAPPING = {
        "guestAllowed": "guest_allowed",
        "ticketLimit": "ticket_limit",
        "remainingTickets": "remaining_tickets",
        "cancellationDeadline": "cancellation_deadline",
        "checkinRadiusMeters": "checkin_radius_meters",
        "eventStartTime": "event_start_time",
        "eventEndTime": "event_end_time",
        "registrationStart": "registration_start",
        "registrationEnd": "registration_end",
        "isDraft": "is_draft"
    }

    def __init__(self, repository: EventRepository):
        self.repo = repository

    def create_event(self, event_in: EventCreate) -> Event:
        event_id = uuid.uuid4().hex[:10]
        event_data = event_in.model_dump(by_alias=False)
        
        # 建立模型實例並映射欄位
        init_data = {"event_id": event_id}
        for key, value in event_data.items():
            attr_name = self.COLUMN_MAPPING.get(key, key)
            init_data[attr_name] = value
            
        db_event = Event(**init_data)
        return self.repo.create(db_event)

    def get_event(self, event_id: str) -> Optional[Event]:
        return self.repo.get_by_id(event_id)

    def get_filtered_events(
        self, 
        page: int, 
        limit: int, 
        keyword: str = None, 
        category: str = None, 
        status: int = None
    ) -> Tuple[List[Event], int]:
        return self.repo.get_filtered(page, limit, keyword, category, status)

    def update_event(self, event_id: str, update_data: EventUpdate) -> Optional[Event]:
        db_event = self.repo.get_by_id(event_id)
        if not db_event:
            return None
            
        update_dict = update_data.model_dump(exclude_unset=True, by_alias=False)
        self._apply_updates(db_event, update_dict)
            
        return self.repo.update(db_event)

    def batch_update(self, updates: List[BatchUpdateItem]) -> dict:
        succeeded = []
        failed = []

        for item in updates:
            try:
                success_id, error = self._process_single_batch_item(item)
                if error:
                    failed.append({"eventId": item.eventId, "error": error})
                else:
                    succeeded.append(success_id)
            except Exception as e:
                self.repo.rollback()
                failed.append({"eventId": item.eventId, "error": str(e)})
                
        return {"succeeded": succeeded, "failed": failed}

    def delete_event(self, event_id: str) -> bool:
        db_event = self.repo.get_by_id(event_id)
        if not db_event:
            return False
        
        return self.repo.delete(db_event)

    def update_statuses(self, now: datetime) -> dict:
        return self.repo.update_statuses(now)

    def _process_single_batch_item(self, item: BatchUpdateItem) -> Tuple[Optional[str], Optional[str]]:
        db_event = self.repo.get_by_id(item.eventId)
        if not db_event:
            return None, "Event not found"
        
        update_dict = item.model_dump(exclude={"eventId"}, exclude_unset=True, by_alias=False)
        self._apply_updates(db_event, update_dict)
        
        self.repo.save()
        return item.eventId, None

    def _apply_updates(self, db_event: Event, update_dict: dict):
        for key, value in update_dict.items():
            attr_name = self.COLUMN_MAPPING.get(key, key)
            if hasattr(db_event, attr_name):
                setattr(db_event, attr_name, value)
