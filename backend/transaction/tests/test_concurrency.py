"""併發報名測試：驗證 advisory lock 能避免超賣。

用多執行緒同時對「只剩 1 個名額」的活動報名，確認：
- 恰好 1 人 confirmed，其餘全部 waitlist（不會超賣成 2 人 confirmed）
- 不會因為 partial unique index 衝突而炸掉（每個 user 不同）

注意：這個測試直接呼叫 service 層（不透過 TestClient），因為要用各自獨立的
DB session 來模擬真正的並行連線。
"""
import threading
from datetime import timedelta

from app.core.database import SessionLocal
from app.models.transaction import Transaction
from app.services import transaction_service
from tests.conftest import NOW, FakeAccountClient, FakeEventClient, FakeTicketClient


def test_concurrent_registration_no_oversell(db):
    """20 人同時搶 1 個名額 → 只有 1 人 confirmed。"""
    # 清空（db fixture 已清，但保險起見）
    db.query(Transaction).delete()
    db.commit()

    n_users = 20
    ticket_limit = 1
    event_id = "e-race"

    acc = FakeAccountClient()
    evt = FakeEventClient()
    evt.set_event(event_id, ticket_limit=ticket_limit)
    for i in range(n_users):
        acc.set_profile(f"u-{i}")

    results: list[str] = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(n_users)

    def worker(user_id: str):
        # 每個 thread 自己的 session（模擬獨立連線）
        session = SessionLocal()
        tkt = FakeTicketClient()
        try:
            barrier.wait()  # 所有 thread 同時開跑
            tx = transaction_service.create_registration(
                user_id=user_id, event_id=event_id,
                request_guest_count=None, request_diet_type=None, request_self_driving=None,
                db=session, account_client=acc, event_client=evt, ticket_client=tkt,
            )
            with results_lock:
                results.append(tx.status)
        except Exception as exc:  # noqa: BLE001
            with results_lock:
                results.append(f"error:{exc}")
        finally:
            session.close()

    threads = [threading.Thread(target=worker, args=(f"u-{i}",)) for i in range(n_users)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    confirmed = [r for r in results if r == "confirmed"]
    waitlist = [r for r in results if r == "waitlist"]
    errors = [r for r in results if r.startswith("error")]

    assert len(errors) == 0, f"unexpected errors: {errors}"
    assert len(confirmed) == ticket_limit, f"oversell! confirmed={len(confirmed)}"
    assert len(waitlist) == n_users - ticket_limit

    # DB 真實狀態也要對
    db_confirmed = (
        db.query(Transaction)
        .filter(Transaction.event_id == event_id, Transaction.status == "confirmed")
        .count()
    )
    assert db_confirmed == ticket_limit

    # 清理
    db.query(Transaction).delete()
    db.commit()


def test_concurrent_cancel_and_register(db):
    """同時有人取消、有人報名，最終 confirmed 數不超過上限。"""
    db.query(Transaction).delete()
    db.commit()

    event_id = "e-mix"
    ticket_limit = 3
    acc = FakeAccountClient()
    evt = FakeEventClient()
    evt.set_event(event_id, ticket_limit=ticket_limit,
                  cancellation_deadline=NOW + timedelta(days=3))

    # 先塞滿 3 個 confirmed + 5 個 waitlist
    setup_session = SessionLocal()
    tkt = FakeTicketClient()
    confirmed_ids = []
    for i in range(8):
        acc.set_profile(f"u-{i}")
        tx = transaction_service.create_registration(
            user_id=f"u-{i}", event_id=event_id,
            request_guest_count=None, request_diet_type=None, request_self_driving=None,
            db=setup_session, account_client=acc, event_client=evt, ticket_client=tkt,
        )
        if tx.status == "confirmed":
            confirmed_ids.append(tx.transaction_id)
    setup_session.close()

    from app.core.dependencies import CurrentUser

    def canceller(tx_id, user_id):
        s = SessionLocal()
        try:
            transaction_service.cancel_registration(
                transaction_id=tx_id,
                current_user=CurrentUser(user_id=user_id, role="employee"),
                db=s, event_client=evt, ticket_client=FakeTicketClient(),
            )
        finally:
            s.close()

    # 同時取消 2 個 confirmed（會觸發補位）
    threads = [
        threading.Thread(target=canceller, args=(confirmed_ids[0], "u-0")),
        threading.Thread(target=canceller, args=(confirmed_ids[1], "u-1")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 取消 2 個 → 補 2 個，confirmed 應該維持 3（沒超賣、沒少補）
    final_confirmed = (
        db.query(Transaction)
        .filter(Transaction.event_id == event_id, Transaction.status == "confirmed")
        .count()
    )
    assert final_confirmed == ticket_limit, f"expected {ticket_limit}, got {final_confirmed}"

    db.query(Transaction).delete()
    db.commit()