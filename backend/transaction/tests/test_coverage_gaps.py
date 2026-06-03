"""
- saveAutofill=True 時會呼叫 Account 的 update_autofill
- saveAutofill 失敗不阻斷報名
- 限名額活動 PATCH guestCount=0 是允許的（不報錯）
- cancel waitlist 報名時，不會去 void ticket（waitlist 本來就沒 ticket）
- 後台清單在 Account 查不到 username 時以 null 帶過、不中斷
"""
from datetime import timedelta

from tests.conftest import NOW


# --- saveAutofill ---
def test_save_autofill_calls_account(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006", diet="none", driving=False)
    fake_event.set_event("event_005", ticket_limit=None)
    r = client.post(
        "/v1/transactions",
        headers=auth("user_006"),
        json={"eventId": "event_005", "dietType": "veg", "selfDriving": True, "saveAutofill": True},
    )
    assert r.status_code == 201
    # 應該有一筆 autofill 更新被送到 Account
    assert len(fake_account.autofill_updates) == 1
    upd = fake_account.autofill_updates[0]
    assert upd["userId"] == "user_006"
    assert upd["dietType"] == "veg"
    assert upd["selfDriving"] is True


def test_save_autofill_failure_does_not_block_registration(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)

    def _boom(*args, **kwargs):
        raise RuntimeError("account down")

    fake_account.update_autofill = _boom  # 模擬 Account 掛掉

    r = client.post(
        "/v1/transactions",
        headers=auth("user_006"),
        json={"eventId": "event_005", "saveAutofill": True},
    )
    # 報名仍成功
    assert r.status_code == 201
    assert r.json()["data"]["status"] == "confirmed"


# --- PATCH 限名額活動 guestCount=0 ---
def test_update_limited_event_guest_zero_allowed(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)
    tx_id = client.post(
        "/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"}
    ).json()["data"]["transactionId"]
    r = client.patch(
        f"/v1/transactions/{tx_id}", headers=auth("user_006"), json={"guestCount": 0}
    )
    assert r.status_code == 200
    assert r.json()["data"]["updated"] is True


# --- cancel waitlist 不 void ticket ---
def test_cancel_waitlist_does_not_void_ticket(client, fake_account, fake_event, fake_ticket, auth):
    fake_event.set_event("event_005", ticket_limit=1, cancellation_deadline=NOW + timedelta(days=3))
    fake_account.set_profile("user_006")
    fake_account.set_profile("user_007")
    client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})  # confirmed
    tx2 = client.post(
        "/v1/transactions", headers=auth("user_007"), json={"eventId": "event_005"}
    ).json()["data"]["transactionId"]  # waitlist

    r = client.delete(f"/v1/transactions/{tx2}", headers=auth("user_007"))
    assert r.status_code == 200
    # waitlist 沒有 ticket，所以 void_ticket 不該被呼叫
    assert fake_ticket.voided == []
    # 也不會 promote 任何人（取消的是 waitlist）
    assert "promoted" not in r.json()["data"]


# --- 後台清單 username 查不到時不中斷 ---
def test_backstage_missing_username_is_null(client, fake_account, fake_event, auth):
    # 報名者 user_005 有 profile，但我們在查 username 時刻意讓 Account 報錯
    fake_event.set_event("event_005", ticket_limit=5)
    fake_account.set_profile("user_005", username=None)
    client.post("/v1/transactions", headers=auth("user_005"), json={"eventId": "event_005"})

    from app.core.external import ExternalServiceError

    def _boom(_uid):
        raise ExternalServiceError("AccountService", "down", 500)

    fake_account.get_registration_profile = _boom

    r = client.get("/v1/events/event_005/registrations", headers=auth("user_008", "welfare_member"))
    assert r.status_code == 200
    regs = r.json()["data"]["registrations"]
    assert regs[0]["username"] is None  # 查不到以 null 帶過


# --- no-show：unused ticket 對不到 confirmed transaction 時記入 skipped ---
def test_no_show_skips_unmatched_ticket(client, fake_account, fake_event, fake_ticket):
    from app.core.config import settings

    fake_event.set_event("event_005", ticket_limit=5)
    fake_account.set_profile("user_005")
    # user_005 報名 → 產生 tk-1
    # 但我們在 unused 清單裡塞一個不存在的 ticket id
    from fastapi.testclient import TestClient  # noqa: F401

    # 直接呼叫 internal endpoint 前先建立一筆報名
    # （用 service 層的 client fixture 已注入 fake）
    # 這裡借用 conftest 的 auth 不方便，改用既有 fake 行為：
    fake_ticket.unused = ["tk-does-not-exist"]
    r = client.post(
        "/v1/internal/events/event_005/punish-no-shows",
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["punishedCount"] == 0
    assert len(d["skipped"]) == 1
    assert d["skipped"][0]["ticketId"] == "tk-does-not-exist"