"""Pydantic schemas：request / response 結構。

對外 API 用 camelCase（對齊前端 / Event Service 慣例）
對內 ORM 用 snake_case，由 from_model() 做轉換。
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import Transaction


# ============================================================================
# Request
# ============================================================================

class RegistrationCreateRequest(BaseModel):
    """POST /v1/transactions 的 body。

    eventId 必填；其他三個欄位若不給，由 service 層用 Account Service 的 autofill 補上。
    saveAutofill=True 表示希望把這次填的偏好存回 Account Service 當預設值
    （目前 Account Service 尚未提供對應 internal endpoint，router 會先忽略此 flag，
    詳見 router 內註解與 Phase 5 說明）。
    """
    model_config = ConfigDict(extra="forbid")

    eventId: str = Field(..., min_length=1, max_length=50)
    guestCount: int | None = Field(default=None, ge=0, le=10)
    dietType: Literal["veg", "non-veg", "none"] | None = None
    selfDriving: bool | None = None
    saveAutofill: bool = False


class RegistrationUpdateRequest(BaseModel):
    """PATCH /v1/transactions/{id} 的 body。所有欄位都是 optional，只更新有給的。"""
    model_config = ConfigDict(extra="forbid")

    guestCount: int | None = Field(default=None, ge=0, le=10)
    dietType: Literal["veg", "non-veg", "none"] | None = None
    selfDriving: bool | None = None


# ============================================================================
# Response
# ============================================================================

class RegistrationResponse(BaseModel):
    """單筆報名紀錄的對外表示。"""
    transactionId: str
    userId: str
    eventId: str
    status: str
    waitlistNumber: int | None
    guestCount: int
    dietType: str | None
    selfDriving: bool | None
    ticketId: str | None
    registeredAt: datetime
    cancelledAt: datetime | None
    updatedAt: datetime

    @classmethod
    def from_model(cls, tx: Transaction) -> "RegistrationResponse":
        return cls(
            transactionId=tx.transaction_id,
            userId=tx.user_id,
            eventId=tx.event_id,
            status=tx.status,
            waitlistNumber=tx.waitlist_number,
            guestCount=tx.guest_count,
            dietType=tx.diet_type,
            selfDriving=tx.self_driving,
            ticketId=tx.ticket_id,
            registeredAt=tx.registered_at,
            cancelledAt=tx.cancelled_at,
            updatedAt=tx.updated_at,
        )


class AutofillSchema(BaseModel):
    dietType: str | None
    selfDriving: bool | None


class EligibilityResponse(BaseModel):
    """GET /v1/events/{eventId}/eligibility 的回應。

    eligible=True 的情況下，前端可以接著開報名表單；reasonCode 可能是
    'WILL_BE_WAITLIST'（仍可報，但會進候補）
    eligible=False 的情況下，reasonCode/reasonMessage 解釋為什麼不能報。
    """
    eligible: bool
    reasonCode: str | None = None
    reasonMessage: str | None = None
    willBeWaitlist: bool = False
    autofill: AutofillSchema | None = None


class CancellationResponse(BaseModel):
    """DELETE /v1/transactions/{id} 的回應。

    若取消的是 confirmed 且有人在候補，promoted 會帶被升上來的那筆紀錄。
    前端可以用這個資訊提示「您的取消已釋出給 OOO」。
    """
    cancelled: RegistrationResponse
    promoted: RegistrationResponse | None = None