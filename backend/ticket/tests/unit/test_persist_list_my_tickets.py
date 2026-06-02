def test_persist_list_my_tickets_filters_by_status(ticket_repo, make_db_ticket):
    ticket_repo.create(make_db_ticket(ticket_id="ticket_001", user_id="user_001", transaction_id="tx_001", status="unused"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_002", user_id="user_001", transaction_id="tx_002", status="used"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_003", user_id="user_002", transaction_id="tx_003", status="unused"))

    all_user_tickets = ticket_repo.get_user_tickets("user_001")
    unused_user_tickets = ticket_repo.get_user_tickets("user_001", status="unused")

    assert {ticket.ticket_id for ticket in all_user_tickets} == {"ticket_001", "ticket_002"}
    assert [ticket.ticket_id for ticket in unused_user_tickets] == ["ticket_001"]
