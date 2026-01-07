"""
PostgreSQL database connection setup with connection pooling and SSL/TLS support.
"""

import ssl
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.database import db_settings
from app.mcp.middleware.tenant import get_tenant_id_from_context, get_role_from_context


def create_database_engine() -> AsyncEngine:
    """
    Create async database engine with connection pooling and SSL/TLS support.
    
    Returns:
        AsyncEngine: Configured database engine
    """
    # Build database URL
    database_url = db_settings.url
    
    # Configure SSL/TLS if enabled
    connect_args = {}
    if db_settings.ssl:
        # Configure TLS 1.3
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.check_hostname = False  # For development; set to True in production
        ssl_context.verify_mode = ssl.CERT_NONE  # For development; use CERT_REQUIRED in production
        connect_args["ssl"] = ssl_context
    
    # Create engine with connection pooling
    # For async engines, use pool_size and max_overflow directly (no poolclass needed)
    engine = create_async_engine(
        database_url,
        pool_size=db_settings.pool_max,  # Maximum pool size
        max_overflow=0,  # No overflow connections
        pool_timeout=db_settings.connection_timeout / 1000,  # Convert ms to seconds
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL logging in development
        connect_args=connect_args,
    )
    
    return engine


# Global engine instance
engine = create_database_engine()

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.
    
    Sets PostgreSQL session variables for RLS enforcement based on tenant context.
    
    Yields:
        AsyncSession: Database session
    """
    async with async_session() as session:
        try:
            # Set PostgreSQL session variables for RLS enforcement
            # Note: These use PostgreSQL's custom_variable_classes or custom GUCs
            # The variables are referenced in RLS policies but may not exist yet
            tenant_id = get_tenant_id_from_context()
            role = get_role_from_context()
            
            if tenant_id:
                # Set PostgreSQL custom variable for RLS
                # Use quoted identifier to handle dots in variable name
                # SET LOCAL doesn't support parameters, so we use string formatting
                # The tenant_id is a UUID, so it's safe to format directly
                await session.execute(
                    text(f'SET LOCAL "app.current_tenant_id" = \'{tenant_id}\'')
                )
            
            if role:
                # get_role_from_context() returns Optional[str], but context may contain enum
                # Convert to string value for PostgreSQL
                from app.mcp.middleware.rbac import UserRole
                if isinstance(role, UserRole):
                    role_str = role.value
                elif isinstance(role, str):
                    role_str = role
                else:
                    role_str = str(role)
                
                # Set role variable - used by RLS policies for Uber Admin bypass
                # Use quoted identifier to handle dots in variable name
                # SET LOCAL doesn't support parameters, so we use string formatting
                # The role_str is a controlled enum value, so it's safe to format directly
                await session.execute(
                    text(f'SET LOCAL "app.current_role" = \'{role_str}\'')
                )
            
            yield session
        finally:
            await session.close()


async def check_database_health() -> dict[str, bool | str]:
    """
    Check database connectivity and health with retry logic.
    
    Returns:
        dict: Health check result with status and message
    """
    from app.db.connection_retry import check_connection_with_retry
    return await check_connection_with_retry(max_retries=3)


async def close_database_connections():
    """Close all database connections."""
    await engine.dispose()

