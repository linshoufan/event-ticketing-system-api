from unittest.mock import patch


def test_ticket_service_get_ticket_detail_api(client, shared_ticket, shared_user, shared_event):
    with patch("app.services.ticket_service.TicketService.get_ticket_detail") as mock_service:
        mock_service.return_value = {
            "ticketId": shared_ticket["id"],
            "userId": shared_user["user_id"],
            "eventId": shared_event["id"],
            "status": "unused",
            "checkinAvailable": True,
        }

        response = client.get(f"/v1/tickets/{shared_ticket['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["ticketId"] == shared_ticket["id"]
    mock_service.assert_called_once()
