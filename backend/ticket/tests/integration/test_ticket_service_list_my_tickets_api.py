from unittest.mock import patch


def test_ticket_service_list_my_tickets_api(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.get_user_tickets") as mock_service:
        mock_service.return_value = [
            {
                "ticketId": shared_ticket["id"],
                "eventId": shared_ticket["event_id"],
                "status": "unused",
                "checkinAvailable": True,
            }
        ]

        response = client.get("/v1/tickets")

    assert response.status_code == 200
    assert response.json()["data"][0]["ticketId"] == shared_ticket["id"]
