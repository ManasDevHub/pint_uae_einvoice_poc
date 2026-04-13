from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "UAE PINT AE E-Invoice Engine"
    environment: str = "development"
    api_version: str = "1.0.0"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./invoices.db"
    api_keys: str = "demo-key-123"
    allowed_origins: str = "*"
    max_payload_bytes: int = 52_428_800 # 50MB
    max_batch_size: int = 500
    rate_limit_per_minute: int = 200
    duplicate_cache_ttl: int = 86400
    log_level: str = "INFO"
    enable_metrics: bool = True
    celery_task_always_eager: bool = False

    # -- Database Credentials (Postgres) --
    postgres_user: str = "einvoicedev"
    postgres_password: str = "uae_inv_2026_secure"
    postgres_db: str = "uae_einvoice"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
