"""
Base settings configuration using Pydantic Settings.
All service-specific configurations inherit from this base class.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Configuration
    app_name: str = Field(default="mem0-rag", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # MCP Server Configuration
    mcp_server_host: str = Field(default="0.0.0.0", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    mcp_server_transport: str = Field(default="http", description="MCP server transport (http/sse)")

    # Multi-Tenant Configuration
    tenant_isolation_enabled: bool = Field(default=True, description="Enable tenant isolation")
    tenant_id_header: str = Field(default="X-Tenant-ID", description="HTTP header for tenant ID")
    tenant_validation_enabled: bool = Field(default=True, description="Enable tenant validation")

    # Compliance Configuration
    audit_logging_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_retention_days: int = Field(default=365, description="Audit log retention in days")
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=1000, description="Rate limit per tenant per minute")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")

    # Feature Flags
    feature_multimodal: bool = Field(default=False, description="Enable multimodal processing")
    feature_cross_modal_search: bool = Field(default=False, description="Enable cross-modal search")
    feature_advanced_analytics: bool = Field(default=False, description="Enable advanced analytics")


# Global settings instance
settings = Settings()








