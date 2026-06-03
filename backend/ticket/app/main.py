from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.tickets import router as tickets_router
from app.routers.events import router as events_router
from app.routers.internal import router as internal_router


def _csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


app = FastAPI(
    title="Corporate Event Ticketing - Ticket Service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_csv_setting(settings.cors_origins),
    allow_credentials=True,
    allow_methods=_csv_setting(settings.cors_methods),
    allow_headers=_csv_setting(settings.cors_headers),
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
        "message": "Ticket Service is running!",
        "environment": settings.env,
    }

# Public APIs (require JWT)
app.include_router(tickets_router, prefix="/v1")
app.include_router(events_router, prefix="/v1")

# Internal APIs (require X-Internal-Key)
app.include_router(internal_router, prefix="/v1")
