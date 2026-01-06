#!/usr/bin/env python3
"""
OpenProject Parent-Child Relationship Setup Script

This script sets up parent-child relationships for work packages in OpenProject
using the OpenProject API v3. It establishes the hierarchy:
- Epic → Feature → User Story

Usage:
    python scripts/set_openproject_parents.py

Environment Variables Required:
    OPENPROJECT_URL: Base URL of OpenProject instance (e.g., https://openproject.example.com)
    OPENPROJECT_API_KEY: API key for authentication
    OPENPROJECT_PROJECT_ID: Project ID (default: 8 for Mem0-RAG)
"""

import os
import sys
import json
import requests
from typing import Dict, Optional, Tuple
from requests.auth import HTTPBasicAuth


# Configuration
OPENPROJECT_URL = os.getenv("OPENPROJECT_URL", "https://openproject.bionicaisolutions.com")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
OPENPROJECT_PROJECT_ID = int(os.getenv("OPENPROJECT_PROJECT_ID", "8"))

# Mem0-RAG Project Structure
# Format: {child_id: parent_id}
PARENT_RELATIONSHIPS = {
    # Epic 1: Platform Foundation (82)
    # Features under Epic 1
    85: 82,  # Feature 1.1: Multi-Tenant Authentication → Epic 1
    86: 82,  # Feature 1.2: Database Schema & Models → Epic 1
    87: 82,  # Feature 1.3: MCP Server Framework → Epic 1
    
    # Stories under Feature 1.1
    94: 85,  # Story 1.1.1: OAuth 2.0 Implementation → Feature 1.1
    95: 85,  # Story 1.1.2: Tenant Isolation Middleware → Feature 1.1
    
    # Stories under Feature 1.2
    96: 86,  # Story 1.2.1: Core Schema Design → Feature 1.2
    97: 86,  # Story 1.2.2: RLS Policies Implementation → Feature 1.2
    
    # Stories under Feature 1.3
    98: 87,  # Story 1.3.1: FastMCP Server Setup → Feature 1.3
    99: 87,  # Story 1.3.2: Tool Registration System → Feature 1.3
    
    # Epic 2: RAG Capabilities (83)
    # Features under Epic 2
    88: 83,  # Feature 2.1: Document Ingestion → Epic 2
    89: 83,  # Feature 2.2: Vector Search → Epic 2
    90: 83,  # Feature 2.3: Query Processing → Epic 2
    
    # Stories under Feature 2.1
    100: 88,  # Story 2.1.1: Document Parser Implementation → Feature 2.1
    101: 88,  # Story 2.1.2: Text Chunking & Embedding → Feature 2.1
    
    # Stories under Feature 2.2
    102: 89,  # Story 2.2.1: Vector Index Management → Feature 2.2
    103: 89,  # Story 2.2.2: Similarity Search Implementation → Feature 2.2
    
    # Stories under Feature 2.3
    104: 90,  # Story 2.3.1: LLM Query Processing → Feature 2.3
    
    # Epic 3: Mem0 Integration (84)
    # Features under Epic 3
    91: 84,  # Feature 3.1: Mem0 Service Integration → Epic 3
    92: 84,  # Feature 3.2: Memory Management → Epic 3
    93: 84,  # Feature 3.3: User Context Tracking → Epic 3
    
    # Stories under Feature 3.1
    105: 91,  # Story 3.1.1: Mem0 API Client → Feature 3.1
    
    # Stories under Feature 3.2
    106: 92,  # Story 3.2.1: Memory Storage & Retrieval → Feature 3.2
    
    # Stories under Feature 3.3
    107: 93,  # Story 3.3.1: Session Context Tracking → Feature 3.3
}

# Work Package Names for reference
WORK_PACKAGE_NAMES = {
    82: "Epic 1: Platform Foundation",
    83: "Epic 2: RAG Capabilities",
    84: "Epic 3: Mem0 Integration",
    85: "Feature 1.1: Multi-Tenant Authentication",
    86: "Feature 1.2: Database Schema & Models",
    87: "Feature 1.3: MCP Server Framework",
    88: "Feature 2.1: Document Ingestion",
    89: "Feature 2.2: Vector Search",
    90: "Feature 2.3: Query Processing",
    91: "Feature 3.1: Mem0 Service Integration",
    92: "Feature 3.2: Memory Management",
    93: "Feature 3.3: User Context Tracking",
    94: "Story 1.1.1: OAuth 2.0 Implementation",
    95: "Story 1.1.2: Tenant Isolation Middleware",
    96: "Story 1.2.1: Core Schema Design",
    97: "Story 1.2.2: RLS Policies Implementation",
    98: "Story 1.3.1: FastMCP Server Setup",
    99: "Story 1.3.2: Tool Registration System",
    100: "Story 2.1.1: Document Parser Implementation",
    101: "Story 2.1.2: Text Chunking & Embedding",
    102: "Story 2.2.1: Vector Index Management",
    103: "Story 2.2.2: Similarity Search Implementation",
    104: "Story 2.3.1: LLM Query Processing",
    105: "Story 3.1.1: Mem0 API Client",
    106: "Story 3.2.1: Memory Storage & Retrieval",
    107: "Story 3.3.1: Session Context Tracking",
}


class OpenProjectClient:
    """Client for OpenProject API v3"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        # Use API key authentication
        self.session.auth = HTTPBasicAuth('apikey', api_key)
    
    def get_work_package(self, work_package_id: int) -> Optional[Dict]:
        """Get work package details including lockVersion"""
        url = f"{self.base_url}/api/v3/work_packages/{work_package_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching work package {work_package_id}: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            return None
    
    def set_parent(self, child_id: int, parent_id: int) -> Tuple[bool, str]:
        """Set parent relationship for a work package"""
        # First, get the current work package to obtain lockVersion
        work_package = self.get_work_package(child_id)
        if not work_package:
            return False, f"Failed to fetch work package {child_id}"
        
        lock_version = work_package.get('lockVersion', 0)
        child_name = WORK_PACKAGE_NAMES.get(child_id, f"WP-{child_id}")
        parent_name = WORK_PACKAGE_NAMES.get(parent_id, f"WP-{parent_id}")
        
        # Prepare PATCH request
        url = f"{self.base_url}/api/v3/work_packages/{child_id}"
        payload = {
            "lockVersion": lock_version,
            "_links": {
                "parent": {
                    "href": f"/api/v3/work_packages/{parent_id}"
                }
            }
        }
        
        try:
            response = self.session.patch(url, json=payload)
            response.raise_for_status()
            return True, f"✅ Set {child_name} → {parent_name}"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return False, f"❌ Failed to set {child_name} → {parent_name}: {error_msg}"


def main():
    """Main execution function"""
    print("=" * 80)
    print("OpenProject Parent-Child Relationship Setup")
    print("=" * 80)
    print()
    
    # Validate configuration
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        print()
        print("Please set the following environment variables:")
        print("  export OPENPROJECT_URL='https://openproject.bionicaisolutions.com'")
        print("  export OPENPROJECT_API_KEY='your-api-key-here'")
        print("  export OPENPROJECT_PROJECT_ID='8'  # Optional, defaults to 8")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   OpenProject URL: {OPENPROJECT_URL}")
    print(f"   Project ID: {OPENPROJECT_PROJECT_ID}")
    print(f"   API Key: {'*' * min(len(OPENPROJECT_API_KEY), 20)}...")
    print()
    
    # Initialize client
    client = OpenProjectClient(OPENPROJECT_URL, OPENPROJECT_API_KEY)
    
    # Test connection
    print("🔍 Testing connection...")
    test_wp = client.get_work_package(82)  # Try to get Epic 1
    if not test_wp:
        print("❌ Failed to connect to OpenProject. Please check:")
        print("   1. OPENPROJECT_URL is correct")
        print("   2. OPENPROJECT_API_KEY is valid")
        print("   3. Network connectivity to OpenProject instance")
        sys.exit(1)
    print("✅ Connection successful!")
    print()
    
    # Set parent relationships
    print("🔗 Setting parent-child relationships...")
    print()
    
    success_count = 0
    failure_count = 0
    results = []
    
    for child_id, parent_id in PARENT_RELATIONSHIPS.items():
        success, message = client.set_parent(child_id, parent_id)
        results.append((success, message))
        if success:
            success_count += 1
        else:
            failure_count += 1
        print(message)
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failure_count}")
    print(f"📊 Total: {len(PARENT_RELATIONSHIPS)}")
    print()
    
    if failure_count > 0:
        print("Failed relationships:")
        for success, message in results:
            if not success:
                print(f"  {message}")
        print()
        sys.exit(1)
    else:
        print("🎉 All parent-child relationships set successfully!")
        print()
        print("You can now view the hierarchy in OpenProject:")
        print(f"  {OPENPROJECT_URL}/projects/{OPENPROJECT_PROJECT_ID}/work_packages")


if __name__ == "__main__":
    main()











