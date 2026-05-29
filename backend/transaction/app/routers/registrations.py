"""GET /events/{eventId}/registrations — 後台查看活動報名詳情。

Roles: welfare_member、hr
回應格式對齊 docs/api-spec.txt：
  { "data": { "summary": {...}, "registrations": [...] }, "pagination": {...} }

備註（username 缺口）：
  api-spec 的 registrations 項目含 username，但 Account Service 目前的 internal
  endpoint（registration-profile）不回傳 username。在 Account 端提供 username 查詢
  （或在 registration-profile 加上 username 欄位）之前，這裡先回傳 username=null。
  屆時只要在 _to_registration_item 補上查詢即可，其餘不需更動。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, role_required
from app.core.response import success
from app.models.transaction import Transaction
from app.services import transaction_service

router = APIRouter()


def _to_registration_item(tx: Transaction) -> dict:
    return {
        "transactionId": tx.transaction_id,
        "userId": tx.user_id,
        "username": None,  # 見檔頭備註：待 Account Service 提供 username 查詢
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
            "registrations": [_to_registration_item(tx) for tx in items],
        },
        "pagination": {"page": page, "limit": limit, "total": total},
    }
