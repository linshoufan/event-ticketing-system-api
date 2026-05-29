"""POST /v1/internal/events/{eventId}/punish-no-shows 測試。"""
from app.core.config import settings


def test_punish_no_shows_with_key(client, fake_account, fake_event, fake_ticket, auth):
    fake_event.set_event("e-1", ticket_limit=5)
    for i in range(2):
        fake_account.set_profile(f"u-{i}")
        client.post("/v1/transactions", headers=auth(f"u-{i}"), json={"eventId": "e-1"})
    # 假設 tk-1, tk-2 都沒 check-in
    fake_ticket.unused = ["tk-1", "tk-2"]

    r = client.post(
        "/v1/internal/events/e-1/punish-no-shows",
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["punishedCount"] == 2
    assert sorted(d["punishedUserIds"]) == ["u-0", "u-1"]
    assert sorted(fake_account.punished) == ["u-0", "u-1"]


def test_punish_no_shows_empty(client, fake_account, fake_event, fake_ticket):
    fake_event.set_event("e-1", ticket_limit=5)
    fake_ticket.unused = []
    r = client.post(
        "/v1/internal/events/e-1/punish-no-shows",
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert r.status_code == 200
    assert r.json()["data"]["punishedCount"] == 0


def test_punish_no_shows_wrong_key(client):
    r = client.post(
        "/v1/internal/events/e-1/punish-no-shows",
        headers={"X-Internal-Key": "wrong-key"},
    )
    assert r.status_code == 401


def test_punish_no_shows_missing_key(client):
    r = client.post("/v1/internal/events/e-1/punish-no-shows")
    assert r.status_code == 422