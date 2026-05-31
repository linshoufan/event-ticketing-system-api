from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def decode_access_token(token: str) -> dict:
    """驗證並解析 JWT。Token 是 Account Service 發的，所以 secret 必須一致。"""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
        )