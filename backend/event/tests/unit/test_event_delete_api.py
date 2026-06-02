import pytest

def test_delete_event_success(client):
    c = client("hr")
    payload = {
        "name": "Delete Test", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }
    res = c.post("/v1/events/", json=payload)
    event_id = res.json()["data"]["eventId"]
    
    del_res = c.delete(f"/v1/events/{event_id}")
    assert del_res.status_code == 200
    
    get_res = c.get(f"/v1/events/{event_id}")
    assert get_res.status_code == 404
