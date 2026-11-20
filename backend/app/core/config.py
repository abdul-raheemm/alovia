"""Settings read from backend/.env (docs/ENVIRONMENT.md §1).

Only the variables used so far are declared; database and Supabase settings are added by the
tasks that use them.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Must equal the version in docs/legal/CONSENT_TEXT.md (DEC-031); a test checks it.
CONSENT_VERSION = "2026-11-v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = []
    # token verification (SECURITY.md §1); required, so the app refuses to start without them
    supabase_jwks_url: str
    supabase_jwt_issuer: str
    database_url: str
    # separate, empty database used only by the migration tests (never the main project)
    test_database_url: str | None = None
    # base of the invite links doctors send (Dashboard §8.2); the deployed URL is set in Phase 9
    patient_app_url: str = "http://localhost:5173"
    # private Storage bucket for medical records (Dashboard §14); records answer 503 without them
    supabase_url: str | None = None
    supabase_service_role_key: SecretStr | None = None  # backend only; hidden when printed
    storage_bucket: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        # .env holds a comma-separated string, not JSON
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # required values come from backend/.env; missing ones stop startup
