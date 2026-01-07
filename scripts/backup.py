#!/usr/bin/env python3
"""
Backup script for PostgreSQL, FAISS indices, and Mem0 memory.

Supports:
- PostgreSQL daily backups (pg_dump)
- FAISS indices daily snapshots
- Mem0 memory daily snapshots
- Backup retention (30 days for data, 7 days for indices)
- Backup storage in MinIO backup bucket
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import structlog

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from app.services.minio_client import create_minio_client, get_tenant_bucket
from app.services.redis_client import get_redis_client
from app.utils.minio_buckets import get_tenant_bucket_name

logger = structlog.get_logger(__name__)

# Backup configuration
BACKUP_RETENTION_DAYS_DATA = 30
BACKUP_RETENTION_DAYS_INDICES = 7
BACKUP_BUCKET_PREFIX = "backup"


async def backup_postgresql(backup_dir: Path) -> Optional[str]:
    """
    Backup PostgreSQL database.
    
    Args:
        backup_dir: Directory to store backup file
        
    Returns:
        str: Path to backup file or None if failed
    """
    try:
        from app.config.postgres import postgres_settings
        
        backup_file = backup_dir / f"postgresql_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        # Use pg_dump to backup database
        env = os.environ.copy()
        if postgres_settings.password:
            env["PGPASSWORD"] = postgres_settings.password
        
        cmd = [
            "pg_dump",
            "-h", postgres_settings.host,
            "-p", str(postgres_settings.port),
            "-U", postgres_settings.user,
            "-d", postgres_settings.database,
            "-f", str(backup_file),
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("PostgreSQL backup created", backup_file=str(backup_file))
            return str(backup_file)
        else:
            logger.error("PostgreSQL backup failed", error=result.stderr)
            return None
    except Exception as e:
        logger.error("PostgreSQL backup error", error=str(e))
        return None


async def backup_faiss_indices(backup_dir: Path) -> Optional[str]:
    """
    Backup FAISS indices.
    
    Args:
        backup_dir: Directory to store backup file
        
    Returns:
        str: Path to backup archive or None if failed
    """
    try:
        from app.config.faiss import faiss_settings
        
        indices_dir = Path(faiss_settings.index_path)
        if not indices_dir.exists():
            logger.warning("FAISS indices directory does not exist", path=str(indices_dir))
            return None
        
        backup_file = backup_dir / f"faiss_indices_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        
        # Create tar.gz archive of indices
        cmd = [
            "tar",
            "-czf",
            str(backup_file),
            "-C",
            str(indices_dir.parent),
            indices_dir.name,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("FAISS indices backup created", backup_file=str(backup_file))
            return str(backup_file)
        else:
            logger.error("FAISS indices backup failed", error=result.stderr)
            return None
    except Exception as e:
        logger.error("FAISS indices backup error", error=str(e))
        return None


async def backup_mem0_memory(backup_dir: Path) -> Optional[str]:
    """
    Backup Mem0 memory from Redis.
    
    Args:
        backup_dir: Directory to store backup file
        
    Returns:
        str: Path to backup file or None if failed
    """
    try:
        redis_client = await get_redis_client()
        
        # Get all memory keys from Redis
        # Pattern: tenant:{tenant_id}:user:{user_id}:memory:*
        memory_keys = []
        async for key in redis_client.scan_iter(match="tenant:*:user:*:memory:*"):
            memory_keys.append(key)
        
        if not memory_keys:
            logger.info("No Mem0 memory data to backup")
            return None
        
        backup_file = backup_dir / f"mem0_memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Export memory data to JSON
        import json
        memory_data = {}
        for key in memory_keys:
            value = await redis_client.get(key)
            if value:
                try:
                    memory_data[key.decode() if isinstance(key, bytes) else key] = json.loads(value)
                except:
                    memory_data[key.decode() if isinstance(key, bytes) else key] = value.decode() if isinstance(value, bytes) else value
        
        with open(backup_file, "w") as f:
            json.dump(memory_data, f, indent=2)
        
        logger.info("Mem0 memory backup created", backup_file=str(backup_file), keys=len(memory_keys))
        return str(backup_file)
    except Exception as e:
        logger.error("Mem0 memory backup error", error=str(e))
        return None


async def upload_to_minio(backup_file: str, backup_type: str) -> bool:
    """
    Upload backup file to MinIO backup bucket.
    
    Args:
        backup_file: Path to backup file
        backup_type: Type of backup (postgresql, faiss, mem0)
        
    Returns:
        bool: True if upload successful
    """
    try:
        from minio import Minio
        from app.config.minio import minio_settings
        
        minio_client = create_minio_client()
        backup_bucket = f"{BACKUP_BUCKET_PREFIX}-{backup_type}"
        
        # Create backup bucket if it doesn't exist
        if not minio_client.bucket_exists(backup_bucket):
            minio_client.make_bucket(backup_bucket, location=minio_settings.bucket_region)
        
        # Upload backup file
        backup_path = Path(backup_file)
        object_name = backup_path.name
        
        minio_client.fput_object(
            backup_bucket,
            object_name,
            backup_file,
        )
        
        logger.info("Backup uploaded to MinIO", bucket=backup_bucket, object=object_name)
        return True
    except Exception as e:
        logger.error("MinIO upload error", error=str(e))
        return False


async def cleanup_old_backups(backup_type: str, retention_days: int):
    """
    Clean up old backups from MinIO.
    
    Args:
        backup_type: Type of backup (postgresql, faiss, mem0)
        retention_days: Number of days to retain backups
    """
    try:
        from minio import Minio
        from app.config.minio import minio_settings
        
        minio_client = create_minio_client()
        backup_bucket = f"{BACKUP_BUCKET_PREFIX}-{backup_type}"
        
        if not minio_client.bucket_exists(backup_bucket):
            return
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # List all objects in backup bucket
        objects = minio_client.list_objects(backup_bucket, recursive=True)
        
        deleted_count = 0
        for obj in objects:
            # Check if object is older than retention period
            if obj.last_modified < cutoff_date:
                minio_client.remove_object(backup_bucket, obj.object_name)
                deleted_count += 1
                logger.debug("Deleted old backup", bucket=backup_bucket, object=obj.object_name)
        
        if deleted_count > 0:
            logger.info("Cleaned up old backups", bucket=backup_bucket, deleted=deleted_count)
    except Exception as e:
        logger.error("Backup cleanup error", error=str(e))


async def main():
    """Main backup function."""
    logger.info("Starting backup process")
    
    # Create backup directory
    backup_dir = Path("/tmp/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup PostgreSQL
    postgres_backup = await backup_postgresql(backup_dir)
    if postgres_backup:
        await upload_to_minio(postgres_backup, "postgresql")
        await cleanup_old_backups("postgresql", BACKUP_RETENTION_DAYS_DATA)
    
    # Backup FAISS indices
    faiss_backup = await backup_faiss_indices(backup_dir)
    if faiss_backup:
        await upload_to_minio(faiss_backup, "faiss")
        await cleanup_old_backups("faiss", BACKUP_RETENTION_DAYS_INDICES)
    
    # Backup Mem0 memory
    mem0_backup = await backup_mem0_memory(backup_dir)
    if mem0_backup:
        await upload_to_minio(mem0_backup, "mem0")
        await cleanup_old_backups("mem0", BACKUP_RETENTION_DAYS_DATA)
    
    logger.info("Backup process completed")


if __name__ == "__main__":
    asyncio.run(main())








