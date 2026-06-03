from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import events, internal
from .core.config import settings
from .core.scheduler import start_scheduler, stop_scheduler
from contextlib import asynccontextmanager


def _cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]


def _csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    start_scheduler()
    yield
    # Shutdown logic
    stop_scheduler()

app = FastAPI(
    title="Event Service",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": exc.detail}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        }),
    )

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=_csv_setting(settings.cors_methods),
    allow_headers=_csv_setting(settings.cors_headers),
)

# Include routers
app.include_router(events.router)
app.include_router(internal.router)

@app.get("/")
def read_root():
    return {"message": "Event Service is running"}
