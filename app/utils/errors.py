"""
Centralized error handling framework for structured error responses.

Provides consistent error format across all MCP tools with:
- Error code
- Error message
- Error details
- Recovery suggestions
- Request ID
- Appropriate HTTP status codes
"""

import uuid
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class RAGSystemError(Exception):
    """
    Base exception for RAG system errors.
    
    All custom errors should inherit from this class to ensure
    consistent error handling and serialization.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-ERROR-003",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
        request_id: Optional[str] = None,
    ):
        """
        Initialize RAG system error.
        
        Args:
            message: Human-readable error message
            error_code: Error code (e.g., "FR-ERROR-003", "FR-AUTH-001")
            status_code: HTTP status code (400, 401, 403, 404, 429, 500, 503)
            details: Additional error details (dict)
            recovery_suggestions: List of recovery suggestions
            request_id: Request ID for tracking
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.request_id = request_id or str(uuid.uuid4())
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to structured dictionary format.
        
        Returns:
            dict: Structured error response
        """
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "recovery_suggestions": self.recovery_suggestions,
                "request_id": self.request_id,
            },
            "status_code": self.status_code,
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


# HTTP Status Code Mappings
class HTTPStatus:
    """HTTP status code constants."""
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# Domain-Specific Error Classes

class AuthenticationError(RAGSystemError):
    """Authentication error (401 Unauthorized)."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-AUTH-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        recovery_suggestions = recovery_suggestions or [
            "Check that your authentication token is valid",
            "Verify your API key is correct",
            "Ensure your token has not expired",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.UNAUTHORIZED,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class AuthorizationError(RAGSystemError):
    """Authorization error (403 Forbidden)."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-AUTH-002",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        recovery_suggestions = recovery_suggestions or [
            "Check that your role has permission for this operation",
            "Contact your tenant administrator for access",
            "Verify you are accessing the correct tenant",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class RateLimitExceededError(RAGSystemError):
    """Rate limit exceeded error (429 Too Many Requests)."""
    
    def __init__(
        self,
        message: str,
        retry_after: int,
        limit: int,
        remaining: int,
        reset_time: int,
        error_code: str = "FR-ERROR-004",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        details = details or {}
        details.update({
            "retry_after": retry_after,
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time,
        })
        recovery_suggestions = recovery_suggestions or [
            f"Wait {retry_after} seconds before retrying",
            f"Rate limit: {limit} requests per minute",
            f"Reset time: {reset_time}",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )
        self.retry_after = retry_after


class TenantNotFoundError(RAGSystemError):
    """Tenant not found error (404 Not Found)."""
    
    def __init__(
        self,
        tenant_id: str,
        error_code: str = "FR-TENANT-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        message = f"Tenant not found: {tenant_id}"
        details = details or {}
        details["tenant_id"] = tenant_id
        recovery_suggestions = recovery_suggestions or [
            "Verify the tenant ID is correct",
            "Check that the tenant exists",
            "Contact support if the tenant should exist",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.NOT_FOUND,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class DocumentNotFoundError(RAGSystemError):
    """Document not found error (404 Not Found)."""
    
    def __init__(
        self,
        document_id: str,
        error_code: str = "FR-DOC-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        message = f"Document not found: {document_id}"
        details = details or {}
        details["document_id"] = document_id
        recovery_suggestions = recovery_suggestions or [
            "Verify the document ID is correct",
            "Check that the document exists",
            "Ensure you have access to the document",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.NOT_FOUND,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class ResourceNotFoundError(RAGSystemError):
    """Generic resource not found error (404 Not Found)."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: str = "FR-RESOURCE-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        recovery_suggestions = recovery_suggestions or [
            "Verify the resource ID is correct",
            "Check that the resource exists",
            "Ensure you have access to the resource",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.NOT_FOUND,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class ValidationError(RAGSystemError):
    """Validation error (400 Bad Request)."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        error_code: str = "FR-VALIDATION-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        recovery_suggestions = recovery_suggestions or [
            "Check the request parameters",
            "Verify all required fields are provided",
            "Ensure field formats are correct",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.BAD_REQUEST,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class ServiceUnavailableError(RAGSystemError):
    """Service unavailable error (503 Service Unavailable)."""
    
    def __init__(
        self,
        service: str,
        error_code: str = "FR-SERVICE-001",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        message = f"Service unavailable: {service}"
        details = details or {}
        details["service"] = service
        recovery_suggestions = recovery_suggestions or [
            "The service is temporarily unavailable",
            "Please try again in a few moments",
            "Contact support if the issue persists",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class TenantIsolationError(RAGSystemError):
    """Tenant isolation violation error (403 Forbidden)."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-ERROR-003",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        recovery_suggestions = recovery_suggestions or [
            "Verify you are accessing the correct tenant",
            "Check your tenant membership",
            "Contact support if you believe this is an error",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class TenantValidationError(RAGSystemError):
    """Tenant validation error (403 Forbidden)."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-ERROR-003",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        recovery_suggestions = recovery_suggestions or [
            "Verify the tenant ID is correct",
            "Check your tenant membership",
            "Contact support if you believe this is an error",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


class MemoryAccessError(RAGSystemError):
    """Memory access error (403 Forbidden)."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "FR-DATA-002",
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        recovery_suggestions = recovery_suggestions or [
            "Verify you are accessing your own memory",
            "Check that the user_id is correct",
            "Only Tenant Admins can access other users' memories",
        ]
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
            recovery_suggestions=recovery_suggestions,
        )


def handle_error(error: Exception, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Handle and serialize an error to structured format.
    
    Args:
        error: Exception to handle
        request_id: Optional request ID for tracking
        
    Returns:
        dict: Structured error response
    """
    # If it's already a RAGSystemError, use its serialization
    if isinstance(error, RAGSystemError):
        if request_id:
            error.request_id = request_id
        return error.to_dict()
    
    # Map common exceptions to RAGSystemError
    if isinstance(error, ValueError):
        rag_error = ValidationError(
            message=str(error),
            request_id=request_id,
        )
    elif isinstance(error, KeyError):
        rag_error = ValidationError(
            message=f"Missing required field: {str(error)}",
            request_id=request_id,
        )
    else:
        # Unknown error - log and return generic error
        logger.error(
            "Unhandled error",
            error=str(error),
            error_type=type(error).__name__,
            request_id=request_id,
        )
        rag_error = RAGSystemError(
            message="Internal server error",
            error_code="FR-ERROR-500",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details={"original_error": str(error)},
            recovery_suggestions=[
                "An unexpected error occurred",
                "Please try again",
                "Contact support if the issue persists",
            ],
            request_id=request_id,
        )
    
    return rag_error.to_dict()

