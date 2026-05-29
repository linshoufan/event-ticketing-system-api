"""/transactions 相關 endpoints（報名管理對外 API）。

對齊 docs/api-spec.txt：
- GET    /transactions            列出自己的報名（含 eventName / eventStartTime）
- GET    /transactions/{id}       查單筆
- POST   /transactions            報名
- PATCH  /transactions/{id}       修改報名細節
- DELETE /transactions/{id}       取消報名
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, role_required
from app.core.external import (
    AccountClient,
    EventClient,
    ExternalServiceError,
    TicketClient,
    get_account_client,
    get_event_client,
    get_ticket_client,
)
from app.core.response import paginated, success
from app.models.transaction import Transaction
from app.schemas.transaction import (
    RegistrationCreateRequest,
    RegistrationUpdateRequest,
)
from app.services import transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# 內部 helper：把單筆 Transaction 轉成 api-spec 的清單項目（含活動資訊）
# ---------------------------------------------------------------------------
def _enrich_with_event(tx: Transaction, event_client: EventClient) -> dict:
    """補上 eventName / eventStartTime；活動查不到時以 null 帶過，不讓整批失敗。"""
    event_name = None
    event_start = None
    try:
        event = event_client.get_event(tx.event_id)
        event_name = event.name
        event_start = event.event_start_time.isoformat() if event.event_start_time else None
    except ExternalServiceError as exc:
        logger.warning("Failed to enrich event %s: %s", tx.event_id, exc)

    return {
        "transactionId": tx.transaction_id,
        "eventId": tx.event_id,
        "eventName": event_name,
        "eventStartTime": event_start,
        "status": tx.status,
        "waitlistNumber": tx.waitlist_number,
        "guestCount": tx.guest_count,
        "dietType": tx.diet_type,
        "selfDriving": tx.self_driving,
        "registeredAt": tx.registered_at.isoformat(),
        "ticketId": tx.ticket_id,
    }


# ---------------------------------------------------------------------------
# GET /transactions — 查自己的報名紀錄
# ---------------------------------------------------------------------------
@router.get("/transactions", response_model=dict)
def list_my_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(confirmed|waitlist|cancelled)$"),
    current_user: CurrentUser = Depends(role_required("employee")),
    db: Session = Depends(get_db),
    event_client: EventClient = Depends(get_event_client),
):
    items, total = transaction_service.list_user_registrations(
        user_id=current_user.user_id,
        status_filter=status,
        db=db,
        page=page,
        limit=limit,
    )
    data = [_enrich_with_event(tx, event_client) for tx in items]
    return paginated(data=data, page=page, limit=limit, total=total)


# ---------------------------------------------------------------------------
# GET /transactions/{id} — 查單筆（本人或 welfare_member）
# ---------------------------------------------------------------------------
@router.get("/transactions/{transaction_id}", response_model=dict)
def get_transaction(
    transaction_id: str = Path(...),
    current_user: CurrentUser = Depends(role_required("employee", "welfare_member")),
    db: Session = Depends(get_db),
    event_client: EventClient = Depends(get_event_client),
):
    tx = transaction_service.get_registration(
        transaction_id=transaction_id, current_user=current_user, db=db
    )
    return success(_enrich_with_event(tx, event_client))


# ---------------------------------------------------------------------------
# POST /transactions — 報名
# ---------------------------------------------------------------------------
@router.post("/transactions", response_model=dict, status_code=201)
def create_transaction(
    body: RegistrationCreateRequest,
    current_user: CurrentUser = Depends(role_required("employee")),
    db: Session = Depends(get_db),
    account_client: AccountClient = Depends(get_account_client),
    event_client: EventClient = Depends(get_event_client),
    ticket_client: TicketClient = Depends(get_ticket_client),
):
    tx = transaction_service.create_registration(
        user_id=current_user.user_id,
        event_id=body.eventId,
        request_guest_count=body.guestCount,
        request_diet_type=body.dietType,
        request_self_driving=body.selfDriving,
        db=db,
        account_client=account_client,
        event_client=event_client,
        ticket_client=ticket_client,
    )

    # saveAutofill：api-spec 要求把這次填的偏好存回帳戶當預設。
    # Account Service 目前沒有對應的 internal endpoint，故先記 log，不阻擋報名。
    # 待 Account 端提供 PATCH internal autofill endpoint 後再接上。
    if body.saveAutofill:
        logger.info(
            "saveAutofill requested by user=%s (diet=%s, driving=%s) — "
            "skipped: Account Service internal autofill endpoint not available yet",
            current_user.user_id, body.dietType, body.selfDriving,
        )

    return success({
        "transactionId": tx.transaction_id,
        "status": tx.status,
        "waitlistNumber": tx.waitlist_number,
        "ticketId": tx.ticket_id,
        "registeredAt": tx.registered_at.isoformat(),
    })


# ---------------------------------------------------------------------------
# PATCH /transactions/{id} — 修改報名細節
# ---------------------------------------------------------------------------
@router.patch("/transactions/{transaction_id}", response_model=dict)
def update_transaction(
    body: RegistrationUpdateRequest,
    transaction_id: str = Path(...),
    current_user: CurrentUser = Depends(role_required("employee")),
    db: Session = Depends(get_db),
    event_client: EventClient = Depends(get_event_client),
):
    tx = transaction_service.update_registration(
        transaction_id=transaction_id,
        current_user=current_user,
        guest_count=body.guestCount,
        diet_type=body.dietType,
        self_driving=body.selfDriving,
        db=db,
        event_client=event_client,
    )
    return success({"updated": True, "updatedAt": tx.updated_at.isoformat()})


# ---------------------------------------------------------------------------
# DELETE /transactions/{id} — 取消報名（含自動補位）
# ---------------------------------------------------------------------------
@router.delete("/transactions/{transaction_id}", response_model=dict)
def cancel_transaction(
    transaction_id: str = Path(...),
    current_user: CurrentUser = Depends(role_required("employee")),
    db: Session = Depends(get_db),
    event_client: EventClient = Depends(get_event_client),
    ticket_client: TicketClient = Depends(get_ticket_client),
):
    _, promoted = transaction_service.cancel_registration(
        transaction_id=transaction_id,
        current_user=current_user,
        db=db,
        event_client=event_client,
        ticket_client=ticket_client,
    )
    data = {"cancelled": True}
    # 額外回傳補位資訊（api-spec 沒要求，但對前端有用，放在 data 內不破壞契約）
    if promoted is not None:
        data["promoted"] = {
            "transactionId": promoted.transaction_id,
            "userId": promoted.user_id,
            "status": promoted.status,
            "ticketId": promoted.ticket_id,
        }
    return success(data)
