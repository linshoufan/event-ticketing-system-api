def test_list_my_tickets_enriches_event_data(ticket_service, repo, event_client, make_ticket, make_event_info, shared_user):
    ticket = make_ticket(user_id=shared_user["user_id"], status="unused")
    repo.get_user_tickets.return_value = [ticket]
    event_client.get_event.return_value = make_event_info()

    result = ticket_service.get_user_tickets(shared_user["user_id"])

    assert result[0]["ticketId"] == ticket.ticket_id
    assert result[0]["eventName"]
    assert result[0]["checkinAvailable"] is True
