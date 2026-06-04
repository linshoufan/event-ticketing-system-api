def test_list_events_excludes_ended_by_default(client, valid_event_payload):
    c = client("welfare_member")
    c.post("/v1/events/", json={**valid_event_payload, "name": "Open event", "status": "registering"})
    c.post("/v1/events/", json={**valid_event_payload, "name": "Ended event", "status": "ended"})

    response = client("employee").get("/v1/events/?page=1&limit=10")

    assert response.status_code == 200
    statuses = [event["status"] for event in response.json()["data"]]
    print(valid_event_payload)
    assert "registering" not in statuses
    assert "ended" not in statuses


def test_list_events_can_filter_ended_explicitly(client, valid_event_payload):
    c = client("welfare_member")
    c.post("/v1/events/", json={**valid_event_payload, "name": "Ended event", "status": "ended"})

    response = client("employee").get("/v1/events/?status=ended")

    assert response.status_code == 200
    assert [event["status"] for event in response.json()["data"]] == ["ended"]


def test_list_events_filters_keyword_category_and_dates(client, valid_event_payload):
    c = client("welfare_member")
    c.post("/v1/events/", json={
        **valid_event_payload,
        "name": "Year End Dinner",
        "description": "Company gathering",
        "category": "dining",
        "eventStartTime": "2026-12-25T18:00:00Z",
        "eventEndTime": "2026-12-25T22:00:00Z",
    })
    c.post("/v1/events/", json={
        **valid_event_payload,
        "name": "Q1 Travel",
        "description": "North coast",
        "category": "travel",
        "eventStartTime": "2027-01-15T08:00:00Z",
        "eventEndTime": "2027-01-15T20:00:00Z",
    })

    response = client("hr").get(
        "/v1/events/?keyword=Dinner&category=dining"
        "&startDate=2026-12-01T00:00:00Z&endDate=2026-12-31T23:59:59Z"
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 1
    assert response.json()["data"][0]["name"] == "Year End Dinner"


def test_list_events_unauthorized(raw_client):
    response = raw_client.get("/v1/events/")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_LOGGED_IN"
