from datetime import datetime, timezone, timedelta

from app.core.scheduler import auto_unlock_users


def test_expired_locked_user_is_unlocked(db_session, make_user):
    # unlock_at 在過去 → 應該被解鎖
    user = make_user(
        registration_status="locked",
        unlock_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    auto_unlock_users(db=db_session)
    db_session.refresh(user)
    assert user.registration_status == "active"
    assert user.unlock_at is None


def test_not_expired_locked_user_stays_locked(db_session, make_user):
    # unlock_at 在未來 → 不應該被解鎖
    user = make_user(
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
