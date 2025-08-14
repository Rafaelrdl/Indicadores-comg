"""Centralized configuration management for the application."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = {
        "extra": "ignore",  # Allow extra fields to be ignored
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "",
    }

    # API Settings
    arkmeds_base_url: str = Field(
        default="https://comg.arkmeds.com", description="Base URL for Arkmeds API"
    )
    arkmeds_email: str | None = Field(default=None, description="Email for Arkmeds authentication")
    arkmeds_password: str | None = Field(
        default=None, description="Password for Arkmeds authentication"
    )
    arkmeds_token: str | None = Field(
        default=None, description="JWT token for Arkmeds authentication"
    )
    arkmeds_login_path: str = Field(
        default="/rest-auth/token-auth/", description="Login endpoint path"
    )

    # UI Settings
    page_title: str = Field(default="Indicadores COMG", description="Application page title")
    page_icon: str = Field(default="🩺", description="Page icon for browser tab")
    layout: str = Field(default="wide", description="Streamlit layout mode")
    sidebar_state: str = Field(default="expanded", description="Default sidebar state")

    # Performance Settings
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent API requests")

    # Scheduler Settings
    sync_interval_minutes: int = Field(default=15, description="Automatic sync interval in minutes")
    scheduler_timezone: str = Field(
        default="America/Sao_Paulo", description="Timezone for scheduler operations"
    )
    max_scheduler_instances: int = Field(
        default=1, description="Maximum concurrent scheduler instances"
    )
    scheduler_coalesce: bool = Field(default=True, description="Combine missed scheduler runs")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Application log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    enable_structlog: bool = Field(
        default=True, description="Enable structlog for structured logging"
    )
    log_include_timestamp: bool = Field(
        default=True, description="Include timestamp in structured logs"
    )
    log_include_request_id: bool = Field(
        default=True, description="Include request_id in log context"
    )

    # Development Settings
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    dev_mode: bool = Field(default=False, description="Enable development mode features")

    @classmethod
    def from_streamlit_secrets(cls) -> Settings:
        """Load settings from Streamlit secrets.toml."""
        try:
            import streamlit as st

            # Extract from secrets if available
            secrets = getattr(st, "secrets", {})
            arkmeds_config = secrets.get("arkmeds", {})
            
            # Se há configuração no secrets e tem valores não-nulos, use ela
            if arkmeds_config and any(v for v in arkmeds_config.values() if v):
                return cls(
                    arkmeds_base_url=arkmeds_config.get("base_url", "https://comg.arkmeds.com"),
                    arkmeds_email=arkmeds_config.get("email"),
                    arkmeds_password=arkmeds_config.get("password"),
                    arkmeds_token=arkmeds_config.get("token"),
                    arkmeds_login_path=arkmeds_config.get("login_path", "/rest-auth/token-auth/"),
                )
            else:
                # Se não há configuração no secrets, use instância normal que carregará .env
                return cls()
                
        except ImportError:
            # Fallback to environment variables
            return cls()


# Global settings instance - Lazy initialization
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_streamlit_secrets()
    return _settings
