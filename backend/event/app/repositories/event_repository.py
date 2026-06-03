from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_
from ..models.event import Event, EventID

class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: str) -> Optional[Event]:
        return self.db.query(Event).filter(Event.event_id == event_id).first()

    def get_filtered(
        self, 
        page: int, 
        limit: int, 
        keyword: Optional[str] = None, 
        category: Optional[str] = None, 
        status: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[Event], int]:
        query = self.db.query(Event)
        query = self._apply_filters(query, keyword, category, status, start_date, end_date)
        
        total = query.count()
        events = query.order_by(Event.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return events, total

    def _apply_filters(
        self, 
        query: Query, 
        keyword: Optional[str] = None, 
        category: Optional[str] = None, 
        status: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Query:
        if status is None:
            query = query.filter(Event.status != 4)
        
        if keyword:
            query = query.filter(
                or_(
                    Event.name.ilike(f"%{keyword}%"),
                    Event.description.ilike(f"%{keyword}%")
                )
            )
        
        if category:
            query = query.filter(Event.category == category)
            
        if status is not None:
            query = query.filter(Event.status == status)

        if start_date:
            query = query.filter(Event.event_start_time >= start_date)

        if end_date:
            query = query.filter(Event.event_start_time <= end_date)
            
        return query

    def get_by_ids(self, event_ids: List[str]) -> List[Event]:
        return self.db.query(Event).filter(Event.event_id.in_(event_ids)).all()

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update(self, event: Event) -> Event:
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event: Event) -> bool:
        self.db.delete(event)
        self.db.commit()
        return True

    def save(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def update_statuses(self, now: datetime) -> dict:
        # 0: NOT_OPEN, 1: REGISTERING, 2: WAITLIST, 3: CLOSED, 4: ENDED
        counts = {
            "registering": self._transition_status(0, 1, (Event.registration_start <= now) & (Event.registration_end > now)),
            "closed": self._transition_status([1, 2], 3, (Event.registration_end <= now)),
            "ended": self._transition_status(None, 4, (Event.event_end_time <= now), exclude_status=4)
        }
        
        if any(counts.values()):
            self.db.commit()
            
        return counts

    def _transition_status(self, from_status, to_status, condition, exclude_status=None) -> int:
        query = self.db.query(Event).filter(condition)
        
        if from_status is not None:
            if isinstance(from_status, list):
                query = query.filter(Event.status.in_(from_status))
            else:
                query = query.filter(Event.status == from_status)
        
        if exclude_status is not None:
            query = query.filter(Event.status != exclude_status)
            
        events = query.all()
        for e in events:
            e.status = to_status
        return len(events)

    def get_latest_available_id(self) -> Tuple[Optional[EventID], int]:
        query = self.db.query(EventID)
        total = query.count()
        query = query.filter(not EventID.isOccupied)
        query = query.order_by(EventID.id.asc()).first()

        return query, total

    def get_greatest_occupied_id(self) -> EventID:
        query = self.db.query(EventID)
        query = query.order_by(EventID.id.desc()).first()

        return query

    def create_event_id(self) -> None:
        id_entity = EventID(id=1, isOccupied=True)
        self.db.add(id_entity)
        self.db.commit()
        self.db.refresh(id_entity)

    def update_event_id(self, event_id: EventID) -> None:
        if event_id is None:
            raise Exception("Update event id failed: receiving null parameter")

        self.db.commit()
        self.db.refresh(event_id)
