from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


def build_database_url() -> str:
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.account_db_user}:{settings.account_db_password}"
            f"@/{settings.account_db_name}?host={settings.account_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.account_db_user}:{settings.account_db_password}"
        f"@{settings.account_db_host}:{settings.account_db_port}/{settings.account_db_name}"
    )


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
