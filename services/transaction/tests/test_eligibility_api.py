"""GET /v1/events/{eventId}/eligibility 的測試。"""


def test_eligibility_ok(client, fake_account, fake_event, auth):
    fake_account.set_profile("u-1")
    fake_event.set_event("e-1", ticket_limit=5)
    r = client.get("/v1/events/e-1/eligibility", headers=auth("u-1"))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["eligible"] is True
    assert d["reason"] is None
    assert d["remainingTickets"] == 5
    assert d["isWaitlist"] is False


def test_eligibility_unlimited_remaining_null(client, fake_account, fake_event, auth):
    fake_account.set_profile("u-1")
    fake_event.set_event("e-1", ticket_limit=None)
    r = client.get("/v1/events/e-1/eligibility", headers=auth("u-1"))
    assert r.json()["data"]["remainingTickets"] is None


def test_eligibility_locked(client, fake_account, fake_event, auth):
    fake_account.set_profile("u-1", locked=True)
    fake_event.set_event("e-1", ticket_limit=5)
    r = client.get("/v1/events/e-1/eligibility", headers=auth("u-1"))
    d = r.json()["data"]
    assert d["eligible"] is False
    assert d["reason"] == "LOCKED"
    assert "unlockAt" in d


def test_eligibility_event_not_found(client, fake_account, fake_event, auth):
    fake_account.set_profile("u-1")
    r = client.get("/v1/events/nope/eligibility", headers=auth("u-1"))
    d = r.json()["data"]
    assert d["eligible"] is False
    assert d["reason"] == "EVENT_NOT_FOUND"


def test_eligibility_already_registered(client, fake_account, fake_event, auth):
    fake_account.set_profile("u-1")
    fake_event.set_event("e-1", ticket_limit=5)
    # 先報名
    client.post("/v1/transactions", headers=auth("u-1"), json={"eventId": "e-1"})
    r = client.get("/v1/events/e-1/eligibility", headers=auth("u-1"))
    d = r.json()["data"]
    assert d["eligible"] is False
    assert d["reason"] == "ALREADY_REGISTERED"


def test_eligibility_full_is_waitlist(client, fake_account, fake_event, auth):
    fake_event.set_event("e-1", ticket_limit=1)
    fake_account.set_profile("u-1")
    fake_account.set_profile("u-2")
    client.post("/v1/transactions", headers=auth("u-1"), json={"eventId": "e-1"})
    r = client.get("/v1/events/e-1/eligibility", headers=auth("u-2"))
    d = r.json()["data"]
    assert d["eligible"] is True
    assert d["isWaitlist"] is True
    assert d["reason"] == "NO_TICKETS"


def test_eligibility_requires_employee_role(client, fake_account, fake_event, auth):
    fake_account.set_profile("wf-1", role="welfare_member")
    fake_event.set_event("e-1", ticket_limit=5)
    r = client.get("/v1/events/e-1/eligibility", headers=auth("wf-1", "welfare_member"))
    assert r.status_code == 403


def test_eligibility_no_token(client):
    r = client.get("/v1/events/e-1/eligibility")
    assert r.status_code == 401