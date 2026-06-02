import requests
import pytest

def test_batch_update_events(base_url, shared_data):
    # Setup: Create two events
    e1_payload = {
        "name": "Batch 1", "category": "music", "ticketLimit": 100, "remainingTickets": 100,
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z", "status": "published"
    }
    e2_payload = {
        "name": "Batch 2", "category": "it", "ticketLimit": 200, "remainingTickets": 200,
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z", "status": "published"
    }
    
    id1 = requests.post(f"{base_url}/v1/events", json=e1_payload).json()["data"]["eventId"]
    id2 = requests.post(f"{base_url}/v1/events", json=e2_payload).json()["data"]["eventId"]
    
    # Batch Update Logic
    batch_payload = [
        {"eventId": id1, "ticketLimit": 150},
        {"eventId": id2, "status": "cancelled"}
    ]
    
    # Note: Assuming the endpoint exists as /v1/internal/events/batch (based on common internal patterns)
    # If it's a different endpoint, adjust accordingly. 
    # Let's check routes to be sure.
    response = requests.patch(f"{base_url}/v1/events", json=batch_payload)
    assert response.status_code == 200
    
    # Verify
    assert requests.get(f"{base_url}/v1/events/{id1}").json()["data"]["ticketLimit"] == 150
    # Depending on how 'cancelled' is handled in the system
