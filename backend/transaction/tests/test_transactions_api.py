"""POST / GET / PATCH / DELETE /v1/transactions 的測試。"""

# POST /transactions
def test_register_confirmed(client, fake_account, fake_event, fake_ticket, auth):
    fake_account.set_profile("user_006", diet="veg", driving=True)
    fake_event.set_event("event_005", ticket_limit=5)
    r = client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["status"] == "confirmed"
    assert d["ticketId"] == "tk-1"
    assert d["waitlistNumber"] is None

def test_register_autofill_applied(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006", diet="veg", driving=True)
    fake_event.set_event("event_005", ticket_limit=None)  # unlimited 才看得出 guest
    r = client.post("/v1/transactions", headers=auth("user_006"),
                    json={"eventId": "event_005"})
    tx_id = r.json()["data"]["transactionId"]
    detail = client.get(f"/v1/transactions/{tx_id}", headers=auth("user_006")).json()["data"]
    assert detail["dietType"] == "veg"
    assert detail["selfDriving"] is True

def test_register_duplicate_409(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)
    client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    r = client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_REGISTERED"

def test_register_waitlist_when_full(client, fake_account, fake_event, auth):
    fake_event.set_event("event_005", ticket_limit=2)
    for i in range(3):
        fake_account.set_profile(f"user_test_{i:03d}")
    statuses = []
    for i in range(3):
        r = client.post("/v1/transactions", headers=auth(f"user_test_{i:03d}"), json={"eventId": "event_005"})
        statuses.append(r.json()["data"]["status"])
    assert statuses == ["confirmed", "confirmed", "waitlist"]

def test_register_locked_409_account_locked(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006", locked=True)
    fake_event.set_event("event_005", ticket_limit=5)
    r = client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "ACCOUNT_LOCKED"
    assert "unlockAt" in err

def test_register_limited_event_forces_guest_zero(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)
    r = client.post("/v1/transactions", headers=auth("user_006"),
                    json={"eventId": "event_005", "guestCount": 3})
    tx_id = r.json()["data"]["transactionId"]
    detail = client.get(f"/v1/transactions/{tx_id}", headers=auth("user_006")).json()["data"]
    assert detail["guestCount"] == 0

def test_register_unlimited_event_allows_guest(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=None)
    r = client.post("/v1/transactions", headers=auth("user_006"),
                    json={"eventId": "event_005", "guestCount": 4})
    tx_id = r.json()["data"]["transactionId"]
    detail = client.get(f"/v1/transactions/{tx_id}", headers=auth("user_006")).json()["data"]
    assert detail["guestCount"] == 4

def test_register_draft_event_blocked(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5, is_draft=True)
    r = client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    assert r.status_code >= 400


# GET /transactions
def test_list_my_transactions_enriched(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)
    client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    r = client.get("/v1/transactions", headers=auth("user_006"))
    assert r.status_code == 200
    body = r.json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["eventName"] == "Event event_005"
    assert body["data"][0]["eventStartTime"] is not None

def test_list_my_transactions_status_filter(client, fake_account, fake_event, auth):
    fake_event.set_event("event_005", ticket_limit=1)
    fake_account.set_profile("user_006")
    fake_account.set_profile("user_007")
    client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    client.post("/v1/transactions", headers=auth("user_007"), json={"eventId": "event_005"})
    r = client.get("/v1/transactions?status=waitlist", headers=auth("user_007"))
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "waitlist"

def test_get_single_not_found(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    r = client.get("/v1/transactions/nonexistent", headers=auth("user_006"))
    assert r.status_code == 404

def test_get_single_other_user_forbidden(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_account.set_profile("user_007")
    fake_event.set_event("event_005", ticket_limit=5)
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    # user_007 嘗試看 user_006 的報名
    r = client.get(f"/v1/transactions/{tx_id}", headers=auth("user_007"))
    assert r.status_code == 403


# PATCH /transactions
def test_update_transaction(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=None)
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    r = client.patch(f"/v1/transactions/{tx_id}", headers=auth("user_006"),
                     json={"dietType": "veg", "guestCount": 2})
    assert r.status_code == 200
    assert r.json()["data"]["updated"] is True
    detail = client.get(f"/v1/transactions/{tx_id}", headers=auth("user_006")).json()["data"]
    assert detail["dietType"] == "veg"
    assert detail["guestCount"] == 2

def test_update_guest_on_limited_event_rejected(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5)
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    r = client.patch(f"/v1/transactions/{tx_id}", headers=auth("user_006"),
                     json={"guestCount": 3})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "GUEST_NOT_ALLOWED"


# DELETE /transactions
def test_cancel_confirmed_promotes_waitlist(client, fake_account, fake_event, fake_ticket, auth):
    from datetime import timedelta
    from tests.conftest import NOW
    fake_event.set_event("event_005", ticket_limit=1, cancellation_deadline=NOW + timedelta(days=3))
    fake_account.set_profile("user_006")
    fake_account.set_profile("user_007")
    tx1 = client.post("/v1/transactions", headers=auth("user_006"),
                      json={"eventId": "event_005"}).json()["data"]["transactionId"]
    client.post("/v1/transactions", headers=auth("user_007"), json={"eventId": "event_005"})  # waitlist
    r = client.delete(f"/v1/transactions/{tx1}", headers=auth("user_006"))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["cancelled"] is True
    assert d["promoted"]["userId"] == "user_007"
    assert d["promoted"]["status"] == "confirmed"

def test_cancel_no_deadline_blocked(client, fake_account, fake_event, auth):
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5, cancellation_deadline=None)
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    r = client.delete(f"/v1/transactions/{tx_id}", headers=auth("user_006"))
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "NOT_CANCELLABLE"

def test_cancel_past_deadline_blocked(client, fake_account, fake_event, auth):
    from datetime import timedelta
    from tests.conftest import NOW
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5, cancellation_deadline=NOW - timedelta(days=1))
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    r = client.delete(f"/v1/transactions/{tx_id}", headers=auth("user_006"))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "PAST_CANCELLATION_DEADLINE"

def test_cancel_then_reregister_allowed(client, fake_account, fake_event, auth):
    from datetime import timedelta
    from tests.conftest import NOW
    fake_account.set_profile("user_006")
    fake_event.set_event("event_005", ticket_limit=5, cancellation_deadline=NOW + timedelta(days=3))
    tx_id = client.post("/v1/transactions", headers=auth("user_006"),
                        json={"eventId": "event_005"}).json()["data"]["transactionId"]
    client.delete(f"/v1/transactions/{tx_id}", headers=auth("user_006"))
    # 取消後可以再報
    r = client.post("/v1/transactions", headers=auth("user_006"), json={"eventId": "event_005"})
    assert r.status_code == 201
    assert r.json()["data"]["status"] == "confirmed"