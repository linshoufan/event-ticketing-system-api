"""Transaction Service 自己對外暴露的 internal endpoint。

目前只有一個：觸發某活動的 No-Show 處罰。
需帶 X-Internal-Key（供 cron job / Cloud Scheduler / welfare_member 後台呼叫）。

未來可由以下任一方式觸發：
- Cloud Scheduler 每天打這個 endpoint，掃過去結束的活動
- Event Service 在把活動狀態改成 ENDED 時，透過 Pub/Sub 通知後再呼叫
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import verify_internal_key
from app.core.external import (
    AccountClient,
    TicketClient,
    get_account_client,
    get_ticket_client,
)
from app.core.response import success
from app.services import no_show_service

router = APIRouter()


@router.post("/internal/events/{event_id}/punish-no-shows", response_model=dict)
def punish_no_shows(
    event_id: str = Path(..., min_length=1, max_length=50),
    db: Session = Depends(get_db),
    account_client: AccountClient = Depends(get_account_client),
    ticket_client: TicketClient = Depends(get_ticket_client),
    _: None = Depends(verify_internal_key),
):
    result = no_show_service.punish_no_shows_for_event(
        event_id=event_id,
        db=db,
        ticket_client=ticket_client,
        account_client=account_client,
    )
    return success({
        "eventId": result.event_id,
        "punishedUserIds": result.punished_user_ids,
        "punishedCount": len(result.punished_user_ids),
        "skipped": result.skipped,
        "errors": result.errors,
    })
