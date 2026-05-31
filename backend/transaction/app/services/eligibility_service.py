"""報名資格檢查。

獨立的 service，方便：
- GET /v1/events/{eventId}/eligibility 直接呼叫（前端 pre-check 用）
- 在報名 flow 內部呼叫（create_registration 內部會 re-check 一次）

回傳 EligibilityResult dataclass，不做任何 DB 寫入或 ticket 操作。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.external import (
    EVENT_STATUS_REGISTERING,
    EVENT_STATUS_WAITLIST,
    AccountClient,
    EventClient,
    EventInfo,
    ExternalNotFoundError,
    RegistrationProfile,
)
from app.models.transaction import ACTIVE_STATUSES, Transaction


# 所有可能的 reasonCode（供前端 i18n、測試對齊）
REASON_OK = None
REASON_USER_NOT_FOUND = "USER_NOT_FOUND"
REASON_FORBIDDEN_ROLE = "FORBIDDEN_ROLE"           # welfare_member / hr 不能報名
REASON_USER_LOCKED = "USER_LOCKED"                  # 被處罰中
REASON_EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
REASON_EVENT_DRAFT = "EVENT_DRAFT"                  # 還沒發佈
REASON_REGISTRATION_NOT_OPEN = "REGISTRATION_NOT_OPEN"
REASON_REGISTRATION_CLOSED = "REGISTRATION_CLOSED"  # 報名截止
REASON_EVENT_ENDED = "EVENT_ENDED"
REASON_ALREADY_REGISTERED = "ALREADY_REGISTERED"
REASON_WILL_BE_WAITLIST = "WILL_BE_WAITLIST"        # 仍可報，但會進候補


@dataclass
class EligibilityResult:
    eligible: bool
    reason_code: str | None
    reason_message: str | None
    will_be_waitlist: bool
    # 額外帶出，方便上游使用
    profile: RegistrationProfile | None = None
    event: EventInfo | None = None
    # 剩餘名額：有限制活動 = ticket_limit - confirmed；無限制活動 = None
    remaining_tickets: int | None = None


def check_eligibility(
    *,
    user_id: str,
    event_id: str,
    db: Session,
    account_client: AccountClient,
    event_client: EventClient,
    now: datetime | None = None,
) -> EligibilityResult:
    """檢查 user 是否能報名某 event。

    流程：
      1. 取 user profile：判斷 role 與 locked 狀態
      2. 取 event：判斷 draft、status、registration window
      3. 看 transactions 表：判斷有沒有 active 報名
      4. 若以上都過，看 capacity（限制活動且無剩餘 → will_be_waitlist=True）
    """
    now = now or datetime.now(timezone.utc)

    # === 1. User ===
    try:
        profile = account_client.get_registration_profile(user_id)
    except ExternalNotFoundError:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_USER_NOT_FOUND,
            reason_message="User does not exist",
            will_be_waitlist=False,
        )

    if profile.role != "employee":
        # 福委會、HR 不參與報名（依需求書「福委會成員預設不參與活動」）
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_FORBIDDEN_ROLE,
            reason_message=f"Role '{profile.role}' cannot register for events",
            will_be_waitlist=False,
            profile=profile,
        )

    if profile.is_locked:
        unlock_str = profile.unlock_at.isoformat() if profile.unlock_at else "unknown"
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_USER_LOCKED,
            reason_message=f"Account is locked until {unlock_str}",
            will_be_waitlist=False,
            profile=profile,
        )

    # === 2. Event ===
    try:
        event = event_client.get_event(event_id)
    except ExternalNotFoundError:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_EVENT_NOT_FOUND,
            reason_message="Event does not exist",
            will_be_waitlist=False,
            profile=profile,
        )

    if event.is_draft:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_EVENT_DRAFT,
            reason_message="Event is not yet published",
            will_be_waitlist=False,
            profile=profile,
            event=event,
        )

    # registration window 早於現在 → 還沒開
    if now < event.registration_start:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_REGISTRATION_NOT_OPEN,
            reason_message=f"Registration opens at {event.registration_start.isoformat()}",
            will_be_waitlist=False,
            profile=profile,
            event=event,
        )

    # registration window 晚於現在 → 已截止
    if now > event.registration_end:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_REGISTRATION_CLOSED,
            reason_message="Registration period has ended",
            will_be_waitlist=False,
            profile=profile,
            event=event,
        )

    # event status 還要再防一道（不只看時間，也看 event service 標記的狀態）
    # 只有 REGISTERING / WAITLIST 兩種狀態允許新增報名
    if event.status not in (EVENT_STATUS_REGISTERING, EVENT_STATUS_WAITLIST):
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_EVENT_ENDED,
            reason_message="Event is closed or ended",
            will_be_waitlist=False,
            profile=profile,
            event=event,
        )

    # === 3. 是否已報名 ===
    existing = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.event_id == event_id,
            Transaction.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )
    if existing is not None:
        return EligibilityResult(
            eligible=False,
            reason_code=REASON_ALREADY_REGISTERED,
            reason_message=(
                f"Already registered (status={existing.status}, "
                f"transactionId={existing.transaction_id})"
            ),
            will_be_waitlist=False,
            profile=profile,
            event=event,
        )

    # === 4. 容量檢查（決定 will_be_waitlist）===
    # 注意：這只是「預估」，正式報名 flow 內會在 advisory lock 下再 count 一次才算數
    will_be_waitlist = False
    remaining_tickets: int | None = None
    if event.has_capacity_limit:
        confirmed_count = (
            db.query(func.count(Transaction.transaction_id))
            .filter(
                Transaction.event_id == event_id,
                Transaction.status == "confirmed",
            )
            .scalar()
        )
        remaining_tickets = max(event.ticket_limit - confirmed_count, 0)
        if confirmed_count >= event.ticket_limit:
            will_be_waitlist = True

    return EligibilityResult(
        eligible=True,
        reason_code=REASON_WILL_BE_WAITLIST if will_be_waitlist else REASON_OK,
        reason_message="Will be added to waitlist" if will_be_waitlist else None,
        will_be_waitlist=will_be_waitlist,
        profile=profile,
        event=event,
        remaining_tickets=remaining_tickets,
    )