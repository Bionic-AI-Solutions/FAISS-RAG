"""
PostgreSQL database configuration using Pydantic Settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="DB_",
    )

    # Database Connection
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="mem0_rag_db", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres_password", description="Database password")
    ssl: bool = Field(default=False, description="Enable SSL/TLS connection (TLS 1.3)")

    # Connection Pooling
    # NFR-SCALE-004: 200 concurrent users/tenant requires pool_max=50
    # Calculation: 200 tenants × 200 users × 10% active = 4,000 concurrent queries
    # With 50 connections × 100 queries/connection = 5,000 capacity (sufficient)
    pool_min: int = Field(default=5, description="Minimum connection pool size")
    pool_max: int = Field(default=50, description="Maximum connection pool size (NFR: 200 concurrent users/tenant)")
    connection_timeout: int = Field(default=60000, description="Connection timeout in milliseconds")

    # Alternative: Database URL
    database_url: str | None = Field(default=None, alias="DATABASE_URL", description="Full database URL")

    @property
    def url(self) -> str:
        """Get database URL."""
        if self.database_url:
            return self.database_url
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


# Global database settings instance
db_settings = DatabaseSettings()



