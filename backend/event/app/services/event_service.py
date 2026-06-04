from datetime import datetime, timezone
from typing import List, Tuple, Optional
from sqlalchemy.exc import IntegrityError
from ..models.event import Event, EventID
from ..schemas.event import EventCreate, EventUpdate, BatchUpdateItem, normalize_status
from ..repositories.event_repository import EventRepository

class DuplicateEventNameError(Exception):
    pass

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
        event_num_limit = 10000
        next_available_id, record_num = self.repo.get_latest_available_id()

        next_id = 1
        if not next_available_id:
            if record_num == 0:
                self.repo.create_event_id(None)
            elif 0 < record_num and record_num <= event_num_limit:
                greatest_used_id = self.repo.get_greatest_occupied_id()
                if greatest_used_id:
                    next_id = greatest_used_id.id + 1
                    new_event_id = EventID(id=next_id, isOccupied=True)
                    self.repo.create_event_id(new_event_id)
            else:
                raise Exception("EVENT_LIMIT_EXCEEDED")
        else:
            next_id = next_available_id.id
            update_next_id = EventID(id=next_id, isOccupied=True)
            self.repo.update_event_id(update_next_id)

        event_id = f"event_{next_id}"
        event_data = event_in.model_dump(by_alias=False)

        # 建立模型實例並映射欄位
        init_data = {"event_id": event_id}
        for key, value in event_data.items():
            attr_name = self.COLUMN_MAPPING.get(key, key)
            init_data[attr_name] = value
            
        db_event = Event(**init_data)
        try:
            return self.repo.create(db_event)
        except IntegrityError as e:
            self.repo.rollback()
            raise DuplicateEventNameError("duplicate key value") from e

    def get_event(self, event_id: str) -> Optional[Event]:
        return self.repo.get_by_id(event_id)

    def get_filtered_events(
        self, 
        page: int, 
        limit: int, 
        keyword: str = None, 
        category: str = None, 
        status: int | str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Tuple[List[Event], int]:
        normalized_status = normalize_status(status) if status is not None else None
        return self.repo.get_filtered(page, limit, keyword, category, normalized_status, start_date, end_date)

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

    def delete_event(self, event_id: str) -> str:
        db_event = self.repo.get_by_id(event_id)
        if not db_event:
            return "not_found"

        if not self._is_deletable(db_event):
            return "not_deletable"

        release_id = int(event_id.replace("event_", ""))
        update_release_id = EventID(id=release_id, isOccupied=False)

        self.repo.delete(db_event)
        self.repo.update_event_id(update_release_id)
        return "deleted"

    def batch_create(self, events: List[EventCreate]) -> dict:
        succeeded = []
        failed = []

        for index, event_in in enumerate(events):
            try:
                db_event = self.create_event(event_in)
                succeeded.append({"eventId": db_event.event_id, "name": db_event.name})
            except Exception as e:
                self.repo.rollback()
                failed.append({
                    "index": index,
                    "name": getattr(event_in, "name", None),
                    "error": self._format_batch_error(e),
                })

        # Update event status
        now = datetime.now(timezone.utc)
        updated = self.update_statuses(now)
        if any(updated.values()):
            print(f"[scheduler] Updated event statuses: {updated['registering']} registering, {updated['closed']} closed, {updated['ended']} ended.")

        return {"succeeded": succeeded, "failed": failed}

    def batch_query(self, event_ids: List[str]) -> dict:
        found_events = self.repo.get_by_ids(event_ids)
        found_by_id = {event.event_id: event for event in found_events}
        found = [found_by_id[event_id] for event_id in event_ids if event_id in found_by_id]
        not_found = [event_id for event_id in event_ids if event_id not in found_by_id]
        return {"found": found, "notFound": not_found, "total": len(found)}

    def batch_delete(self, event_ids: List[str]) -> dict:
        succeeded = []
        failed = []

        for event_id in event_ids:
            result = self.delete_event(event_id)
            if result == "deleted":
                succeeded.append(event_id)
            elif result == "not_found":
                failed.append({"eventId": event_id, "error": "EVENT_NOT_FOUND"})
            else:
                failed.append({"eventId": event_id, "error": "EVENT_NOT_DELETABLE"})

        return {"succeeded": succeeded, "failed": failed}

    def update_statuses(self, now: datetime) -> dict:
        return self.repo.update_statuses(now)

    def _process_single_batch_item(self, item: BatchUpdateItem) -> Tuple[Optional[str], Optional[str]]:
        db_event = self.repo.get_by_id(item.eventId)
        if not db_event:
            return None, "EVENT_NOT_FOUND"
        
        update_dict = item.model_dump(exclude={"eventId"}, exclude_unset=True, by_alias=False)
        self._apply_updates(db_event, update_dict)
        
        self.repo.save()
        return item.eventId, None

    def _apply_updates(self, db_event: Event, update_dict: dict):
        for key, value in update_dict.items():
            attr_name = self.COLUMN_MAPPING.get(key, key)
            if hasattr(db_event, attr_name):
                setattr(db_event, attr_name, value)

    def _is_deletable(self, db_event: Event) -> bool:
        if db_event.is_draft:
            return True

        now = datetime.now(timezone.utc)
        registration_start = db_event.registration_start
        if registration_start is None:
            return False
        if registration_start.tzinfo is None:
            now = now.replace(tzinfo=None)
        return registration_start > now

    def _format_batch_error(self, error: Exception) -> str:
        if isinstance(error, (DuplicateEventNameError, IntegrityError)):
            return "duplicate key value"
        return str(error)
