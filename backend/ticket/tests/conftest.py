from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.dependencies import CurrentUser, get_current_user, verify_internal_key
from app.core.external import AccountClient, EventInfo, get_event_client, get_account_client
from app.models.ticket import Ticket
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_service import TicketService
from main import app

# Use Real PostgreSQL for consistency across services
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.ticket_db_user}:{settings.ticket_db_password}"
    f"@{settings.ticket_db_host}:{settings.ticket_db_port}/test_ticket_db"
)

def clear_database(session):
    """Clean all tables to ensure test isolation."""
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

@pytest.fixture(scope="session")
def shared_data():
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def shared_user(shared_data):
    return shared_data["users"][0]

@pytest.fixture
def shared_ticket(shared_data):
    return shared_data["tickets"][0]

@pytest.fixture
def shared_event(shared_data):
    return shared_data["events"][0]

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    clear_database(session)
    try:
        yield session
    finally:
        session.rollback()
        clear_database(session)
        session.close()

@pytest.fixture
def ticket_repo(db_session):
    return TicketRepository(db_session)

@pytest.fixture
def make_ticket(shared_user, shared_event):
    def _make_ticket(
        *,
        ticket_id=None,
        user_id=None,
        event_id=None,
        transaction_id="tx_001",
        status="unused",
    ):
        return Ticket(
            ticket_id=ticket_id or "ticket_001",
            user_id=user_id or shared_user["user_id"],
            event_id=event_id or shared_event["id"],
            transaction_id=transaction_id,
            status=status,
        )
    return _make_ticket

@pytest.fixture
def make_db_ticket(shared_ticket):
    def _make_db_ticket(
        *,
        ticket_id=None,
        user_id=None,
        event_id=None,
        transaction_id=None,
        status=None,
    ):
        return Ticket(
            ticket_id=ticket_id or shared_ticket["id"],
            user_id=user_id or shared_ticket["user_id"],
            event_id=event_id or shared_ticket["event_id"],
            transaction_id=transaction_id or shared_ticket["transaction_id"],
            status=status or shared_ticket["status"],
        )
    return _make_db_ticket

@pytest.fixture
def make_event_info(shared_event):
    def _make_event_info(
        *,
        event_id=None,
        name=None,
        location=None,
        latitude=25.0339,
        longitude=121.5644,
        checkin_radius_meters=100,
        event_start_time=None,
        event_end_time=None,
    ):
        now = datetime.now(timezone.utc)
        return EventInfo(
            event_id=event_id or shared_event["id"],
            name=name or shared_event["name"],
            location=location or shared_event["location"],
            latitude=latitude,
            longitude=longitude,
            checkin_radius_meters=checkin_radius_meters,
            event_start_time=event_start_time or now - timedelta(hours=1),
            event_end_time=event_end_time or now + timedelta(hours=1),
        )
    return _make_event_info

@pytest.fixture
def repo():
    return MagicMock(spec=TicketRepository)

@pytest.fixture
def event_client():
    return MagicMock()

@pytest.fixture
def account_client():
    return MagicMock(spec=AccountClient)

@pytest.fixture
def ticket_service(repo, event_client, account_client):
    return TicketService(repo, event_client, account_client)

@pytest.fixture
def current_user_role():
    return "employee"

@pytest.fixture
def client(shared_user, current_user_role, db_session, event_client, account_client):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=shared_user["user_id"],
        role=current_user_role,
    )
    app.dependency_overrides[verify_internal_key] = lambda: None
    app.dependency_overrides[get_event_client] = lambda: event_client
    app.dependency_overrides[get_account_client] = lambda: account_client

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
