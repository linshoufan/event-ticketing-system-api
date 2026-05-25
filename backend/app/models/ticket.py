from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

# mock first, will be replaced by the actual event service in the future
class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    checkin_radius_meters: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    event_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_ticket_event_user"),)

    ticket_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    event: Mapped[Event] = relationship(back_populates="tickets")
