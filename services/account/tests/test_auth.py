from unittest.mock import patch, MagicMock

from app.core.security import decode_access_token
from app.models.user import User


def mock_google_responses(email="test@company.com", name="Test User"):
    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "fake_access_token"}

    mock_userinfo_response = MagicMock()
    mock_userinfo_response.status_code = 200
    mock_userinfo_response.json.return_value = {"email": email, "name": name}

    return mock_token_response, mock_userinfo_response


def test_first_login_creates_user(client, db_session):
    mock_token_res, mock_userinfo_res = mock_google_responses()

    with patch("httpx.post", return_value=mock_token_res), \
         patch("httpx.get", return_value=mock_userinfo_res):
        response = client.get("/v1/auth/callback?code=fake_code")

    assert response.status_code == 200
    assert "token" in response.json()["data"]
    assert response.json()["data"]["role"] == "employee"

    user = db_session.query(User).filter(User.email == "test@company.com").first()
    assert user is not None
    assert user.username == "Test User"
    assert user.role == "employee"

# Test that logging in again with the same email does not create a duplicate user
def test_second_login_does_not_duplicate_user(client, db_session):
    mock_token_res, mock_userinfo_res = mock_google_responses(
        email="duplicate@company.com", name="Duplicate User"
    )

    with patch("httpx.post", return_value=mock_token_res), \
         patch("httpx.get", return_value=mock_userinfo_res):
        client.get("/v1/auth/callback?code=fake_code_1")
        client.get("/v1/auth/callback?code=fake_code_2")

    users = db_session.query(User).filter(User.email == "duplicate@company.com").all()
    assert len(users) == 1


def test_token_payload_is_correct(client, db_session):
    mock_token_res, mock_userinfo_res = mock_google_responses(
        email="payload@company.com", name="Payload User"
    )

    with patch("httpx.post", return_value=mock_token_res), \
         patch("httpx.get", return_value=mock_userinfo_res):
        response = client.get("/v1/auth/callback?code=fake_code")

    token = response.json()["data"]["token"]
    payload = decode_access_token(token)

    assert payload["role"] == "employee"

    user = db_session.query(User).filter(User.email == "payload@company.com").first()
    assert payload["user_id"] == user.user_id
