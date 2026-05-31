import uuid
from datetime import datetime, timezone, timedelta

from app.core.scheduler import auto_unlock_users
from app.models.user import User


def make_user(db, registration_status="active", unlock_at=None):
    user_id = str(uuid.uuid4())
    username = f"user_{user_id[:8]}"
    user = User(
        user_id=user_id,
        username=username,
        email=f"{username}@company.com",
        role="employee",
        registration_status=registration_status,
        unlock_at=unlock_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_expired_locked_user_is_unlocked(db_session):
    # unlock_at 在過去 → 應該被解鎖
    user = make_user(
        db_session,
        registration_status="locked",
        unlock_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    auto_unlock_users(db=db_session)
    db_session.refresh(user)
    assert user.registration_status == "active"
    assert user.unlock_at is None


def test_not_expired_locked_user_stays_locked(db_session):
    # unlock_at 在未來 → 不應該被解鎖
    user = make_user(
        db_session,
        registration_status="locked",
        unlock_at=datetime.now(timezone.utc) + timedelta(days=10),
    )
    auto_unlock_users(db=db_session)
    db_session.refresh(user)
    assert user.registration_status == "locked"
    assert user.unlock_at is not None


def test_no_locked_users_does_not_crash(db_session):
    # 沒有任何 locked user，正常跑完不報錯
    auto_unlock_users(db=db_session)
