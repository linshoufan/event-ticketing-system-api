from jose import JWTError, jwt
from fastapi import HTTPException, status
from .config import settings

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        # jose 的 JWTError 涵蓋了過期與無效 Token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Could not validate credentials"},
        )
