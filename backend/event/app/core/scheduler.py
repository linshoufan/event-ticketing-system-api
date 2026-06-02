from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from .database import SessionLocal
from ..repositories.event_repository import EventRepository
from ..services.event_service import EventService

scheduler = BackgroundScheduler()

def update_event_statuses():
    """Update event statuses based on current time."""
    db = SessionLocal()
    repo = EventRepository(db)
    service = EventService(repo)
    
    try:
        now = datetime.now(timezone.utc)
        updated = service.update_statuses(now)
        
        if any(updated.values()):
            print(f"[scheduler] Updated event statuses: {updated['registering']} registering, {updated['closed']} closed, {updated['ended']} ended.")
            
    finally:
        db.close()

def start_scheduler():
    # Runs every day at midnight
    scheduler.add_job(update_event_statuses, "cron", hour=0, minute=0)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()
