"""pytest 共用 fixtures。

設計：
- 用真實 Postgres（advisory lock 與 partial index 需要），連線資訊由環境變數帶入
- 每個 test 前後清空 transactions 表，確保互不干擾
- 外部服務（Account / Event / Ticket）一律用 fake 物件，透過 dependency_overrides 注入
- token fixture 用與 settings 相同的 secret 簽 JWT，連帶測到 dependency 的解析

需要的環境變數（CI / 本地都要設）：
    TRANSACTION_DB_USER / PASSWORD / HOST / PORT / NAME
    JWT_SECRET_KEY / JWT_ALGORITHM / INTERNAL_API_KEY
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from app.core.dependencies import get_current_user, CurrentUser
from app.core.external import (
    EVENT_STATUS_REGISTERING,
    EventInfo,
    RegistrationProfile,
    get_account_client,
    get_event_client,
    get_ticket_client,
)
from app.main import app
from app.models.transaction import Transaction

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _ensure_schema():
    """確保 transactions 表存在（測試環境用 create_all，正式環境走 alembic）。"""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    # 清空，確保乾淨起點
    session.query(Transaction).delete()
    session.commit()
    try:
        yield session
    finally:
        session.query(Transaction).delete()
        session.commit()
        session.close()


# ---------------------------------------------------------------------------
# Fake external clients
# ---------------------------------------------------------------------------
class FakeAccountClient:
    def __init__(self):
        self.profiles: dict[str, RegistrationProfile] = {}
        self.punished: list[str] = []

    def set_profile(self, user_id, role="employee", locked=False,
                    diet="non-veg", driving=False):
        self.profiles[user_id] = RegistrationProfile(
            user_id=user_id, role=role,
            registration_status="locked" if locked else "active",
            unlock_at=(NOW + timedelta(days=30)) if locked else None,
            autofill_diet_type=diet, autofill_self_driving=driving,
            preferences=[],
        )

    def get_registration_profile(self, user_id):
        from app.core.external import ExternalNotFoundError
        if user_id not in self.profiles:
            raise ExternalNotFoundError("AccountService", "user not found", 404)
        return self.profiles[user_id]

    def punish_user(self, user_id):
        self.punished.append(user_id)
        return {"userId": user_id, "registrationStatus": "locked"}


class FakeEventClient:
    def __init__(self):
        self.events: dict[str, EventInfo] = {}

    def set_event(self, event_id, ticket_limit=None, cancellation_deadline=None,
                  is_draft=False, status=EVENT_STATUS_REGISTERING,
                  reg_open=True):
        self.events[event_id] = EventInfo(
            event_id=event_id, name=f"Event {event_id}", status=status,
            is_draft=is_draft, guest_allowed=(ticket_limit is None),
            ticket_limit=ticket_limit, remaining_tickets=0,
            cancellation_deadline=cancellation_deadline,
            registration_start=(NOW - timedelta(days=1)) if reg_open else (NOW + timedelta(days=1)),
            registration_end=NOW + timedelta(days=7),
            event_start_time=NOW + timedelta(days=10),
            event_end_time=NOW + timedelta(days=10, hours=4),
        )

    def get_event(self, event_id):
        from app.core.external import ExternalNotFoundError
        if event_id not in self.events:
            raise ExternalNotFoundError("EventService", "event not found", 404)
        return self.events[event_id]


class FakeTicketClient:
    def __init__(self):
        self._counter = 0
        self.issued: list[str] = []
        self.voided: list[str] = []
        self.unused: list[str] = []

    def issue_ticket(self, *, user_id, event_id, transaction_id):
        self._counter += 1
        tid = f"tk-{self._counter}"
        self.issued.append(tid)
        return tid

    def void_ticket(self, ticket_id):
        self.voided.append(ticket_id)

    def list_unused_tickets(self, event_id):
        return list(self.unused)


@pytest.fixture
def fake_account():
    return FakeAccountClient()


@pytest.fixture
def fake_event():
    return FakeEventClient()


@pytest.fixture
def fake_ticket():
    return FakeTicketClient()


# ---------------------------------------------------------------------------
# Client with overrides
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db, fake_account, fake_event, fake_ticket):
    from app.core.database import get_db

    def _get_db_override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_account_client] = lambda: fake_account
    app.dependency_overrides[get_event_client] = lambda: fake_event
    app.dependency_overrides[get_ticket_client] = lambda: fake_ticket

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def make_token(user_id: str, role: str = "employee") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@pytest.fixture
def auth():
    def _auth(user_id: str, role: str = "employee") -> dict:
        return {"Authorization": f"Bearer {make_token(user_id, role)}"}
    return _auth