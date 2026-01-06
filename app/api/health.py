"""
Health check API endpoints.

Health check endpoints bypass authentication and rate limiting for monitoring purposes.
"""

import time
from fastapi import APIRouter

from app.services.health import check_all_services_health, check_service_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Unified health check endpoint for all infrastructure services.
    
    Returns:
        dict: Health status for all services with overall status
    """
    start_time = time.time()
    health_status = await check_all_services_health()
    elapsed_ms = (time.time() - start_time) * 1000
    
    # Add response time to health status
    health_status["response_time_ms"] = elapsed_ms
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes.
    
    Returns:
        dict: Readiness status (all services must be available)
    """
    start_time = time.time()
    health_status = await check_all_services_health()
    elapsed_ms = (time.time() - start_time) * 1000
    
    # Check if all services are ready
    services = health_status.get("services", {})
    all_ready = all(
        service.get("status", False) for service in services.values()
    )
    
    return {
        "ready": all_ready,
        "status": "ready" if all_ready else "not_ready",
        "services": services,
        "response_time_ms": elapsed_ms,
    }


@router.get("/{service_name}")
async def service_health_check(service_name: str):
    """
    Health check endpoint for a specific service.
    
    Args:
        service_name: Name of the service (postgresql, redis, minio, meilisearch, mem0, langfuse)
    
    Returns:
        dict: Health status for the service
    """
    start_time = time.time()
    health_status = await check_service_health(service_name)
    elapsed_ms = (time.time() - start_time) * 1000
    
    health_status["response_time_ms"] = elapsed_ms
    
    return health_status






