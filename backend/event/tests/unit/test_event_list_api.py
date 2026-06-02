import pytest

def test_list_events_no_filters(client):
    c = client()
    # Create some events
    for i in range(5):
        payload = {
            "name": f"Event {i}", "description": "desc", "location": "loc",
            "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
            "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
            "remainingTickets": 100, "status": "registering"
        }
        c.post("/v1/events/", json=payload)
    
    response = c.get("/v1/events/?page=1&limit=10")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 5
    assert response.json()["pagination"]["total"] == 5

def test_list_events_filter_by_keyword(client):
    c = client()
    c.post("/v1/events/", json={
        "name": "Target Movie", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    })
    c.post("/v1/events/", json={
        "name": "Other Party", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    })
    
    response = c.get("/v1/events/?keyword=Movie")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["name"] == "Target Movie"
