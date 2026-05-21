import uuid

from app.core.security import create_access_token
from app.models.user import User


def make_user(db, role="employee", username=None, registration_status="active"):
    user_id = str(uuid.uuid4())
    username = username or f"user_{user_id[:8]}"
    user = User(
        user_id=user_id,
        username=username,
        email=f"{username}@company.com",
        role=role,
        registration_status=registration_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user: User) -> dict:
    token = create_access_token(user_id=user.user_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_employee_cannot_access_user_list(client, db_session):
    employee = make_user(db_session, role="employee")
    response = client.get("/v1/users", headers=auth_headers(employee))
    assert response.status_code == 403


def test_employee_can_access_own_profile(client, db_session):
    employee = make_user(db_session, role="employee")
    response = client.get(f"/v1/users/{employee.user_id}", headers=auth_headers(employee))
    assert response.status_code == 200
    assert response.json()["data"]["userId"] == employee.user_id


def test_employee_cannot_access_other_profile(client, db_session):
    employee = make_user(db_session, role="employee")
    other = make_user(db_session, role="employee")
    response = client.get(f"/v1/users/{other.user_id}", headers=auth_headers(employee))
    assert response.status_code == 403


def test_welfare_member_can_access_any_profile(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    other = make_user(db_session, role="employee")
    response = client.get(f"/v1/users/{other.user_id}", headers=auth_headers(welfare))
    assert response.status_code == 200
    assert response.json()["data"]["userId"] == other.user_id


def test_unlock_non_locked_user_returns_409(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    active_user = make_user(db_session, role="employee", registration_status="active")
    response = client.patch(
        f"/v1/users/{active_user.user_id}/unlock",
        headers=auth_headers(welfare),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USER_NOT_LOCKED"


def test_welfare_member_can_create_user(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    response = client.post(
        "/v1/users",
        json={"username": "new_user", "role": "employee"},
        headers=auth_headers(welfare),
    )
    assert response.status_code == 201
    assert response.json()["data"]["username"] == "new_user"
    assert response.json()["data"]["role"] == "employee"


def test_employee_can_update_own_profile(client, db_session):
    employee = make_user(db_session, role="employee")
    response = client.patch(
        f"/v1/users/{employee.user_id}",
        json={"preferences": ["sport", "food"], "autofill": {"dietType": "veg", "selfDriving": True}},
        headers=auth_headers(employee),
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated"] is True


def test_welfare_member_can_delete_user(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    target = make_user(db_session, role="employee")
    response = client.delete(
        f"/v1/users/{target.user_id}",
        headers=auth_headers(welfare),
    )
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True


def test_welfare_member_can_change_user_role(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    target = make_user(db_session, role="employee")
    response = client.patch(
        f"/v1/users/{target.user_id}/role",
        json={"role": "hr"},
        headers=auth_headers(welfare),
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated"] is True


def test_welfare_member_cannot_change_own_role(client, db_session):
    welfare = make_user(db_session, role="welfare_member")
    response = client.patch(
        f"/v1/users/{welfare.user_id}/role",
        json={"role": "employee"},
        headers=auth_headers(welfare),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CANNOT_MODIFY_OWN_ROLE"
