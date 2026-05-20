import secrets
import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_google_login_url() -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": secrets.token_urlsafe(16),
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query_string}"


def handle_google_callback(code: str, db: Session) -> dict:
    access_token = _exchange_code_for_token(code)
    user_info = _get_google_user_info(access_token)

    email = user_info.get("email")
    name = user_info.get("name", email)

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            user_id=str(uuid.uuid4()),
            username=name,
            email=email,
            role="employee",
            registration_status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user_id=user.user_id, role=user.role)
    return {"token": token, "role": user.role}


def _exchange_code_for_token(code: str) -> str:
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_OAUTH_CODE", "message": "Failed to exchange OAuth code"},
        )
    return response.json()["access_token"]


def _get_google_user_info(access_token: str) -> dict:
    response = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_ACCESS_TOKEN", "message": "Failed to fetch user info"},
        )
    return response.json()
