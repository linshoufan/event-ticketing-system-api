"""pytest 共用 fixtures。

測試使用 PostgreSQL (test_transaction_db)；外部服務（Account / Event / Ticket）一律用 fake 物件，
透過 dependency_overrides 注入。token fixture 用與 settings 相同的 secret 簽 JWT。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core import database as database_module
from app.core.database import Base
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
_UNSET = object()

TEST_DB_NAME = "test_transaction_db"

def ensure_test_db_exists():
    """確保 PostgreSQL 測試資料庫存在。"""
    admin_url = f"postgresql+psycopg2://{settings.transaction_db_user}:{settings.transaction_db_password}@{settings.transaction_db_host}:{settings.transaction_db_port}/postgres"
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'"))
        if not result.fetchone():
            print(f"🛠️ Creating test database: {TEST_DB_NAME}")
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    engine.dispose()

try:
    ensure_test_db_exists()
except Exception as e:
    print(f"⚠️ Warning: Failed to ensure test database exists: {e}")

TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.transaction_db_user}:{settings.transaction_db_password}"
    f"@{settings.transaction_db_host}:{settings.transaction_db_port}/{TEST_DB_NAME}"
)

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

database_module.engine = test_engine
database_module.SessionLocal = TestingSessionLocal


def _load_shared_mock_data() -> dict:
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)


_SHARED_MOCK_DATA = _load_shared_mock_data()
_SHARED_USERS = {u["user_id"]: u for u in _SHARED_MOCK_DATA.get("users", [])}
_SHARED_EVENTS = {e["id"]: e for e in _SHARED_MOCK_DATA.get("events", [])}


def _shared_user(user_id: str) -> dict:
    return _SHARED_USERS.get(user_id, {})


def _shared_event(event_id: str) -> dict:
    return _SHARED_EVENTS.get(event_id, {})

# DB
@pytest.fixture(scope="session", autouse=True)
def db_engine():
    Base.metadata.create_all(bind=test_engine)
    yield test_engine

@pytest.fixture
def db(db_engine):
    session = TestingSessionLocal()
    # 測試前清空
    session.query(Transaction).delete()
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

# Fake external clients
class FakeAccountClient:
    def __init__(self):
        self.profiles: dict[str, RegistrationProfile] = {}
        self.punished: list[str] = []
        self.autofill_updates: list[dict] = []
        self.invalidated: list[str] = []

    def set_profile(self, user_id, role=None, locked=False,
                    diet=None, driving=None, username=None, guest_count=None):
        shared = _shared_user(user_id)
        registration_status = shared.get("registration_status", "active")
        role = role or shared.get("role", "employee")
        locked = locked or registration_status == "locked"
        diet = diet if diet is not None else shared.get("diet_type", "non-veg")
        driving = driving if driving is not None else shared.get("self_driving", False)
        username = username if username is not None else shared.get("username")
        self.profiles[user_id] = RegistrationProfile(
            user_id=user_id, role=role,
            registration_status="locked" if locked else "active",
            unlock_at=(NOW + timedelta(days=30)) if locked else None,
            autofill_diet_type=diet, autofill_self_driving=driving,
            autofill_guest_count=guest_count,  
            preferences=[],
            username=username,
        )

    def get_registration_profile(self, user_id, category=None):
        from app.core.external import ExternalNotFoundError
        if user_id not in self.profiles:
            raise ExternalNotFoundError("AccountService", "user not found", 404)
        return self.profiles[user_id]


    def update_autofill(self, user_id, diet_type, self_driving, category=None, guest_count=None):
        self.autofill_updates.append({
            "userId": user_id, "category": category,
            "dietType": diet_type, "selfDriving": self_driving, "guestCount": guest_count,
        })
        if user_id in self.profiles:
            prof = self.profiles[user_id]
            if diet_type is not None:
                prof.autofill_diet_type = diet_type
            if self_driving is not None:
                prof.autofill_self_driving = self_driving

    def invalidate_profile_cache(self, user_id):
        self.invalidated.append(user_id)

    def punish_user(self, user_id):
        self.punished.append(user_id)
        self.invalidate_profile_cache(user_id)
        return {"userId": user_id, "registrationStatus": "locked"}


class FakeEventClient:
    def __init__(self):
        self.events: dict[str, EventInfo] = {}

    def set_event(self, event_id, ticket_limit=_UNSET, cancellation_deadline=_UNSET,
                  is_draft=False, status=EVENT_STATUS_REGISTERING,
                  reg_open=True, category=None):
        shared = _shared_event(event_id)
        if ticket_limit is _UNSET:
            ticket_limit = shared.get("ticket_limit")
        if cancellation_deadline is _UNSET:
            if "cancellation_offset" in shared:
                cancellation_deadline = NOW + timedelta(hours=shared["time_offset"] - shared["cancellation_offset"])
            else:
                cancellation_deadline = None

        guest_allowed = shared.get("guest_allowed")
        if guest_allowed is None:
            guest_allowed = ticket_limit is None

        event_name = shared.get("name", f"Event {event_id}")
        self.events[event_id] = EventInfo(
            event_id=event_id, name=event_name, status=status,
            category=category or shared.get("category"),
            is_draft=is_draft, guest_allowed=guest_allowed,
            ticket_limit=ticket_limit, remaining_tickets=shared.get("remaining_tickets", 0),
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


# Client with overrides
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


# Auth helpers
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
