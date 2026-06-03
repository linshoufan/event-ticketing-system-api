def test_list_event_tickets_returns_summary(ticket_service, repo, make_ticket, shared_event):
    repo.get_event_tickets.return_value = [make_ticket(ticket_id="ticket_001")]
    repo.count_event_tickets.return_value = 1
    repo.get_event_summary.return_value = {"used": 0, "unused": 1, "invalid": 0}

    result = ticket_service.get_event_tickets(shared_event["id"], status_filter="unused", page=1, limit=50)

    assert result["summary"]["unused"] == 1
    assert result["tickets"][0]["ticketId"] == "ticket_001"
    assert result["tickets"][0]["status"] == "unused"
    assert result["total"] == 1
