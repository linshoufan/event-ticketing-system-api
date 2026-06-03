from .config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def build_database_url() -> str:
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}"
            f"@/{settings.event_db_name}?host={settings.event_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.event_db_user}:{settings.event_db_password}"
        f"@{settings.event_db_host}:{settings.event_db_port}/{settings.event_db_name}"
    )


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
