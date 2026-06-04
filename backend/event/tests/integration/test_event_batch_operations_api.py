def test_batch_create_events_success(client, valid_event_payload):
    response = client("welfare_member").post(
        "/v1/events/batch",
        json={"events": [{**valid_event_payload, "name": "Q1 Travel"}]},
    )

    assert response.status_code == 201
    assert response.json()["data"]["succeeded"][0]["name"] == "Q1 Travel"
    assert response.json()["data"]["failed"] == []


def test_batch_create_events_partial_failure_on_duplicate_name(client, valid_event_payload):
    response = client("welfare_member").post(
        "/v1/events/batch",
        json={"events": [
            {**valid_event_payload, "name": "Duplicate Event"},
            {**valid_event_payload, "name": "Duplicate Event"},
        ]},
    )

    assert response.status_code == 207
    assert response.json()["data"]["succeeded"] == [
        {"eventId": response.json()["data"]["succeeded"][0]["eventId"], "name": "Duplicate Event"}
    ]
    assert response.json()["data"]["failed"] == [
        {"index": 1, "name": "Duplicate Event", "error": "duplicate key value"}
    ]


def test_batch_create_rejects_more_than_100_events(client, valid_event_payload):
    response = client("welfare_member").post(
        "/v1/events/batch",
        json={"events": [valid_event_payload] * 101},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_batch_create_forbidden_for_employee(client, valid_event_payload):
    response = client("employee").post(
        "/v1/events/batch",
        json={"events": [valid_event_payload]},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_batch_query_events(client, valid_event_payload):
    c = client("welfare_member")
    event_id = c.post("/v1/events/", json={**valid_event_payload, "name": "Batch Query"}).json()["data"]["eventId"]

    response = client("employee").post(
        "/v1/events/batch/query",
        json={"eventIds": [event_id, "ghost_id"]},
    )

    print(response.json()["data"])
    assert response.status_code == 200
    assert response.json()["data"]["found"][0]["eventId"] == event_id
    assert response.json()["data"]["found"][0]["status"] == "not_open"
    assert response.json()["data"]["notFound"] == ["ghost_id"]
    assert response.json()["data"]["total"] == 1


def test_batch_query_rejects_more_than_200_ids(client):
    response = client("employee").post(
        "/v1/events/batch/query",
        json={"eventIds": ["id"] * 201},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_batch_delete_events_all_succeeded(client, valid_event_payload):
    c = client("welfare_member")
    id1 = c.post("/v1/events/", json={**valid_event_payload, "name": "Draft 1", "isDraft": True}).json()["data"]["eventId"]
    id2 = c.post("/v1/events/", json={**valid_event_payload, "name": "Draft 2", "isDraft": True}).json()["data"]["eventId"]

    response = c.request("DELETE", "/v1/events/batch", json={"eventIds": [id1, id2]})

    assert response.status_code == 200
    assert response.json()["data"] == {"succeeded": [id1, id2], "failed": []}


def test_batch_delete_events_partial_failure(client, valid_event_payload):
    c = client("welfare_member")
    deletable_id = c.post("/v1/events/", json={**valid_event_payload, "name": "Draft", "isDraft": True}).json()["data"]["eventId"]
    locked_id = c.post("/v1/events/", json={
        **valid_event_payload,
        "name": "Published",
        "isDraft": False,
        "registrationStart": "2026-01-01T00:00:00Z",
        "registrationEnd": "2026-12-01T23:59:59Z",
    }).json()["data"]["eventId"]

    response = c.request("DELETE", "/v1/events/batch", json={"eventIds": [deletable_id, locked_id, "missing_id"]})

    assert response.status_code == 207
    assert response.json()["data"]["succeeded"] == [deletable_id]
    assert response.json()["data"]["failed"] == [
        {"eventId": locked_id, "error": "EVENT_NOT_DELETABLE"},
        {"eventId": "missing_id", "error": "EVENT_NOT_FOUND"},
    ]


def test_batch_delete_rejects_more_than_100_ids(client):
    response = client("welfare_member").request(
        "DELETE",
        "/v1/events/batch",
        json={"eventIds": ["id"] * 101},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
