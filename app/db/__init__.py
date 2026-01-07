"""
Database layer for the application.
"""

from app.db.base import Base, BaseModel, TenantScopedModel
from app.db.connection import (
    async_session,
    check_database_health,
    close_database_connections,
    create_database_engine,
    engine,
    get_db_session,
)
from app.db.models import (
    AuditLog,
    Document,
    Tenant,
    TenantApiKey,
    User,
)

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TenantScopedModel",
    # Connection
    "engine",
    "async_session",
    "get_db_session",
    "create_database_engine",
    "check_database_health",
    "close_database_connections",
    # Models
    "Tenant",
    "User",
    "Document",
    "AuditLog",
    "TenantApiKey",
]












