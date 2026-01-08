#!/usr/bin/env python3
"""
Generate image using Nano Banana MCP Server.

This script calls the nb_generate_image tool to generate images
using the Gemini API through the nano MCP server.
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

# Nano MCP Server configuration
NANO_MCP_URL = "https://mcp.baisoln.com/nano-banana/mcp"
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
                "name": "nano-image-generator",
                "version": "1.0"
            }
        },
        "id": 1
    }
    
    try:
        response = requests.post(
            NANO_MCP_URL,
            json=init_payload,
            headers=HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = parse_sse_response(response.text)
            if data and 'result' in data:
                server_info = data['result'].get('serverInfo', {})
                print(f"   ✓ Connected to {server_info.get('name', 'Nano Server')} v{server_info.get('version', 'Unknown')}")
                # Extract session ID from response - it might be in headers or response
                # For SSE, session might be managed through the connection
                session_id = response.headers.get('X-Session-Id') or response.headers.get('Mcp-Session-Id')
                if session_id:
                    return session_id
                # Try to get from response
                return str(data.get('id', 'init-1'))
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    return None


def register_tenant(
    tenant_id: str,
    gemini_api_key: str
) -> bool:
    """
    Register a tenant with the nano MCP server.
    
    Args:
        tenant_id: Tenant ID to register
        gemini_api_key: Google Gemini API key
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n📝 Registering tenant: {tenant_id}...")
    print(f"   API Key: {gemini_api_key[:20]}...{gemini_api_key[-10:]}")
    
    # Initialize session
    session_id = initialize_mcp_session()
    
    # Prepare registration call
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "nb_register_tenant",
            "arguments": {
                "tenant_id": tenant_id,
                "gemini_api_key": gemini_api_key
            }
        },
        "id": 3
    }
    
    headers = HEADERS.copy()
    if session_id:
        headers["X-Session-Id"] = session_id
        headers["Mcp-Session-Id"] = session_id
    
    try:
        response = requests.post(
            NANO_MCP_URL,
            json=tool_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = parse_sse_response(response.text)
            if data and 'result' in data:
                result = data['result']
                # Check if registration was successful
                if isinstance(result, dict):
                    content = result.get('content', [])
                    structured = result.get('structuredContent', {})
                    
                    # Check structured content first
                    if isinstance(structured, dict):
                        if structured.get('success'):
                            print(f"   ✓ Tenant registered successfully")
                            return True
                        elif 'error' in structured:
                            error_msg = structured['error']
                            print(f"   ✗ Registration error: {error_msg[:100]}")
                            return False
                    
                    # Check text content
                    if content and isinstance(content, list):
                        for item in content:
                            if item.get('type') == 'text':
                                text = item.get('text', '')
                                try:
                                    # Try to parse JSON in text
                                    text_data = json.loads(text)
                                    if text_data.get('success'):
                                        print(f"   ✓ Tenant registered successfully")
                                        return True
                                    elif 'error' in text_data:
                                        print(f"   ✗ Error: {text_data['error'][:100]}")
                                        return False
                                except:
                                    # Not JSON, check text
                                    if 'success' in text.lower() or 'registered' in text.lower():
                                        print(f"   ✓ Tenant registered successfully")
                                        return True
                                    elif 'already' in text.lower() or 'exists' in text.lower():
                                        print(f"   ℹ️  Tenant already exists")
                                        return True
                
                print(f"   Response: {json.dumps(result, indent=2)[:500]}")
                return True
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   {response.text[:300]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    return False


def generate_image(
    tenant_id: str,
    prompt: str
) -> Optional[Dict[str, Any]]:
    """
    Generate an image using nb_generate_image tool.
    
    Args:
        tenant_id: Tenant ID for multi-tenant isolation
        prompt: Text prompt describing the image (include style, size, etc. in prompt)
    
    Returns:
        Dictionary with image data or None if failed
    """
    print("\n🎨 Generating image...")
    print(f"   Tenant: {tenant_id}")
    print(f"   Prompt: {prompt[:100]}...")
    
    # Initialize session first and keep connection
    session_id = initialize_mcp_session()
    
    # Prepare tool call - only use accepted parameters
    # Based on error, only tenant_id and prompt are accepted
    tool_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "nb_generate_image",
            "arguments": {
                "tenant_id": tenant_id,
                "prompt": prompt
                # Note: style, size, quality are not accepted parameters
                # Include style in the prompt instead
            }
        },
        "id": 2
    }
    
    # Try different session header formats
    headers = HEADERS.copy()
    if session_id:
        # Try multiple header formats
        headers["X-Session-Id"] = session_id
        headers["Mcp-Session-Id"] = session_id
        headers["Session-Id"] = session_id
        # Also try in payload
        tool_payload["session_id"] = session_id
    
    try:
        response = requests.post(
            NANO_MCP_URL,
            json=tool_payload,
            headers=headers,
            timeout=120  # Image generation can take time
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response length: {len(response.text)}")
        print(f"   Response preview: {response.text[:500]}")
        
        # Save full response for debugging
        debug_file = project_root / "nano_response_debug.txt"
        with open(debug_file, 'w') as f:
            f.write(response.text)
        print(f"   Full response saved to: {debug_file}")
        
        if response.status_code == 200:
            # Parse SSE response
            data = parse_sse_response(response.text)
            
            if data:
                if 'result' in data:
                    result = data['result']
                    print(f"   ✓ Image generation successful!")
                    print(f"   Result type: {type(result)}")
                    print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    return result
                elif 'error' in data:
                    error = data['error']
                    print(f"   ✗ Error: {error.get('message', 'Unknown error')}")
                    if 'code' in error:
                        print(f"   Code: {error['code']}")
                    return None
            else:
                # Try regular JSON
                try:
                    data = response.json()
                    if 'result' in data:
                        result = data['result']
                        print(f"   ✓ Image generation successful!")
                        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        return result
                    elif 'error' in data:
                        error = data['error']
                        print(f"   ✗ Error: {error.get('message', 'Unknown error')}")
                        return None
                except:
                    print(f"   ✗ Could not parse response")
                    print(f"   Response type: {type(response.text)}")
                    print(f"   Response length: {len(response.text)}")
                    print(f"   Response preview: {response.text[:1000]}")
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
    
    # First check structuredContent for success/error
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
                # Direct image data
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
                # Text might contain JSON with image info
                text = item.get('text', '')
                try:
                    text_data = json.loads(text)
                    if isinstance(text_data, dict):
                        if text_data.get('success') and 'image' in text_data:
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
                                return download_image_from_url(image_url, output_path)
                except:
                    pass
    
    # Check for image data in various formats
    image_data = None
    image_url = None
    
    if 'image' in result:
        image_data = result['image']
    elif 'image_data' in result:
        image_data = result['image_data']
    elif 'data' in result:
        image_data = result['data']
    
    if 'image_url' in result:
        image_url = result['image_url']
    elif 'url' in result:
        image_url = result['url']
    
    # Handle base64 image data
    if image_data:
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Base64 encoded image
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
            elif image_data.startswith('http'):
                image_url = image_data
    
    # Handle image URL
    if image_url:
        print(f"   ℹ️  Image URL: {image_url}")
        print(f"   Downloading...")
        try:
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"   ✓ Image downloaded and saved to: {output_path}")
                print(f"   Size: {len(img_response.content)} bytes")
                return True
            else:
                print(f"   ✗ Download failed: {img_response.status_code}")
        except Exception as e:
            print(f"   ✗ Download error: {e}")
    
    # If we have result but no image, show what we got
    print(f"   ⚠️  Could not extract image from result")
    print(f"   Result keys: {list(result.keys())}")
    print(f"   Full result: {json.dumps(result, indent=2)[:500]}")
    
    return False


def main():
    """Main function to generate image."""
    print("=" * 60)
    print("Nano Banana MCP - Image Generation")
    print("=" * 60)
    
    # Load tenant configuration
    config_path = project_root / "nano_tenant_config.json"
    if not config_path.exists():
        print(f"✗ Configuration file not found: {config_path}")
        print("  Please ensure nano_tenant_config.json exists with tenant configuration.")
        return 1
    
    with open(config_path) as f:
        tenant_config = json.load(f)
    
    tenant_id = tenant_config.get("tenant_id", "fedfina")
    gemini_api_key = tenant_config.get("gemini_api_key")
    
    # Register tenant first if we have API key
    # Always re-register to ensure the latest API key is used
    if gemini_api_key:
        print(f"\n📝 Registering/updating tenant with new API key...")
        if not register_tenant(tenant_id, gemini_api_key):
            print("⚠️  Tenant registration failed, but continuing...")
    else:
        print("⚠️  No Gemini API key found in config, skipping registration")
    
    # Image generation parameters
    # Include style and details in the prompt since they're not separate parameters
    base_prompt = "Flying pigs in Van Gogh style, swirling brushstrokes, vibrant colors, post-impressionist painting, starry night sky with pigs flying, dramatic and expressive"
    
    # Allow command line arguments to override
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = base_prompt
    
    # Generate image (only tenant_id and prompt are accepted)
    result = generate_image(
        tenant_id=tenant_id,
        prompt=prompt
    )
    
    if result:
        # Save image
        output_dir = project_root / "generated_images"
        output_dir.mkdir(exist_ok=True)
        
        # Create filename from prompt
        filename = "flying_pigs_vangogh.png"
        output_path = output_dir / filename
        
        if save_image(result, output_path):
            print(f"\n✅ Success! Image generated and saved.")
            print(f"   Location: {output_path}")
            return 0
        else:
            print(f"\n⚠️  Image generated but could not be saved.")
            print(f"   Result: {json.dumps(result, indent=2)}")
            return 1
    else:
        print(f"\n❌ Failed to generate image.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
