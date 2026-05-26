from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GrantOps AI"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./grantops.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    openalex_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    google_application_credentials: Optional[str] = None
    google_sheets_spreadsheet_id: Optional[str] = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
