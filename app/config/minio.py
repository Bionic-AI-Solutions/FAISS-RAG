"""
MinIO (S3-compatible storage) configuration using Pydantic Settings.
"""

import os
import socket
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_containerized_environment() -> bool:
    """Check if the application is running inside a Docker container."""
    return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", "false").lower() == "true"


def _get_minio_endpoint() -> str:
    """Determine the MinIO endpoint based on the environment."""
    # Check if explicitly set via environment variable
    explicit_endpoint = os.getenv("MINIO_ENDPOINT")
    if explicit_endpoint:
        return explicit_endpoint
    
    # Auto-detect containerized environment
    if _is_containerized_environment():
        # Try to resolve Docker network name
        try:
            socket.gethostbyname("mem0-rag-minio")
            return "mem0-rag-minio"
        except (socket.gaierror, OSError):
            # Fallback: try "minio" alias
            try:
                socket.gethostbyname("minio")
                return "minio"
            except (socket.gaierror, OSError):
                # If network name doesn't resolve, fall back to localhost
                return "localhost"
    
    # Default to localhost for host environments
    return "localhost"


class MinIOSettings(BaseSettings):
    """MinIO configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="MINIO_",
    )

    # MinIO Connection
    endpoint: str = Field(default=_get_minio_endpoint(), description="MinIO endpoint")
    port: int = Field(default=9000, description="MinIO port")
    access_key: str = Field(default="minioadmin", description="MinIO access key")
    secret_key: str = Field(default="minioadmin123", description="MinIO secret key")
    use_ssl: bool = Field(default=False, description="Use SSL/TLS")
    region: str = Field(default="us-east-1", description="MinIO region")

    # Bucket Configuration
    bucket_name: str = Field(default="mem0-rag-storage", description="Default bucket name")
    bucket_region: str = Field(default="us-east-1", description="Bucket region")

    # Console (optional)
    console_port: int = Field(default=9001, description="MinIO console port")

    @property
    def endpoint_url(self) -> str:
        """Get MinIO endpoint URL."""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.endpoint}:{self.port}"


# Global MinIO settings instance
minio_settings = MinIOSettings()















