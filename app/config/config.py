from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Network Monitoring Utility"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./network_monitor.db"

    # Monitoring worker
    monitoring_interval_seconds: int = 30
    monitoring_timeout_seconds: float = 5.0

    # Logging — console
    log_level: str = "INFO"

    # Logging — file sink (disabled when log_file is empty / not set)
    log_file: Optional[str] = None
    log_rotation: str = "10 MB"   # rotate when file reaches this size
    log_retention: str = "1 week" # delete rotated files older than this

    # Server (used by uvicorn entry-point)
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
