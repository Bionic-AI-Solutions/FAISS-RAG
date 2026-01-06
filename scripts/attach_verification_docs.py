#!/usr/bin/env python3
"""
Script to attach verification documents to OpenProject stories.
"""

import base64
import sys
from pathlib import Path

# Add parent directory to path to import MCP tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import mcp_openproject_add_work_package_attachment


def attach_verification_doc(work_package_id: int, doc_path: str, description: str = None):
    """Attach a verification document to an OpenProject work package."""
    doc_file = Path(doc_path)
    if not doc_file.exists():
        print(f"Error: File not found: {doc_path}")
        return False
    
    # Read and encode file
    with open(doc_file, 'rb') as f:
        content = f.read()
        encoded = base64.b64encode(content).decode('utf-8')
    
    # Attach to OpenProject
    result = mcp_openproject_add_work_package_attachment(
        work_package_id=work_package_id,
        file_data=encoded,
        filename=doc_file.name,
        content_type="text/markdown",
        description=description or f"Verification document: {doc_file.name}"
    )
    
    if result.get("success"):
        print(f"✅ Successfully attached {doc_file.name} to work package {work_package_id}")
        return True
    else:
        print(f"❌ Failed to attach {doc_file.name}: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    # Story 1.6: Authorization & RBAC Middleware (ID: 114)
    attach_verification_doc(
        114,
        "docs/STORY_1_6_VERIFICATION.md",
        "Story 1.6 Verification Report - Complete verification of all acceptance criteria"
    )
    
    # Story 1.5: Authentication Middleware (ID: 113)
    attach_verification_doc(
        113,
        "docs/STORY_1_5_VERIFICATION.md",
        "Story 1.5 Verification Report - Complete verification of all acceptance criteria"
    )
    
    attach_verification_doc(
        113,
        "docs/STORY_1_5_TEST_ALIGNMENT_VERIFICATION.md",
        "Story 1.5 Test Alignment Verification - Verification that tests align with acceptance criteria"
    )





