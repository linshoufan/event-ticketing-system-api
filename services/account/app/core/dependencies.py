from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("user_id")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )
    return user


def role_required(*roles: str):
    def check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return current_user
    return check


def self_or_role(*roles: str):
    def check(
        user_id: str,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.user_id != user_id and current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return current_user
    return check


def verify_internal_key(x_internal_key: str = Header(...)) -> None:
    # FastAPI 自動從 request header 取值
    # 參數名 x_internal_key 對應 header 名 X-Internal-Key（底線→連字號，大小寫不敏感）
    # Header(...) 的 ... 代表必填，沒帶 header 時 FastAPI 自動回 422
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_INTERNAL_KEY", "message": "Invalid internal API key"},
        )
