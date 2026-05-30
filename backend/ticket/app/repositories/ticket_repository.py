from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket

class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, ticket_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

    def get_by_transaction_id(self, transaction_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.transaction_id == transaction_id).first()

    def get_active_ticket(self, user_id: str, event_id: str) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(
            Ticket.user_id == user_id,
            Ticket.event_id == event_id,
            Ticket.status == "unused"
        ).first()

    def get_user_tickets(self, user_id: str, status: Optional[str] = None) -> List[Ticket]:
        query = self.db.query(Ticket).filter(Ticket.user_id == user_id)
        if status:
            query = query.filter(Ticket.status == status)
        return query.all()

    def get_event_tickets(self, event_id: str, status: Optional[str] = None, page: int = 1, limit: int = 50) -> List[Ticket]:
        query = self.db.query(Ticket).filter(Ticket.event_id == event_id)
        if status:
            query = query.filter(Ticket.status == status)
        return query.offset((page - 1) * limit).limit(limit).all()

    def count_event_tickets(self, event_id: str, status: Optional[str] = None) -> int:
        query = self.db.query(Ticket).filter(Ticket.event_id == event_id)
        if status:
            query = query.filter(Ticket.status == status)
        return query.count()

    def get_event_summary(self, event_id: str) -> dict:
        summary = self.db.query(
            Ticket.status, func.count(Ticket.ticket_id)
        ).filter(Ticket.event_id == event_id).group_by(Ticket.status).all()
        
        result = {"used": 0, "unused": 0, "invalid": 0}
        for s, count in summary:
            if s in result:
                result[s] = count
        return result

    def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def delete(self, ticket: Ticket):
        self.db.delete(ticket)
        self.db.commit()

    def save(self):
        self.db.commit()
