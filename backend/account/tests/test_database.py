from unittest.mock import patch
from app.core.database import build_database_url


def test_local_database_url():
    with patch("app.core.database.settings") as mock_settings:
        mock_settings.env = "local"
        mock_settings.account_db_user = "postgres"
        mock_settings.account_db_password = "secret"
        mock_settings.account_db_host = "localhost"
        mock_settings.account_db_port = 5433
        mock_settings.account_db_name = "account_db"

        url = build_database_url()

        assert url == "postgresql+psycopg2://postgres:secret@localhost:5433/account_db"


def test_production_database_url():
    with patch("app.core.database.settings") as mock_settings:
        mock_settings.env = "production"
        mock_settings.account_db_user = "postgres"
        mock_settings.account_db_password = "secret"
        mock_settings.account_db_host = "/cloudsql/project:region:instance"
        mock_settings.account_db_name = "account_db"

        url = build_database_url()

        assert url == "postgresql+psycopg2://postgres:secret@/account_db?host=/cloudsql/project:region:instance"
