def test_get_event_success_for_employee(client, valid_event_payload):
    c_admin = client("welfare_member")
    create_res = c_admin.post("/v1/events/", json={**valid_event_payload, "name": "Get Test"})
    event_id = create_res.json()["data"]["eventId"]

    response = client("employee").get(f"/v1/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Get Test"


def test_get_event_not_found(client):
    response = client("employee").get("/v1/events/non_existent_id")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_get_event_unauthorized(raw_client):
    response = raw_client.get("/v1/events/any_id")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_LOGGED_IN"
