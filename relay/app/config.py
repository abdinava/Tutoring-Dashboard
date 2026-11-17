"""Relay settings from environment variables / .env (lists and dicts are JSON)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allowed_courses: list[str]
    device_token_hashes: dict[str, str]
    qualtrics_base_url: str = ""
    qualtrics_api_token: SecretStr = SecretStr("")
    qualtrics_survey_id: str = ""
    dry_run: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
