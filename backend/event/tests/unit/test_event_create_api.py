def test_create_event_success(client, valid_event_payload):
    c = client("welfare_member")
    response = c.post("/v1/events/", json=valid_event_payload)

    assert response.status_code == 201
    assert response.json()["data"]["eventId"] is not None


def test_create_event_accepts_path_without_trailing_slash(client, valid_event_payload):
    c = client("welfare_member")
    response = c.post("/v1/events", json=valid_event_payload, follow_redirects=False)

    assert response.status_code == 201
    assert "location" not in response.headers
    assert response.json()["data"]["eventId"] is not None


def test_create_event_preflight_allows_vercel_frontend(raw_client):
    response = raw_client.options(
        "/v1/events",
        headers={
            "Origin": "https://event-ticketing-system-frontend-eight.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://event-ticketing-system-frontend-eight.vercel.app"
    )
    assert response.headers["access-control-allow-credentials"] == "true"


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
    assert response.json()["error"]["code"] == "NOT_LOGGED_IN"


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
        headers=auth_headers(user_id="u_test", role="welfare_member", expired=True),
        json=valid_event_payload,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_create_event_incomplete_token(raw_client, auth_headers, valid_event_payload):
    response = raw_client.post(
        "/v1/events/",
        headers=auth_headers(user_id="u_test", role="welfare_member", incomplete=True),
        json=valid_event_payload,
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


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
