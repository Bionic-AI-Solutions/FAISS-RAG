"""
Redis configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    host: str = Field(default="localhost", description="Redis host")
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








