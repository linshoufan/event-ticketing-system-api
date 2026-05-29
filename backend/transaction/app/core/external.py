"""跨服務 HTTP clients：AccountClient, EventClient, TicketClient。

設計原則：
1. Client 是「翻譯層」：HTTP response → 對 service 層友善的 Python dict / dataclass。
   service 層不該看到 httpx.Response 或 status_code，只看到 typed 結果或 exception。
2. 跨服務錯誤一律轉成 ExternalServiceError 子類別，service 層 catch 後再決定要不要
   轉成對使用者的 HTTPException（避免把對方服務的錯誤訊息直接吐給使用者）。
3. 短期 TTL cache 減少重複呼叫（會在 service 層 invalidate）。
4. TicketClient 支援 mock 模式（settings.ticket_service_enabled=False 時走 mock），
   等真實 Ticket Service 整合後改 True 即可，service 層程式碼一行都不用改。
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class ExternalServiceError(Exception):
    """跨服務呼叫的 base exception。"""
    def __init__(self, service: str, message: str, status_code: int | None = None):
        self.service = service
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")


class ExternalNotFoundError(ExternalServiceError):
    """對方服務回 404（resource 不存在）。"""
    pass


class ExternalUnavailableError(ExternalServiceError):
    """對方服務 5xx 或無法連線。"""
    pass


# ============================================================================
# Event Status（對齊 Event Service 的 enum）
# ============================================================================
# Event Service 的 status 是 int：
#   0 = NOT_OPEN (報名未開放)
#   1 = REGISTERING (報名中)
#   2 = WAITLIST (候補登記)
#   3 = CLOSED (報名截止)
#   4 = ENDED (活動結束)
EVENT_STATUS_NOT_OPEN = 0
EVENT_STATUS_REGISTERING = 1
EVENT_STATUS_WAITLIST = 2
EVENT_STATUS_CLOSED = 3
EVENT_STATUS_ENDED = 4


# ============================================================================
# Result dataclasses（給 service 層用，避免直接傳 dict）
# ============================================================================

@dataclass
class RegistrationProfile:
    """Account Service 回傳的使用者報名資料。"""
    user_id: str
    role: str
    registration_status: str  # 'active' / 'locked'
    unlock_at: datetime | None
    autofill_diet_type: str | None
    autofill_self_driving: bool | None
    preferences: list[str]

    @property
    def is_locked(self) -> bool:
        return self.registration_status == "locked"


@dataclass
class EventInfo:
    """Event Service 回傳的活動詳情（只保留 transaction service 需要的欄位）。"""
    event_id: str
    name: str
    status: int  # EVENT_STATUS_* 之一
    is_draft: bool
    guest_allowed: bool
    ticket_limit: int | None  # None = 無限制
    remaining_tickets: int    # 對方算出來的，僅供顯示，我們的真實來源還是自己的 DB
    cancellation_deadline: datetime | None
    registration_start: datetime
    registration_end: datetime
    event_start_time: datetime
    event_end_time: datetime

    @property
    def has_capacity_limit(self) -> bool:
        return self.ticket_limit is not None

    def is_registration_open(self, now: datetime | None = None) -> bool:
        """是否在報名期間內。"""
        now = now or datetime.now(timezone.utc)
        return self.registration_start <= now <= self.registration_end


# ============================================================================
# 輔助函式
# ============================================================================

def _parse_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    # Python 3.11+ 的 fromisoformat 支援 ISO 8601 with timezone
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _classify_http_error(service: str, exc: httpx.HTTPStatusError) -> ExternalServiceError:
    status = exc.response.status_code
    try:
        body = exc.response.json()
        message = body.get("error", {}).get("message") or body.get("message") or str(body)
    except Exception:
        message = exc.response.text or str(exc)
    if status == 404:
        return ExternalNotFoundError(service, message, status_code=status)
    if status >= 500:
        return ExternalUnavailableError(service, message, status_code=status)
    return ExternalServiceError(service, message, status_code=status)


# ============================================================================
# AccountClient
# ============================================================================

class AccountClient:
    """呼叫 Account Service 的 internal API。"""

    def __init__(self, base_url: str | None = None, internal_key: str | None = None, timeout: float = 5.0):
        self._client = httpx.Client(
            base_url=base_url or settings.account_service_url,
            timeout=timeout,
            headers={"X-Internal-Key": internal_key or settings.internal_api_key},
        )
        self._cache = TTLCache(default_ttl=15.0)  # registration profile 15 秒快取夠了

    def close(self) -> None:
        self._client.close()

    def get_registration_profile(self, user_id: str) -> RegistrationProfile:
        """GET /v1/internal/users/{user_id}/registration-profile"""
        cache_key = f"profile:{user_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self._client.get(f"/v1/internal/users/{user_id}/registration-profile")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _classify_http_error("AccountService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("AccountService", f"network error: {exc}") from exc

        data = response.json().get("data", {})
        autofill = data.get("autofill", {}) or {}
        profile = RegistrationProfile(
            user_id=data["userId"],
            role=data["role"],
            registration_status=data["registrationStatus"],
            unlock_at=_parse_iso(data.get("unlockAt")),
            autofill_diet_type=autofill.get("dietType"),
            autofill_self_driving=autofill.get("selfDriving"),
            preferences=data.get("preferences", []),
        )
        self._cache.set(cache_key, profile)
        return profile

    def invalidate_profile_cache(self, user_id: str) -> None:
        self._cache.invalidate(f"profile:{user_id}")

    def punish_user(self, user_id: str) -> dict[str, Any]:
        """POST /v1/internal/users/{user_id}/punish

        對使用者進行 30 天停權處罰（爽約懲罰）。
        呼叫成功會自動 invalidate 該 user 的 profile cache。
        """
        try:
            response = self._client.post(f"/v1/internal/users/{user_id}/punish")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _classify_http_error("AccountService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("AccountService", f"network error: {exc}") from exc

        self.invalidate_profile_cache(user_id)
        return response.json().get("data", {})


# ============================================================================
# EventClient
# ============================================================================

class EventClient:
    """呼叫 Event Service 的公開 API（無需 internal key）。"""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self._client = httpx.Client(
            base_url=base_url or settings.event_service_url,
            timeout=timeout,
        )
        self._cache = TTLCache(default_ttl=30.0)

    def close(self) -> None:
        self._client.close()

    def get_event(self, event_id: str) -> EventInfo:
        """GET /v1/events/{eventId}"""
        cache_key = f"event:{event_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            response = self._client.get(f"/v1/events/{event_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _classify_http_error("EventService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("EventService", f"network error: {exc}") from exc

        data = response.json().get("data", {})
        event = EventInfo(
            event_id=data["eventId"],
            name=data["name"],
            status=data["status"],
            is_draft=data.get("isDraft", False),
            guest_allowed=data.get("guestAllowed", False),
            ticket_limit=data.get("ticketLimit"),
            remaining_tickets=data.get("remainingTickets", 0),
            cancellation_deadline=_parse_iso(data.get("cancellationDeadline")),
            registration_start=_parse_iso(data["registrationStart"]),
            registration_end=_parse_iso(data["registrationEnd"]),
            event_start_time=_parse_iso(data["eventStartTime"]),
            event_end_time=_parse_iso(data["eventEndTime"]),
        )
        self._cache.set(cache_key, event)
        return event

    def invalidate_event_cache(self, event_id: str) -> None:
        self._cache.invalidate(f"event:{event_id}")


# ============================================================================
# TicketClient
# ============================================================================

class TicketClient:
    """呼叫 Ticket Service 的 internal API。

    ⚠️ 目前 Ticket Service 尚未在 dev branch 整合，所以這個 client 預設走 mock 模式：
    - mock 模式：issue_ticket 直接產生 UUID 當 ticket_id 回傳，不打 HTTP
    - 真實模式：依 docs/internal-api-spec.md 中「Ticket Service」段落實作

    切換方式：設定 TICKET_SERVICE_ENABLED=true（settings.ticket_service_enabled）
    """

    def __init__(self, base_url: str | None = None, internal_key: str | None = None, timeout: float = 5.0):
        self._enabled = settings.ticket_service_enabled
        self._client = httpx.Client(
            base_url=base_url or settings.ticket_service_url,
            timeout=timeout,
            headers={"X-Internal-Key": internal_key or settings.internal_api_key},
        )

    def close(self) -> None:
        self._client.close()

    def issue_ticket(self, *, user_id: str, event_id: str, transaction_id: str) -> str:
        """配發票券 → 回傳 ticket_id。

        對應的真實 API: POST /v1/internal/tickets
        """
        if not self._enabled:
            mock_ticket_id = f"mock-{uuid.uuid4()}"
            logger.info(
                "TicketClient(mock) issue_ticket → %s for user=%s event=%s tx=%s",
                mock_ticket_id, user_id, event_id, transaction_id,
            )
            return mock_ticket_id

        try:
            response = self._client.post(
                "/v1/internal/tickets",
                json={
                    "userId": user_id,
                    "eventId": event_id,
                    "transactionId": transaction_id,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _classify_http_error("TicketService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("TicketService", f"network error: {exc}") from exc

        return response.json()["data"]["ticketId"]

    def void_ticket(self, ticket_id: str) -> None:
        """作廢票券（取消報名時呼叫）。

        對應的真實 API: DELETE /v1/internal/tickets/{ticket_id}
        若 ticket 已被 check-in（used），對方會回 409；我們的呼叫時機是
        cancellation deadline 之前，理論上不會 used，但仍應正確處理。
        """
        if not self._enabled:
            logger.info("TicketClient(mock) void_ticket → %s", ticket_id)
            return

        try:
            response = self._client.delete(f"/v1/internal/tickets/{ticket_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # 404 視為已不存在 → 視為成功（idempotent）
            if exc.response.status_code == 404:
                return
            raise _classify_http_error("TicketService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("TicketService", f"network error: {exc}") from exc

    def list_unused_tickets(self, event_id: str) -> list[str]:
        """活動結束後，撈出該活動所有「狀態為 unused」的 ticket_id 清單，
        給 transaction service 跑 no-show punishment 用。

        對應的真實 API: GET /v1/internal/tickets/no-show?eventId=...
        """
        if not self._enabled:
            logger.info("TicketClient(mock) list_unused_tickets event=%s → []", event_id)
            return []

        try:
            response = self._client.get(
                "/v1/internal/tickets/no-show",
                params={"eventId": event_id},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise _classify_http_error("TicketService", exc) from exc
        except httpx.RequestError as exc:
            raise ExternalUnavailableError("TicketService", f"network error: {exc}") from exc

        return response.json().get("data", {}).get("ticketIds", [])


# ============================================================================
# Module-level singletons + FastAPI dependencies
# ============================================================================
# 每個 client 都是 thread-safe 的 httpx.Client wrapper，pod 內共用一個 instance
# 就好；FastAPI 用 Depends 注入，方便測試時 monkeypatch。

_account_client: AccountClient | None = None
_event_client: EventClient | None = None
_ticket_client: TicketClient | None = None


def get_account_client() -> AccountClient:
    global _account_client
    if _account_client is None:
        _account_client = AccountClient()
    return _account_client


def get_event_client() -> EventClient:
    global _event_client
    if _event_client is None:
        _event_client = EventClient()
    return _event_client


def get_ticket_client() -> TicketClient:
    global _ticket_client
    if _ticket_client is None:
        _ticket_client = TicketClient()
    return _ticket_client