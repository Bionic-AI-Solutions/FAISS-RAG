"""
Meilisearch configuration using Pydantic Settings.
"""

import os
import socket
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_containerized_environment() -> bool:
    """Check if the application is running inside a Docker container."""
    return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", "false").lower() == "true"


def _get_meilisearch_host() -> str:
    """Determine the Meilisearch host based on the environment."""
    # Check if explicitly set via environment variable
    explicit_host = os.getenv("MEILISEARCH_HOST")
    if explicit_host:
        return explicit_host
    
    # Auto-detect containerized environment
    if _is_containerized_environment():
        # Try to resolve Docker network name
        try:
            socket.gethostbyname("mem0-rag-meilisearch")
            return "http://mem0-rag-meilisearch"
        except (socket.gaierror, OSError):
            # Fallback: try "meilisearch" alias
            try:
                socket.gethostbyname("meilisearch")
                return "http://meilisearch"
            except (socket.gaierror, OSError):
                # If network name doesn't resolve, fall back to localhost
                return "http://localhost"
    
    # Default to localhost for host environments
    return "http://localhost"


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
    host: str = Field(default=_get_meilisearch_host(), description="Meilisearch host")
    port: int = Field(default=7700, description="Meilisearch port")
    api_key: str = Field(default="masterKey", description="Meilisearch API key")
    timeout: int = Field(default=5000, description="Request timeout in milliseconds")

    @property
    def url(self) -> str:
        """Get Meilisearch URL."""
        return f"{self.host}:{self.port}"


# Global Meilisearch settings instance
meilisearch_settings = MeilisearchSettings()















