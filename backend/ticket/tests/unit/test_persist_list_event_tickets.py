def test_persist_list_event_tickets_filters_and_paginates(ticket_repo, make_db_ticket):
    for index in range(5):
        ticket_repo.create(
            make_db_ticket(
                ticket_id=f"ticket_{index:03d}",
                user_id=f"user_{index:03d}",
                event_id="event_005",
                transaction_id=f"tx_{index:03d}",
                status="unused",
            )
        )
    ticket_repo.create(
        make_db_ticket(
            ticket_id="ticket_used",
            user_id="user_999",
            event_id="event_005",
            transaction_id="tx_used",
            status="used",
        )
    )

    page_two = ticket_repo.get_event_tickets("event_005", status="unused", page=2, limit=2)

    assert [ticket.ticket_id for ticket in page_two] == ["ticket_002", "ticket_003"]


def test_count_event_tickets(ticket_repo, make_db_ticket):
    ticket_repo.create(make_db_ticket(ticket_id="ticket_001", event_id="event_005", transaction_id="tx_001", status="unused"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_002", event_id="event_005", transaction_id="tx_002", status="used"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_003", event_id="event_006", transaction_id="tx_003", status="unused"))

    assert ticket_repo.count_event_tickets("event_005") == 2
    assert ticket_repo.count_event_tickets("event_005", status="unused") == 1


def test_summarize_event_tickets(ticket_repo, make_db_ticket):
    ticket_repo.create(make_db_ticket(ticket_id="ticket_001", event_id="event_005", transaction_id="tx_001", status="unused"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_002", event_id="event_005", transaction_id="tx_002", status="used"))
    ticket_repo.create(make_db_ticket(ticket_id="ticket_003", event_id="event_005", transaction_id="tx_003", status="used"))

    summary = ticket_repo.get_event_summary("event_005")

    assert summary == {"used": 2, "unused": 1, "invalid": 0}
