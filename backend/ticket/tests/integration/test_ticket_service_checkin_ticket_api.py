from unittest.mock import patch


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
