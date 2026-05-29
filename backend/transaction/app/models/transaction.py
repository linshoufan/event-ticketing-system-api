from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# 可選值列舉（給 service / schema 層 import 用）
VALID_STATUSES = ("confirmed", "waitlist", "cancelled")
VALID_DIET_TYPES = ("veg", "non-veg", "none")

# 「仍佔用名額」的狀態 — service 層判斷重複報名、釋出名額時都會用到
ACTIVE_STATUSES = ("confirmed", "waitlist")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    """報名紀錄。

    一個 row = 一次報名動作。
    取消報名不會刪 row，而是把 status 改成 'cancelled'，保留審計軌跡。
    No-Show 偵測也會掃這張表（看活動結束時 ticket 仍未 check-in 的 confirmed 報名）。
    """

    __tablename__ = "transactions"
    __table_args__ = (
        # DB 層守住 status 與 diet_type 的可選值
        CheckConstraint(
            "status IN ('confirmed','waitlist','cancelled')",
            name="check_transaction_status",
        ),
        CheckConstraint(
            "diet_type IN ('veg','non-veg','none')",
            name="check_transaction_diet_type",
        ),
        CheckConstraint("guest_count >= 0", name="check_transaction_guest_count_non_negative"),

        # ⚠️ 關鍵約束：同一個 user 對同一個 event 不能有 2 筆 active 紀錄
        # 但允許重複報名再取消再報（cancelled 不在 partial index 範圍內）
        Index(
            "uq_active_registration",
            "user_id",
            "event_id",
            unique=True,
            postgresql_where="status IN ('confirmed','waitlist')",
        ),

        # 後台查詢「某活動的報名者」會走這個 index
        Index("ix_transactions_event_status", "event_id", "status"),

        # 使用者查「我的報名紀錄」走這個 index
        Index("ix_transactions_user_id", "user_id"),
    )

    # === 主鍵 ===
    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # === 外部 reference（不設 FK，因為跨服務）===
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # === 狀態 ===
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    waitlist_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # === 報名時填入的內容（autofill 帶進來的或使用者改的）===
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    diet_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    self_driving: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # === 配發的票券 ===
    # 只有 confirmed 才會有；waitlist 補位升為 confirmed 時才會填入
    ticket_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # === 時間戳 ===
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )