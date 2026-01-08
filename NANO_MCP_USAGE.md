# Nano Banana MCP Server - Usage Guide

## Overview

The **Nano Banana MCP Server** is a multi-tenant AI image generation and editing service that uses Google's Gemini API. It's configured at:

- **URL**: `https://mcp.baisoln.com/nano-banana/mcp`
- **Transport**: HTTP with SSE (Server-Sent Events) support
- **Server Version**: 2.14.2
- **Protocol**: MCP (Model Context Protocol) 2024-11-05

## Capabilities

### 1. Image Generation
- Generate images from text prompts using Gemini API
- Support for various styles and sizes
- Multi-tenant isolation

### 2. Image Editing
- Edit existing images based on text prompts
- Iterative editing capabilities
- Support for multiple edit operations

### 3. Multi-Tenant Support
- Tenant-based isolation
- Per-tenant configuration
- Secure API key management

## Configuration

The server is already configured in your MCP setup at `~/.cursor/mcp.json`:

```json
{
  "nano": {
    "url": "https://mcp.baisoln.com/nano-banana/mcp",
    "description": "Nano Banana MCP Server - AI image generation with Gemini API - External access via HTTPS"
  }
}
```

## Active Tenant

**Primary Tenant: `fedfina`**

- **Tenant ID**: `fedfina`
- **Gemini API Key**: Configured (stored in `nano_tenant_config.json`)
- **Status**: Active
- **Default Style**: Photorealistic
- **Max Image Size**: 2048x2048

**Note**: All nano MCP operations should use `tenant_id: "fedfina"` going forward.

## Usage Patterns

### Basic Image Generation

```python
# Example: Generate an image from a text prompt
# Tool: generate_image or create_image
{
    "prompt": "A beautiful sunset over mountains with birds flying",
    "style": "photorealistic",  # Optional
    "size": "1024x1024"  # Optional
}
```

### Image Editing

```python
# Example: Edit an existing image
# Tool: edit_image or modify_image
{
    "image_id": "img_12345",
    "edit_prompt": "Add birds flying in the sky",
    "preserve_original": true  # Optional
}
```

### Tenant Registration (if required)

```python
# Example: Register a tenant for multi-tenant usage
# Tool: register_tenant
{
    "tenant_id": "my-tenant",
    "gemini_api_key": "your-gemini-api-key",
    "config": {
        "default_style": "photorealistic",
        "max_image_size": "2048x2048"
    }
}
```

## Expected Tools

Based on the server capabilities, the following tools should be available:

1. **Image Generation**
   - `generate_image` / `create_image` - Generate images from prompts
   - Parameters: `prompt`, `style`, `size`, `quality`, etc.

2. **Image Editing**
   - `edit_image` / `modify_image` - Edit existing images
   - Parameters: `image_id` or `image_data`, `edit_prompt`, `options`

3. **Image Management**
   - `list_images` - List generated images for a tenant
   - `get_image` - Retrieve a specific image
   - `delete_image` - Delete an image

4. **Tenant Management** (if multi-tenant)
   - `register_tenant` - Register a new tenant
   - `get_tenant_info` - Get tenant configuration
   - `update_tenant_config` - Update tenant settings

## Server-Specific Notes

### SSE (Server-Sent Events)
The server uses SSE for streaming responses, which means:
- Responses may be streamed in chunks
- The MCP client handles SSE automatically
- Direct HTTP calls need proper SSE handling

### Multi-Tenant Architecture
Similar to other MCP servers (postgres, minio), this server supports:
- Tenant isolation
- Per-tenant API keys (Gemini API keys)
- Tenant-specific configurations

## Example Workflows

### Workflow 1: Generate and Edit an Image

1. **Generate Image**
   ```
   Prompt: "A serene lake at sunset"
   ```

2. **Edit Image**
   ```
   Edit: "Add a boat in the middle of the lake"
   ```

3. **Continue Editing**
   ```
   Edit: "Make the colors more vibrant"
   ```

### Workflow 2: Batch Image Generation

1. Register tenant (if first time)
2. Generate multiple images with different prompts
3. List all generated images
4. Select and edit specific images

## Troubleshooting

### Common Issues

1. **"Missing session ID" error**
   - The server requires proper MCP session initialization
   - Ensure you're using the MCP client, not direct HTTP calls

2. **"Tenant not found" error**
   - Register the tenant first using `register_tenant`
   - Ensure tenant_id is provided in requests

3. **"API key invalid" error**
   - Verify Gemini API key is valid
   - Check tenant configuration

4. **SSE connection issues**
   - Ensure Accept header includes `text/event-stream`
   - Use proper MCP client that handles SSE

## Integration with Other Tools

The Nano Banana MCP Server can be used in combination with:

- **MinIO MCP Server**: Store generated images
- **Postgres MCP Server**: Track image metadata
- **PDF Generator MCP Server**: Include images in PDFs

## Resources

- **Server URL**: https://mcp.baisoln.com/nano-banana/mcp
- **Server Info Resource**: `nano-banana://info`
- **GitHub**: https://github.com/zhongweili/nanobanana-mcp-server (if available)
- **PyPI**: https://pypi.org/project/nanobanana-mcp-server/

## Next Steps

1. **Test Image Generation**
   - Try generating a simple image with a basic prompt
   - Verify the response format and image data

2. **Test Image Editing**
   - Generate an image first
   - Then try editing it with a simple modification

3. **Explore Advanced Features**
   - Test different styles and sizes
   - Try iterative editing workflows
   - Integrate with other MCP servers

## Notes

- The server uses Google Gemini API, so you'll need a valid Gemini API key
- Multi-tenant support means each tenant needs their own API key
- Images are likely returned as base64-encoded data or URLs
- The server supports streaming responses via SSE

