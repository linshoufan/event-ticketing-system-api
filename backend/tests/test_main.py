from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_login_returns_login_url():
    response = client.get("/v1/auth/login")
    assert response.status_code == 200
    assert "data" in response.json()
    assert "loginUrl" in response.json()["data"]


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