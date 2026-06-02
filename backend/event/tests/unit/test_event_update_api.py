import requests
import pytest

def test_update_event_success(base_url, shared_data):
    # Setup: Create an event
    shared_event = next(e for e in shared_data["events"] if e["id"] == "event_011")
    payload = {
        "name": "Update Test",
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
    
    # Update
    update_payload = {"ticketLimit": 500, "guestAllowed": False}
    patch_res = requests.patch(f"{base_url}/v1/events/{event_id}", json=update_payload)
    assert patch_res.status_code == 200
    
    # Verify
    get_res = requests.get(f"{base_url}/v1/events/{event_id}")
    updated_data = get_res.json()["data"]
    assert updated_data["ticketLimit"] == 500
    assert updated_data["guestAllowed"] is False

def test_update_event_invalid_type(base_url):
    # Setup: Create an event
    payload = {
        "name": "Type Test", "category": "music", "ticketLimit": 100,
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z", "status": "published"
    }
    res = requests.post(f"{base_url}/v1/events", json=payload)
    event_id = res.json()["data"]["eventId"]

    # Update with wrong type
    response = requests.patch(f"{base_url}/v1/events/{event_id}", json={"ticketLimit": "string_not_number"})
    assert response.status_code == 400
