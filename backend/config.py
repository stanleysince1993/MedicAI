from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql+psycopg2://medicai:medicai@localhost:5432/medicai"
    jwt_secret: str = "super-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_min: int = 60
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:5500"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @property
    def allowed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
