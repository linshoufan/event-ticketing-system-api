import os
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="NTHU 福委會系統 - 帳戶管理微服務",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "Account Management Service is running!",
        "environment": os.getenv("ACCOUNT_DB_HOST", "Local Mode")
    }

auth_router = APIRouter()

@auth_router.get("/auth/login")
def login_placeholder():
    return {"message": "Placeholder for login API"}

app.include_router(auth_router, prefix="/v1")