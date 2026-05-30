from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def build_database_url() -> str:
    """Use Cloud SQL Unix socket in production, standard TCP in local."""
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.ticket_db_user}:{settings.ticket_db_password}"
            f"@/{settings.ticket_db_name}?host={settings.ticket_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.ticket_db_user}:{settings.ticket_db_password}"
        f"@{settings.ticket_db_host}:{settings.ticket_db_port}/{settings.ticket_db_name}"
    )


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: opens a session for each request and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
