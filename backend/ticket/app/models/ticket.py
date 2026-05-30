import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True, default=lambda: f"tk_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    transaction_id = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default="unused")  # unused, used, invalid
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    checked_in_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "ticketId": self.ticket_id,
            "userId": self.user_id,
            "eventId": self.event_id,
            "transactionId": self.transaction_id,
            "status": self.status,
            "issuedAt": self.issued_at.isoformat() if self.issued_at else None,
            "checkedInAt": self.checked_in_at.isoformat() if self.checked_in_at else None,
        }
