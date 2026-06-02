from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import events
from .core.scheduler import start_scheduler, stop_scheduler
from contextlib import asynccontextmanager

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
    lifespan=lifespan
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": exc.detail}},
    )

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)

@app.get("/")
def read_root():
    return {"message": "Event Service is running"}
