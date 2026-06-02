def test_remove_ticket_deletes_record(ticket_repo, make_db_ticket, shared_ticket):
    ticket = ticket_repo.create(make_db_ticket())

    ticket_repo.delete(ticket)

    assert ticket_repo.get_by_id(shared_ticket["id"]) is None
