from unittest.mock import MagicMock, patch


def test_ticket_service_issue_ticket_api(client, shared_user, shared_event):
    with patch("app.services.ticket_service.TicketService.create_ticket") as mock_create:
        mock_ticket = MagicMock()
        mock_ticket.to_dict.return_value = {"ticketId": "ticket_new"}
        mock_create.return_value = mock_ticket

        payload = {
            "userId": shared_user["user_id"],
            "eventId": shared_event["id"],
            "transactionId": "tx_new",
        }

        response = client.post("/v1/internal/tickets", json=payload)

    assert response.status_code == 201
    assert response.json()["data"]["ticketId"] == "ticket_new"
