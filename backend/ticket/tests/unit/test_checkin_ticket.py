from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException


def test_calculate_checkin_distance(ticket_service):
    # Taipei 101 to Taipei Station, roughly 5km.
    dist = ticket_service._calculate_distance(25.0339, 121.5644, 25.0478, 121.5170)

    assert dist > 5000
    assert dist < 5100


def test_checkin_ticket_success(ticket_service, repo, event_client, make_ticket, make_event_info, shared_user, shared_ticket):
    ticket = make_ticket(ticket_id=shared_ticket["id"], user_id=shared_user["user_id"])
    repo.get_by_id.return_value = ticket
    event_client.get_event.return_value = make_event_info()

    result = ticket_service.checkin(shared_ticket["id"], shared_user["user_id"], 25.0339, 121.5644)

    assert result["checkedIn"] is True
    assert ticket.status == "used"
    assert ticket.checked_in_at is not None
    repo.save.assert_called_once()


def test_checkin_ticket_rejects_out_of_range(
    ticket_service,
    repo,
    event_client,
    make_ticket,
    make_event_info,
    shared_user,
    shared_ticket,
):
    ticket = make_ticket(ticket_id=shared_ticket["id"], user_id=shared_user["user_id"])
    repo.get_by_id.return_value = ticket
    event_client.get_event.return_value = make_event_info(checkin_radius_meters=100)

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.checkin(shared_ticket["id"], shared_user["user_id"], 25.0478, 121.5170)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "OUT_OF_RANGE"
    repo.save.assert_not_called()


def test_checkin_ticket_rejects_outside_event_time(
    ticket_service,
    repo,
    event_client,
    make_ticket,
    make_event_info,
    shared_user,
):
    now = datetime.now(timezone.utc)
    ticket = make_ticket(user_id=shared_user["user_id"])
    repo.get_by_id.return_value = ticket
    event_client.get_event.return_value = make_event_info(
        event_start_time=now + timedelta(hours=1),
        event_end_time=now + timedelta(hours=2),
    )

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.checkin(ticket.ticket_id, shared_user["user_id"], 25.0339, 121.5644)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "NOT_EVENT_TIME"


def test_checkin_ticket_rejects_wrong_user(ticket_service, repo, make_ticket, shared_ticket):
    repo.get_by_id.return_value = make_ticket(ticket_id=shared_ticket["id"], user_id="user_001")

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.checkin(shared_ticket["id"], "user_002", 25.0339, 121.5644)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "TICKET_NOT_FOUND"
