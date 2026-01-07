"""
Langfuse (observability) configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LangfuseSettings(BaseSettings):
    """Langfuse configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="LANGFUSE_",
    )

    # Langfuse Connection
    public_key: str = Field(default="pk-lf-xxx", description="Langfuse public key")
    secret_key: str = Field(default="sk-lf-xxx", description="Langfuse secret key")
    host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")
    project_name: str = Field(default="mem0-rag", description="Langfuse project name")
    timeout: int = Field(default=5000, description="Request timeout in milliseconds")

    # Feature Flag
    enabled: bool = Field(default=True, description="Enable Langfuse observability")


# Global Langfuse settings instance
langfuse_settings = LangfuseSettings()















