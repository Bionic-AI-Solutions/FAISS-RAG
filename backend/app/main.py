"""
REST Proxy Backend for Admin UI.

This FastAPI application provides REST endpoints that translate HTTP requests
to MCP tool calls, enabling the frontend to interact with the RAG platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import tenants, documents, analytics, auth, health
from app.middleware.error_handler import error_handler

app = FastAPI(
    title="RAG Platform Admin UI API",
    description="REST API proxy for Admin UI - integrates with MCP tools",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Error handling middleware (must be first)
app.add_middleware(BaseHTTPMiddleware, dispatch=error_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(documents.router)
app.include_router(analytics.router)
app.include_router(health.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "admin-ui-backend"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Platform Admin UI API",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
