from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TicketCreateInternal(BaseModel):
    userId: str
    eventId: str
    transactionId: str


class TicketCheckin(BaseModel):
    latitude: float
    longitude: float


class TicketBase(BaseModel):
    ticketId: str
    eventId: str
    eventName: Optional[str] = None
    eventStartTime: Optional[datetime] = None
    status: str
    checkinAvailable: bool = False


class TicketDetail(TicketBase):
    userId: str
    eventEndTime: Optional[datetime] = None
    eventLocation: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    checkinRadiusMeters: Optional[int] = None
    qrPayload: str


class TicketSummary(BaseModel):
    used: int
    unused: int
    invalid: int


class EventTicketItem(BaseModel):
    ticketId: str
    userId: str
    username: Optional[str] = None
    status: str


class EventTicketsResponse(BaseModel):
    summary: TicketSummary
    tickets: List[EventTicketItem]
