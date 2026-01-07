"""
Redis configuration using Pydantic Settings.
"""

import os
import socket
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_containerized_environment() -> bool:
    """
    Detect if running in a containerized environment.
    
    Checks for common indicators:
    - /.dockerenv file exists (Docker)
    - Container hostname pattern
    - Environment variables indicating containerization
    """
    # Check for Docker indicator
    if os.path.exists("/.dockerenv"):
        return True
    
    # Check hostname pattern (Docker containers often have hash-like hostnames)
    hostname = socket.gethostname()
    if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname):
        # Docker container ID pattern
        return True
    
    # Check environment variables
    if os.getenv("CONTAINER_ID") or os.getenv("DOCKER_CONTAINER"):
        return True
    
    return False


def _get_redis_host() -> str:
    """
    Get Redis host based on environment.
    
    In containerized environments, use Docker network name.
    On host, use localhost.
    """
    # Check if explicitly set via environment variable
    explicit_host = os.getenv("REDIS_HOST")
    if explicit_host:
        return explicit_host
    
    # Auto-detect containerized environment
    if _is_containerized_environment():
        # Try to resolve Docker network name
        try:
            socket.gethostbyname("mem0-rag-redis")
            return "mem0-rag-redis"
        except (socket.gaierror, OSError):
            # Fallback: try "redis" alias
            try:
                socket.gethostbyname("redis")
                return "redis"
            except (socket.gaierror, OSError):
                # If network name doesn't resolve, fall back to localhost
                # (might be on host or network not configured)
                return "localhost"
    
    # Default to localhost for host environments
    return "localhost"


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="REDIS_",
    )

    # Redis Connection
    host: str = Field(default_factory=_get_redis_host, description="Redis host (auto-detected in containers)")
    port: int = Field(default=6379, description="Redis port")
    password: str | None = Field(default=None, description="Redis password")
    db: int = Field(default=0, description="Redis database number")

    # Connection Pool
    pool_size: int = Field(default=10, description="Connection pool size")
    connect_timeout: int = Field(default=10000, description="Connection timeout in milliseconds")
    command_timeout: int = Field(default=5000, description="Command timeout in milliseconds")

    # Redis Cluster (if using cluster)
    cluster_enabled: bool = Field(default=False, description="Enable Redis cluster")
    cluster_nodes: str | None = Field(default=None, description="Comma-separated cluster nodes")

    # Alternative: Redis URL
    redis_url: str | None = Field(default=None, alias="REDIS_URL", description="Full Redis URL")

    @property
    def url(self) -> str:
        """Get Redis URL."""
        if self.redis_url:
            return self.redis_url
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


# Global Redis settings instance
redis_settings = RedisSettings()















