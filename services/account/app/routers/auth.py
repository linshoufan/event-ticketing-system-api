from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.user import LoginRequest, LoginResponse
from app.services import auth_service

router = APIRouter()


@router.post("/auth/login", response_model=dict)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    result = auth_service.login(
        employee_id=body.employeeId,
        password=body.password,
        role=body.role,
        db=db,
    )
    return success(LoginResponse(**result).model_dump())


@router.post("/auth/logout", response_model=dict)
def logout():
    return success({"loggedOut": True})
