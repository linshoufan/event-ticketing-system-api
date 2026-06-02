from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from jose import jwt

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.dependencies import CurrentUser, get_current_user
from app.models.event import Event  # noqa: F401 ensure metadata is loaded

TEST_DATABASE_URL = "sqlite://"

@pytest.fixture(scope="session")
def shared_data():
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        # 清空所有資料表確保測試獨立
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

@pytest.fixture
def client(db_session):
    app.dependency_overrides.clear()
    
    def _client(role="welfare_member"):
        def override_get_db():
            yield db_session
        
        def override_role_check():
            if role is None:
                raise HTTPException(status_code=401, detail={"code": "NOT_LOGGED_IN"})
            return CurrentUser(user_id="test_user", role=role)
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_role_check
        return TestClient(app)
    
    yield _client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def base_url():
    return ""

@pytest.fixture
def raw_client(db_session):
    app.dependency_overrides.clear()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    def _auth_headers(role="welfare_member", expires_delta=timedelta(hours=1)):
        payload = {
            "user_id": "u_test",
            "email": "test@example.com",
            "role": role,
            "exp": datetime.now(timezone.utc) + expires_delta,
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers

@pytest.fixture
def valid_event_payload():
    return {
        "name": "2026 Year End Dinner",
        "description": "Company dinner",
        "location": "Company rooftop",
        "category": "entertainment",
        "guestAllowed": False,
        "remainingTickets": 100,
        "eventStartTime": "2026-12-25T18:00:00Z",
        "eventEndTime": "2026-12-25T22:00:00Z",
        "registrationStart": "2026-11-01T00:00:00Z",
        "registrationEnd": "2026-12-01T23:59:59Z",
        "status": "not_open",
        "isDraft": False,
    }
