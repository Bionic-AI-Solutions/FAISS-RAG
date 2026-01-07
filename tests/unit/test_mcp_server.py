"""
Unit tests for MCP server framework implementation.
"""

import pytest
from uuid import uuid4

from app.mcp.middleware.context import (
    MCPContext,
    ContextValidationError,
    validate_mcp_context,
)


class TestMCPContext:
    """Tests for MCPContext class."""
    
    def test_context_creation(self):
        """Test creating a valid MCP context."""
        tenant_id = uuid4()
        user_id = uuid4()
        context = MCPContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role="user"
        )
        assert context.tenant_id == tenant_id
        assert context.user_id == user_id
        assert context.role == "user"
        assert context.is_valid() is True
    
    def test_context_invalid_missing_tenant(self):
        """Test context is invalid when tenant_id is missing."""
        context = MCPContext(
            tenant_id=None,
            user_id=uuid4(),
            role="user"
        )
        assert context.is_valid() is False
    
    def test_context_invalid_missing_user(self):
        """Test context is invalid when user_id is missing."""
        context = MCPContext(
            tenant_id=uuid4(),
            user_id=None,
            role="user"
        )
        assert context.is_valid() is False
    
    def test_context_invalid_missing_role(self):
        """Test context is invalid when role is missing."""
        context = MCPContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            role=None
        )
        assert context.is_valid() is False
    
    def test_context_to_dict(self):
        """Test context conversion to dictionary."""
        tenant_id = uuid4()
        user_id = uuid4()
        context = MCPContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role="user"
        )
        context_dict = context.to_dict()
        assert context_dict["tenant_id"] == str(tenant_id)
        assert context_dict["user_id"] == str(user_id)
        assert context_dict["role"] == "user"


class TestContextValidation:
    """Tests for context validation functions."""
    
    def test_validate_context_valid(self):
        """Test validation with valid context."""
        tenant_id = str(uuid4())
        user_id = str(uuid4())
        context = validate_mcp_context(
            tenant_id=tenant_id,
            user_id=user_id,
            role="user"
        )
        assert context.is_valid() is True
        assert str(context.tenant_id) == tenant_id
        assert str(context.user_id) == user_id
        assert context.role == "user"
    
    def test_validate_context_invalid_tenant_id_format(self):
        """Test validation fails with invalid tenant_id format."""
        with pytest.raises(ContextValidationError) as exc_info:
            validate_mcp_context(
                tenant_id="invalid-uuid",
                user_id=str(uuid4()),
                role="user"
            )
        assert exc_info.value.error_code == "FR-ERROR-003"
        assert "Invalid tenant_id format" in exc_info.value.message
    
    def test_validate_context_invalid_user_id_format(self):
        """Test validation fails with invalid user_id format."""
        with pytest.raises(ContextValidationError) as exc_info:
            validate_mcp_context(
                tenant_id=str(uuid4()),
                user_id="invalid-uuid",
                role="user"
            )
        assert exc_info.value.error_code == "FR-ERROR-003"
        assert "Invalid user_id format" in exc_info.value.message
    
    def test_validate_context_missing_tenant_id(self):
        """Test validation fails when tenant_id is missing."""
        with pytest.raises(ContextValidationError) as exc_info:
            validate_mcp_context(
                tenant_id=None,
                user_id=str(uuid4()),
                role="user"
            )
        assert exc_info.value.error_code == "FR-ERROR-003"
        assert "Missing required context fields" in exc_info.value.message
        assert "tenant_id" in exc_info.value.message
    
    def test_validate_context_missing_user_id(self):
        """Test validation fails when user_id is missing."""
        with pytest.raises(ContextValidationError) as exc_info:
            validate_mcp_context(
                tenant_id=str(uuid4()),
                user_id=None,
                role="user"
            )
        assert exc_info.value.error_code == "FR-ERROR-003"
        assert "Missing required context fields" in exc_info.value.message
        assert "user_id" in exc_info.value.message
    
    def test_validate_context_missing_role(self):
        """Test validation fails when role is missing."""
        with pytest.raises(ContextValidationError) as exc_info:
            validate_mcp_context(
                tenant_id=str(uuid4()),
                user_id=str(uuid4()),
                role=None
            )
        assert exc_info.value.error_code == "FR-ERROR-003"
        assert "Missing required context fields" in exc_info.value.message
        assert "role" in exc_info.value.message












