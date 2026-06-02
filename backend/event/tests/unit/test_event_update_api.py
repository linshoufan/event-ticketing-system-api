def test_update_event_success(client, valid_event_payload):
    c = client("welfare_member")
    create_res = c.post("/v1/events/", json={**valid_event_payload, "name": "Update Test"})
    event_id = create_res.json()["data"]["eventId"]

    patch_res = c.patch(f"/v1/events/{event_id}", json={"ticketLimit": 500, "status": "closed"})

    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["updated"] is True

    get_res = client("employee").get(f"/v1/events/{event_id}")
    assert get_res.json()["data"]["ticketLimit"] == 500
    assert get_res.json()["data"]["status"] == "closed"


def test_update_event_forbidden_for_employee(client, valid_event_payload):
    c_admin = client("welfare_member")
    create_res = c_admin.post("/v1/events/", json={**valid_event_payload, "name": "Protected Event"})
    event_id = create_res.json()["data"]["eventId"]

    response = client("employee").patch(f"/v1/events/{event_id}", json={"name": "Hacked"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_update_event_forbidden_for_hr(client, valid_event_payload):
    c_admin = client("welfare_member")
    create_res = c_admin.post("/v1/events/", json={**valid_event_payload, "name": "Protected Event"})
    event_id = create_res.json()["data"]["eventId"]

    response = client("hr").patch(f"/v1/events/{event_id}", json={"name": "Hacked"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_update_event_not_found(client):
    response = client("welfare_member").patch("/v1/events/non_existent_id", json={"name": "Missing"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"
