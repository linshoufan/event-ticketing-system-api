from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.eligibility import router as eligibility_router
from app.routers.internal import router as internal_router
from app.routers.registrations import router as registrations_router
from app.routers.transactions import router as transactions_router


app = FastAPI(
    title="Corporate Event Ticketing - Transaction Service",
    version="1.0.0",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """統一錯誤回應格式：{"error": {"code": ..., "message": ...}}"""
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
        "message": "Transaction Service is running!",
        "environment": settings.env,
    }


# 對外 API（需 JWT）
app.include_router(transactions_router, prefix="/v1")
app.include_router(eligibility_router, prefix="/v1")
app.include_router(registrations_router, prefix="/v1")
# 內部 API（需 X-Internal-Key）
app.include_router(internal_router, prefix="/v1")