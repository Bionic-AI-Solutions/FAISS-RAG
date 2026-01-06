"""
Mem0 (memory management service) configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Mem0Settings(BaseSettings):
    """Mem0 configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="MEM0_",
    )

    # Mem0 Connection
    api_url: str = Field(default="http://localhost:8001", description="Mem0 API URL")
    api_key: str = Field(default="mem0_api_key", description="Mem0 API key")
    timeout: int = Field(default=30000, description="Request timeout in milliseconds")

    # Fallback Configuration
    fallback_to_redis: bool = Field(default=True, description="Fallback to Redis if Mem0 unavailable")


# Global Mem0 settings instance
mem0_settings = Mem0Settings()








