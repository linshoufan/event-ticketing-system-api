def test_batch_update_events_success(client, valid_event_payload):
    c = client("welfare_member")
    event_id = c.post("/v1/events/", json=valid_event_payload).json()["data"]["eventId"]

    response = c.patch("/v1/events/", json={"updates": [{"eventId": event_id, "ticketLimit": 999}]})

    assert response.status_code == 207
    assert response.json()["data"]["succeeded"] == [event_id]
    assert response.json()["data"]["failed"] == []


def test_batch_update_events_partial_failure(client, valid_event_payload):
    c = client("welfare_member")
    event_id = c.post("/v1/events/", json=valid_event_payload).json()["data"]["eventId"]

    response = c.patch(
        "/v1/events/",
        json={"updates": [
            {"eventId": event_id, "status": "closed"},
            {"eventId": "non_existent", "ticketLimit": 100},
        ]},
    )

    assert response.status_code == 207
    assert response.json()["data"]["succeeded"] == [event_id]
    assert response.json()["data"]["failed"] == [
        {"eventId": "non_existent", "error": "EVENT_NOT_FOUND"}
    ]
    assert "totalProcessed" not in response.json()["data"]


def test_batch_update_forbidden_for_employee(client):
    response = client("employee").patch(
        "/v1/events/",
        json={"updates": [{"eventId": "event_001", "status": "closed"}]},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
