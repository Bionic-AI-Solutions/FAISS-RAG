"""
Unified health check service for all infrastructure services.
"""

import asyncio
from typing import Dict, Any

from app.db.connection import check_database_health as check_db_connection
from app.services.redis_client import check_redis_health
from app.services.minio_client import check_minio_health
from app.services.meilisearch_client import check_meilisearch_health
from app.services.mem0_client import mem0_client
from app.services.langfuse_client import check_langfuse_health
from app.services.faiss_manager import faiss_manager
from pathlib import Path


async def check_mem0_health() -> Dict[str, Any]:
    """
    Check Mem0 health using the SDK client.
    
    Returns:
        dict: Health status for Mem0
    """
    is_healthy = await mem0_client.check_connection()
    return {
        "status": is_healthy,
        "message": "Mem0 is operational" if is_healthy else "Mem0 is down",
    }


async def check_database_health() -> Dict[str, Any]:
    """
    Check database health.
    
    Returns:
        dict: Health status for database
    """
    return await check_db_connection()


async def check_faiss_health() -> Dict[str, Any]:
    """
    Check FAISS health by verifying index manager initialization and index path accessibility.
    
    Returns:
        dict: Health status for FAISS
    """
    try:
        # Check if FAISS manager is initialized
        if not faiss_manager:
            return {
                "status": False,
                "message": "FAISS manager not initialized",
            }
        
        # Check if index path is accessible
        try:
            faiss_manager._ensure_index_path()
            index_path = faiss_manager.index_path
            
            # Verify path exists or can be created
            if not index_path.exists():
                # Try to create it
                try:
                    index_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return {
                        "status": False,
                        "message": f"FAISS index path not accessible: {str(e)}",
                    }
            
            # Check if path is writable
            test_file = index_path / ".health_check"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                return {
                    "status": False,
                    "message": f"FAISS index path not writable: {str(e)}",
                }
            
            return {
                "status": True,
                "message": f"FAISS is operational (Index path: {index_path})",
            }
        except Exception as e:
            return {
                "status": False,
                "message": f"FAISS health check failed: {str(e)}",
            }
    except Exception as e:
        return {
            "status": False,
            "message": f"FAISS health check error: {str(e)}",
        }


async def check_all_services_health() -> Dict[str, Any]:
    """
    Check health of all infrastructure services.
    
    Returns:
        dict: Health status for all services with overall status
    """
    # Check all services in parallel
    results = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_minio_health(),
        check_meilisearch_health(),
        check_mem0_health(),
        check_faiss_health(),
        check_langfuse_health(),
        return_exceptions=True,
    )
    
    # Map results to service names
    services = {
        "postgresql": results[0] if not isinstance(results[0], Exception) else {"status": False, "message": str(results[0])},
        "redis": results[1] if not isinstance(results[1], Exception) else {"status": False, "message": str(results[1])},
        "minio": results[2] if not isinstance(results[2], Exception) else {"status": False, "message": str(results[2])},
        "meilisearch": results[3] if not isinstance(results[3], Exception) else {"status": False, "message": str(results[3])},
        "mem0": results[4] if not isinstance(results[4], Exception) else {"status": False, "message": str(results[4])},
        "faiss": results[5] if not isinstance(results[5], Exception) else {"status": False, "message": str(results[5])},
        "langfuse": results[6] if not isinstance(results[6], Exception) else {"status": False, "message": str(results[6])},
    }
    
    # Calculate overall status
    all_healthy = all(service.get("status", False) for service in services.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services,
    }


async def check_service_health(service_name: str) -> Dict[str, Any]:
    """
    Check health of a specific service.
    
    Args:
        service_name: Name of the service to check
    
    Returns:
        dict: Health status for the service
    """
    service_checks = {
        "postgresql": check_database_health,
        "redis": check_redis_health,
        "minio": check_minio_health,
        "meilisearch": check_meilisearch_health,
        "mem0": check_mem0_health,
        "faiss": check_faiss_health,
        "langfuse": check_langfuse_health,
    }
    
    if service_name not in service_checks:
        return {"status": False, "message": f"Unknown service: {service_name}"}
    
    return await service_checks[service_name]()

