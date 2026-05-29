"""GET /events/{eventId}/eligibility — 檢查當前使用者報名資格。

回應格式對齊 docs/api-spec.txt：
  { "data": { "eligible", "reason", "remainingTickets", "isWaitlist", "unlockAt"? } }
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, role_required
from app.core.external import (
    AccountClient,
    EventClient,
    get_account_client,
    get_event_client,
)
from app.core.response import success
from app.services import eligibility_service

router = APIRouter()


# 把內部 reason_code 對應成 api-spec 的 reason 字串
_REASON_MAP = {
    "USER_LOCKED": "LOCKED",
    "ALREADY_REGISTERED": "ALREADY_REGISTERED",
    "WILL_BE_WAITLIST": "NO_TICKETS",
    # 其他（draft / 未開放 / 截止 / 結束 / 角色）直接沿用內部 code
}


@router.get("/events/{event_id}/eligibility", response_model=dict)
def check_eligibility(
    event_id: str = Path(..., min_length=1, max_length=50),
    current_user: CurrentUser = Depends(role_required("employee")),
    db: Session = Depends(get_db),
    account_client: AccountClient = Depends(get_account_client),
    event_client: EventClient = Depends(get_event_client),
):
    result = eligibility_service.check_eligibility(
        user_id=current_user.user_id,
        event_id=event_id,
        db=db,
        account_client=account_client,
        event_client=event_client,
    )

    reason = None if result.eligible and not result.will_be_waitlist else _REASON_MAP.get(
        result.reason_code, result.reason_code
    )

    payload = {
        "eligible": result.eligible,
        "reason": reason,
        "remainingTickets": result.remaining_tickets,  # 無限制活動為 null
        "isWaitlist": result.will_be_waitlist,
    }

    # 帳號鎖定時附上解鎖時間
    if result.reason_code == "USER_LOCKED" and result.profile and result.profile.unlock_at:
        payload["unlockAt"] = result.profile.unlock_at.isoformat()

    return success(payload)
