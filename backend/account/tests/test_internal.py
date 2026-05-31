import uuid
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.models.user import User

VALID_KEY = settings.internal_api_key
WRONG_KEY = "wrong-key"
INTERNAL_KEY_HEADER = "X-Internal-Key"


def make_user(db, role="employee", username=None, registration_status="active"):
    user_id = str(uuid.uuid4())
    username = username or f"user_{user_id[:8]}"
    user = User(
        user_id=user_id,
        username=username,
        email=f"{username}@company.com",
        role=role,
        registration_status=registration_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_no_key_returns_422(client, db_session):
    # Header(...) 必填；未帶 header 時 FastAPI 自動回 422，不會進到我們的驗證邏輯
    user = make_user(db_session)
    response = client.get(f"/v1/internal/users/{user.user_id}/registration-profile")
    assert response.status_code == 422


def test_wrong_key_returns_401(client, db_session):
    user = make_user(db_session)
    response = client.get(
        f"/v1/internal/users/{user.user_id}/registration-profile",
        headers={INTERNAL_KEY_HEADER: WRONG_KEY},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_INTERNAL_KEY"


def test_registration_profile_returns_all_fields(client, db_session):
    user = make_user(db_session, role="employee", registration_status="active")
    response = client.get(
        f"/v1/internal/users/{user.user_id}/registration-profile",
        headers={INTERNAL_KEY_HEADER: VALID_KEY},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["userId"] == user.user_id
    assert data["role"] == "employee"
    assert data["registrationStatus"] == "active"
    assert "unlockAt" in data
    assert "autofill" in data
    assert "preferences" in data


def test_punish_active_user_becomes_locked(client, db_session):
    user = make_user(db_session, role="employee", registration_status="active")
    before = datetime.now(timezone.utc)
    response = client.post(
        f"/v1/internal/users/{user.user_id}/punish",
        headers={INTERNAL_KEY_HEADER: VALID_KEY},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["registrationStatus"] == "locked"
    unlock_at = datetime.fromisoformat(data["unlockAt"])
    expected = before + timedelta(days=30)
    assert abs((unlock_at - expected).total_seconds()) < 5


def test_punish_already_locked_user_resets_unlock_at(client, db_session):
    user = make_user(db_session, role="employee", registration_status="locked")
    # punish 第一次
    client.post(
        f"/v1/internal/users/{user.user_id}/punish",
        headers={INTERNAL_KEY_HEADER: VALID_KEY},
    )
    # 稍等一下，讓時間有差距
    import time
    time.sleep(1)
    before_second = datetime.now(timezone.utc)
    # punish 第二次，unlockAt 應該被重置
    response = client.post(
        f"/v1/internal/users/{user.user_id}/punish",
        headers={INTERNAL_KEY_HEADER: VALID_KEY},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["registrationStatus"] == "locked"
    unlock_at = datetime.fromisoformat(data["unlockAt"])
    expected = before_second + timedelta(days=30)
    assert abs((unlock_at - expected).total_seconds()) < 5
