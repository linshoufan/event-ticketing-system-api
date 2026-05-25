from unittest.mock import patch
from app.core.database import build_database_url


def test_local_database_url():
    with patch("app.core.database.settings") as mock_settings:
        mock_settings.env = "local"
        mock_settings.db_user = "postgres"
        mock_settings.db_password = "secret"
        mock_settings.db_host = "localhost"
        mock_settings.db_port = 5433
        mock_settings.db_name = "event_ticketing_db"

        url = build_database_url()

        assert url == "postgresql+psycopg2://postgres:secret@localhost:5433/event_ticketing_db"


def test_production_database_url():
    with patch("app.core.database.settings") as mock_settings:
        mock_settings.env = "production"
        mock_settings.db_user = "postgres"
        mock_settings.db_password = "secret"
        mock_settings.db_host = "/cloudsql/project:region:instance"
        mock_settings.db_name = "event_ticketing_db"

        url = build_database_url()

        assert url == "postgresql+psycopg2://postgres:secret@/event_ticketing_db?host=/cloudsql/project:region:instance"
