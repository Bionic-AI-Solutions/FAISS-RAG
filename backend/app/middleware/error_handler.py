"""
Error handling middleware for REST API.

Provides consistent error responses and handles exceptions.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def error_handler(request: Request, call_next):
    """
    Global error handler middleware.
    
    Catches all exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except RequestValidationError as e:
        logger.warning(
            f"Request validation error: path={request.url.path}, errors={e.errors()}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Invalid request parameters",
                "details": e.errors(),
            },
        )
    except StarletteHTTPException as e:
        logger.warning(
            f"HTTP exception: path={request.url.path}, status={e.status_code}, detail={e.detail}"
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "HTTP Error",
                "message": e.detail,
            },
        )
    except ValueError as e:
        logger.error(
            f"Value error: path={request.url.path}, error={str(e)}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Bad Request",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(
            f"Unhandled exception: {str(e)}",
            extra={"path": request.url.path},
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            },
        )
