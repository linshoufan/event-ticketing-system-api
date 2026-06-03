from unittest.mock import patch


def test_ticket_service_list_no_show_tickets_api(client, shared_event):
    with patch("app.services.ticket_service.TicketService.get_unused_tickets_for_ended_event") as mock_service:
        mock_service.return_value = ["ticket_001", "ticket_002"]

        response = client.get(f"/v1/internal/tickets/no-show?eventId={shared_event['id']}")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "eventId": shared_event["id"],
        "ticketIds": ["ticket_001", "ticket_002"],
    }
