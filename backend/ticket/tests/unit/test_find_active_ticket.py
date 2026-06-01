def test_find_active_ticket_returns_unused_only(ticket_repo, make_db_ticket):
    ticket_repo.create(
        make_db_ticket(
            ticket_id="ticket_used",
            user_id="user_001",
            event_id="event_001",
            transaction_id="tx_used",
            status="used",
        )
    )
    ticket_repo.create(
        make_db_ticket(
            ticket_id="ticket_unused",
            user_id="user_001",
            event_id="event_001",
            transaction_id="tx_unused",
            status="unused",
        )
    )

    found = ticket_repo.get_active_ticket("user_001", "event_001")

    assert found.ticket_id == "ticket_unused"
