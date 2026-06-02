import requests
import pytest

def test_health_check_or_db_status(base_url):
    # Node.js service doesn't have a specific /health but we can check if it's alive
    # by calling an existing endpoint or a dedicated health endpoint if it exists.
    # For parity with db.test.ts, we ensure the service can respond.
    response = requests.get(f"{base_url}/v1/events")
    assert response.status_code == 200
