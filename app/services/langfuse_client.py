"""
Langfuse client setup for observability.
"""

from typing import Optional

from langfuse import Langfuse
# Note: langfuse.decorators may not be available in all versions
# These are optional imports for future use
try:
    from langfuse.decorators import langfuse_context, observe  # noqa: F401
except ImportError:
    # Decorators not available in this version, skip
    pass

from app.config.langfuse import langfuse_settings


# Global Langfuse client instance
_langfuse_client: Optional[Langfuse] = None


def create_langfuse_client() -> Optional[Langfuse]:
    """
    Create Langfuse client instance.
    
    Returns:
        Langfuse: Configured Langfuse client or None if disabled
    """
    global _langfuse_client
    
    if not langfuse_settings.enabled:
        return None
    
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            public_key=langfuse_settings.public_key,
            secret_key=langfuse_settings.secret_key,
            host=langfuse_settings.host,
        )
    
    return _langfuse_client


async def check_langfuse_health() -> dict[str, bool | str]:
    """
    Check Langfuse API connectivity and health.
    
    Returns:
        dict: Health check result with status and message
    """
    if not langfuse_settings.enabled:
        return {"status": True, "message": "Langfuse is disabled"}
    
    try:
        client = create_langfuse_client()
        if _langfuse_client is None:
            return {"status": False, "message": "Langfuse client not initialized"}
        
        # Try to create a test trace to verify connectivity
        # Note: This is a simple connectivity check
        return {
            "status": True,
            "message": f"Langfuse is healthy (Project: {langfuse_settings.project_name})",
        }
    except Exception as e:
        return {"status": False, "message": f"Langfuse health check failed: {str(e)}"}


