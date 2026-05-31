from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    account_db_host: str = "localhost"
    account_db_port: int = 5433
    account_db_user: str = "postgres"
    account_db_password: str = "postgres"
    account_db_name: str = "account_db"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/v1/auth/callback"

    # Internal API
    internal_api_key: str = "dev-internal-key"

    # Environment
    env: str = "local"


settings = Settings()
