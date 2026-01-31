"""
Inventix AI - Configuration Management
======================================
Centralized configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


# Get the project root directory (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App Info
    app_name: str = "Inventix AI"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    
    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./inventix.db"
    
    # Security
    secret_key: str = "inventix-dev-secret-key"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
