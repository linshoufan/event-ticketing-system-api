"""跨服務 client 的單元測試。

用 httpx.MockTransport 模擬對方服務的 HTTP 回應，不需要實際跑 Account / Event Service。
"""
from datetime import datetime, timezone

import httpx
import pytest

from app.core.external import (
    AccountClient,
    EventClient,
    ExternalNotFoundError,
    ExternalUnavailableError,
    TicketClient,
    EVENT_STATUS_REGISTERING,
)


# ============================================================================
# AccountClient
# ============================================================================

def _make_account_client(handler) -> AccountClient:
    """用 mock transport 建立 AccountClient。"""
    client = AccountClient(base_url="http://test", internal_key="test-key")
    client._client = httpx.Client(
        base_url="http://test",
        headers={"X-Internal-Key": "test-key"},
        transport=httpx.MockTransport(handler),
    )
    return client


def test_account_client_get_registration_profile_active():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Internal-Key"] == "test-key"
        assert request.url.path == "/v1/internal/users/u-1/registration-profile"
        return httpx.Response(200, json={
            "data": {
                "userId": "u-1",
                "role": "employee",
                "registrationStatus": "active",
                "unlockAt": None,
                "autofill": {"dietType": "veg", "selfDriving": True},
                "preferences": ["sport"],
            }
        })

    client = _make_account_client(handler)
    profile = client.get_registration_profile("u-1")

    assert profile.user_id == "u-1"
    assert profile.role == "employee"
    assert profile.registration_status == "active"
    assert profile.is_locked is False
    assert profile.autofill_diet_type == "veg"
    assert profile.autofill_self_driving is True
    assert profile.preferences == ["sport"]


def test_account_client_get_registration_profile_locked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {
                "userId": "u-2",
                "role": "employee",
                "registrationStatus": "locked",
                "unlockAt": "2026-06-20T08:00:00+00:00",
                "autofill": {"dietType": "non-veg", "selfDriving": False},
                "preferences": [],
            }
        })

    client = _make_account_client(handler)
    profile = client.get_registration_profile("u-2")

    assert profile.is_locked is True
    assert profile.unlock_at == datetime(2026, 6, 20, 8, 0, tzinfo=timezone.utc)


def test_account_client_404_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"code": "USER_NOT_FOUND", "message": "no such user"}})

    client = _make_account_client(handler)
    with pytest.raises(ExternalNotFoundError):
        client.get_registration_profile("nope")


def test_account_client_5xx_raises_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream down")

    client = _make_account_client(handler)
    with pytest.raises(ExternalUnavailableError):
        client.get_registration_profile("u-1")


def test_account_client_caches_profile():
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json={
            "data": {
                "userId": "u-1", "role": "employee",
                "registrationStatus": "active", "unlockAt": None,
                "autofill": {"dietType": None, "selfDriving": None},
                "preferences": [],
            }
        })

    client = _make_account_client(handler)
    client.get_registration_profile("u-1")
    client.get_registration_profile("u-1")
    client.get_registration_profile("u-1")
    assert call_count["n"] == 1, "second call should be served from cache"


def test_account_client_punish_invalidates_cache():
    """punish_user 後再 get_registration_profile，必須重新打 API（不能拿到舊的 active）。"""
    call_log = []

    def handler(request: httpx.Request) -> httpx.Response:
        call_log.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, json={
                "data": {
                    "userId": "u-1", "role": "employee",
                    "registrationStatus": "active", "unlockAt": None,
                    "autofill": {"dietType": None, "selfDriving": None},
                    "preferences": [],
                }
            })
        return httpx.Response(200, json={
            "data": {
                "userId": "u-1",
                "registrationStatus": "locked",
                "unlockAt": "2026-12-31T00:00:00+00:00",
            }
        })

    client = _make_account_client(handler)
    client.get_registration_profile("u-1")    # GET (1)
    client.get_registration_profile("u-1")    # cached
    client.punish_user("u-1")                  # POST (2), invalidates cache
    client.get_registration_profile("u-1")    # GET again (3)

    methods = [m for m, _ in call_log]
    assert methods == ["GET", "POST", "GET"]


# ============================================================================
# EventClient
# ============================================================================

def _make_event_client(handler) -> EventClient:
    client = EventClient(base_url="http://test")
    client._client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler))
    return client


def test_event_client_get_event_with_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/events/evt-1"
        return httpx.Response(200, json={
            "data": {
                "eventId": "evt-1",
                "name": "Family Day",
                "status": 1,  # REGISTERING
                "isDraft": False,
                "guestAllowed": True,
                "ticketLimit": 100,
                "remainingTickets": 42,
                "cancellationDeadline": "2026-06-01T00:00:00Z",
                "registrationStart": "2026-05-01T00:00:00Z",
                "registrationEnd": "2026-06-15T00:00:00Z",
                "eventStartTime": "2026-06-20T00:00:00Z",
                "eventEndTime": "2026-06-20T08:00:00Z",
            }
        })

    client = _make_event_client(handler)
    event = client.get_event("evt-1")

    assert event.event_id == "evt-1"
    assert event.status == EVENT_STATUS_REGISTERING
    assert event.has_capacity_limit is True
    assert event.ticket_limit == 100
    assert event.guest_allowed is True
    assert event.cancellation_deadline == datetime(2026, 6, 1, tzinfo=timezone.utc)


def test_event_client_unlimited_event():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {
                "eventId": "evt-2", "name": "Open Lecture", "status": 1,
                "isDraft": False, "guestAllowed": False,
                "ticketLimit": None, "remainingTickets": 0,
                "cancellationDeadline": None,
                "registrationStart": "2026-05-01T00:00:00Z",
                "registrationEnd": "2026-12-31T00:00:00Z",
                "eventStartTime": "2026-06-20T00:00:00Z",
                "eventEndTime": "2026-06-20T08:00:00Z",
            }
        })

    client = _make_event_client(handler)
    event = client.get_event("evt-2")
    assert event.has_capacity_limit is False
    assert event.ticket_limit is None


def test_event_client_is_registration_open():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": {
                "eventId": "evt-3", "name": "X", "status": 1,
                "isDraft": False, "guestAllowed": False,
                "ticketLimit": None, "remainingTickets": 0,
                "cancellationDeadline": None,
                "registrationStart": "2026-05-01T00:00:00Z",
                "registrationEnd": "2026-06-01T00:00:00Z",
                "eventStartTime": "2026-06-20T00:00:00Z",
                "eventEndTime": "2026-06-20T08:00:00Z",
            }
        })

    client = _make_event_client(handler)
    event = client.get_event("evt-3")
    assert event.is_registration_open(now=datetime(2026, 5, 15, tzinfo=timezone.utc)) is True
    assert event.is_registration_open(now=datetime(2026, 7, 1, tzinfo=timezone.utc)) is False


def test_event_client_404():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"code": "EVENT_NOT_FOUND", "message": "..."}})

    client = _make_event_client(handler)
    with pytest.raises(ExternalNotFoundError):
        client.get_event("nope")


# ============================================================================
# TicketClient
# ============================================================================

def test_ticket_client_mock_mode_issue_returns_uuid(monkeypatch):
    """ticket_service_enabled=False 時，issue_ticket 不打 HTTP，直接給 mock id。"""
    monkeypatch.setattr("app.core.external.settings.ticket_service_enabled", False)
    client = TicketClient()
    ticket_id = client.issue_ticket(user_id="u-1", event_id="evt-1", transaction_id="tx-1")
    assert ticket_id.startswith("mock-")


def test_ticket_client_mock_mode_void_is_noop(monkeypatch):
    monkeypatch.setattr("app.core.external.settings.ticket_service_enabled", False)
    client = TicketClient()
    # 應該完全不丟錯
    client.void_ticket("any-id")


def test_ticket_client_mock_mode_list_unused_returns_empty(monkeypatch):
    monkeypatch.setattr("app.core.external.settings.ticket_service_enabled", False)
    client = TicketClient()
    assert client.list_unused_tickets("evt-1") == []


def test_ticket_client_real_mode_issue_ticket(monkeypatch):
    """模擬 ticket service enabled 時打真實 HTTP。"""
    monkeypatch.setattr("app.core.external.settings.ticket_service_enabled", True)

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
    ticket_id = client.issue_ticket(user_id="u-1", event_id="evt-1", transaction_id="tx-1")
    assert ticket_id == "real-ticket-xyz"


def test_ticket_client_void_404_is_treated_as_success(monkeypatch):
    """void_ticket 收到 404 應該視為成功（idempotent）。"""
    monkeypatch.setattr("app.core.external.settings.ticket_service_enabled", True)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"message": "gone"}})

    client = TicketClient(base_url="http://test", internal_key="test-key")
    client._client = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    )
    # 不應丟錯
    client.void_ticket("ticket-x")