from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .security import decode_access_token
from .config import settings

security_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user_id: str
    role: str


def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> CurrentUser:
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_LOGGED_IN", "message": "Not logged in"},
        )

    token = auth.credentials
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
    def check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return current_user
    return check


def verify_internal_key(x_internal_key: str = Header(...)):
    """缺 header → 422；key 錯 → 401。"""
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_INTERNAL_KEY", "message": "Invalid internal API key"},
        )
