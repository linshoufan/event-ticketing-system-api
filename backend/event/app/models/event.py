from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Numeric, JSON
from sqlalchemy.sql import func
from ..core.database import Base

class Event(Base):
    __tablename__ = "events"

    event_id = Column("event_id", String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    category = Column(String(50), index=True, nullable=True)
    guest_allowed = Column("guest_allowed", Boolean, default=False, nullable=False)
    ticket_limit = Column("ticket_limit", Integer, nullable=True)
    remaining_tickets = Column("remaining_tickets", Integer, default=0, nullable=False)
    cancellation_deadline = Column("cancellation_deadline", DateTime(timezone=True), nullable=True)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    checkin_radius_meters = Column("checkin_radius_meters", Numeric(9, 6), nullable=True)
    event_start_time = Column("event_start_time", DateTime(timezone=True), nullable=False)
    event_end_time = Column("event_end_time", DateTime(timezone=True), nullable=False)
    registration_start = Column("registration_start", DateTime(timezone=True), nullable=False)
    registration_end = Column("registration_end", DateTime(timezone=True), nullable=False)
    faqs = Column(JSON, default=[], nullable=True)
    status = Column(Integer, default=0, nullable=False)
    is_draft = Column("is_draft", Boolean, default=True, nullable=False)
    created_at = Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column("updated_at", DateTime(timezone=True), onupdate=func.now(), nullable=True)
