from unittest.mock import patch


def test_ticket_service_void_ticket_api(client, shared_ticket):
    with patch("app.services.ticket_service.TicketService.void_ticket") as mock_void:
        mock_void.return_value = True

        response = client.delete(f"/v1/internal/tickets/{shared_ticket['id']}")

    assert response.status_code == 200
    assert response.json()["data"] == {"ticketId": shared_ticket["id"], "voided": True}


def test_ticket_service_delete_event_tickets_api(client, shared_event):
    with patch("app.services.ticket_service.TicketService.delete_event_tickets") as mock_delete:
        mock_delete.return_value = 2

        response = client.delete(f"/v1/internal/tickets/events/{shared_event['id']}")

    assert response.status_code == 200
    assert response.json()["data"] == {"eventId": shared_event["id"], "deletedCount": 2}
    mock_delete.assert_called_once_with(shared_event["id"])
