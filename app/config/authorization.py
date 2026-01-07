"""
Authorization configuration settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.settings import Settings


class AuthorizationSettings(BaseSettings):
    """Authorization settings for RBAC (Role-Based Access Control)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # RBAC Configuration
    rbac_enabled: bool = Field(
        default=True, description="Enable RBAC (Role-Based Access Control)"
    )
    
    # Default role for unauthenticated users (should not be used in production)
    default_role: str = Field(
        default="end_user",
        description="Default role for users without explicit role assignment (should be 'end_user' in production)",
    )
    
    # Authorization behavior
    strict_mode: bool = Field(
        default=True,
        description="Strict mode: deny access if tool not found in permissions (True) or allow (False)",
    )
    
    # Performance Configuration
    authorization_timeout_ms: int = Field(
        default=50,
        description="Maximum authorization time in milliseconds (should be <50ms for performance)",
    )
    
    # Audit Logging Configuration
    log_all_authorization_attempts: bool = Field(
        default=True,
        description="Log all authorization attempts (success and failure) to audit log",
    )
    
    # Role Hierarchy Configuration
    # Roles are hierarchical: uber_admin > tenant_admin > project_admin > end_user
    # Higher roles inherit permissions from lower roles (if configured)
    enable_role_inheritance: bool = Field(
        default=False,
        description="Enable role inheritance (higher roles inherit lower role permissions). Currently disabled - explicit permissions only.",
    )


# Global authorization settings instance
authorization_settings = AuthorizationSettings()












