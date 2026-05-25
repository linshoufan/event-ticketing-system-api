from datetime import datetime

from pydantic import BaseModel


class CheckinRequest(BaseModel):
    latitude: float
    longitude: float


class CheckedInResponse(BaseModel):
    checkedIn: bool
    checkedInAt: datetime


class TicketListItemResponse(BaseModel):
    ticketId: str
    eventId: str
    eventName: str
    eventStartTime: datetime
    eventLocation: str
    status: str
    checkinAvailable: bool


class TicketDetailResponse(BaseModel):
    ticketId: str
    userId: str
    eventId: str
    eventName: str
    eventStartTime: datetime
    eventEndTime: datetime
    eventLocation: str
    latitude: float
    longitude: float
    checkinRadiusMeters: int
    status: str
    checkinAvailable: bool
    qrPayload: str
