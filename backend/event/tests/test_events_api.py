from __future__ import annotations

from copy import deepcopy


def test_create_event_persists_record(api_client, db_conn, shared_event_payload):
    response = api_client.post("/v1/events", json=shared_event_payload)

    assert response.status_code == 201
    event_id = response.json()["data"]["eventId"]
    assert event_id

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT name, location, remaining_tickets FROM events WHERE event_id = %s",
            (event_id,),
        )
        row = cur.fetchone()

    assert row == (
        shared_event_payload["name"],
        shared_event_payload["location"],
        shared_event_payload["remainingTickets"],
    )

    with db_conn.cursor() as cur:
        cur.execute("DELETE FROM events WHERE event_id = %s", (event_id,))


def test_create_event_rejects_end_before_start(api_client, db_conn, shared_event_payload):
    payload = deepcopy(shared_event_payload)
    payload["eventStartTime"] = "2026-06-02T09:00:00Z"
    payload["eventEndTime"] = "2026-06-01T18:00:00Z"

    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM events")
        count_before = cur.fetchone()[0]

    response = api_client.post("/v1/events", json=payload)

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["details"][0]["path"] == "body.eventEndTime"

    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM events")
        assert cur.fetchone()[0] == count_before


def test_get_event_details(api_client, insert_event, shared_event_payload):
    insert_event("pytest_read_001")

    response = api_client.get("/v1/events/pytest_read_001")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["eventId"] == "pytest_read_001"
    assert data["name"] == shared_event_payload["name"]


def test_get_event_details_returns_404_for_missing_event(api_client):
    response = api_client.get("/v1/events/pytest_missing_001")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_list_events_filters_by_category(api_client, insert_event):
    insert_event("pytest_list_food", category="food", name="Food Event")
    insert_event("pytest_list_sport", category="sport", name="Sport Event")

    response = api_client.get("/v1/events", params={"page": 1, "limit": 20, "category": "food"})

    assert response.status_code == 200
    body = response.json()
    returned_ids = {item["eventId"] for item in body["data"]}
    assert "pytest_list_food" in returned_ids
    assert "pytest_list_sport" not in returned_ids
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["limit"] == 20


def test_update_event_persists_patch(api_client, db_conn, insert_event, shared_event_payload):
    insert_event("pytest_update_001")

    response = api_client.patch(
        "/v1/events/pytest_update_001",
        json={"ticketLimit": 500, "guestAllowed": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["updated"] is True

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT ticket_limit, guest_allowed, name FROM events WHERE event_id = %s",
            ("pytest_update_001",),
        )
        row = cur.fetchone()

    assert row == (500, False, shared_event_payload["name"])


def test_update_event_rejects_invalid_field_type(api_client):
    response = api_client.patch("/v1/events/pytest_update_001", json={"ticketLimit": "五百"})

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["path"] == "body.ticketLimit"


def test_batch_update_events_returns_multi_status(api_client, db_conn, insert_event):
    insert_event("pytest_batch_001")

    response = api_client.patch(
        "/v1/events",
        json={
            "updates": [
                {"eventId": "pytest_batch_001", "ticketLimit": 300},
                {"eventId": "pytest_batch_missing", "ticketLimit": 400},
            ]
        },
    )

    assert response.status_code == 207
    data = response.json()["data"]
    assert "pytest_batch_001" in data["succeeded"]
    assert data["failed"] == [{"eventId": "pytest_batch_missing", "error": "Event not found"}]

    with db_conn.cursor() as cur:
        cur.execute("SELECT ticket_limit FROM events WHERE event_id = %s", ("pytest_batch_001",))
        assert cur.fetchone()[0] == 300


def test_delete_event_removes_record(api_client, db_conn, insert_event):
    insert_event("pytest_delete_001")

    response = api_client.delete("/v1/events/pytest_delete_001")

    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True

    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM events WHERE event_id = %s", ("pytest_delete_001",))
        assert cur.fetchone()[0] == 0
