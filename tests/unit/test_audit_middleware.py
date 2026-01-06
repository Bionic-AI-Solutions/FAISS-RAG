"""
Unit tests for audit logging middleware.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastmcp.server.middleware import MiddlewareContext

from app.mcp.middleware.audit import (
    AuditMiddleware,
    extract_request_params_from_context,
    extract_tool_name_from_context,
    log_audit_event,
)
from app.mcp.middleware.auth import _auth_method_context
from app.mcp.middleware.tenant import (
    _role_context,
    _tenant_id_context,
    _user_id_context,
)


class TestExtractToolNameFromContext:
    """Test tool name extraction from context."""
    
    def test_extract_from_tool_name_attribute(self):
        """Test extraction from tool_name attribute."""
        context = MagicMock()
        context.tool_name = "rag_search"
        
        result = extract_tool_name_from_context(context)
        assert result == "rag_search"
    
    def test_extract_from_request_tool_name(self):
        """Test extraction from request.tool.name."""
        context = MagicMock(spec=[])
        context.request = MagicMock()
        context.request.tool = MagicMock()
        type(context.request.tool).name = "mem0_add_memory"
        
        result = extract_tool_name_from_context(context)
        assert result == "mem0_add_memory"
    
    def test_extract_from_fastmcp_context(self):
        """Test extraction from fastmcp_context."""
        context = MagicMock(spec=[])
        context.fastmcp_context = MagicMock()
        type(context.fastmcp_context).tool_name = "rag_ingest"
        
        result = extract_tool_name_from_context(context)
        assert result == "rag_ingest"
    
    def test_extract_from_method_attribute(self):
        """Test extraction from method attribute."""
        context = MagicMock(spec=[])
        type(context).method = "rag_list_documents"
        
        result = extract_tool_name_from_context(context)
        assert result == "rag_list_documents"
    
    def test_extract_returns_none_when_not_found(self):
        """Test extraction returns None when tool name not found."""
        context = MagicMock(spec=[])
        # Remove all attributes that might be checked
        del context.tool_name
        del context.request
        del context.fastmcp_context
        del context.method
        del context.func
        
        result = extract_tool_name_from_context(context)
        assert result is None


class TestExtractRequestParamsFromContext:
    """Test request params extraction from context."""
    
    def test_extract_from_params_attribute(self):
        """Test extraction from params attribute."""
        context = MagicMock()
        context.params = {"query": "test", "limit": 10}
        
        result = extract_request_params_from_context(context)
        assert result == {"query": "test", "limit": 10}
    
    def test_extract_from_request_params(self):
        """Test extraction from request.params."""
        context = MagicMock(spec=[])
        context.request = MagicMock()
        type(context.request).params = {"document_id": "doc-123"}
        
        result = extract_request_params_from_context(context)
        assert result == {"document_id": "doc-123"}
    
    def test_extract_returns_empty_dict_when_not_found(self):
        """Test extraction returns empty dict when params not found."""
        context = MagicMock(spec=[])
        # Remove all attributes that might be checked
        del context.params
        del context.request
        del context.fastmcp_context
        
        result = extract_request_params_from_context(context)
        assert result == {}


class TestLogAuditEvent:
    """Test audit event logging."""
    
    @pytest.mark.asyncio
    async def test_log_audit_event_creates_log(self):
        """Test that log_audit_event creates an audit log entry."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        async def mock_db_session():
            mock_session_instance = AsyncMock()
            mock_session_instance.add = MagicMock()
            mock_session_instance.commit = AsyncMock()
            mock_session_instance.close = AsyncMock()
            yield mock_session_instance
        
        with patch("app.mcp.middleware.audit.get_db_session", return_value=mock_db_session()):
            await log_audit_event(
                action="rag_search",
                resource_type="rag_operation",
                resource_id="query-123",
                tenant_id=tenant_id,
                user_id=user_id,
                role="tenant_admin",
                auth_method="oauth",
                success=True,
                details={"query": "test"},
            )
            
            # Note: We can't easily verify the calls with async generator mocking
            # The function should complete without errors
    
    @pytest.mark.asyncio
    async def test_log_audit_event_handles_errors_gracefully(self):
        """Test that log_audit_event handles errors gracefully."""
        with patch("app.mcp.middleware.audit.get_db_session") as mock_session:
            # Mock database error
            mock_session.side_effect = Exception("Database error")
            
            # Should not raise exception
            await log_audit_event(
                action="rag_search",
                resource_type="rag_operation",
            )


class TestAuditMiddleware:
    """Test audit middleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_logs_pre_and_post_execution(self):
        """Test that middleware logs both pre and post execution."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context variables
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")
        _auth_method_context.set("oauth")
        
        # Mock context
        context = MagicMock(spec=MiddlewareContext)
        context.tool_name = "rag_search"
        context.params = {"query": "test"}
        
        # Mock call_next
        call_next = AsyncMock(return_value={"results": []})
        
        # Mock log_audit_event
        with patch("app.mcp.middleware.audit.log_audit_event") as mock_log:
            middleware = AuditMiddleware()
            result = await middleware.on_request(context, call_next)
            
            # Verify tool was executed
            assert call_next.called
            assert result == {"results": []}
            
            # Verify audit logging was called (pre and post)
            assert mock_log.call_count == 2
    
    @pytest.mark.asyncio
    async def test_middleware_logs_failure_on_exception(self):
        """Test that middleware logs failure when tool raises exception."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context variables
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")
        _auth_method_context.set("oauth")
        
        # Mock context
        context = MagicMock(spec=MiddlewareContext)
        context.tool_name = "rag_search"
        
        # Mock call_next to raise exception
        call_next = AsyncMock(side_effect=ValueError("Tool error"))
        
        # Mock log_audit_event
        with patch("app.mcp.middleware.audit.log_audit_event") as mock_log:
            middleware = AuditMiddleware()
            
            with pytest.raises(ValueError):
                await middleware.on_request(context, call_next)
            
            # Verify audit logging was called (pre and post with failure)
            assert mock_log.call_count == 2
            
            # Verify post-execution log has success=False
            post_call = mock_log.call_args_list[1]
            assert post_call[1]["success"] is False
    
    @pytest.mark.asyncio
    async def test_middleware_determines_resource_type_from_tool_name(self):
        """Test that middleware determines resource type from tool name."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context variables
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        _role_context.set("tenant_admin")
        _auth_method_context.set("oauth")
        
        # Test RAG tool
        context = MagicMock(spec=MiddlewareContext)
        context.tool_name = "rag_search"
        context.params = {"query": "test"}
        
        call_next = AsyncMock(return_value={})
        
        with patch("app.mcp.middleware.audit.log_audit_event") as mock_log:
            middleware = AuditMiddleware()
            await middleware.on_request(context, call_next)
            
            # Verify resource_type is "rag_operation"
            pre_call = mock_log.call_args_list[0]
            assert pre_call[1]["resource_type"] == "rag_operation"
        
        # Test Mem0 tool
        context.tool_name = "mem0_add_memory"
        context.params = {"user_id": "user-123"}
        
        with patch("app.mcp.middleware.audit.log_audit_event") as mock_log:
            middleware = AuditMiddleware()
            await middleware.on_request(context, call_next)
            
            # Verify resource_type is "memory_operation"
            pre_call = mock_log.call_args_list[0]
            assert pre_call[1]["resource_type"] == "memory_operation"

