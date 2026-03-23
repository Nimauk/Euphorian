import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional, Any

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    GEMINI_API_KEY: Optional[str] = None
    YTDLP_COOKIES_BROWSER: Optional[str] = None
    ALLOWED_USER_IDS: List[int] = []
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("ALLOWED_USER_IDS", mode="before")
    @classmethod
    def parse_allowed_ids(cls, v: Any) -> List[int]:
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            if not v.strip():
                return []
            v = v.strip("[]")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

settings = Settings()
