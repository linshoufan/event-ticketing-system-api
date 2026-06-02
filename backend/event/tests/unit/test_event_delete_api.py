def test_delete_event_success_for_draft(client, valid_event_payload):
    c = client("welfare_member")
    create_res = c.post("/v1/events/", json={**valid_event_payload, "isDraft": True})
    event_id = create_res.json()["data"]["eventId"]

    del_res = c.delete(f"/v1/events/{event_id}")

    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True
    assert client("employee").get(f"/v1/events/{event_id}").status_code == 404


def test_delete_event_success_before_registration_starts(client, valid_event_payload):
    c = client("welfare_member")
    # Today is June 2, 2026. Setting dates to the far future.
    payload = {
        **valid_event_payload,
        "isDraft": False,
        "registrationStart": "2026-12-01T00:00:00Z",
        "registrationEnd": "2026-12-31T23:59:59Z",
        "eventStartTime": "2027-01-01T00:00:00Z",
        "eventEndTime": "2027-01-01T23:59:59Z",
    }
    create_res = c.post("/v1/events/", json=payload)
    assert create_res.status_code == 201
    event_id = create_res.json()["data"]["eventId"]

    del_res = c.delete(f"/v1/events/{event_id}")

    assert del_res.status_code == 200


def test_delete_event_not_found(client):
    response = client("welfare_member").delete("/v1/events/nonexistent_id")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVENT_NOT_FOUND"


def test_delete_event_not_deletable_after_registration_started(client, valid_event_payload):
    c = client("welfare_member")
    create_res = c.post("/v1/events/", json={
        **valid_event_payload,
        "isDraft": False,
        "registrationStart": "2026-01-01T00:00:00Z",
        "registrationEnd": "2026-12-01T23:59:59Z",
    })
    event_id = create_res.json()["data"]["eventId"]

    response = c.delete(f"/v1/events/{event_id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVENT_NOT_DELETABLE"


def test_delete_event_forbidden_for_hr(client, valid_event_payload):
    c = client("welfare_member")
    create_res = c.post("/v1/events/", json={**valid_event_payload, "isDraft": True})
    event_id = create_res.json()["data"]["eventId"]

    response = client("hr").delete(f"/v1/events/{event_id}")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
