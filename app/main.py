"""
Main FastAPI application with FastMCP integration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
import structlog

from app.api import router as api_router
from app.config.settings import settings
from app.mcp.server import mcp_server
from app.services.initialization import cleanup_all_services, initialize_all_services

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Application lifespan manager for FastAPI.
    Handles startup and shutdown of all services.
    """
    # Startup
    logger.info("Starting application services...")
    try:
        await initialize_all_services()
        logger.info("Application services initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize application services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application services...")
    try:
        await cleanup_all_services()
        logger.info("Application services cleaned up successfully")
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e))


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application with FastMCP integration.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-tenant RAG system with Mem0 integration",
        lifespan=app_lifespan,
    )
    
    # Mount API router
    app.include_router(api_router, prefix="/api")
    
    # Mount FastMCP server at /mcp endpoint
    mcp_app = mcp_server.http_app(path="/mcp")
    app.mount("/mcp", mcp_app)
    
    logger.info(
        "FastAPI application created",
        app_name=settings.app_name,
        mcp_path="/mcp"
    )
    
    return app


# Create application instance
app = create_app()





