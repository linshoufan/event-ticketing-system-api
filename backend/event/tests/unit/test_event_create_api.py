import requests
import pytest

def test_create_event_success(base_url, shared_data):
    shared_event = next(e for e in shared_data["events"] if e["id"] == "event_011")
    payload = {
        "name": f"Python Test Event {shared_event['name']}",
        "description": shared_event["description"],
        "location": shared_event["location"],
        "category": shared_event["category"],
        "guestAllowed": shared_event["guest_allowed"],
        "ticketLimit": shared_event["ticket_limit"],
        "remainingTickets": shared_event["remaining_tickets"],
        "eventStartTime": shared_event["event_start_time"],
        "eventEndTime": shared_event["event_end_time"],
        "registrationStart": shared_event["registration_start"],
        "registrationEnd": shared_event["registration_end"],
        "status": shared_event["status"],
        "isDraft": shared_event["is_draft"],
        "createdAt": shared_event["created_at"]
    }
    
    response = requests.post(f"{base_url}/v1/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "eventId" in data["data"]
    
    event_id = data["data"]["eventId"]
    
    # Verify via GET
    get_res = requests.get(f"{base_url}/v1/events/{event_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == payload["name"]

def test_create_event_invalid_time_schema(base_url, shared_data):
    shared_event = next(e for e in shared_data["events"] if e["id"] == "event_011")
    payload = {
        "name": "Invalid Time Event",
        "category": "music",
        "eventStartTime": "2026-06-02T18:00:00Z", # Start is AFTER end
        "eventEndTime": "2026-06-02T09:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z",
        "registrationEnd": "2026-06-01T18:00:00Z",
        "status": "published"
    }
    response = requests.post(f"{base_url}/v1/events", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
