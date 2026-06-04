from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict, AliasChoices
from datetime import datetime
from typing import List, Optional, Any, Union, Literal
from decimal import Decimal

# 狀態映射表
STATUS_MAP = {
    0: "not_open",
    1: "registering",
    2: "waitlist",
    3: "closed",
    4: "ended"
}

VALID_CATEGORIES = ("sport", "food", "travel", "culture", "family", "contest", "music")

# 反向映射表 (用於寫入)
REVERSE_STATUS_MAP = {v: k for k, v in STATUS_MAP.items()}

def normalize_status(value: Any) -> int:
    if isinstance(value, str):
        if value not in REVERSE_STATUS_MAP:
            raise ValueError(f"Invalid status string: {value}")
        return REVERSE_STATUS_MAP[value]
    if isinstance(value, int):
        if value not in STATUS_MAP:
            raise ValueError(f"Invalid status value: {value}")
        return value
    raise ValueError(f"Invalid status value: {value}")

class FAQSchema(BaseModel):
    question: str
    answer: str

class EventBase(BaseModel):
    name: str
    description: str
    location: str
    category: Literal["sport", "food", "travel", "culture", "family", "contest", "music"] | None = None
    
    guestAllowed: bool = Field(
        default=False, 
        validation_alias=AliasChoices("guestAllowed", "guest_allowed"),
        serialization_alias="guestAllowed"
    )
    ticketLimit: Optional[int] = Field(
        default=None, 
        validation_alias=AliasChoices("ticketLimit", "ticket_limit"),
        serialization_alias="ticketLimit"
    )
    remainingTickets: int = Field(
        default=0, 
        validation_alias=AliasChoices("remainingTickets", "remaining_tickets"),
        serialization_alias="remainingTickets"
    )
    cancellationDeadline: Optional[datetime] = Field(
        default=None, 
        validation_alias=AliasChoices("cancellationDeadline", "cancellation_deadline"),
        serialization_alias="cancellationDeadline"
    )
    
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    checkinRadiusMeters: Optional[Decimal] = Field(
        default=None, 
        validation_alias=AliasChoices("checkinRadiusMeters", "checkin_radius_meters"),
        serialization_alias="checkinRadiusMeters"
    )
    
    eventStartTime: datetime = Field(
        ..., 
        validation_alias=AliasChoices("eventStartTime", "event_start_time"),
        serialization_alias="eventStartTime"
    )
    eventEndTime: datetime = Field(
        ..., 
        validation_alias=AliasChoices("eventEndTime", "event_end_time"),
        serialization_alias="eventEndTime"
    )
    registrationStart: datetime = Field(
        ..., 
        validation_alias=AliasChoices("registrationStart", "registration_start"),
        serialization_alias="registrationStart"
    )
    registrationEnd: datetime = Field(
        ..., 
        validation_alias=AliasChoices("registrationEnd", "registration_end"),
        serialization_alias="registrationEnd"
    )
    
    faqs: Optional[List[FAQSchema]] = None
    status: Union[int, str] = 0 # 支援傳入 int 或 str
    isDraft: bool = Field(
        default=True, 
        validation_alias=AliasChoices("isDraft", "is_draft"),
        serialization_alias="isDraft"
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> int:
        return normalize_status(v)

class EventCreate(EventBase):
    @field_validator("eventEndTime", mode="after")
    @classmethod
    def check_event_times(cls, v: datetime, info: Any) -> datetime:
        if "eventStartTime" in info.data and v <= info.data["eventStartTime"]:
            raise ValueError("活動結束時間必須晚於開始時間")
        return v

    @field_validator("registrationEnd", mode="after")
    @classmethod
    def check_registration_times(cls, v: datetime, info: Any) -> datetime:
        if "registrationStart" in info.data and v <= info.data["registrationStart"]:
            raise ValueError("報名結束時間必須晚於報名開始時間")
        return v

class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category: Literal["sport", "food", "travel", "culture", "family", "contest", "music"] | None = None
    guestAllowed: Optional[bool] = Field(default=None, alias="guestAllowed")
    ticketLimit: Optional[int] = Field(default=None, alias="ticketLimit")
    remainingTickets: Optional[int] = Field(default=None, alias="remainingTickets")
    cancellationDeadline: Optional[datetime] = Field(default=None, alias="cancellationDeadline")
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    checkinRadiusMeters: Optional[Decimal] = Field(default=None, alias="checkinRadiusMeters")
    eventStartTime: Optional[datetime] = Field(default=None, alias="eventStartTime")
    eventEndTime: Optional[datetime] = Field(default=None, alias="eventEndTime")
    registrationStart: Optional[datetime] = Field(default=None, alias="registrationStart")
    registrationEnd: Optional[datetime] = Field(default=None, alias="registrationEnd")
    faqs: Optional[List[FAQSchema]] = None
    status: Optional[Union[int, str]] = None
    isDraft: Optional[bool] = Field(default=None, alias="isDraft")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        return normalize_status(v)

class BatchUpdateItem(EventUpdate):
    eventId: str = Field(..., alias="eventId")

class BatchUpdateSchema(BaseModel):
    updates: List[BatchUpdateItem]

class BatchCreateSchema(BaseModel):
    events: List[EventCreate] = Field(..., min_length=1, max_length=100)

class BatchQuerySchema(BaseModel):
    eventIds: List[str] = Field(..., min_length=1, max_length=200, alias="eventIds")

    model_config = ConfigDict(populate_by_name=True)

class BatchDeleteSchema(BaseModel):
    eventIds: List[str] = Field(..., min_length=1, max_length=100, alias="eventIds")

    model_config = ConfigDict(populate_by_name=True)

class EventResponse(EventBase):
    eventId: str = Field(
        ..., 
        validation_alias=AliasChoices("eventId", "event_id"),
        serialization_alias="eventId"
    )
    createdAt: datetime = Field(
        ..., 
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt"
    )
    updatedAt: Optional[datetime] = Field(
        default=None, 
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt"
    )
    category: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @field_serializer("status")
    def serialize_status(self, v: int) -> str:
        return STATUS_MAP.get(v, "unknown")

class SingleEventResponse(BaseModel):
    data: EventResponse

    model_config = ConfigDict(from_attributes=True)

class PaginatedEventResponse(BaseModel):
    data: List[EventResponse]
    pagination: dict

    model_config = ConfigDict(from_attributes=True)
