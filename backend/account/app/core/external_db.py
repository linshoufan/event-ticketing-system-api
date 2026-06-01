from pathlib import Path

import yaml

from app.core.config import settings

# 外部員工資料的結構
# { "employee_id": str, "password": str, "name": str, "email": str }

# Mock 資料，開發階段使用
# 正式環境換成真正連外部 DB 的邏輯
def _load_mock_employees() -> dict:
    yaml_path = Path(__file__).resolve().parents[4] / "scripts" / "mock_data.yaml"
    if not yaml_path.exists():
        return {}

    with yaml_path.open("r") as f:
        data = yaml.safe_load(f)

    employees = {}
    for user in data.get("users", []):
        employee_id = user.get("employee_id")
        password = user.get("password")
        if not employee_id or not password:
            continue
        employees[employee_id] = {
            "employee_id": employee_id,
            "password": password,
            "name": user.get("name", user.get("username", employee_id)),
            "email": user["email"],
        }
    return employees


_MOCK_EMPLOYEES = _load_mock_employees()


def verify_employee(employee_id: str, password: str) -> dict | None:
    """
    去外部員工 DB 驗證帳號密碼。
    成功回傳員工資料 dict，失敗回傳 None。
    正式環境：把 mock 換成真正的 DB 查詢。
    """
    if settings.env == "production":
        # TODO: 換成真正的外部 DB 連線
        raise NotImplementedError("External DB connection not implemented yet")

    employee = _MOCK_EMPLOYEES.get(employee_id)
    if not employee:
        return None
    if employee["password"] != password:
        return None
    return employee
