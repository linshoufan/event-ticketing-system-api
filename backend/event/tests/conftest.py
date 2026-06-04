from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.dependencies import get_current_user, CurrentUser
from app.core.security import jwt

# 測試資料庫名稱
TEST_DB_NAME = "test_event_db"

def ensure_test_db_exists():
    """確保 PostgreSQL 測試資料庫存在。"""
    admin_url = f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}@{settings.event_db_host}:{settings.event_db_port}/postgres"
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
    f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}"
    f"@{settings.event_db_host}:{settings.event_db_port}/{TEST_DB_NAME}"
)

@pytest.fixture(scope="session")
def shared_data():
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture
def client(db_session):
    app.dependency_overrides.clear()
    
    def _client(role="hr"):
        def override_get_db():
            yield db_session
        
        def override_user_check():
            if role is None:
                raise HTTPException(status_code=401, detail={"code": "NOT_LOGGED_IN"})
            return CurrentUser(user_id="test_user", role=role)
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_user_check
        return TestClient(app)
    
    yield _client
    app.dependency_overrides.clear()

@pytest.fixture
def raw_client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    def _auth_headers(user_id: str, role: str, expired: bool = False, incomplete: bool = False) -> dict:
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        if expired:
            payload["exp"] = datetime.now(timezone.utc) - timedelta(hours=1)
        if incomplete:
            del payload["role"]
            
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers

@pytest.fixture
def valid_event_payload():
    return {
        "name": "Original Event Name",
        "description": "desc",
        "location": "loc",
        "category": "music",
        "guestAllowed": True,
        "ticketLimit": 100,
        "remainingTickets": 100,
        "eventStartTime": "2026-06-02T09:00:00Z",
        "eventEndTime": "2026-06-02T18:00:00Z",
        "registrationStart": "2026-06-01T09:00:00Z",
        "registrationEnd": "2026-06-01T18:00:00Z",
        "status": "not_open",
        "isDraft": False
    }

@pytest.fixture(scope="session")
def base_url():
    return ""
