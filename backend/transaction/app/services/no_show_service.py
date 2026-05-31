"""No-Show 處罰 service。

呼叫流程：
  1. 從 Ticket Service 拿出該活動所有「狀態仍為 unused」的 ticket_id 清單
  2. 對應到本地的 transactions（status=confirmed），取出對應的 user_id
  3. 對每個 user 呼叫 Account Service `punish_user`（停權 30 天）

設計考量：
- 這個 function 是 idempotent 的（重複呼叫只會讓 punish_user 重置 unlockAt 為「現在+30天」）
- 不在 lock 下執行，因為跑的時點是「活動結束後」，沒有併發報名要保護
- 失敗的個別 user 不會中斷整批，會記在回傳的 errors 裡

Phase 4 只提供 service function，不接 scheduler。
未來的觸發方式可能是：
  - cron job：每天掃過去 24 小時結束的活動
  - 活動結束後 welfare_member 手動觸發
  - Pub/Sub event：event service 把 status 改成 ENDED 時發訊息
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.external import AccountClient, ExternalServiceError, TicketClient
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


@dataclass
class NoShowResult:
    event_id: str
    punished_user_ids: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)  # {ticketId, reason}
    errors: list[dict] = field(default_factory=list)   # {userId, error}


def punish_no_shows_for_event(
    *,
    event_id: str,
    db: Session,
    ticket_client: TicketClient,
    account_client: AccountClient,
) -> NoShowResult:
    result = NoShowResult(event_id=event_id)

    try:
        unused_ticket_ids = ticket_client.list_unused_tickets(event_id)
    except ExternalServiceError as exc:
        logger.error("Failed to fetch unused tickets for event %s: %s", event_id, exc)
        raise

    if not unused_ticket_ids:
        return result

    # 找出對應的 transaction（必須是 confirmed 且 ticket_id 還在；cancelled 的不算）
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.event_id == event_id,
            Transaction.ticket_id.in_(unused_ticket_ids),
            Transaction.status == "confirmed",
        )
        .all()
    )

    found_ticket_ids = {tx.ticket_id for tx in txs}
    for tkt in unused_ticket_ids:
        if tkt not in found_ticket_ids:
            result.skipped.append({"ticketId": tkt, "reason": "no matching confirmed transaction"})

    # 去重：同一 user 在同活動只算一次（理論上 partial unique 已避免，但 defensive）
    seen_users: set[str] = set()
    for tx in txs:
        if tx.user_id in seen_users:
            continue
        seen_users.add(tx.user_id)
        try:
            account_client.punish_user(tx.user_id)
            result.punished_user_ids.append(tx.user_id)
            logger.info(
                "Punished user %s for no-show at event %s (tx=%s ticket=%s)",
                tx.user_id, event_id, tx.transaction_id, tx.ticket_id,
            )
        except ExternalServiceError as exc:
            result.errors.append({"userId": tx.user_id, "error": str(exc)})
            logger.error("Failed to punish user %s: %s", tx.user_id, exc)

    return result