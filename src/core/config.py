import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

class AppSettings(BaseSettings):
    """Application configuration loaded from .env"""

    # LLM Configuration
    llm_provider: str = Field(default="google")
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    openai_model_name: str = Field(default="gpt-4-turbo")
    google_model_name: str = Field(default="gemini-3.5-flash-lite")

    # External APIs
    tavily_api_key: Optional[str] = Field(default=None)
    openai_image_model: str = Field(default="dall-e-3")

    # Publishing APIs
    devto_api_key: Optional[str] = Field(default=None)
    medium_access_token: Optional[str] = Field(default=None)
    medium_user_id: Optional[str] = Field(default=None)

    # Database
    mongodb_uri: str = Field(default="mongodb://localhost:27017/")
    mongodb_database: str = Field(default="autoblog")
    sqlite_db_path: str = Field(default="./data/blog_checkpoints.db")

    # Application Settings
    app_debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    max_blog_iterations: int = Field(default=3)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


def load_yaml_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config or {}


def get_settings() -> AppSettings:
    """Get application settings from .env"""
    return AppSettings()


def get_config() -> Dict[str, Any]:
    """Get configuration from config.yaml"""
    return load_yaml_config()


def get_llm_config(settings: AppSettings, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get LLM-specific configuration"""
    # Resolve model name based on provider
    if settings.llm_provider == "google":
        model_name = settings.google_model_name
    elif settings.llm_provider == "anthropic":
        model_name = "claude-3-sonnet"
    else:
        model_name = settings.openai_model_name

    return {
        "provider": settings.llm_provider,
        "model": model_name,
        "temperature": config.get("llm", {}).get("temperature", 0.7),
        "max_tokens": config.get("llm", {}).get("max_tokens_per_agent", {}),
    }


def get_database_config(settings: AppSettings, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get database configuration"""
    return {
        "sqlite_path": settings.sqlite_db_path,
        "mongodb_uri": settings.mongodb_uri,
        "mongodb_database": settings.mongodb_database,
    }


# Singleton instances
_settings: Optional[AppSettings] = None
_config: Optional[Dict[str, Any]] = None


def init_config() -> None:
    """Initialize configuration (call once at app startup)"""
    global _settings, _config
    load_dotenv()
    _settings = get_settings()
    _config = get_config()


def get_app_settings() -> AppSettings:
    """Get cached settings"""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def get_app_config() -> Dict[str, Any]:
    """Get cached config"""
    global _config
    if _config is None:
        _config = get_config()
    return _config
