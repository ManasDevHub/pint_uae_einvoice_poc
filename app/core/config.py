from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "UAE PINT AE E-Invoice Engine"
    environment: str = "development"
    api_version: str = "1.0.0"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./invoices.db"
    api_keys: str = "demo-key-123"
    allowed_origins: str = "*"
    max_payload_bytes: int = 2_097_152
    max_batch_size: int = 500
    rate_limit_per_minute: int = 200
    duplicate_cache_ttl: int = 86400
    log_level: str = "INFO"
    enable_metrics: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
