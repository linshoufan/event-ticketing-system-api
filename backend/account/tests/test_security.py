import pytest
from fastapi import HTTPException
from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_token():
    token = create_access_token(user_id="user_123", role="employee")
    payload = decode_access_token(token)

    assert payload["user_id"] == "user_123"
    assert payload["role"] == "employee"


def test_decode_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("this.is.invalid")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "INVALID_TOKEN"


def test_decode_tampered_token():
    token = create_access_token(user_id="user_123", role="employee")
    tampered = token[:-5] + "XXXXX"

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered)

    assert exc_info.value.status_code == 401
