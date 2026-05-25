from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.scheduler import start_scheduler, stop_scheduler
from app.routers.auth import router as auth_router
from app.routers.internal import router as internal_router
from app.routers.me import router as me_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="NTHU 福委會系統 - 帳戶管理微服務",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content={"error": detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": detail}},
    )


@app.get("/")
def read_root():
    return {
        "message": "Account Management Service is running!",
        "environment": settings.account_db_host
    }


app.include_router(auth_router, prefix="/v1")
app.include_router(internal_router, prefix="/v1")
app.include_router(me_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")
