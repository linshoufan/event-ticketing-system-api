from unittest.mock import patch

import pytest


@pytest.fixture
def current_user_role(request):
    return getattr(request, "param", "welfare_member")


def test_ticket_service_list_event_tickets_api(client, shared_event):
    with patch("app.services.ticket_service.TicketService.get_event_tickets") as mock_service:
        mock_service.return_value = {
            "summary": {"used": 1, "unused": 1, "invalid": 0},
            "tickets": [
                {"ticketId": "ticket_001", "userId": "user_001", "status": "used"},
                {"ticketId": "ticket_002", "userId": "user_002", "status": "unused"},
            ],
            "total": 2,
        }

        response = client.get(f"/v1/events/{shared_event['id']}/tickets?page=1&limit=2")

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 2
    assert response.json()["data"]["summary"]["used"] == 1
    assert len(response.json()["data"]["tickets"]) == 2


@pytest.mark.parametrize("current_user_role", ["hr"], indirect=True)
def test_ticket_service_list_event_tickets_api_allows_hr(client, shared_event):
    with patch("app.services.ticket_service.TicketService.get_event_tickets") as mock_service:
        mock_service.return_value = {
            "summary": {"used": 0, "unused": 0, "invalid": 0},
            "tickets": [],
            "total": 0,
        }

        response = client.get(f"/v1/events/{shared_event['id']}/tickets?page=1&limit=2")

    assert response.status_code == 200
