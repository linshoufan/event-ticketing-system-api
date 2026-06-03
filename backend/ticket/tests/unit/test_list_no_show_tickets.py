from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException


def test_list_no_show_tickets_for_ended_event(
    ticket_service,
    repo,
    event_client,
    make_ticket,
    make_event_info,
    shared_event,
):
    now = datetime.now(timezone.utc)
    event_client.get_event.return_value = make_event_info(
        event_start_time=now - timedelta(hours=3),
        event_end_time=now - timedelta(hours=1),
    )
    repo.get_event_tickets.return_value = [
        make_ticket(ticket_id="ticket_001", event_id=shared_event["id"]),
        make_ticket(ticket_id="ticket_002", event_id=shared_event["id"]),
    ]

    result = ticket_service.get_unused_tickets_for_ended_event(shared_event["id"])

    assert result == ["ticket_001", "ticket_002"]


def test_list_no_show_tickets_rejects_active_event(ticket_service, event_client, make_event_info, shared_event):
    event_client.get_event.return_value = make_event_info()

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.get_unused_tickets_for_ended_event(shared_event["id"])

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "EVENT_NOT_ENDED"
