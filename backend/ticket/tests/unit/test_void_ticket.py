import pytest
from fastapi import HTTPException


def test_void_ticket_success(ticket_service, repo, make_ticket, shared_ticket):
    ticket = make_ticket(ticket_id=shared_ticket["id"], status="unused")
    repo.get_by_id.return_value = ticket

    result = ticket_service.void_ticket(shared_ticket["id"])

    assert result is True
    repo.delete.assert_called_once_with(ticket)


def test_void_missing_ticket_is_idempotent(ticket_service, repo, shared_ticket):
    repo.get_by_id.return_value = None

    result = ticket_service.void_ticket(shared_ticket["id"])

    assert result is True
    repo.delete.assert_not_called()


def test_void_used_ticket_is_rejected(ticket_service, repo, make_ticket, shared_ticket):
    repo.get_by_id.return_value = make_ticket(ticket_id=shared_ticket["id"], status="used")

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.void_ticket(shared_ticket["id"])

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "ALREADY_USED"
    repo.delete.assert_not_called()
