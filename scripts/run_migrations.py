#!/usr/bin/env python3
"""
Script to run Alembic database migrations.

This script ensures the database is accessible and runs migrations.
It can be used in CI/CD pipelines or local development.

Usage:
    python scripts/run_migrations.py [upgrade|downgrade|current|history]
    
    Default: upgrade head
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from app.config.database import db_settings


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    
    # Override database URL from settings
    # Convert asyncpg URL to sync URL for Alembic
    db_url = db_settings.url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    return alembic_cfg


async def check_database_connection():
    """Check if database is accessible."""
    try:
        from sqlalchemy import text
        from app.db.connection import get_db_session
        
        async for session in get_db_session():
            # Try a simple query
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Database URL: {db_settings.url}")
        print("\n💡 Make sure:")
        print("   1. Docker services are running: docker compose -f docker/docker-compose.yml up -d")
        print("   2. Database is accessible at the configured URL")
        print("   3. Environment variables are set correctly")
        return False


def run_migrations(action: str = "upgrade", target: str = "head"):
    """Run Alembic migrations."""
    alembic_cfg = get_alembic_config()
    
    if action == "upgrade":
        print(f"🔄 Running migrations: upgrade {target}")
        command.upgrade(alembic_cfg, target)
        print("✅ Migrations completed successfully")
    elif action == "downgrade":
        print(f"🔄 Rolling back migrations: downgrade {target}")
        command.downgrade(alembic_cfg, target)
        print("✅ Rollback completed successfully")
    elif action == "current":
        print("📊 Current migration revision:")
        command.current(alembic_cfg)
    elif action == "history":
        print("📜 Migration history:")
        command.history(alembic_cfg)
    else:
        print(f"❌ Unknown action: {action}")
        print("   Valid actions: upgrade, downgrade, current, history")
        sys.exit(1)


async def main():
    """Main entry point."""
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    target = sys.argv[2] if len(sys.argv) > 2 else "head"
    
    print("=" * 60)
    print("Database Migration Script")
    print("=" * 60)
    print(f"Database: {db_settings.host}:{db_settings.port}/{db_settings.name}")
    print()
    
    # Check database connection
    if not await check_database_connection():
        sys.exit(1)
    
    print()
    
    # Run migrations
    try:
        run_migrations(action, target)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

