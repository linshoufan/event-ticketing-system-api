import os
from pathlib import Path
import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.dependencies import get_current_user_role

# 使用與 Account/Transaction 一致的 PostgreSQL 測試資料庫
TEST_DATABASE_URL = (
    f"postgresql://{settings.event_db_user}:{settings.event_db_password}"
    f"@{settings.event_db_host}:{settings.event_db_port}/test_event_db"
)

@pytest.fixture(scope="session")
def shared_data():
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)

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
    
    def _client(role="hr"):
        def override_get_db():
            yield db_session
        
        def override_role_check():
            if role is None:
                raise HTTPException(status_code=401, detail={"code": "NOT_LOGGED_IN"})
            return {"user_id": "test_user", "role": role}
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user_role] = override_role_check
        return TestClient(app)
    
    yield _client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def base_url():
    return ""
