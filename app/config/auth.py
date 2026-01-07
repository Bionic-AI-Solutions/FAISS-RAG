"""
Authentication configuration settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.settings import Settings


class AuthSettings(BaseSettings):
    """Authentication settings for OAuth 2.0 and API key authentication."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OAuth 2.0 Configuration
    oauth_enabled: bool = Field(default=True, description="Enable OAuth 2.0 authentication")
    oauth_issuer: str = Field(
        default="", description="OAuth 2.0 token issuer URL (e.g., https://auth.example.com)"
    )
    oauth_jwks_uri: str = Field(
        default="",
        description="OAuth 2.0 JWKS endpoint URL (e.g., https://auth.example.com/.well-known/jwks.json)",
    )
    oauth_audience: str = Field(
        default="", description="OAuth 2.0 token audience (expected audience claim)"
    )
    oauth_algorithms: list[str] = Field(
        default_factory=lambda: ["RS256", "ES256"], description="Supported JWT algorithms"
    )
    oauth_user_id_claim: str = Field(
        default="sub", description="JWT claim name for user ID"
    )
    oauth_tenant_id_claim: str = Field(
        default="tenant_id", description="JWT claim name for tenant ID"
    )
    oauth_role_claim: str = Field(
        default="role", description="JWT claim name for user role"
    )
    oauth_user_profile_endpoint: str = Field(
        default="",
        description="OAuth provider user profile endpoint for fallback lookup (e.g., https://auth.example.com/userinfo)",
    )

    # API Key Configuration
    api_key_enabled: bool = Field(
        default=True, description="Enable API key authentication"
    )
    api_key_header: str = Field(
        default="X-API-Key", description="HTTP header name for API key"
    )
    api_key_hash_algorithm: str = Field(
        default="bcrypt", description="API key hashing algorithm (bcrypt or argon2)"
    )

    # Performance Configuration
    auth_timeout_ms: int = Field(
        default=50, description="Maximum authentication time in milliseconds (FR-AUTH-001, FR-AUTH-002)"
    )
    jwks_cache_ttl: int = Field(
        default=3600, description="JWKS cache TTL in seconds"
    )


# Global auth settings instance
auth_settings = AuthSettings()












