import requests
import pytest

def test_get_event_not_found(base_url):
    response = requests.get(f"{base_url}/v1/events/non_existent_id")
    assert response.status_code == 404
