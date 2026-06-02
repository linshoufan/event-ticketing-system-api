import pytest

def test_list_events_no_filters(client):
    # 先以 HR 身分建立活動
    c_admin = client("hr")
    for i in range(5):
        payload = {
            "name": f"Event {i}", "description": "desc", "location": "loc",
            "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
            "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
            "remainingTickets": 100, "status": "registering"
        }
        res = c_admin.post("/v1/events/", json=payload)
        assert res.status_code == 201
    
    # 再切換為一般員工身分讀取列表
    c_user = client("employee")
    response = c_user.get("/v1/events/?page=1&limit=10")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 5

def test_list_events_unauthorized(client):
    c = client(role=None)
    response = c.get("/v1/events/")
    assert response.status_code == 401
