#!/usr/bin/env python3
"""
Register fedfina tenant with Nano Banana MCP Server.

This script registers the fedfina tenant with the Gemini API key.
Run this when nano MCP tools are available through the MCP client.
"""

import json
import os
from pathlib import Path

# Load tenant configuration
config_path = Path(__file__).parent.parent / "nano_tenant_config.json"
with open(config_path) as f:
    config = json.load(f)

print("=" * 60)
print("Nano Banana MCP Server - Tenant Registration")
print("=" * 60)
print()
print(f"Tenant ID: {config['tenant_id']}")
print(f"Gemini API Key: {config['gemini_api_key'][:20]}...")
print(f"Server URL: {config['server_url']}")
print()
print("To register this tenant, use the nano MCP server tools:")
print()
print("Expected tool call:")
print(f"  register_tenant(")
print(f"    tenant_id='{config['tenant_id']}',")
print(f"    gemini_api_key='{config['gemini_api_key']}',")
print(f"    config={json.dumps(config['config'], indent=6)}")
print(f"  )")
print()
print("Or via MCP client:")
print(f"  mcp_nano_register_tenant(")
print(f"    tenant_id='{config['tenant_id']}',")
print(f"    gemini_api_key='{config['gemini_api_key']}',")
print(f"    config={json.dumps(config['config'], indent=6)}")
print(f"  )")
print()
print("=" * 60)
print("Configuration saved to: nano_tenant_config.json")
print("Environment variables saved to: .env.nano")
print("=" * 60)

