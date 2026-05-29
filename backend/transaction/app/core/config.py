from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    transaction_db_host: str = "localhost"
    transaction_db_port: int = 5434
    transaction_db_user: str = "postgres"
    transaction_db_password: str = "postgres"
    transaction_db_name: str = "transaction_db"

    # JWT（需與 Account Service 共用同一把 key，才能驗證 token）
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Internal API key（呼叫 Account / Ticket Service 的 internal API 時帶上）
    internal_api_key: str = "dev-internal-key"

    # 其他服務的 base URL（Phase 3 跨服務呼叫會用）
    account_service_url: str = "http://localhost:8000"
    event_service_url: str = "http://localhost:3000"
    ticket_service_url: str = "http://localhost:8001"

    # Ticket Service 是否啟用
    # 因為 Ticket Service 尚未整合到 dev branch，先設 False
    # 改 True 後，報名成功時會真的打 Ticket Service 建立票券
    ticket_service_enabled: bool = False

    # Environment
    env: str = "local"


settings = Settings()