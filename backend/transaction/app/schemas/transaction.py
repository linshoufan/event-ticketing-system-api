"""Pydantic schemas：request / response 結構。

對外 API 用 camelCase。所有回應都包在 {"data": ...}（列表再加 "pagination"）的
envelope 裡，因此 response model 以 envelope 為單位定義，直接掛在 router 的 response_model。
錯誤回應由 main.py 的 exception handler 處理，不走這些 model。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Request 
class RegistrationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eventId: str = Field(..., min_length=1, max_length=50)
    guestCount: int | None = Field(default=None, ge=0, le=10)
    dietType: Literal["veg", "non-veg", "none"] | None = None
    selfDriving: bool | None = None
    saveAutofill: bool = False


class RegistrationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guestCount: int | None = Field(default=None, ge=0, le=10)
    dietType: Literal["veg", "non-veg", "none"] | None = None
    selfDriving: bool | None = None


# 共用 
class Pagination(BaseModel):
    page: int
    limit: int
    total: int

# POST /transactions 
class RegistrationCreateResult(BaseModel):
    transactionId: str
    status: str
    waitlistNumber: int | None = None
    ticketId: str | None = None
    guestCount: int | None = None 
    registeredAt: str


class RegistrationCreateResponse(BaseModel):
    data: RegistrationCreateResult


# GET /transactions、GET /transactions/{id} 
class TransactionItem(BaseModel):
    transactionId: str
    eventId: str
    eventName: str | None = None
    eventStartTime: str | None = None
    status: str
    waitlistNumber: int | None = None
    guestCount: int
    dietType: str | None = None
    selfDriving: bool | None = None
    registeredAt: str
    ticketId: str | None = None

class TransactionDetailResponse(BaseModel):
    data: TransactionItem

class TransactionListResponse(BaseModel):
    data: list[TransactionItem]
    pagination: Pagination


# PATCH /transactions/{id} 
class UpdateResult(BaseModel):
    updated: bool
    updatedAt: str

class UpdateResponse(BaseModel):
    data: UpdateResult


# DELETE /transactions/{id} 
class PromotedInfo(BaseModel):
    transactionId: str
    userId: str
    status: str
    ticketId: str | None = None

class CancelResult(BaseModel):
    cancelled: bool
    promoted: PromotedInfo | None = None

class CancelResponse(BaseModel):
    data: CancelResult


# GET /events/{id}/eligibility 
class EligibilityPayload(BaseModel):
    eligible: bool
    reason: str | None = None
    remainingTickets: int | None = None
    isWaitlist: bool = False
    unlockAt: str | None = None

class EligibilityResponse(BaseModel):
    data: EligibilityPayload


# GET /events/{id}/registrations（後台）
class RegistrationSummary(BaseModel):
    totalConfirmed: int
    totalWaitlist: int
    totalCancelled: int

class EventRegistrationItem(BaseModel):
    transactionId: str
    userId: str
    username: str | None = None
    status: str
    waitlistNumber: int | None = None
    guestCount: int
    dietType: str | None = None
    selfDriving: bool | None = None
    registeredAt: str

class EventRegistrationsData(BaseModel):
    summary: RegistrationSummary
    registrations: list[EventRegistrationItem]

class EventRegistrationsResponse(BaseModel):
    data: EventRegistrationsData
    pagination: Pagination