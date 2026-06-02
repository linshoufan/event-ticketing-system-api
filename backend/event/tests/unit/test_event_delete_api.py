import requests
import pytest

def test_delete_event_success(base_url):
    # Setup: Create an event
    payload = {
        "name": "Delete Test",
        "description": "desc",
        "location": "loc",
        "category": "music",
        "guestAllowed": True,
        "ticketLimit": 100,
        "remainingTickets": 100,
        "eventStartTime": "2026-06-02T09:00:00Z",
        "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z",
        "registrationEnd": "2026-06-01T18:00:00Z",
        "status": "published"
    }
    res = requests.post(f"{base_url}/v1/events", json=payload)
    event_id = res.json()["data"]["eventId"]
    
    # Delete
    del_res = requests.delete(f"{base_url}/v1/events/{event_id}")
    assert del_res.status_code == 200
    
    # Verify deletion
    get_res = requests.get(f"{base_url}/v1/events/{event_id}")
    assert get_res.status_code == 404
