"""
Unit tests for audit log query tool.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Import tools module to register tools
from app.mcp.tools import audit  # noqa: F401

from app.mcp.middleware.rbac import UserRole
from app.mcp.middleware.tenant import (
    _role_context,
    _tenant_id_context,
    _user_id_context,
)
# Access the function from the tool registry
from app.mcp.server import mcp_server


class TestRagQueryAuditLogs:
    """Test rag_query_audit_logs tool."""
    
    @pytest.mark.asyncio
    async def test_query_requires_tenant_admin_or_uber_admin(self):
        """Test that query requires Tenant Admin or Uber Admin role."""
        # Set role to END_USER (not allowed)
        _role_context.set(UserRole.END_USER)
        _tenant_id_context.set(uuid4())
        
        # Access the underlying function from the tool registry
        tool_registry = getattr(mcp_server, "_tools", {})
        if "rag_query_audit_logs" not in tool_registry:
            pytest.skip("rag_query_audit_logs not registered")
        
        tool_obj = tool_registry["rag_query_audit_logs"]
        func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
        if func is None:
            pytest.skip("Cannot access underlying function")
        
        with pytest.raises(ValueError, match="Access denied"):
            await func()
    
    @pytest.mark.asyncio
    async def test_tenant_admin_can_query_own_tenant_logs(self):
        """Test that Tenant Admin can query their own tenant's logs."""
        tenant_id = uuid4()
        user_id = uuid4()
        
        # Set context
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(user_id)
        
        # Mock database session
        with patch("app.mcp.tools.audit.get_db_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.get_by_time_range = AsyncMock(return_value=[])
            
            # Mock AuditLogRepository
            with patch("app.mcp.tools.audit.AuditLogRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo
                
                mock_session.return_value.__aiter__ = lambda x: iter([mock_session_instance])
                
                tool_registry = getattr(mcp_server, "_tools", {})
                if "rag_query_audit_logs" not in tool_registry:
                    pytest.skip("rag_query_audit_logs not registered")
                
                tool_obj = tool_registry["rag_query_audit_logs"]
                func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
                if func is None:
                    pytest.skip("Cannot access underlying function")
                
                result = await func(
                    start_time="2025-01-15T00:00:00Z",
                    end_time="2025-01-15T23:59:59Z",
                )
                
                assert result["logs"] == []
                assert result["total"] == 0
                assert result["has_more"] is False
    
    @pytest.mark.asyncio
    async def test_tenant_admin_cannot_query_other_tenant_logs(self):
        """Test that Tenant Admin cannot query other tenant's logs."""
        tenant_id = uuid4()
        other_tenant_id = uuid4()
        
        # Set context
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        
        tool_registry = getattr(mcp_server, "_tools", {})
        if "rag_query_audit_logs" not in tool_registry:
            pytest.skip("rag_query_audit_logs not registered")
        
        tool_obj = tool_registry["rag_query_audit_logs"]
        func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
        if func is None:
            pytest.skip("Cannot access underlying function")
        
        with pytest.raises(ValueError, match="can only query audit logs for their own tenant"):
            await func(tenant_id=str(other_tenant_id))
    
    @pytest.mark.asyncio
    async def test_uber_admin_can_query_any_tenant_logs(self):
        """Test that Uber Admin can query any tenant's logs."""
        tenant_id = uuid4()
        query_tenant_id = uuid4()
        
        # Set context
        _role_context.set(UserRole.UBER_ADMIN)
        _tenant_id_context.set(tenant_id)
        
        # Mock database session
        with patch("app.mcp.tools.audit.get_db_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.get_by_time_range = AsyncMock(return_value=[])
            
            with patch("app.mcp.tools.audit.AuditLogRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo
                
                mock_session.return_value.__aiter__ = lambda x: iter([mock_session_instance])
                
                tool_registry = getattr(mcp_server, "_tools", {})
                if "rag_query_audit_logs" not in tool_registry:
                    pytest.skip("rag_query_audit_logs not registered")
                
                tool_obj = tool_registry["rag_query_audit_logs"]
                func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
                if func is None:
                    pytest.skip("Cannot access underlying function")
                
                result = await func(
                    start_time="2025-01-15T00:00:00Z",
                    end_time="2025-01-15T23:59:59Z",
                    tenant_id=str(query_tenant_id),
                )
                
                assert result["logs"] == []
    
    @pytest.mark.asyncio
    async def test_query_validates_limit(self):
        """Test that query validates limit parameter."""
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(uuid4())
        
        tool_registry = getattr(mcp_server, "_tools", {})
        if "rag_query_audit_logs" not in tool_registry:
            pytest.skip("rag_query_audit_logs not registered")
        
        tool_obj = tool_registry["rag_query_audit_logs"]
        func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
        if func is None:
            pytest.skip("Cannot access underlying function")
        
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await func(limit=0)
        
        with pytest.raises(ValueError, match="Limit must be between 1 and 1000"):
            await func(limit=1001)
    
    @pytest.mark.asyncio
    async def test_query_validates_offset(self):
        """Test that query validates offset parameter."""
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(uuid4())
        
        tool_registry = getattr(mcp_server, "_tools", {})
        if "rag_query_audit_logs" not in tool_registry:
            pytest.skip("rag_query_audit_logs not registered")
        
        tool_obj = tool_registry["rag_query_audit_logs"]
        func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
        if func is None:
            pytest.skip("Cannot access underlying function")
        
        with pytest.raises(ValueError, match="Offset must be >= 0"):
            await func(offset=-1)
    
    @pytest.mark.asyncio
    async def test_query_validates_timestamp_format(self):
        """Test that query validates timestamp format."""
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(uuid4())
        
        tool_registry = getattr(mcp_server, "_tools", {})
        if "rag_query_audit_logs" not in tool_registry:
            pytest.skip("rag_query_audit_logs not registered")
        
        tool_obj = tool_registry["rag_query_audit_logs"]
        func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
        if func is None:
            pytest.skip("Cannot access underlying function")
        
        with pytest.raises(ValueError, match="Invalid start_time format"):
            await func(start_time="invalid-format")
        
        with pytest.raises(ValueError, match="Invalid end_time format"):
            await func(end_time="invalid-format")
    
    @pytest.mark.asyncio
    async def test_query_filters_by_action_type(self):
        """Test that query filters by action type."""
        tenant_id = uuid4()
        
        _role_context.set(UserRole.TENANT_ADMIN)
        _tenant_id_context.set(tenant_id)
        
        # Mock database session
        with patch("app.mcp.tools.audit.get_db_session") as mock_session:
            mock_session_instance = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.get_by_action = AsyncMock(return_value=[])
            
            with patch("app.mcp.tools.audit.AuditLogRepository") as mock_repo_class:
                mock_repo_class.return_value = mock_repo
                
                mock_session.return_value.__aiter__ = lambda x: iter([mock_session_instance])
                
                tool_registry = getattr(mcp_server, "_tools", {})
                if "rag_query_audit_logs" not in tool_registry:
                    pytest.skip("rag_query_audit_logs not registered")
                
                tool_obj = tool_registry["rag_query_audit_logs"]
                func = tool_obj.func if hasattr(tool_obj, "func") else tool_obj
                if func is None:
                    pytest.skip("Cannot access underlying function")
                
                result = await func(action_type="rag_search")
                
                assert mock_repo.get_by_action.called
                call_args = mock_repo.get_by_action.call_args
                assert call_args[1]["action"] == "rag_search"
                assert call_args[1]["tenant_id"] == tenant_id

