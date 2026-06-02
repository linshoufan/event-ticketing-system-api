import httpx
from app.core.external import TicketClient

def test_ticket_client_issue_ticket(monkeypatch):
    """測試 ticket service 發票。"""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/internal/tickets"
        return httpx.Response(201, json={"data": {"ticketId": "real-ticket-xyz"}})

    client = TicketClient(base_url="http://test", internal_key="test-key")
    client._client = httpx.Client(
        base_url="http://test",
        headers={"X-Internal-Key": "test-key"},
        transport=httpx.MockTransport(handler),
    )
    ticket_id = client.issue_ticket(user_id="user_006", event_id="event_008", transaction_id="tx_001")
    assert ticket_id == "real-ticket-xyz"

def test_ticket_client_void_404_is_treated_as_success(monkeypatch):
    """void_ticket 收到 404 應該視為成功（idempotent）。"""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "gone"}})

    client = TicketClient(base_url="http://test", internal_key="test-key")
    client._client = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    )
    # 不應丟錯
    client.void_ticket("ticket-x")
