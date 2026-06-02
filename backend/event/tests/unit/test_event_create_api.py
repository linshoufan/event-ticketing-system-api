import pytest

def test_create_event_success(client, shared_data):
    c = client("welfare_member")
    shared_event = next(e for e in shared_data["events"] if e["id"] == "event_011")
    payload = {
        "name": f"Test Event {shared_event['name']}",
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
        "status": "registering"
    }
    
    response = c.post("/v1/events/", json=payload)
    assert response.status_code == 201
    
def test_create_event_forbidden_for_employee(client):
    c = client("employee")
    payload = {
        "name": "Forbidden Event", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }
    response = c.post("/v1/events/", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"

def test_create_event_unauthorized(client):
    c = client(role=None)
    response = c.post("/v1/events/", json={})
    assert response.status_code == 401
