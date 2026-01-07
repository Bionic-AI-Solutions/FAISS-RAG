"""
Pytest configuration for integration tests.

This module provides session-scoped fixtures to ensure database connections
and event loops are properly managed across integration tests.

It also ensures all required services (PostgreSQL, Redis, MinIO, Meilisearch)
are running before integration tests execute.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest
import pytest_asyncio

# Set Redis password from environment or use default
if not os.getenv("REDIS_PASSWORD"):
    os.environ["REDIS_PASSWORD"] = "redis_password"
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create a session-scoped event loop for integration tests.
    
    This ensures all integration tests run in the same event loop,
    avoiding issues with SQLAlchemy's connection pool and asyncpg
    connections being attached to different loops.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)  # Set as current event loop
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_engine(event_loop) -> AsyncEngine:
    """
    Create a session-scoped database engine for integration tests.
    
    Uses NullPool to avoid connection pooling issues across event loops.
    Each database operation gets a fresh connection that's closed immediately.
    """
    from app.config.database import db_settings
    
    database_url = db_settings.url
    
    # Create engine with NullPool for tests - avoids event loop issues
    engine = create_async_engine(
        database_url,
        poolclass=NullPool,  # No pooling - each request gets fresh connection
        echo=False,
    )
    
    yield engine
    
    # Cleanup: dispose of engine when session ends
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_db_session_factory(test_db_engine) -> async_sessionmaker:
    """
    Create a session-scoped session factory for integration tests.
    """
    return async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_services_running():
    """
    Ensure all required services are running before integration tests.
    
    This fixture automatically starts services (PostgreSQL, Redis, MinIO, Meilisearch)
    if they're not running, ensuring integration tests always have access to live services.
    """
    project_root = Path(__file__).parent.parent.parent
    ensure_services_script = project_root / "scripts" / "ensure_services_running.py"
    
    if ensure_services_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(ensure_services_script)],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                print("\n⚠️  Warning: Some services may not be healthy")
                print("   Integration tests may fail if services are unavailable")
                print(f"   Output: {result.stdout}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"\n⚠️  Warning: Could not ensure services are running: {e}")
            print("   Please ensure services are running manually:")
            print("   docker compose -f docker/docker-compose.yml up -d")
    else:
        print("\n⚠️  Warning: ensure_services_running.py not found")
        print("   Please ensure services are running manually:")
        print("   docker compose -f docker/docker-compose.yml up -d")
    
    yield  # Tests run here
    
    # No cleanup needed - services should remain running


@pytest.fixture(scope="session", autouse=True)
def setup_test_database_engine(test_db_engine, test_db_session_factory):
    """
    Patch the global database engine and session factory for integration tests.
    
    This ensures that all integration tests use the test-specific engine
    that's created within the test session's event loop.
    """
    import app.db.connection as db_module
    
    # Save original references
    original_engine = db_module.engine
    original_async_session = db_module.async_session
    
    # Patch with test versions
    db_module.engine = test_db_engine
    db_module.async_session = test_db_session_factory
    
    yield
    
    # Restore original references (for other test suites)
    db_module.engine = original_engine
    db_module.async_session = original_async_session
