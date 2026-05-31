from app.core.response import success, paginated


def test_success():
    result = success({"userId": "u_123", "role": "employee"})
    assert result == {"data": {"userId": "u_123", "role": "employee"}}


def test_paginated():
    result = paginated(data=[1, 2, 3], page=1, limit=20, total=100)
    assert result["data"] == [1, 2, 3]
    assert result["pagination"] == {"page": 1, "limit": 20, "total": 100}
