from unittest.mock import patch

import pytest


@pytest.fixture
def current_user_role(request):
    return getattr(request, "param", "employee")


def test_ticket_service_checkin_ticket_api(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.checkin") as mock_service:
        mock_service.return_value = {
            "checkedIn": True,
            "checkedInAt": "2026-06-01T00:00:00+00:00",
        }

        response = client.post(
            f"/v1/tickets/{shared_ticket['id']}/checkin",
            json={"latitude": 25.0339, "longitude": 121.5644},
        )

    assert response.status_code == 200
    assert response.json()["data"]["checkedIn"] is True
    mock_service.assert_called_once_with(
        shared_ticket["id"],
        "1000001",
        25.0339,
        121.5644,
    )


@pytest.mark.parametrize("current_user_role", ["welfare_member"], indirect=True)
def test_ticket_service_checkin_ticket_api_allows_welfare_member(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.checkin_by_welfare") as mock_service:
        mock_service.return_value = {
            "checkedIn": True,
            "checkedInAt": "2026-06-01T00:00:00+00:00",
        }

        response = client.post(
            f"/v1/tickets/{shared_ticket['id']}/checkin",
            json={"latitude": 0, "longitude": 0},
        )

    assert response.status_code == 200
    mock_service.assert_called_once_with(shared_ticket["id"])


@pytest.mark.parametrize("current_user_role", ["welfare_member"], indirect=True)
def test_ticket_service_checkin_ticket_api_allows_welfare_member_without_body(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.checkin_by_welfare") as mock_service:
        mock_service.return_value = {
            "checkedIn": True,
            "checkedInAt": "2026-06-01T00:00:00+00:00",
        }

        response = client.post(f"/v1/tickets/{shared_ticket['id']}/checkin")

    assert response.status_code == 200
    mock_service.assert_called_once_with(shared_ticket["id"])


@pytest.mark.parametrize("current_user_role", ["welfare_member"], indirect=True)
def test_ticket_service_checkin_ticket_api_allows_welfare_member_with_invalid_body(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.checkin_by_welfare") as mock_service:
        mock_service.return_value = {
            "checkedIn": True,
            "checkedInAt": "2026-06-01T00:00:00+00:00",
        }

        response = client.post(
            f"/v1/tickets/{shared_ticket['id']}/checkin",
            json={"unexpected": "value"},
        )

    assert response.status_code == 200
    mock_service.assert_called_once_with(shared_ticket["id"])


def test_ticket_service_checkin_ticket_api_requires_body_for_employee(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.checkin") as mock_service:
        response = client.post(f"/v1/tickets/{shared_ticket['id']}/checkin")

    assert response.status_code == 422
    mock_service.assert_not_called()
