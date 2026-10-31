from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "TESTORA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "change_this_to_a_secure_random_secret_key_in_production"
    ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./testora.db"

    # Authentication & Session Cookies
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_NAME: str = "testora_session"

    # Seed Admin Defaults
    FIRST_SUPERUSER_EMAIL: str = "admin@testora.local"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@123"
    FIRST_SUPERUSER_NAME: str = "Administrator"

    # AI Configuration (Anthropic API - backend only)
    ANTHROPIC_API_KEY: str = ""

    # File Storage / Attachments
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 5

    @property
    def upload_dir_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        if p.is_absolute():
            return p
        return BACKEND_DIR / p

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
