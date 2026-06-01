import pytest
from fastapi import HTTPException


def test_issue_ticket_success(ticket_service, repo, account_client, shared_user, shared_event):
    repo.get_by_transaction_id.return_value = None
    repo.get_active_ticket.return_value = None
    account_client.verify_user_exists.return_value = True

    ticket_service.create_ticket(
        shared_user["user_id"],
        shared_event["id"],
        "tx_new",
    )

    repo.create.assert_called_once()


def test_issue_ticket_is_idempotent(ticket_service, repo, account_client, make_ticket, shared_user, shared_event):
    existing = make_ticket(transaction_id="tx_001")
    repo.get_by_transaction_id.return_value = existing
    account_client.verify_user_exists.return_value = True

    result = ticket_service.create_ticket(shared_user["user_id"], shared_event["id"], "tx_001")

    assert result is existing
    repo.get_active_ticket.assert_not_called()
    repo.create.assert_not_called()


def test_issue_ticket_rejects_unknown_user(ticket_service, account_client, shared_user, shared_event):
    account_client.verify_user_exists.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.create_ticket(shared_user["user_id"], shared_event["id"], "tx_new")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "USER_NOT_FOUND"


def test_issue_ticket_rejects_existing_active_ticket(
    ticket_service,
    repo,
    account_client,
    make_ticket,
    shared_user,
    shared_event,
):
    active_ticket = make_ticket(ticket_id="ticket_001")
    repo.get_by_transaction_id.return_value = None
    repo.get_active_ticket.return_value = active_ticket
    account_client.verify_user_exists.return_value = True

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.create_ticket(shared_user["user_id"], shared_event["id"], "tx_new")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "TICKET_ALREADY_EXISTS"
