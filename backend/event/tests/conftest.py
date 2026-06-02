import os
from pathlib import Path
import pytest
import yaml

@pytest.fixture(scope="session")
def shared_data():
    yaml_path = Path(__file__).resolve().parents[3] / "scripts" / "mock_data.yaml"
    with yaml_path.open("r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def base_url():
    # 這裡可以根據環境變數調整 API 位址
    return os.getenv("EVENT_API_URL", "http://localhost:3000")
