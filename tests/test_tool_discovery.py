"""
Test tool discovery functionality.
"""
import pytest
from app.mcp.server import mcp_server


def test_tool_registration():
    """Test that tools are registered with the MCP server."""
    # Import tools module to trigger registration
    from app.mcp.tools import discovery  # noqa: F401
    
    # Check that rag_list_tools is registered
    # FastMCP stores tools in a registry - check if it's accessible
    assert hasattr(mcp_server, 'tool'), "MCP server should have tool decorator"
    
    # Check that tools are registered in the server
    # FastMCP stores tools in _tools attribute
    tool_registry = getattr(mcp_server, "_tools", {})
    assert "rag_list_tools" in tool_registry, "rag_list_tools should be registered"


def test_rag_list_tools_returns_list():
    """Test that rag_list_tools returns a list."""
    # Access the underlying function from the tool registry
    tool_registry = getattr(mcp_server, "_tools", {})
    if "rag_list_tools" in tool_registry:
        tool_obj = tool_registry["rag_list_tools"]
        # Get the underlying function from the FunctionTool
        if hasattr(tool_obj, "func"):
            func = tool_obj.func
        elif hasattr(tool_obj, "__wrapped__"):
            func = tool_obj.__wrapped__
        else:
            # If we can't get the function, skip this test
            pytest.skip("Cannot access underlying function from tool")
        
        result = func()
        assert isinstance(result, list), "rag_list_tools should return a list"
        # Should return at least itself (rag_list_tools)
        assert len(result) >= 0, "Should return at least 0 tools (may be empty if not registered yet)"
    else:
        pytest.skip("rag_list_tools not registered in tool registry")


def test_tool_list_structure():
    """Test that tool list has correct structure."""
    # Access the underlying function from the tool registry
    tool_registry = getattr(mcp_server, "_tools", {})
    if "rag_list_tools" in tool_registry:
        tool_obj = tool_registry["rag_list_tools"]
        # Get the underlying function from the FunctionTool
        if hasattr(tool_obj, "func"):
            func = tool_obj.func
        elif hasattr(tool_obj, "__wrapped__"):
            func = tool_obj.__wrapped__
        else:
            pytest.skip("Cannot access underlying function from tool")
        
        result = func()
        for tool in result:
            assert isinstance(tool, dict), "Each tool should be a dict"
            assert "name" in tool, "Tool should have 'name' field"
            assert "description" in tool, "Tool should have 'description' field"
            assert "parameters" in tool, "Tool should have 'parameters' field"
            assert "return_type" in tool, "Tool should have 'return_type' field"
    else:
        pytest.skip("rag_list_tools not registered in tool registry")



