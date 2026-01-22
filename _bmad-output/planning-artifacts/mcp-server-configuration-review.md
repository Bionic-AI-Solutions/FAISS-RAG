# FastMCP Server Configuration Review

**Date:** 2026-01-19  
**Status:** MCP Server Running, Session Configuration Issue

---

## Summary

The MCP server is now running and responding, but requires session initialization. The FastMCP mounting configuration has been reviewed and updated.

---

## Configuration Review

### Current Configuration

**File:** `app/main.py`

```python
# Create FastMCP app with path="/" and stateless_http=True
_mcp_app = mcp_server.http_app(path="/", stateless_http=True)

# Mount at /mcp endpoint
app.mount("/mcp", _mcp_app)
```

**Key Findings:**
1. ✅ FastMCP `http_app()` returns `StarletteWithLifespan` object
2. ✅ Mounting at `/mcp` with `path="/"` makes endpoint accessible at `/mcp/`
3. ✅ FastMCP lifespan must be integrated for task group initialization
4. ⚠️ FastMCP requires session initialization (even with `stateless_http=True`)

---

## Endpoint Format Verification

### MCP Protocol Endpoint

- **Endpoint:** `POST /mcp/`
- **Content-Type:** `application/json`
- **Accept:** `application/json, text/event-stream` (required)
- **Protocol:** JSON-RPC 2.0

### Current Behavior

1. **Without Accept header:** Returns `406 Not Acceptable`
2. **With Accept header:** Returns `400 Bad Request: Missing session ID`
3. **Endpoint accessible:** ✅ Yes, endpoint responds (not 404)

---

## Testing Results

### Test 1: Basic Endpoint Access
```bash
curl -X POST http://localhost:8001/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

**Result:** `400 Bad Request: Missing session ID`

### Test 2: Initialize First
```bash
curl -X POST http://localhost:8001/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

**Result:** Need to test

---

## Configuration Options Tested

### Option 1: Default http_app()
```python
mcp_app = mcp_server.http_app()
app.mount("/mcp", mcp_app)
```
- **Endpoint:** `/mcp/mcp/` (nested path)
- **Status:** ❌ Not ideal

### Option 2: http_app(path="/")
```python
mcp_app = mcp_server.http_app(path="/")
app.mount("/mcp", mcp_app)
```
- **Endpoint:** `/mcp/` (correct)
- **Status:** ✅ Correct path, but requires session

### Option 3: stateless_http=True
```python
mcp_app = mcp_server.http_app(path="/", stateless_http=True)
app.mount("/mcp", mcp_app)
```
- **Endpoint:** `/mcp/` (correct)
- **Status:** ⚠️ Still requires session (may be a FastMCP limitation)

---

## Lifespan Integration

### Issue
FastMCP requires its lifespan to be integrated for task group initialization. Without this, you get:
```
RuntimeError: Task group is not initialized. Make sure to use run().
```

### Solution
```python
# Global reference to MCP app
_mcp_app = None

@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    global _mcp_app
    if _mcp_app and hasattr(_mcp_app, 'lifespan'):
        async with _mcp_app.lifespan(_mcp_app):
            # Initialize services
            await initialize_all_services()
            yield
            # Cleanup services
            await cleanup_all_services()
```

**Status:** ✅ Implemented and working

---

## Backend Client Configuration

### File: `backend/app/services/mcp_client.py`

**Current Configuration:**
```python
# FastMCP redirects /mcp to /mcp/, so use trailing slash
self.mcp_base_url = mcp_base_url.rstrip("/") + "/"

# FastMCP requires Accept header to include both application/json and text/event-stream
request_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
```

**Status:** ✅ Updated with correct headers

---

## Next Steps

### Option 1: Implement Session Management in Backend Client

The backend client needs to:
1. Call `initialize` method first to establish session
2. Store session ID from response
3. Include session ID in subsequent requests

### Option 2: Use Stateless HTTP Mode

If FastMCP supports true stateless mode, configure it to not require sessions.

### Option 3: Use Different Transport

Consider using SSE transport or a different MCP transport mode that doesn't require sessions.

---

## Recommendations

1. **Implement session initialization** in `backend/app/services/mcp_client.py`
2. **Test with initialize call** to verify session flow
3. **Update backend client** to handle MCP protocol session lifecycle
4. **Document session requirements** for future reference

---

## Current Status

- ✅ MCP server starts successfully
- ✅ Endpoint accessible at `/mcp/`
- ✅ Lifespan integration working
- ✅ Backend client configured with correct headers
- ⚠️ Session initialization required (needs implementation)
- ❌ Backend cannot call MCP tools yet (waiting for session support)

---

## Files Modified

1. `app/main.py` - Updated FastMCP mounting and lifespan integration
2. `backend/app/services/mcp_client.py` - Updated Accept header

---

**Next Action:** Implement session management in backend MCP client.
