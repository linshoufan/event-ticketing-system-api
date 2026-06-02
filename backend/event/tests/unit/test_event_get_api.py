import pytest

def test_get_event_success(client):
    c = client("employee") # 使用合法角色
    # 先建立一個活動 (需要 hr/welfare 權限)
    c_admin = client("hr")
    payload = {
        "name": "Get Test", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }
    res = c_admin.post("/v1/events/", json=payload)
    event_id = res.json()["data"]["eventId"]
    
    # 測試取得 (employee 權限)
    response = c.get(f"/v1/events/{event_id}")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Get Test"

def test_get_event_not_found(client):
    c = client("employee")
    response = c.get("/v1/events/non_existent_id")
    assert response.status_code == 404

def test_get_event_unauthorized(client):
    c = client(role=None)
    response = c.get("/v1/events/any_id")
    assert response.status_code == 401
