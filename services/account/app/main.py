from fastapi import FastAPI

from app.core.config import settings
from app.routers.auth import router as auth_router

app = FastAPI(
    title="NTHU 福委會系統 - 帳戶管理微服務",
    version="1.0.0"
)


@app.get("/")
def read_root():
    return {
        "message": "Account Management Service is running!",
        "environment": settings.account_db_host
    }


app.include_router(auth_router, prefix="/v1")
