from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.external_db import verify_employee
from app.core.security import create_access_token
from app.models.user import User


def login(employee_id: str, password: str, role: str | None, db: Session) -> dict:
    # 1. 去外部員工 DB 驗證
    employee = verify_employee(employee_id=employee_id, password=password)
    if employee is None:
        # 先查有沒有這個 employee_id
        from app.core.external_db import _MOCK_EMPLOYEES
        if employee_id not in _MOCK_EMPLOYEES:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found"},
            )
        # employee_id 存在但密碼錯
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid password"},
        )

    # 2. 查自己的 DB
    user = db.query(User).filter(User.username == employee_id).first()

    if user is None:
        # 第一次登入，建立 user
        user = User(
            user_id=employee_id,
            username=employee_id,
            email=employee["email"],
            role="employee",
            registration_status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # 之後登入：如果有帶 role，確認是否吻合
        if role is not None and user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "INVALID_ROLE", "message": "Role does not match"},
            )

    token = create_access_token(user_id=user.user_id, role=user.role)
    return {"token": token, "role": user.role}
