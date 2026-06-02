from datetime import timedelta


def test_create_event_success(client, valid_event_payload):
    c = client("welfare_member")
    response = c.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 201
    assert response.json()["data"] == {
        "eventId": response.json()["data"]["eventId"],
        "isDraft": False,
        "createdAt": response.json()["data"]["createdAt"],
    }


def test_create_event_duplicate_name_returns_conflict(client, valid_event_payload):
    c = client("welfare_member")
    assert c.post("/v1/events/", json=valid_event_payload).status_code == 201

    response = c.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_NAME_ALREADY_EXISTS"


def test_create_event_forbidden_for_employee(client, valid_event_payload):
    c = client("employee")
    response = c.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_event_forbidden_for_hr(client, valid_event_payload):
    c = client("hr")
    response = c.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_event_unauthorized(raw_client, valid_event_payload):
    response = raw_client.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_event_invalid_token(raw_client, valid_event_payload):
    response = raw_client.post(
        "/v1/events/",
        headers={"Authorization": "Bearer not.a.valid.token"},
        json=valid_event_payload,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_create_event_expired_token(raw_client, auth_headers, valid_event_payload):
    response = raw_client.post(
        "/v1/events/",
        headers=auth_headers(expires_delta=timedelta(seconds=-1)),
        json=valid_event_payload,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_create_event_validation_error_is_bad_request(client):
    c = client("welfare_member")
    response = c.post("/v1/events/", json={"name": "Missing fields"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_create_event_invalid_status_is_bad_request(client, valid_event_payload):
    c = client("welfare_member")
    payload = {**valid_event_payload, "status": "unknown_status"}
    response = c.post("/v1/events/", json=payload)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
