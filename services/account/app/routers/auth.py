from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.user import CallbackResponse, LoginResponse
from app.services import auth_service

router = APIRouter()


@router.get("/auth/login", response_model=dict)
def login():
    url = auth_service.get_google_login_url()
    return success(LoginResponse(loginUrl=url).model_dump())


@router.get("/auth/callback", response_model=dict)
def callback(code: str, db: Session = Depends(get_db)):
    result = auth_service.handle_google_callback(code=code, db=db)
    return success(CallbackResponse(**result).model_dump())


@router.post("/auth/logout", response_model=dict)
def logout():
    return success({"loggedOut": True})
