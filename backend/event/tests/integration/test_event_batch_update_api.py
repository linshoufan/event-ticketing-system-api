import pytest

def test_batch_update_events_success(client):
    c = client("hr")
    # Setup
    id1 = c.post("/v1/events/", json={
        "name": "E1", "description": "d", "location": "l",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }).json()["data"]["eventId"]
    
    batch_payload = {
        "updates": [
            {"eventId": id1, "ticketLimit": 999}
        ]
    }
    
    response = c.patch("/v1/events/", json=batch_payload)
    assert response.status_code == 207
    assert id1 in response.json()["data"]["succeeded"]

def test_batch_update_events_partial_failure(client):
    c = client("hr")
    batch_payload = {
        "updates": [
            {"eventId": "non_existent", "ticketLimit": 100}
        ]
    }
    response = c.patch("/v1/events/", json=batch_payload)
    assert response.status_code == 207
    assert len(response.json()["data"]["failed"]) == 1
    assert response.json()["data"]["failed"][0]["error"] == "Event not found"
