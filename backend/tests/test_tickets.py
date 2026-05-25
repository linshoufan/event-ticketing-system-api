from datetime import datetime, timedelta, timezone
import uuid

from app.core.security import create_access_token
from app.models.ticket import Event, Ticket
from app.models.user import User


def make_user(db, role="employee", username="john.doe"):
    suffix = uuid.uuid4().hex[:8]
    username = f"{username}_{suffix}"
    user = User(
        user_id=str(uuid.uuid4()),
        username=username,
        email=f"{username}@company.com",
        role=role,
        registration_status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.user_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def make_event(db, event_id=None, starts_in_hours=-1):
    now = datetime.now(timezone.utc)
    event_id = event_id or f"ev_{uuid.uuid4().hex[:8]}"
    event = Event(
        event_id=event_id,
        name="Summer Party",
        location="Taipei Office Rooftop",
        latitude=25.0478,
        longitude=121.5319,
        checkin_radius_meters=200,
        event_start_time=now + timedelta(hours=starts_in_hours),
        event_end_time=now + timedelta(hours=starts_in_hours + 2),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def make_ticket(db, event: Event, user: User, ticket_id=None, checked_in_at=None):
    ticket_id = ticket_id or f"tk_{uuid.uuid4().hex[:8]}"
    ticket = Ticket(
        ticket_id=ticket_id,
        event_id=event.event_id,
        user_id=user.user_id,
        username=user.username,
        checked_in_at=checked_in_at,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def test_list_my_tickets_filters_by_status(client, db_session):
    user = make_user(db_session)
    active_event = make_event(db_session)
    future_event = make_event(db_session, starts_in_hours=24)
    active_ticket = make_ticket(db_session, event=active_event, user=user)
    make_ticket(db_session, event=future_event, user=user)

    response = client.get("/v1/tickets?status=unused", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["ticketId"] == active_ticket.ticket_id
    assert data[0]["status"] == "unused"
    assert data[0]["checkinAvailable"] is True


def test_get_ticket_detail_includes_qr_payload(client, db_session):
    user = make_user(db_session)
    event = make_event(db_session)
    ticket = make_ticket(db_session, event=event, user=user)

    response = client.get(f"/v1/tickets/{ticket.ticket_id}", headers=auth_headers(user))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ticketId"] == ticket.ticket_id
    assert data["userId"] == user.user_id
    assert data["status"] == "unused"
    assert data["qrPayload"].startswith(f"{ticket.ticket_id}:{event.event_id}:{user.user_id}:sig_")


def test_employee_cannot_get_other_users_ticket(client, db_session):
    employee = make_user(db_session, username="employee")
    other = make_user(db_session, username="other")
    event = make_event(db_session)
    ticket = make_ticket(db_session, event=event, user=other)

    response = client.get(f"/v1/tickets/{ticket.ticket_id}", headers=auth_headers(employee))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_checkin_succeeds_and_marks_ticket_used(client, db_session):
    user = make_user(db_session)
    event = make_event(db_session)
    ticket = make_ticket(db_session, event=event, user=user)

    response = client.post(
        f"/v1/tickets/{ticket.ticket_id}/checkin",
        json={"latitude": 25.0479, "longitude": 121.5320},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["data"]["checkedIn"] is True
    checked_ticket = db_session.query(Ticket).filter(Ticket.ticket_id == ticket.ticket_id).first()
    assert checked_ticket.checked_in_at is not None

    duplicate_response = client.post(
        f"/v1/tickets/{ticket.ticket_id}/checkin",
        json={"latitude": 25.0479, "longitude": 121.5320},
        headers=auth_headers(user),
    )
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["error"]["code"] == "TICKET_INVALID"


def test_checkin_rejects_out_of_range_location(client, db_session):
    user = make_user(db_session)
    event = make_event(db_session)
    ticket = make_ticket(db_session, event=event, user=user)

    response = client.post(
        f"/v1/tickets/{ticket.ticket_id}/checkin",
        json={"latitude": 24.1477, "longitude": 120.6736},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "OUT_OF_RANGE"


def test_checkin_rejects_before_event_time(client, db_session):
    user = make_user(db_session)
    event = make_event(db_session, starts_in_hours=24)
    ticket = make_ticket(db_session, event=event, user=user)

    response = client.post(
        f"/v1/tickets/{ticket.ticket_id}/checkin",
        json={"latitude": 25.0479, "longitude": 121.5320},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "NOT_EVENT_TIME"

