#!/usr/bin/env python3
"""Test database connection from host environment."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.database import db_settings
from app.db.connection import get_db_session
from sqlalchemy import text


async def test_connection():
    """Test database connection."""
    print("=" * 80)
    print("Testing Database Connection")
    print("=" * 80)
    print(f"\nDatabase Configuration:")
    print(f"  Host: {db_settings.host}")
    print(f"  Port: {db_settings.port}")
    print(f"  Database: {db_settings.name}")
    print(f"  User: {db_settings.user}")
    print(f"  URL: postgresql://{db_settings.user}:***@{db_settings.host}:{db_settings.port}/{db_settings.name}")
    print()
    
    try:
        print("Attempting connection...")
        async for session in get_db_session():
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Connection successful! Test query result: {row[0]}")
            
            # Test database info
            result = await session.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            print(f"\nDatabase Info:")
            print(f"  Database: {db_info[0]}")
            print(f"  User: {db_info[1]}")
            print(f"  Version: {db_info[2][:50]}...")
            
            break
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_connection())


