from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_login_endpoint_exists():
    # 不帶 body 打 POST /auth/login，預期 422（FastAPI 驗 request body 必填）
    response = client.post("/v1/auth/login")
    assert response.status_code == 422


def test_http_exception_handler_with_dict_detail():
    from app.main import app as fastapi_app

    @fastapi_app.get("/test-error")
    def trigger_error():
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Resource not found"},
        )

    response = client.get("/test-error")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}