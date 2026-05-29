from app.core.config import settings

# 外部員工資料的結構
# { "employee_id": str, "password": str, "name": str, "email": str }

# Mock 資料，開發階段使用
# 正式環境換成真正連外部 DB 的邏輯
_MOCK_EMPLOYEES = {
    "1000001": {
        "employee_id": "1000001",
        "password": "password123",
        "name": "Andy Hsu",
        "email": "andy@company.com",
    },
    "1000002": {
        "employee_id": "1000002",
        "password": "password123",
        "name": "Sarah Li",
        "email": "sarah@company.com",
    },
}


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
