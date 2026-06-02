def test_persist_issued_ticket(ticket_repo, make_db_ticket, shared_ticket):
    ticket = make_db_ticket()

    created = ticket_repo.create(ticket)
    found = ticket_repo.get_by_id(shared_ticket["id"])

    assert created.ticket_id == shared_ticket["id"]
    assert found.ticket_id == shared_ticket["id"]
    assert found.user_id == shared_ticket["user_id"]


def test_find_issued_ticket_by_transaction(ticket_repo, make_db_ticket, shared_ticket):
    ticket_repo.create(make_db_ticket())

    found = ticket_repo.get_by_transaction_id(shared_ticket["transaction_id"])

    assert found.ticket_id == shared_ticket["id"]


def test_save_checked_in_ticket_status(ticket_repo, make_db_ticket, shared_ticket):
    ticket = ticket_repo.create(make_db_ticket(status="unused"))
    ticket.status = "used"

    ticket_repo.save()
    found = ticket_repo.get_by_id(shared_ticket["id"])

    assert found.status == "used"
