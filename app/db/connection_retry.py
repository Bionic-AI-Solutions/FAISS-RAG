"""
Database connection retry logic for handling transient failures.
"""

import asyncio
from typing import Callable, TypeVar, Any

from sqlalchemy.exc import OperationalError, DisconnectionError
import structlog

from app.db.connection import async_session, engine

logger = structlog.get_logger(__name__)

T = TypeVar('T')


async def retry_db_operation(
    operation: Callable[[], Any],
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> T:
    """
    Retry a database operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Result of the operation
        
    Raises:
        Exception: Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (OperationalError, DisconnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                delay = retry_delay * (backoff_factor ** attempt)
                logger.warning(
                    "Database operation failed, retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay=delay,
                    error=str(e)
                )
                await asyncio.sleep(delay)
                
                # Try to reconnect
                try:
                    await engine.dispose()
                    # Engine will be recreated on next use
                    logger.info("Database connection disposed, will reconnect on next operation")
                except Exception as dispose_error:
                    logger.warning("Error disposing database connection", error=str(dispose_error))
            else:
                logger.error(
                    "Database operation failed after all retries",
                    max_retries=max_retries,
                    error=str(e)
                )
        except Exception as e:
            # Non-retryable exceptions are raised immediately
            logger.error("Database operation failed with non-retryable error", error=str(e))
            raise
    
    # If we get here, all retries failed
    raise last_exception


async def check_connection_with_retry(max_retries: int = 3) -> dict[str, bool | str]:
    """
    Check database connectivity with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        dict: Health check result with status and message
    """
    async def check_operation():
        from sqlalchemy import text
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return {"status": True, "message": "Database is healthy"}
    
    try:
        return await retry_db_operation(check_operation, max_retries=max_retries)
    except Exception as e:
        return {"status": False, "message": f"Database health check failed after retries: {str(e)}"}





