"""
API routes and endpoints.
"""

from fastapi import APIRouter

from app.api.health import router as health_router

# Main API router
router = APIRouter()

# Include sub-routers
router.include_router(health_router)

__all__ = ["router", "health_router"]


