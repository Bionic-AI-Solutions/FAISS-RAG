#!/usr/bin/env python3
"""
Cleanup old OpenProject structure

This script removes the old epic/feature/story structure that was created
before the detailed story breakdown. It keeps only the new structure with
proper epic-story relationships.

Old structure to delete:
- Epic 1: Platform Foundation (ID: 82)
- Epic 2: RAG Capabilities (ID: 83)
- Epic 3: Mem0 Integration (ID: 84)
- All Features and Stories under these epics

Usage:
    python scripts/cleanup_old_openproject_structure.py [--dry-run]
"""

import os
import sys
import argparse
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OPENPROJECT_URL = os.getenv("OPENPROJECT_URL", "https://op.zippio.ai")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")

# Old structure IDs to delete
OLD_EPIC_IDS = [82, 83, 84]
OLD_FEATURE_IDS = [85, 86, 87, 88, 89]


class OpenProjectCleaner:
    def __init__(self, base_url: str, api_key: str, dry_run: bool = False):
        self.base_url = base_url
        self.api_key = api_key
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("apikey", api_key)
        self.session.headers.update({"Content-Type": "application/json"})
    
    def delete_work_package(self, wp_id: int) -> bool:
        """Delete a work package"""
        if self.dry_run:
            print(f"🔨 [DRY RUN] Would delete work package ID: {wp_id}")
            return True
        
        url = f"{self.base_url}/api/v3/work_packages/{wp_id}"
        try:
            response = self.session.delete(url)
            if response.status_code == 204:
                print(f"✅ Deleted work package ID: {wp_id}")
                return True
            else:
                print(f"❌ Failed to delete work package ID {wp_id}: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error deleting work package ID {wp_id}: {e}")
            return False
    
    def get_work_package(self, wp_id: int) -> dict:
        """Get work package details"""
        url = f"{self.base_url}/api/v3/work_packages/{wp_id}"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ Error getting work package ID {wp_id}: {e}")
            return {}
    
    def get_children(self, wp_id: int) -> list:
        """Get all child work packages"""
        url = f"{self.base_url}/api/v3/work_packages"
        params = {
            "filters": f'[{{"parent": {{"operator": "=", "values": ["{wp_id}"]}}}}]'
        }
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("_embedded", {}).get("elements", [])
            return []
        except Exception as e:
            print(f"❌ Error getting children for work package ID {wp_id}: {e}")
            return []
    
    def delete_recursive(self, wp_id: int, indent: str = "") -> int:
        """Recursively delete work package and all children"""
        deleted_count = 0
        
        # Get children first
        children = self.get_children(wp_id)
        
        # Delete children first (bottom-up)
        for child in children:
            child_id = child.get("id")
            child_subject = child.get("subject", "")
            print(f"{indent}  Deleting child: {child_subject} (ID: {child_id})")
            deleted_count += self.delete_recursive(child_id, indent + "  ")
        
        # Delete this work package
        wp = self.get_work_package(wp_id)
        subject = wp.get("subject", "Unknown")
        print(f"{indent}Deleting: {subject} (ID: {wp_id})")
        if self.delete_work_package(wp_id):
            deleted_count += 1
        
        return deleted_count
    
    def cleanup_old_structure(self):
        """Clean up old epic/feature/story structure"""
        print("=" * 80)
        print("OpenProject Old Structure Cleanup")
        print("=" * 80)
        print(f"\nOpenProject URL: {OPENPROJECT_URL}")
        print(f"Dry run: {self.dry_run}")
        print()
        
        total_deleted = 0
        
        # Delete old epics (this will cascade delete children if configured)
        print("Deleting old epics and their children...")
        print()
        for epic_id in OLD_EPIC_IDS:
            epic = self.get_work_package(epic_id)
            if epic:
                subject = epic.get("subject", "Unknown")
                print(f"Processing Epic: {subject} (ID: {epic_id})")
                deleted = self.delete_recursive(epic_id)
                total_deleted += deleted
                print()
            else:
                print(f"⚠️  Epic ID {epic_id} not found (may already be deleted)")
                print()
        
        # Also delete old features directly (in case they're orphaned)
        print("Checking for orphaned old features...")
        for feature_id in OLD_FEATURE_IDS:
            feature = self.get_work_package(feature_id)
            if feature:
                subject = feature.get("subject", "Unknown")
                print(f"Found orphaned feature: {subject} (ID: {feature_id})")
                deleted = self.delete_recursive(feature_id)
                total_deleted += deleted
                print()
        
        print("=" * 80)
        print(f"Summary: {total_deleted} work packages {'would be ' if self.dry_run else ''}deleted")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Cleanup old OpenProject structure")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (don't actually delete)")
    
    args = parser.parse_args()
    
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        print("\nSet it with:")
        print("  export OPENPROJECT_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    cleaner = OpenProjectCleaner(OPENPROJECT_URL, OPENPROJECT_API_KEY, args.dry_run)
    cleaner.cleanup_old_structure()


if __name__ == "__main__":
    main()

















