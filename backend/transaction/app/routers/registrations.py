"""GET /events/{eventId}/registrations — 後台查看活動報名詳情。

Roles: welfare_member、hr
回應格式對齊 docs/api-spec.txt：
  { "data": { "summary": {...}, "registrations": [...] }, "pagination": {...} }

username 補充說明：
  當 Account Service 的 registration-profile 回傳 username 後，
  _to_registration_item 會自動帶入；查不到時以 null 帶過，不阻斷整批。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, role_required
from app.core.external import AccountClient, ExternalServiceError, get_account_client
from app.models.transaction import Transaction
from app.services import transaction_service

router = APIRouter()

def _to_registration_item(tx: Transaction, account_client: AccountClient) -> dict:
    username = None
    try:
        profile = account_client.get_registration_profile(tx.user_id)
        username = profile.username
    except ExternalServiceError:
        pass

    return {
        "transactionId": tx.transaction_id,
        "userId": tx.user_id,
        "username": username,
        "status": tx.status,
        "waitlistNumber": tx.waitlist_number,
        "guestCount": tx.guest_count,
        "dietType": tx.diet_type,
        "selfDriving": tx.self_driving,
        "registeredAt": tx.registered_at.isoformat(),
    }

@router.get("/events/{event_id}/registrations", response_model=dict)
def list_event_registrations(
    event_id: str = Path(..., min_length=1, max_length=50),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(confirmed|waitlist|cancelled)$"),
    current_user: CurrentUser = Depends(role_required("welfare_member", "hr")),
    db: Session = Depends(get_db),
    account_client: AccountClient = Depends(get_account_client),
):
    items, total = transaction_service.list_event_registrations(
        event_id=event_id,
        status_filter=status,
        db=db,
        page=page,
        limit=limit,
    )
    summary = transaction_service.get_event_registration_summary(event_id=event_id, db=db)

    return {
        "data": {
            "summary": summary,
            "registrations": [_to_registration_item(tx, account_client) for tx in items],
        },
        "pagination": {"page": page, "limit": limit, "total": total},
    }