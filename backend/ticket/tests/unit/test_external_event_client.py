from datetime import datetime, timezone

import httpx

from app.core.external import EventClient


def test_event_client_calls_internal_event_endpoint_with_internal_key():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["internal_key"] = request.headers.get("x-internal-key")
        return httpx.Response(
            200,
            json={
                "data": {
                    "eventId": "event_002",
                    "name": "Mock Event",
                    "location": "Taipei",
                    "latitude": 25.033,
                    "longitude": 121.565,
                    "checkinRadiusMeters": 100,
                    "eventStartTime": "2026-06-10T10:00:00Z",
                    "eventEndTime": "2026-06-10T12:00:00Z",
                }
            },
        )

    client = EventClient(
        base_url="http://event-service",
        internal_key="test-internal-key",
        transport=httpx.MockTransport(handler),
    )

    event = client.get_event("event_002")

    assert captured == {
        "path": "/v1/internal/events/event_002",
        "internal_key": "test-internal-key",
    }
    assert event.event_id == "event_002"
    assert event.name == "Mock Event"
    assert event.location == "Taipei"
    assert event.event_start_time == datetime(2026, 6, 10, 10, 0, tzinfo=timezone.utc)
