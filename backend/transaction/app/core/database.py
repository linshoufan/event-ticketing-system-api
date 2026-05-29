from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def build_database_url() -> str:
    """生產環境走 Cloud SQL Unix socket，local 走標準 TCP。"""
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.transaction_db_user}:{settings.transaction_db_password}"
            f"@/{settings.transaction_db_name}?host={settings.transaction_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.transaction_db_user}:{settings.transaction_db_password}"
        f"@{settings.transaction_db_host}:{settings.transaction_db_port}/{settings.transaction_db_name}"
    )


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency：每個 request 開一個 session，結束時關閉。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()