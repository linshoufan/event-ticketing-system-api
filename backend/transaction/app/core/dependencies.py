from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import decode_access_token

# tokenUrl 只是給 OpenAPI docs 用的，實際 token 由 Account Service 發
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


@dataclass
class CurrentUser:
    """從 JWT payload 解出來的輕量使用者物件。

    注意：Transaction Service 沒有 users 表，所以這裡只放 token 裡有的欄位。
    如果業務邏輯需要 registrationStatus、autofill、preferences 等，
    請改呼叫 AccountClient.get_registration_profile()（Phase 3 會建立）。
    """
    user_id: str
    role: str


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """從 Authorization header 取出 JWT 並解析。"""
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token payload incomplete"},
        )
    return CurrentUser(user_id=user_id, role=role)


def role_required(*roles: str):
    """依 role 限制 endpoint 存取。用法：Depends(role_required('employee'))"""
    def check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return current_user
    return check


def verify_internal_key(x_internal_key: str = Header(...)) -> None:
    """供 Transaction Service 之後若要暴露 internal API 給其他服務呼叫使用。
    例如：Ticket Service 在 check-in 完成後可能要回呼 Transaction Service。"""
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_INTERNAL_KEY", "message": "Invalid internal API key"},
        )