from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_
from ..models.event import Event

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
        status: Optional[int] = None
    ) -> Tuple[List[Event], int]:
        query = self.db.query(Event)
        query = self._apply_filters(query, keyword, category, status)
        
        total = query.count()
        events = query.order_by(Event.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        
        return events, total

    def _apply_filters(
        self, 
        query: Query, 
        keyword: Optional[str] = None, 
        category: Optional[str] = None, 
        status: Optional[int] = None
    ) -> Query:
        # Default exclude ended events (status 4)
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
            
        return query

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
