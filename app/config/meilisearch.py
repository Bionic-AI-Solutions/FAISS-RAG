"""
Meilisearch configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MeilisearchSettings(BaseSettings):
    """Meilisearch configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="MEILISEARCH_",
    )

    # Meilisearch Connection
    host: str = Field(default="http://localhost", description="Meilisearch host")
    port: int = Field(default=7700, description="Meilisearch port")
    api_key: str = Field(default="masterKey", description="Meilisearch API key")
    timeout: int = Field(default=5000, description="Request timeout in milliseconds")

    @property
    def url(self) -> str:
        """Get Meilisearch URL."""
        return f"{self.host}:{self.port}"


# Global Meilisearch settings instance
meilisearch_settings = MeilisearchSettings()








