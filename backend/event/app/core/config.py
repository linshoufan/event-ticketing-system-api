from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    event_db_host: str = "localhost"
    event_db_port: int = 5432
    event_db_user: str = "postgres"
    event_db_password: str = "postgres"
    event_db_name: str = "event_db"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Internal API
    internal_api_key: str = "dev-internal-key"
    ticket_service_url: str = "http://localhost:8001"

    # CORS
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:5173,"
        "https://event-ticketing-system-frontend-eight.vercel.app"
    )
    cors_methods: str = "GET,POST,PATCH,DELETE,OPTIONS"
    cors_headers: str = "Authorization,Content-Type,X-Internal-Key"

    # Environment
    env: str = "local"

settings = Settings()
