from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)

def get_current_user_role(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict:
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "NOT_LOGGED_IN", "message": "Not logged in"},
        )

    token = auth.credentials
    payload = decode_access_token(token)
    return payload # 包含 user_id, role, exp 等

def role_required(*roles: str):
    def check(payload: dict = Depends(get_current_user_role)):
        if payload.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return payload
    return check
