"""GET /v1/events/{eventId}/registrations 後台查詢測試。"""


def _seed(client, fake_account, fake_event, auth, n_confirmed=2, n_waitlist=1):
    limit = n_confirmed
    fake_event.set_event("e-1", ticket_limit=limit)
    total = n_confirmed + n_waitlist
    for i in range(total):
        fake_account.set_profile(f"u-{i}")
        client.post("/v1/transactions", headers=auth(f"u-{i}"), json={"eventId": "e-1"})


def test_backstage_summary_and_list(client, fake_account, fake_event, auth):
    _seed(client, fake_account, fake_event, auth, n_confirmed=2, n_waitlist=1)
    r = client.get("/v1/events/e-1/registrations", headers=auth("wf", "welfare_member"))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["summary"]["totalConfirmed"] == 2
    assert d["summary"]["totalWaitlist"] == 1
    assert d["summary"]["totalCancelled"] == 0
    assert len(d["registrations"]) == 3
    # 排序：confirmed 在前
    assert d["registrations"][0]["status"] == "confirmed"


def test_backstage_hr_allowed(client, fake_account, fake_event, auth):
    _seed(client, fake_account, fake_event, auth, n_confirmed=1, n_waitlist=0)
    r = client.get("/v1/events/e-1/registrations", headers=auth("hr-1", "hr"))
    assert r.status_code == 200


def test_backstage_employee_forbidden(client, fake_account, fake_event, auth):
    _seed(client, fake_account, fake_event, auth, n_confirmed=1, n_waitlist=0)
    r = client.get("/v1/events/e-1/registrations", headers=auth("u-0", "employee"))
    assert r.status_code == 403


def test_backstage_status_filter(client, fake_account, fake_event, auth):
    _seed(client, fake_account, fake_event, auth, n_confirmed=2, n_waitlist=2)
    r = client.get("/v1/events/e-1/registrations?status=waitlist",
                   headers=auth("wf", "welfare_member"))
    regs = r.json()["data"]["registrations"]
    assert all(x["status"] == "waitlist" for x in regs)
    assert len(regs) == 2


def test_backstage_pagination(client, fake_account, fake_event, auth):
    _seed(client, fake_account, fake_event, auth, n_confirmed=3, n_waitlist=2)
    r = client.get("/v1/events/e-1/registrations?page=1&limit=2",
                   headers=auth("wf", "welfare_member"))
    body = r.json()
    assert body["pagination"]["total"] == 5
    assert len(body["data"]["registrations"]) == 2