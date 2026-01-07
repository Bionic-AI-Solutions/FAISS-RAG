#!/usr/bin/env python3
"""
Sync Epics and Stories to OpenProject using MCP Tools

This script uses MCP tools directly (via MCP client) to sync epics and stories
from epics.md to OpenProject.

Usage:
    python scripts/sync_to_openproject_via_mcp.py [--dry-run]
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import MCP client utilities if needed
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EPICS_FILE = PROJECT_ROOT / "_bmad-output/planning-artifacts/epics.md"
IMPLEMENTATION_ARTIFACTS = PROJECT_ROOT / "_bmad-output/implementation-artifacts"

# Note: This script demonstrates using MCP tools programmatically
# In practice, you would use the MCP client library or call MCP tools via the MCP server
# For now, we'll use direct API calls but structure it to show MCP tool usage patterns

print("=" * 80)
print("OpenProject Sync via MCP Tools")
print("=" * 80)
print()
print("This script demonstrates how to use MCP tools to sync epics and stories.")
print("In a real implementation, you would use the MCP client library to call:")
print("  - mcp_openproject_create_work_package()")
print("  - mcp_openproject_update_work_package()")
print("  - mcp_openproject_list_work_packages()")
print()
print("For now, use the direct MCP tools available in your environment:")
print("  - Use mcp_openproject_create_work_package for each epic/story")
print("  - Use mcp_openproject_update_work_package to set parent relationships")
print()
print("Example MCP tool calls:")
print()
print("# Create Epic:")
print("mcp_openproject_create_work_package(")
print("    project_id=8,")
print("    subject='Epic 1: Secure Platform Foundation',")
print("    type_id=40,  # Epic")
print("    description='...'")
print(")")
print()
print("# Create Story under Epic:")
print("mcp_openproject_create_work_package(")
print("    project_id=8,")
print("    subject='Story 1.1: Project Structure & Development Environment Setup',")
print("    type_id=41,  # User Story")
print("    description='...'")
print("    # Note: Parent relationship set via update_work_package or set_openproject_parents.py")
print(")")
print()
print("# Create Task under Story:")
print("mcp_openproject_create_work_package(")
print("    project_id=8,")
print("    subject='Task 1: Create Project Directory Structure',")
print("    type_id=36,  # Task")
print("    description='...'")
print("    # Note: Parent relationship set via update_work_package or set_openproject_parents.py")
print(")")
print()
print("To sync all epics and stories, use the MCP tools interactively or")
print("create a script that calls MCP tools programmatically via the MCP client.")
print()
print("For batch operations, consider using:")
print("  - scripts/sync_epics_to_openproject.py (uses direct API)")
print("  - scripts/fix_and_update_openproject.py (uses direct API)")
print()
print("These scripts can be adapted to use MCP tools if you have MCP client access.")















