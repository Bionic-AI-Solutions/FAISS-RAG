# Nano Banana MCP Server - Fixes Applied

## Summary

Updated the Nano Banana MCP server to use the official Gemini API documentation for image generation:
https://ai.google.dev/gemini-api/docs/image-generation

## Changes Made

### 1. Model Name Update
- **Old**: `gemini-2.0-flash-exp` (incorrect - this is a text model)
- **New**: `gemini-2.5-flash-image` (correct - Nano Banana image generation model)
- **Alternative**: `gemini-3-pro-image-preview` (for higher quality)

### 2. API Call Structure
- **Removed**: `response_mime_type="application/json"` (not needed for image generation)
- **Updated**: Images are returned directly in `response.parts` with `part.inline_data`
- **Added**: Support for `part.as_image()` method (PIL Image conversion)

### 3. Response Parsing
- **Updated**: Extract images from `response.parts` directly (new API structure)
- **Fallback**: Also check `response.candidates[0].content.parts` (older API versions)
- **Improved**: Added comprehensive None checks to prevent AttributeError

### 4. Aspect Ratio Support
- **Added**: `_calculate_aspect_ratio()` method to map width/height to supported ratios
- **Supported ratios**: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
- **Integration**: Uses `ImageConfig` with aspect ratio when available

### 5. Error Handling
- **Improved**: Added try-except blocks around attribute access
- **Better**: More defensive checks for None values
- **Enhanced**: Detailed error messages for debugging

## Files Modified

1. `/home/skadam/git/MCP/mcp-servers/src/mcp_servers/nano-banana/client.py`
   - Updated `generate_image()` method
   - Updated `edit_image()` method
   - Added `_calculate_aspect_ratio()` helper method
   - Changed default model to `gemini-2.5-flash-image`

2. `/home/skadam/git/MCP/mcp-servers/src/mcp_servers/nano-banana/tenant_manager.py`
   - Updated default model in `NanoBananaTenantConfig`
   - Updated environment variable default

3. `/home/skadam/git/MCP/mcp-servers/src/mcp_servers/nano-banana/server.py`
   - Updated default model parameter in `nb_register_tenant` tool

4. `/home/skadam/git/MCP/mcp-servers/docs/nano-banana.md`
   - Updated documentation with correct model names
   - Updated examples

5. `/home/skadam/git/MCP/mcp-servers/docker-compose.yml`
   - Updated default model environment variable

6. `/home/skadam/git/MCP/mcp-servers/k8s/nano-banana/deployment.yaml`
   - Updated default model in ConfigMap

## Next Steps

1. **Rebuild the Docker image**:
   ```bash
   cd /home/skadam/git/MCP/mcp-servers
   docker compose build mcp-nano-banana-server
   ```

2. **Restart the server**:
   ```bash
   docker compose restart mcp-nano-banana-server
   ```

3. **Or deploy to Kubernetes**:
   ```bash
   kubectl apply -f k8s/nano-banana/deployment.yaml
   ```

4. **Test the image generation**:
   ```bash
   cd /home/skadam/git/mem0-rag
   python3 scripts/generate_image_nano.py "Flying pigs in Van Gogh style"
   ```

## Expected Behavior

After the server is restarted with the updated code:

1. **Tenant Registration**: Should work with `gemini-2.5-flash-image` model
2. **Image Generation**: Should return images in `response.parts[].inline_data`
3. **Image Editing**: Should work with text-and-image-to-image prompts
4. **Error Handling**: Should provide clear error messages if image generation fails

## Known Issues

- The server may need to be restarted to pick up the code changes
- If the error persists, check the server logs for the exact line causing the AttributeError
- The Gemini API may return different response structures depending on the SDK version

## References

- Official Gemini API Documentation: https://ai.google.dev/gemini-api/docs/image-generation
- Nano Banana Models: `gemini-2.5-flash-image` and `gemini-3-pro-image-preview`
