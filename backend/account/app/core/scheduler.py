from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.models.user import User

scheduler = BackgroundScheduler()


def auto_unlock_users(db=None):
    """掃描所有 unlock_at 已到期的 locked user，自動解鎖。
    db 參數用於測試注入，正式環境不傳則自動建立 session。
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        users = (
            db.query(User)
            .filter(User.registration_status == "locked")
            .filter(User.unlock_at <= now)
            .all()
        )
        for user in users:
            user.registration_status = "active"
            user.unlock_at = None
            user.updated_at = now
        if users:
            db.commit()
            print(f"[scheduler] Auto-unlocked {len(users)} user(s).")
    finally:
        if own_session:
            db.close()


def start_scheduler():
    # 每天凌晨 1 點執行
    scheduler.add_job(auto_unlock_users, "cron", hour=1, minute=0)
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
