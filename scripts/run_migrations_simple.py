#!/usr/bin/env python3
"""
Simple migration runner that uses psycopg2 directly.
Can be run from Docker container or host.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config

# Get database connection from environment or use defaults
DB_HOST = os.environ.get("DB_HOST", "postgres")  # Use 'postgres' for Docker network, 'localhost' for host
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "mem0_rag_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres_password")

# Build database URL
db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("=" * 60)
print("Database Migration Runner")
print("=" * 60)
print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
print()

# Configure Alembic
alembic_cfg = Config(str(project_root / "alembic.ini"))
alembic_cfg.set_main_option("sqlalchemy.url", db_url)

# Run migrations
try:
    print("🔄 Running migrations...")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations completed successfully")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)

