"""
Context validation middleware for MCP requests.
"""

from typing import Optional
from uuid import UUID

import structlog

from app.config.settings import settings

logger = structlog.get_logger(__name__)


class MCPContext:
    """
    MCP request context containing tenant, user, and role information.
    """
    
    def __init__(
        self,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        role: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
    
    def is_valid(self) -> bool:
        """
        Check if context has all required fields.
        
        Returns:
            bool: True if context is valid, False otherwise
        """
        return (
            self.tenant_id is not None and
            self.user_id is not None and
            self.role is not None
        )
    
    def to_dict(self) -> dict:
        """
        Convert context to dictionary.
        
        Returns:
            dict: Context as dictionary
        """
        return {
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "role": self.role,
        }


class ContextValidationError(Exception):
    """
    Exception raised when context validation fails.
    """
    
    def __init__(self, message: str, error_code: str = "FR-ERROR-003"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


def validate_mcp_context(
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    role: Optional[str] = None,
) -> MCPContext:
    """
    Validate MCP request context.
    
    Args:
        tenant_id: Tenant ID from request headers/context
        user_id: User ID from request headers/context
        role: User role from request headers/context
    
    Returns:
        MCPContext: Validated context object
    
    Raises:
        ContextValidationError: If context validation fails
    """
    # Convert string UUIDs to UUID objects if provided
    tenant_uuid = None
    user_uuid = None
    
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            raise ContextValidationError(
                f"Invalid tenant_id format: {tenant_id}",
                error_code="FR-ERROR-003"
            )
    
    if user_id:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise ContextValidationError(
                f"Invalid user_id format: {user_id}",
                error_code="FR-ERROR-003"
            )
    
    # Create context
    context = MCPContext(
        tenant_id=tenant_uuid,
        user_id=user_uuid,
        role=role,
    )
    
    # Validate required fields
    if not context.is_valid():
        missing_fields = []
        if not context.tenant_id:
            missing_fields.append("tenant_id")
        if not context.user_id:
            missing_fields.append("user_id")
        if not context.role:
            missing_fields.append("role")
        
        raise ContextValidationError(
            f"Missing required context fields: {', '.join(missing_fields)}",
            error_code="FR-ERROR-003"
        )
    
    logger.debug(
        "MCP context validated",
        tenant_id=str(context.tenant_id),
        user_id=str(context.user_id),
        role=context.role
    )
    
    return context


def extract_context_from_headers(headers: dict) -> MCPContext:
    """
    Extract MCP context from HTTP headers.
    
    Args:
        headers: HTTP request headers
    
    Returns:
        MCPContext: Extracted context
    
    Raises:
        ContextValidationError: If context extraction fails
    """
    tenant_id = headers.get(settings.tenant_id_header.replace("X-", "").replace("-", "_").lower())
    user_id = headers.get("X-User-ID")
    role = headers.get("X-User-Role")
    
    return validate_mcp_context(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
    )





