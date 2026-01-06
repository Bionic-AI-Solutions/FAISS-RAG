#!/usr/bin/env python3
"""
Script to attach Epic 3 documentation files to OpenProject work packages.
"""
import base64
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Files to attach
attachments = [
    {
        'wp_id': 129,
        'filepath': project_root / '_bmad-output/implementation-artifacts/3-1-document-ingestion-mcp-tool.md',
        'filename': '3-1-document-ingestion-mcp-tool.md',
        'description': 'Story 3.1 Implementation Documentation'
    },
    {
        'wp_id': 129,
        'filepath': project_root / 'docs/STORY_3_1_VERIFICATION.md',
        'filename': 'STORY_3_1_VERIFICATION.md',
        'description': 'Story 3.1 Verification Report'
    },
    {
        'wp_id': 130,
        'filepath': project_root / '_bmad-output/implementation-artifacts/3-2-document-versioning.md',
        'filename': '3-2-document-versioning.md',
        'description': 'Story 3.2 Implementation Documentation'
    },
    {
        'wp_id': 130,
        'filepath': project_root / 'docs/STORY_3_2_VERIFICATION.md',
        'filename': 'STORY_3_2_VERIFICATION.md',
        'description': 'Story 3.2 Verification Report'
    },
]

def encode_file(filepath: Path) -> str:
    """Read and base64 encode a file."""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def main():
    """Main function to prepare attachments."""
    print("Preparing attachments for OpenProject...")
    print("=" * 60)
    
    prepared = []
    for att in attachments:
        if not att['filepath'].exists():
            print(f"❌ File not found: {att['filepath']}")
            continue
        
        try:
            content = encode_file(att['filepath'])
            prepared.append({
                'wp_id': att['wp_id'],
                'filename': att['filename'],
                'description': att['description'],
                'content': content,
                'size': len(content)
            })
            print(f"✅ Prepared: WP {att['wp_id']} - {att['filename']} ({len(content)} chars)")
        except Exception as e:
            print(f"❌ Error encoding {att['filepath']}: {e}")
    
    print("=" * 60)
    print(f"\nTotal: {len(prepared)} files ready for attachment")
    print("\nFiles are ready. Use MCP tool to attach them to OpenProject.")
    
    return prepared

if __name__ == '__main__':
    main()

