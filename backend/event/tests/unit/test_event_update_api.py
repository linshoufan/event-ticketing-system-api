import pytest

def test_update_event_success(client):
    c = client("welfare_member")
    payload = {
        "name": "Update Test", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    }
    res = c.post("/v1/events/", json=payload)
    event_id = res.json()["data"]["eventId"]
    
    update_payload = {"ticketLimit": 500, "status": "closed"}
    patch_res = c.patch(f"/v1/events/{event_id}", json=update_payload)
    assert patch_res.status_code == 200
    
    get_res = c.get(f"/v1/events/{event_id}")
    assert get_res.json()["data"]["ticketLimit"] == 500
    assert get_res.json()["data"]["status"] == "closed"

def test_update_event_forbidden_for_employee(client):
    # 先以 HR 身分建立活動
    c_admin = client("hr")
    res = c_admin.post("/v1/events/", json={
        "name": "Admin Event", "description": "desc", "location": "loc",
        "eventStartTime": "2026-06-02T09:00:00Z", "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z", "registrationEnd": "2026-06-01T18:00:00Z",
        "remainingTickets": 100
    })
    event_id = res.json()["data"]["eventId"]
    
    # 再以一般員工身分嘗試更新
    c_user = client("employee")
    response = c_user.patch(f"/v1/events/{event_id}", json={"name": "Hacked"})
    assert response.status_code == 403
