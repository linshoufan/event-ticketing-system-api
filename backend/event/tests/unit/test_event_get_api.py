import pytest

def test_get_event_success(client):
    c = client()
    payload = {
        "name": "Get Test", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }
    res = c.post("/v1/events/", json=payload)
    event_id = res.json()["data"]["eventId"]
    
    response = c.get(f"/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Get Test"

def test_get_event_not_found(client):
    c = client()
    response = c.get("/v1/events/non_existent_id")
    assert response.status_code == 404
