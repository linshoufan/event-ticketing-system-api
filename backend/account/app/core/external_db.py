from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import text
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
    for employee in data.get("employees", []):
        employee_id = employee.get("employee_id")
        password = employee.get("password")
        if not employee_id or not password:
            continue
        employees[employee_id] = {
            "employee_id": employee_id,
            "password": password,
            "name": employee.get("name", employee_id),
            "email": employee["email"],
        }
    return employees


_MOCK_EMPLOYEES = _load_mock_employees()


def build_employee_database_url() -> str:
    if settings.env == "production":
        return (
            f"postgresql+psycopg2://{settings.employee_db_user}:{settings.employee_db_password}"
            f"@/{settings.employee_db_name}?host={settings.employee_db_host}"
        )
    return (
        f"postgresql+psycopg2://{settings.employee_db_user}:{settings.employee_db_password}"
        f"@{settings.employee_db_host}:{settings.employee_db_port}/{settings.employee_db_name}"
    )


def _get_mock_employee(employee_id: str) -> dict | None:
    return _MOCK_EMPLOYEES.get(employee_id)


def _get_database_employee(employee_id: str) -> dict | None:
    employee_engine = create_engine(build_employee_database_url(), pool_pre_ping=True)
    query = text(
        """
        SELECT employee_id, password, name, email
        FROM employees
        WHERE employee_id = :employee_id
        """
    )
    with employee_engine.connect() as conn:
        row = conn.execute(query, {"employee_id": employee_id}).mappings().first()
    return dict(row) if row else None


def _get_employee(employee_id: str) -> dict | None:
    if settings.employee_auth_mode == "database":
        return _get_database_employee(employee_id)
    return _get_mock_employee(employee_id)


def employee_exists(employee_id: str) -> bool:
    return _get_employee(employee_id) is not None


def verify_employee(employee_id: str, password: str) -> dict | None:
    """
    去外部員工 DB 驗證帳號密碼。
    成功回傳員工資料 dict，失敗回傳 None。
    正式環境：把 mock 換成真正的 DB 查詢。
    """
    employee = _get_employee(employee_id)
    if not employee:
        return None
    if employee["password"] != password:
        return None
    return {
        "employee_id": employee["employee_id"],
        "name": employee.get("name", employee["employee_id"]),
        "email": employee["email"],
    }
