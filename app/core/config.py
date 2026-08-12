from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./attendance.db"
    
    # Compliance Engine Configurable Parameters
    MAX_CONTINUOUS_SHIFT_HOURS: float = 10.0
    MAX_CONSECUTIVE_WORKING_DAYS: int = 6
    
    # Deduplication Window (Seconds)
    DEDUPLICATION_WINDOW_SECONDS: int = 60
    
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
