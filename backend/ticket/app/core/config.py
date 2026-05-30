from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    ticket_db_host: str = "localhost"
    ticket_db_port: int = 5435
    ticket_db_user: str = "postgres"
    ticket_db_password: str = "postgres"
    ticket_db_name: str = "ticket_db"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Internal API key
    internal_api_key: str = "dev-internal-key"

    # Other services
    event_service_url: str = "http://localhost:3000"

    # Environment
    env: str = "local"


settings = Settings()
