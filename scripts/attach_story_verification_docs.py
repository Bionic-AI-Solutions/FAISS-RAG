#!/usr/bin/env python3
"""
Script to attach verification documents to OpenProject work packages.

This script reads verification documents, base64 encodes them, and attaches
them to the corresponding OpenProject work packages using the MCP tool.
"""

import base64
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: This script requires the MCP OpenProject server to be available
# and the mcp_openproject_add_work_package_attachment tool to be accessible

async def attach_document(file_path: str, work_package_id: int, description: str):
    """
    Read a file, base64 encode it, and attach it to an OpenProject work package.
    
    Args:
        file_path: Path to the verification document
        work_package_id: OpenProject work package ID
        description: Description for the attachment
    """
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        filename = Path(file_path).name

        print(f"Attaching {filename} to work package {work_package_id}...")
        print(f"  File size: {len(file_content)} bytes")
        print(f"  Base64 length: {len(encoded_content)} chars")
        
        # Note: This requires the MCP tool to be available
        # The actual attachment would be done via:
        # result = await mcp_openproject_add_work_package_attachment(
        #     work_package_id=work_package_id,
        #     filename=filename,
        #     description=description,
        #     file_data=encoded_content
        # )
        
        print(f"  ✅ Ready to attach (MCP tool call needed)")
        return {
            "success": True,
            "file": filename,
            "work_package_id": work_package_id,
            "base64_length": len(encoded_content)
        }
    except FileNotFoundError:
        print(f"❌ Error: File not found at {file_path}")
        return {"success": False, "error": "File not found"}
    except Exception as e:
        print(f"❌ Error attaching {file_path}: {e}")
        return {"success": False, "error": str(e)}


async def main():
    """Main function to attach all verification documents."""
    
    # Story verification documents to attach
    documents = [
        ("docs/STORY_1_2_VERIFICATION.md", 110, "Story 1.2 Verification Report - Complete verification of all acceptance criteria"),
        ("docs/STORY_1_3_VERIFICATION.md", 111, "Story 1.3 Verification Report - Complete verification of all acceptance criteria"),
        ("docs/STORY_1_4_VERIFICATION.md", 112, "Story 1.4 Verification Report - Complete verification of all acceptance criteria"),
    ]
    
    print("=" * 60)
    print("Attaching Story Verification Documents to OpenProject")
    print("=" * 60)
    print()
    
    results = []
    for file_path, wp_id, desc in documents:
        result = await attach_document(file_path, wp_id, desc)
        results.append(result)
        print()
    
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    for result in results:
        if result.get("success"):
            print(f"✅ {result['file']} - Ready for work package {result['work_package_id']}")
        else:
            print(f"❌ {result.get('file', 'Unknown')} - Error: {result.get('error', 'Unknown error')}")
    
    print()
    print("Note: This script prepares the files for attachment.")
    print("The actual attachment requires the MCP OpenProject tool to be available.")
    print("Please use the MCP tool directly or run this script when the tool is available.")


if __name__ == "__main__":
    asyncio.run(main())











