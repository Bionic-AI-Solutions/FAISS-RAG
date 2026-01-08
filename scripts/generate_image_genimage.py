#!/usr/bin/env python3
"""
Generate image using GenImage MCP Server.

This script calls the genimage tool to generate images
using the Runware API through the genimage MCP server.
"""

import requests
import json
import base64
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# GenImage MCP Server configuration
GENIMAGE_MCP_URL = "https://mcp.baisoln.com/genimage/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}


def parse_sse_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse Server-Sent Events (SSE) response format."""
    if "data:" not in text:
        return None
    
    # Parse all data lines and find the one with result
    results = []
    for line in text.split('\n'):
        if line.startswith('data: '):
            try:
                data_str = line[6:]  # Remove 'data: ' prefix
                data = json.loads(data_str)
                # Look for result in the data
                if 'result' in data:
                    return data
                # Also collect all parsed data
                results.append(data)
            except json.JSONDecodeError:
                continue
    
    # If no result found, return the last parsed data (might be the result)
    if results:
        return results[-1]
    
    return None


def initialize_mcp_session() -> Optional[str]:
    """Initialize MCP session and return session ID."""
    print("🔌 Initializing MCP session...")
    
    init_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "genimage-generator",
                "version": "1.0"
            }
        },
        "id": 1
    }
    
    try:
        response = requests.post(
            GENIMAGE_MCP_URL,
            json=init_payload,
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = parse_sse_response(response.text)
            if data and 'result' in data:
                server_info = data['result'].get('serverInfo', {})
                print(f"   ✓ Connected to {server_info.get('name', 'GenImage Server')} v{server_info.get('version', 'Unknown')}")
                # Extract session ID from response
                session_id = response.headers.get('X-Session-Id') or response.headers.get('Mcp-Session-Id')
                if session_id:
                    return session_id
                return str(data.get('id', 'init-1'))
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    return None


def generate_image(
    tenant_id: str,
    prompt: str
) -> Optional[Dict[str, Any]]:
    """
    Generate an image using genimage tool.
    
    Args:
        tenant_id: Tenant ID for multi-tenant isolation
        prompt: Text prompt describing the image
    
    Returns:
        Dictionary with image data or None if failed
    """
    print("\n🎨 Generating image...")
    print(f"   Tenant: {tenant_id}")
    print(f"   Prompt: {prompt[:100]}...")
    
    # Initialize session first
    session_id = initialize_mcp_session()
    
    # Try different possible tool names
    possible_tool_names = [
        "gi_generate_image",
        "genimage_generate_image",
        "generate_image",
        "gi_create_image",
        "create_image"
    ]
    
    headers = HEADERS.copy()
    if session_id:
        headers["X-Session-Id"] = session_id
        headers["Mcp-Session-Id"] = session_id
        headers["Session-Id"] = session_id
    
    # First, try to list available tools
    print("\n🔍 Discovering available tools...")
    tools_payload = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    try:
        response = requests.post(
            GENIMAGE_MCP_URL,
            json=tools_payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = parse_sse_response(response.text) or response.json()
            if 'result' in data:
                tools = data['result'].get('tools', [])
                print(f"   ✓ Found {len(tools)} tools")
                for tool in tools:
                    print(f"      - {tool.get('name', 'unknown')}: {tool.get('description', 'No description')[:60]}")
                
                # Find the image generation tool
                image_tool = None
                for tool in tools:
                    name = tool.get('name', '').lower()
                    if 'generate' in name or 'create' in name or 'image' in name:
                        image_tool = tool.get('name')
                        break
                
                if image_tool:
                    print(f"\n   Using tool: {image_tool}")
                else:
                    # Try the first tool that might be it
                    if tools:
                        image_tool = tools[0].get('name')
                        print(f"\n   Trying tool: {image_tool}")
    except Exception as e:
        print(f"   ⚠️  Could not list tools: {e}")
        image_tool = "gi_generate_image"  # Default fallback
    
    # Prepare tool call
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": image_tool or "gi_generate_image",
            "arguments": {
                "tenant_id": tenant_id,
                "prompt": prompt
            }
        },
        "id": 3
    }
    
    try:
        response = requests.post(
            GENIMAGE_MCP_URL,
            json=tool_payload,
            headers=headers,
            timeout=120  # Image generation can take time
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse SSE response
            data = parse_sse_response(response.text)
            
            if not data:
                # Try regular JSON
                try:
                    data = response.json()
                except:
                    print(f"   ✗ Could not parse response")
                    print(f"   Response: {response.text[:500]}")
                    return None
            
            if 'result' in data:
                result = data['result']
                print(f"   ✓ Image generation successful!")
                return result
            elif 'error' in data:
                error = data['error']
                print(f"   ✗ Error: {error.get('message', 'Unknown error')}")
                if 'code' in error:
                    print(f"   Code: {error['code']}")
                return None
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except requests.Timeout:
        print(f"   ✗ Request timed out (image generation may take longer)")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def save_image(result: Dict[str, Any], output_path: Path) -> bool:
    """Save image from result to file."""
    print(f"\n💾 Saving image...")
    
    # Check structuredContent for success/error
    structured = result.get('structuredContent', {})
    if isinstance(structured, dict):
        if not structured.get('success', False):
            error = structured.get('error', 'Unknown error')
            print(f"   ✗ Generation failed: {error[:200]}")
            return False
    
    # Check content array for image data or URLs
    content = result.get('content', [])
    if isinstance(content, list):
        for item in content:
            item_type = item.get('type', '')
            if item_type == 'image':
                image_data = item.get('data') or item.get('image')
                if image_data:
                    if isinstance(image_data, str) and image_data.startswith('data:image'):
                        try:
                            header, encoded = image_data.split(',', 1)
                            img_bytes = base64.b64decode(encoded)
                            with open(output_path, 'wb') as f:
                                f.write(img_bytes)
                            print(f"   ✓ Image saved to: {output_path}")
                            print(f"   Size: {len(img_bytes)} bytes")
                            return True
                        except Exception as e:
                            print(f"   ✗ Error decoding image: {e}")
            elif item_type == 'text':
                text = item.get('text', '')
                try:
                    text_data = json.loads(text)
                    if isinstance(text_data, dict):
                        # Check for image_data field (base64 encoded JPEG)
                        if text_data.get('success') and 'image_data' in text_data:
                            image_data = text_data['image_data']
                            if isinstance(image_data, str):
                                # Try to decode as base64 (may or may not have data:image prefix)
                                try:
                                    if image_data.startswith('data:image'):
                                        header, encoded = image_data.split(',', 1)
                                        img_bytes = base64.b64decode(encoded)
                                    else:
                                        # Raw base64 string
                                        img_bytes = base64.b64decode(image_data)
                                    with open(output_path, 'wb') as f:
                                        f.write(img_bytes)
                                    print(f"   ✓ Image saved to: {output_path}")
                                    print(f"   Size: {len(img_bytes)} bytes")
                                    return True
                                except Exception as e:
                                    print(f"   ⚠️  Error decoding base64: {e}")
                        # Check for image field
                        elif text_data.get('success') and 'image' in text_data:
                            image_data = text_data['image']
                            if isinstance(image_data, str) and image_data.startswith('data:image'):
                                header, encoded = image_data.split(',', 1)
                                img_bytes = base64.b64decode(encoded)
                                with open(output_path, 'wb') as f:
                                    f.write(img_bytes)
                                print(f"   ✓ Image saved to: {output_path}")
                                return True
                        elif 'image_url' in text_data or 'url' in text_data:
                            image_url = text_data.get('image_url') or text_data.get('url')
                            if image_url:
                                img_response = requests.get(image_url, timeout=30)
                                if img_response.status_code == 200:
                                    with open(output_path, 'wb') as f:
                                        f.write(img_response.content)
                                    print(f"   ✓ Image downloaded and saved to: {output_path}")
                                    return True
                except json.JSONDecodeError:
                    # Not JSON, skip
                    pass
                except Exception as e:
                    print(f"   ⚠️  Error processing text content: {e}")
    
    # Check for image data in various formats
    image_data = result.get('image') or result.get('image_data') or result.get('data')
    image_url = result.get('image_url') or result.get('url')
    
    if image_data and isinstance(image_data, str):
        if image_data.startswith('data:image'):
            try:
                header, encoded = image_data.split(',', 1)
                img_bytes = base64.b64decode(encoded)
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                print(f"   ✓ Image saved to: {output_path}")
                return True
            except Exception as e:
                print(f"   ✗ Error decoding image: {e}")
        elif image_data.startswith('http'):
            image_url = image_data
    
    if image_url:
        try:
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"   ✓ Image downloaded and saved to: {output_path}")
                return True
        except Exception as e:
            print(f"   ✗ Download error: {e}")
    
    print(f"   ⚠️  Could not extract image from result")
    print(f"   Result keys: {list(result.keys())}")
    print(f"   Full result: {json.dumps(result, indent=2)[:500]}")
    
    return False


def main():
    """Main function to generate image."""
    print("=" * 60)
    print("GenImage MCP - Image Generation")
    print("=" * 60)
    
    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = "Beautiful girl in a bikini"
    
    tenant_id = "fedfina"
    
    # Generate image
    result = generate_image(
        tenant_id=tenant_id,
        prompt=prompt
    )
    
    if result:
        # Save image
        output_dir = project_root / "generated_images"
        output_dir.mkdir(exist_ok=True)
        
        # Create filename from prompt
        filename = prompt.lower().replace(' ', '_').replace(',', '').replace('.', '')[:50] + ".png"
        output_path = output_dir / filename
        
        if save_image(result, output_path):
            print(f"\n✅ Success! Image generated and saved.")
            print(f"   Location: {output_path}")
            return 0
        else:
            print(f"\n⚠️  Image generated but could not be saved.")
            print(f"   Result: {json.dumps(result, indent=2)[:500]}")
            return 1
    else:
        print(f"\n❌ Failed to generate image.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
