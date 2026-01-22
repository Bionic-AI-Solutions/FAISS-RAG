"""
API routes and endpoints.
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router

# Main API router
router = APIRouter()

# Include sub-routers
router.include_router(auth_router)
router.include_router(health_router)

__all__ = ["router", "auth_router", "health_router"]


