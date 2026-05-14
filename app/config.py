"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PULSEMETRICS_")

    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://pulsemetrics:pulsemetrics@localhost:5432/pulsemetrics"
    )
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300
    webhook_signing_secret: str = "change-me"
    report_cache_prefix: str = "report:weekly"
    max_event_payload_bytes: int = 32_768

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
