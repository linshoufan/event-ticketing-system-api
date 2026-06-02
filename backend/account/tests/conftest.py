from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.models import user as user_model  # noqa: F401 確保 models 被載入，Base.metadata 才知道有哪些 table

TEST_DATABASE_URL = "sqlite://"


def clear_database(session):
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


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
    clear_database(session)
    try:
        yield session
    finally:
        session.rollback()
        clear_database(session)
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session, shared_data):
    users_by_role = {}
    for user_data in shared_data["users"]:
        users_by_role.setdefault(user_data["role"], user_data)

    counter = {"value": 0}

    def _make_user(
        *,
        role="employee",
        source_user_id=None,
        username=None,
        registration_status=None,
        unlock_at=None,
    ):
        counter["value"] += 1
        if source_user_id:
            template = next(u for u in shared_data["users"] if u["user_id"] == source_user_id)
        elif registration_status == "locked":
            template = next(
                (u for u in shared_data["users"] if u.get("registration_status") == "locked"),
                users_by_role[role],
            )
        else:
            template = users_by_role[role]

        suffix = counter["value"]
        base_username = username or template.get("username", template["user_id"])
        user = User(
            user_id=f"{template['user_id']}_{suffix}",
            username=f"{base_username}_{suffix}",
            email=f"{base_username}_{suffix}@company.com",
            role=role,
            registration_status=registration_status or template.get("registration_status", "active"),
            unlock_at=unlock_at,
            diet_type=template.get("diet_type"),
            self_driving=template.get("self_driving"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def auth_headers():
    def _auth_headers(user: User) -> dict:
        token = create_access_token(user_id=user.user_id, role=user.role)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
