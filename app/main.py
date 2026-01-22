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


# Global reference to MCP app for lifespan access
_mcp_app = None

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    """
    Combined application lifespan manager for FastAPI and FastMCP.
    Handles startup and shutdown of all services, including FastMCP's lifespan.
    """
    global _mcp_app
    
    # Startup: Run both lifespans
    logger.info("Starting application services...")
    
    # Start FastMCP lifespan if available
    if _mcp_app and hasattr(_mcp_app, 'lifespan'):
        async with _mcp_app.lifespan(_mcp_app):
            # Start our services
            try:
                await initialize_all_services()
                logger.info("Application services initialization completed (some services may be unavailable)")
            except Exception as e:
                logger.warning("Some services failed to initialize, app will continue", error=str(e))
            
            yield
            
            # Shutdown
            logger.info("Shutting down application services...")
            try:
                await cleanup_all_services()
                logger.info("Application services cleaned up successfully")
            except Exception as e:
                logger.error("Error during application shutdown", error=str(e))
    else:
        # Fallback: Just run our services if MCP app not available
        try:
            await initialize_all_services()
            logger.info("Application services initialization completed (some services may be unavailable)")
        except Exception as e:
            logger.warning("Some services failed to initialize, app will continue", error=str(e))
        
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
    global _mcp_app
    
    # Create FastMCP app first (needed for lifespan)
    # Use path="/" so when mounted at /mcp, endpoint is /mcp/ (not /mcp/mcp/)
    # Use json_response=True for stateless JSON responses (no SSE, no sessions)
    _mcp_app = mcp_server.http_app(path="/", json_response=True)
    
    # Create FastAPI app with combined lifespan
    # FastMCP requires its lifespan to be integrated for task group initialization
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-tenant RAG system with Mem0 integration",
        lifespan=combined_lifespan,
    )
    
    # Mount API router
    app.include_router(api_router, prefix="/api")
    
    # Mount FastMCP server at /mcp endpoint
    # FastMCP http_app() with path="/" creates routes at root
    # When mounted at /mcp, the endpoint becomes /mcp/
    app.mount("/mcp", _mcp_app)
    
    logger.info(
        "FastAPI application created",
        app_name=settings.app_name,
        mcp_path="/mcp"
    )
    
    return app


# Create application instance
app = create_app()












