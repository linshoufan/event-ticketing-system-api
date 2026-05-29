"""報名 / 取消 / 修改 / 查詢的核心業務邏輯。

設計重點：
1. 併發控制用 PostgreSQL advisory lock，per-event scope
   → 不同活動互不阻塞，同活動的 capacity 決策序列化
2. Ticket Service 呼叫在 DB commit 之後（避免 distributed transaction）
   → 接受「commit 成功但 ticket 配發失敗」的小機率風險（mock 模式不會發生）
3. Cancel confirmed 時自動補位 waitlist（不開獨立 endpoint）
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import case, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.core.external import (
    AccountClient,
    EventClient,
    EventInfo,
    TicketClient,
)
from app.models.transaction import ACTIVE_STATUSES, Transaction, utcnow
from app.services import eligibility_service
from app.services.eligibility_service import EligibilityResult

logger = logging.getLogger(__name__)


# ============================================================================
# 內部 helpers
# ============================================================================

def _new_transaction_id() -> str:
    return str(uuid.uuid4())


def _acquire_event_lock(db: Session, event_id: str) -> None:
    """對 event_id 取得 transaction-scoped advisory lock。

    用 hashtext(event_id) 把任意字串 hash 成 int4，再配 namespace=0 組成
    (int4, int4) 形式的 advisory lock key。
    Lock 在 commit / rollback 時自動釋放。
    """
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:event_id), 0)"),
        {"event_id": event_id},
    )


def _count_confirmed(db: Session, event_id: str) -> int:
    return (
        db.query(func.count(Transaction.transaction_id))
        .filter(Transaction.event_id == event_id, Transaction.status == "confirmed")
        .scalar()
        or 0
    )


def _next_waitlist_number(db: Session, event_id: str) -> int:
    """這個 event 目前最大的 waitlist_number + 1；若無候補則 1。"""
    current_max = (
        db.query(func.max(Transaction.waitlist_number))
        .filter(Transaction.event_id == event_id, Transaction.status == "waitlist")
        .scalar()
    )
    return (current_max or 0) + 1


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def _ensure_owner_or_staff(tx: Transaction, current_user: CurrentUser) -> None:
    """報名紀錄只有本人 / welfare_member 能操作。"""
    if tx.user_id == current_user.user_id:
        return
    if current_user.role == "welfare_member":
        return
    raise _http_error(
        status.HTTP_403_FORBIDDEN,
        "FORBIDDEN",
        "You do not have permission to access this registration",
    )


def _apply_autofill(
    *,
    request_guest_count: int | None,
    request_diet_type: str | None,
    request_self_driving: bool | None,
    profile_diet_type: str | None,
    profile_self_driving: bool | None,
    event_has_capacity_limit: bool,
) -> tuple[int, str | None, bool | None]:
    """從 user profile 自動填入未提供的欄位，並套用親友規則。

    親友規則（依 api-spec.txt）：
    - 有票數限制的活動（ticketLimit 有值）→ 僅限本人，guestCount 固定為 0
    - 無票數限制的活動（ticketLimit 為 null）→ 可填親友人數，guestCount >= 0
    """
    diet = request_diet_type if request_diet_type is not None else profile_diet_type
    driving = request_self_driving if request_self_driving is not None else profile_self_driving

    if event_has_capacity_limit:
        guest = 0  # 限名額活動：固定 0，忽略使用者輸入
    else:
        guest = request_guest_count if request_guest_count is not None else 0

    return guest, diet, driving


def _raise_if_ineligible(elig: EligibilityResult) -> None:
    """eligibility 不通過時轉成符合 api-spec.txt 的 HTTPException。"""
    if elig.eligible:
        return

    # 帳號鎖定：api-spec 要求 409 ACCOUNT_LOCKED 並帶 unlockAt
    if elig.reason_code == "USER_LOCKED":
        unlock_at = None
        if elig.profile and elig.profile.unlock_at:
            unlock_at = elig.profile.unlock_at.isoformat()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ACCOUNT_LOCKED", "message": "Account is locked", "unlockAt": unlock_at},
        )

    code_map = {
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "EVENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "ALREADY_REGISTERED": status.HTTP_409_CONFLICT,
        "FORBIDDEN_ROLE": status.HTTP_403_FORBIDDEN,
    }
    http_status = code_map.get(elig.reason_code, status.HTTP_400_BAD_REQUEST)
    raise _http_error(
        http_status,
        elig.reason_code or "INELIGIBLE",
        elig.reason_message or "Not eligible to register",
    )


# ============================================================================
# Create registration（報名）
# ============================================================================

def create_registration(
    *,
    user_id: str,
    event_id: str,
    request_guest_count: int | None,
    request_diet_type: str | None,
    request_self_driving: bool | None,
    db: Session,
    account_client: AccountClient,
    event_client: EventClient,
    ticket_client: TicketClient,
) -> Transaction:
    """報名一場活動。回傳建立的 Transaction（已含 status 與可能的 ticket_id）。"""
    # === Step 1: eligibility check（在 lock 外做，較貴的部分先擋掉）===
    elig = eligibility_service.check_eligibility(
        user_id=user_id,
        event_id=event_id,
        db=db,
        account_client=account_client,
        event_client=event_client,
    )
    _raise_if_ineligible(elig)

    profile = elig.profile
    event = elig.event
    assert profile is not None and event is not None  # eligibility 通過必有

    # === Step 2: autofill + guest 規則 ===
    guest_count, diet_type, self_driving = _apply_autofill(
        request_guest_count=request_guest_count,
        request_diet_type=request_diet_type,
        request_self_driving=request_self_driving,
        profile_diet_type=profile.autofill_diet_type,
        profile_self_driving=profile.autofill_self_driving,
        event_has_capacity_limit=event.has_capacity_limit,
    )

    # === Step 3: 開 transaction + advisory lock ===
    try:
        _acquire_event_lock(db, event_id)

        # 在 lock 下再 count 一次（lock 外的 count 不算數）
        if event.has_capacity_limit:
            confirmed_now = _count_confirmed(db, event_id)
            if confirmed_now < event.ticket_limit:
                tx_status = "confirmed"
                waitlist_number = None
            else:
                tx_status = "waitlist"
                waitlist_number = _next_waitlist_number(db, event_id)
        else:
            tx_status = "confirmed"
            waitlist_number = None

        tx = Transaction(
            transaction_id=_new_transaction_id(),
            user_id=user_id,
            event_id=event_id,
            status=tx_status,
            waitlist_number=waitlist_number,
            guest_count=guest_count,
            diet_type=diet_type,
            self_driving=self_driving,
            ticket_id=None,  # 等 commit 後再 issue
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
    except IntegrityError as exc:
        # 唯一觸發點：partial unique index（短時間內重複報名的 race）
        db.rollback()
        # eligibility 已經擋過正常情況，能走到這通常是兩個 request 賽跑
        raise _http_error(
            status.HTTP_409_CONFLICT,
            "ALREADY_REGISTERED",
            "An active registration for this event already exists",
        ) from exc

    # === Step 4: 配發 ticket（confirmed 才需要）===
    if tx_status == "confirmed":
        _issue_and_attach_ticket(tx=tx, db=db, ticket_client=ticket_client)

    return tx


def _issue_and_attach_ticket(
    *,
    tx: Transaction,
    db: Session,
    ticket_client: TicketClient,
) -> None:
    """配發 ticket 並寫回 transaction.ticket_id。失敗只 log 不丟錯（接受小機率不一致）。"""
    try:
        ticket_id = ticket_client.issue_ticket(
            user_id=tx.user_id,
            event_id=tx.event_id,
            transaction_id=tx.transaction_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to issue ticket for tx=%s user=%s event=%s: %s",
            tx.transaction_id, tx.user_id, tx.event_id, exc,
        )
        return

    tx.ticket_id = ticket_id
    tx.updated_at = utcnow()
    db.commit()
    db.refresh(tx)


# ============================================================================
# Cancel registration（取消，含補位）
# ============================================================================

def cancel_registration(
    *,
    transaction_id: str,
    current_user: CurrentUser,
    db: Session,
    event_client: EventClient,
    ticket_client: TicketClient,
) -> tuple[Transaction, Transaction | None]:
    """取消報名。回傳 (cancelled, promoted_or_None)。

    confirmed → cancelled：必須在 cancellation_deadline 之前。同時觸發 waitlist 補位。
    waitlist → cancelled：永遠可以。
    """
    # === Step 1: 取出 transaction + 權限 check ===
    tx = db.get(Transaction, transaction_id)
    if tx is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "TRANSACTION_NOT_FOUND", "Registration not found")

    _ensure_owner_or_staff(tx, current_user)

    if tx.status == "cancelled":
        raise _http_error(
            status.HTTP_409_CONFLICT,
            "ALREADY_CANCELLED",
            "Registration was already cancelled",
        )

    # === Step 2: 取活動資訊 + cancellation deadline 檢查 ===
    event = event_client.get_event(tx.event_id)

    if tx.status == "confirmed":
        # 規則：cancellation_deadline = NULL 表示「不可取消」
        if event.cancellation_deadline is None:
            raise _http_error(
                status.HTTP_400_BAD_REQUEST,
                "NOT_CANCELLABLE",
                "This event does not allow cancellation",
            )
        if datetime.now(timezone.utc) > event.cancellation_deadline:
            raise _http_error(
                status.HTTP_409_CONFLICT,
                "PAST_CANCELLATION_DEADLINE",
                f"Cancellation deadline ({event.cancellation_deadline.isoformat()}) has passed",
            )

    # === Step 3: lock + 標記 cancelled + 補位 ===
    old_status = tx.status
    old_ticket_id = tx.ticket_id
    promoted_tx: Transaction | None = None

    _acquire_event_lock(db, tx.event_id)

    tx.status = "cancelled"
    tx.cancelled_at = utcnow()
    tx.ticket_id = None  # confirmed 才會有 ticket_id；清掉避免之後查詢時誤用
    tx.updated_at = utcnow()

    if old_status == "confirmed":
        promoted_tx = _promote_next_waitlist(db, tx.event_id)

    db.commit()
    db.refresh(tx)
    if promoted_tx is not None:
        db.refresh(promoted_tx)

    # === Step 4: 對外做 ticket 操作（void 舊的 + issue 新的）===
    if old_ticket_id:
        try:
            ticket_client.void_ticket(old_ticket_id)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to void ticket %s for cancelled tx=%s: %s",
                old_ticket_id, tx.transaction_id, exc,
            )

    if promoted_tx is not None:
        _issue_and_attach_ticket(tx=promoted_tx, db=db, ticket_client=ticket_client)

    return tx, promoted_tx


def _promote_next_waitlist(db: Session, event_id: str) -> Transaction | None:
    """找出 waitlist_number 最小的 waitlist transaction，升為 confirmed。
    回傳該 transaction（已修改但尚未發 ticket），或 None。
    """
    next_tx = (
        db.query(Transaction)
        .filter(
            Transaction.event_id == event_id,
            Transaction.status == "waitlist",
        )
        .order_by(Transaction.waitlist_number.asc())
        .first()
    )
    if next_tx is None:
        return None

    next_tx.status = "confirmed"
    next_tx.waitlist_number = None
    next_tx.updated_at = utcnow()
    return next_tx


# ============================================================================
# Update registration（修改 guest_count 等）
# ============================================================================

def update_registration(
    *,
    transaction_id: str,
    current_user: CurrentUser,
    guest_count: int | None,
    diet_type: str | None,
    self_driving: bool | None,
    db: Session,
    event_client: EventClient,
) -> Transaction:
    """修改報名資料（不能改 status / ticket_id）。"""
    tx = db.get(Transaction, transaction_id)
    if tx is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "TRANSACTION_NOT_FOUND", "Registration not found")

    _ensure_owner_or_staff(tx, current_user)

    if tx.status == "cancelled":
        raise _http_error(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_STATE",
            "Cannot update a cancelled registration",
        )

    if guest_count is not None:
        event = event_client.get_event(tx.event_id)
        # 依 api-spec：guestCount 僅限不限名額的活動可修改
        if event.has_capacity_limit:
            if guest_count > 0:
                raise _http_error(
                    status.HTTP_400_BAD_REQUEST,
                    "GUEST_NOT_ALLOWED",
                    "Limited-capacity events do not allow guests",
                )
            # guest_count == 0 對限名額活動是 no-op，直接略過
        else:
            tx.guest_count = guest_count
    if diet_type is not None:
        tx.diet_type = diet_type
    if self_driving is not None:
        tx.self_driving = self_driving

    tx.updated_at = utcnow()
    db.commit()
    db.refresh(tx)
    return tx


# ============================================================================
# Query
# ============================================================================

def get_registration(
    *,
    transaction_id: str,
    current_user: CurrentUser,
    db: Session,
) -> Transaction:
    tx = db.get(Transaction, transaction_id)
    if tx is None:
        raise _http_error(status.HTTP_404_NOT_FOUND, "TRANSACTION_NOT_FOUND", "Registration not found")
    _ensure_owner_or_staff(tx, current_user)
    return tx


def list_user_registrations(
    *,
    user_id: str,
    status_filter: str | None,
    db: Session,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Transaction], int]:
    """使用者查自己的報名紀錄（分頁）。回傳 (items, total)。"""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if status_filter is not None:
        query = query.filter(Transaction.status == status_filter)
    total = query.count()
    items = (
        query.order_by(Transaction.registered_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def list_event_registrations(
    *,
    event_id: str,
    status_filter: str | None,
    db: Session,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Transaction], int]:
    """供 welfare_member / hr 後台查看（分頁）。回傳 (items, total)。

    排序：confirmed 在前（依報名時間），再 waitlist（依 waitlist_number），再 cancelled。
    """
    query = db.query(Transaction).filter(Transaction.event_id == event_id)
    if status_filter is not None:
        query = query.filter(Transaction.status == status_filter)
    total = query.count()
    # 自訂 status 順序（SQLAlchemy 2.0 的 case 寫法）
    status_order = case(
        (Transaction.status == "confirmed", 0),
        (Transaction.status == "waitlist", 1),
        (Transaction.status == "cancelled", 2),
        else_=3,
    )
    items = (
        query.order_by(
            status_order,
            Transaction.waitlist_number.asc().nullsfirst(),
            Transaction.registered_at.asc(),
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return items, total


def get_event_registration_summary(*, event_id: str, db: Session) -> dict:
    """回傳某活動各狀態的計數，供後台 summary 使用。"""
    rows = (
        db.query(Transaction.status, func.count(Transaction.transaction_id))
        .filter(Transaction.event_id == event_id)
        .group_by(Transaction.status)
        .all()
    )
    counts = {status_value: count for status_value, count in rows}
    return {
        "totalConfirmed": counts.get("confirmed", 0),
        "totalWaitlist": counts.get("waitlist", 0),
        "totalCancelled": counts.get("cancelled", 0),
    }