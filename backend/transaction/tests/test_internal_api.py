"""POST /v1/internal/events/{eventId}/punish-no-shows 測試。"""
from app.core.config import settings


def test_punish_no_shows_with_key(client, fake_account, fake_event, fake_ticket, auth):
    fake_event.set_event("event_005", ticket_limit=5)
    for i in range(2):
        fake_account.set_profile(f"user_test_{i:03d}")
        client.post("/v1/transactions", headers=auth(f"user_test_{i:03d}"), json={"eventId": "event_005"})
    # 假設 tk-1, tk-2 都沒 check-in
    fake_ticket.unused = ["tk-1", "tk-2"]

    r = client.post(
        "/v1/internal/events/event_005/punish-no-shows",
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["punishedCount"] == 2
    assert sorted(d["punishedUserIds"]) == ["user_test_000", "user_test_001"]
    assert sorted(fake_account.punished) == ["user_test_000", "user_test_001"]

def test_punish_no_shows_empty(client, fake_account, fake_event, fake_ticket):
    fake_event.set_event("event_005", ticket_limit=5)
    fake_ticket.unused = []
    r = client.post(
        "/v1/internal/events/event_005/punish-no-shows",
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert r.status_code == 200
    assert r.json()["data"]["punishedCount"] == 0

def test_punish_no_shows_wrong_key(client):
    r = client.post(
        "/v1/internal/events/event_005/punish-no-shows",
        headers={"X-Internal-Key": "wrong-key"},
    )
    assert r.status_code == 401

def test_punish_no_shows_missing_key(client):
    r = client.post("/v1/internal/events/event_005/punish-no-shows")
    assert r.status_code == 422
