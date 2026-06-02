import pytest
from fastapi import HTTPException


def test_get_ticket_detail_rejects_other_user(ticket_service, repo, make_ticket, shared_ticket):
    repo.get_by_id.return_value = make_ticket(ticket_id=shared_ticket["id"], user_id="user_001")

    with pytest.raises(HTTPException) as exc_info:
        ticket_service.get_ticket_detail(shared_ticket["id"], current_user_id="user_002")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "FORBIDDEN"
