from unittest.mock import patch

from app.core.security import decode_access_token
from app.models.user import User

LOGIN_URL = "/v1/auth/login"


def employee_record(shared_data, employee_id):
    user = next(u for u in shared_data["employees"] if u.get("employee_id") == employee_id)
    return {
        "employee_id": user["employee_id"],
        "name": user["name"],
        "email": user["email"],
    }


def mock_verify_employee(shared_data, employee_id="1000001", email=None):
    """回傳 mock 的外部 DB 驗證結果。"""
    employee = employee_record(shared_data, employee_id)
    if email is not None:
        employee["email"] = email
    return employee


def test_first_login_creates_user(client, db_session, shared_data):
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=mock_verify_employee(shared_data, "1000001"),
    ):
        response = client.post(
            LOGIN_URL,
            json={"employeeId": "1000001", "password": "password123", "role": None},
        )

    assert response.status_code == 200
    assert "token" in response.json()["data"]
    assert response.json()["data"]["role"] == "employee"

    user = db_session.query(User).filter(User.username == "1000001").first()
    assert user is not None
    assert user.user_id == "1000001"
    assert user.role == "employee"


def test_second_login_does_not_duplicate_user(client, db_session, shared_data):
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=mock_verify_employee(shared_data, "1000099"),
    ):
        client.post(LOGIN_URL, json={"employeeId": "1000099", "password": "pw", "role": None})
        client.post(LOGIN_URL, json={"employeeId": "1000099", "password": "pw", "role": None})

    users = db_session.query(User).filter(User.username == "1000099").all()
    assert len(users) == 1


def test_token_payload_is_correct(client, db_session, shared_data):
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=mock_verify_employee(shared_data, "1000002", email="payload@company.com"),
    ):
        response = client.post(
            LOGIN_URL,
            json={"employeeId": "1000002", "password": "password123", "role": None},
        )

    token = response.json()["data"]["token"]
    payload = decode_access_token(token)

    assert payload["role"] == "employee"
    assert payload["user_id"] == "1000002"


def test_employee_not_found_returns_404(client, db_session):
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=None,
    ):
        response = client.post(
            LOGIN_URL,
            json={"employeeId": "9999999", "password": "wrong", "role": None},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"


def test_wrong_role_returns_403(client, db_session, shared_data):
    # 先建立一個 employee
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=mock_verify_employee(shared_data, "1000003"),
    ):
        client.post(LOGIN_URL, json={"employeeId": "1000003", "password": "pw", "role": None})

    # 用錯誤的 role 再登入
    with patch(
        "app.services.auth_service.verify_employee",
        return_value=mock_verify_employee(shared_data, "1000003"),
    ):
        response = client.post(
            LOGIN_URL,
            json={"employeeId": "1000003", "password": "pw", "role": "welfare_member"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INVALID_ROLE"
