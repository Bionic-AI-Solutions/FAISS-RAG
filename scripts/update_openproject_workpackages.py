#!/usr/bin/env python3
"""
Update OpenProject Work Packages: Fix Types and Create Tasks

This script:
1. Updates story work packages from Task (36) to User Story (41)
2. Updates feature work packages to Feature type (39)
3. Updates epic work packages to Epic type (40)
4. Creates tasks under stories based on acceptance criteria breakdown

Usage:
    python scripts/update_openproject_workpackages.py [--project-id PROJECT_ID] [--dry-run]
"""

import os
import sys
import json
import re
import argparse
import requests
from typing import Dict, List, Optional, Tuple
from requests.auth import HTTPBasicAuth


# Configuration
OPENPROJECT_URL = os.getenv("OPENPROJECT_URL", "https://op.zippio.ai")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
OPENPROJECT_PROJECT_ID = int(os.getenv("OPENPROJECT_PROJECT_ID", "8"))


class OpenProjectClient:
    """Client for OpenProject API v3"""
    
    def __init__(self, base_url: str, api_key: str, project_id: int):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.project_id = project_id
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.auth = HTTPBasicAuth('apikey', api_key)
    
    def get_all_work_packages(self) -> List[Dict]:
        """Get all work packages for the project"""
        all_wps = []
        offset = 1
        page_size = 100
        
        while True:
            url = f"{self.base_url}/api/v3/work_packages"
            filters = json.dumps([{'project': {'operator': '=', 'values': [str(self.project_id)]}}])
            params = {
                'filters': filters,
                'pageSize': page_size,
                'offset': offset
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                wps = data.get('_embedded', {}).get('elements', [])
                if not wps:
                    break
                
                all_wps.extend(wps)
                
                # Check if there are more pages
                total = data.get('total', 0)
                if len(all_wps) >= total:
                    break
                
                offset += page_size
            except Exception as e:
                print(f"❌ Error fetching work packages: {e}")
                break
        
        return all_wps
    
    def get_work_package(self, work_package_id: int) -> Optional[Dict]:
        """Get work package details"""
        url = f"{self.base_url}/api/v3/work_packages/{work_package_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching work package {work_package_id}: {e}")
            return None
    
    def update_work_package_type(self, wp_id: int, new_type_id: int, dry_run: bool = False) -> Tuple[bool, str]:
        """Update work package type"""
        wp = self.get_work_package(wp_id)
        if not wp:
            return False, f"Could not fetch work package {wp_id}"
        
        current_type_id = wp.get('_embedded', {}).get('type', {}).get('id')
        if current_type_id == new_type_id:
            return True, f"Work package {wp_id} already has correct type"
        
        subject = wp.get('subject', f'WP-{wp_id}')
        lock_version = wp.get('lockVersion', 0)
        
        if dry_run:
            return True, f"[DRY RUN] Would update {subject} (ID: {wp_id}) from type {current_type_id} to {new_type_id}"
        
        url = f"{self.base_url}/api/v3/work_packages/{wp_id}"
        payload = {
            "lockVersion": lock_version,
            "_links": {
                "type": {"href": f"/api/v3/types/{new_type_id}"}
            }
        }
        
        try:
            response = self.session.patch(url, json=payload)
            response.raise_for_status()
            return True, f"✅ Updated {subject} (ID: {wp_id}) to type {new_type_id}"
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return False, f"❌ Failed to update {subject} (ID: {wp_id}): {error_msg}"
    
    def create_task(self, parent_id: int, subject: str, description: str, dry_run: bool = False) -> Optional[int]:
        """Create a task work package under a parent"""
        if dry_run:
            print(f"🔨 [DRY RUN] Would create task: {subject} under parent {parent_id}")
            return None
        
        url = f"{self.base_url}/api/v3/work_packages"
        payload = {
            "subject": subject,
            "description": {
                "raw": description,
                "format": "markdown"
            },
            "_links": {
                "type": {"href": "/api/v3/types/36"},  # Task
                "project": {"href": f"/api/v3/projects/{self.project_id}"},
                "parent": {"href": f"/api/v3/work_packages/{parent_id}"}
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            wp = response.json()
            wp_id = wp.get('id')
            print(f"✅ Created task: {subject} (ID: {wp_id})")
            return wp_id
        except Exception as e:
            print(f"❌ Failed to create task {subject}: {e}")
            return None


def identify_work_package_type(subject: str) -> Optional[str]:
    """Identify work package type from subject"""
    if re.match(r'^Epic \d+:', subject):
        return 'epic'
    elif re.match(r'^Feature \d+\.\d+:', subject):
        return 'feature'
    elif re.match(r'^Story \d+\.\d+:', subject):
        return 'story'
    elif re.match(r'^Task \d+\.\d+\.\d+:', subject):
        return 'task'
    return None


def extract_tasks_from_acceptance_criteria(description: str) -> List[Dict]:
    """Extract task breakdown from acceptance criteria"""
    tasks = []
    
    # Look for "Given/When/Then" patterns that can be broken into tasks
    # This is a simple heuristic - can be improved
    lines = description.split('\n')
    current_task = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for "Given" statements that might indicate a task
        if line.startswith('**Given**') or line.startswith('Given'):
            if current_task:
                tasks.append(current_task)
            task_text = line.replace('**Given**', '').replace('Given', '').strip()
            if task_text:
                current_task = {
                    'subject': f"Task: {task_text[:50]}...",
                    'description': line
                }
        elif current_task and (line.startswith('**When**') or line.startswith('**Then**') or line.startswith('**And**')):
            current_task['description'] += '\n' + line
    
    if current_task:
        tasks.append(current_task)
    
    return tasks


def main():
    parser = argparse.ArgumentParser(description='Update OpenProject work package types and create tasks')
    parser.add_argument('--project-id', type=int, default=OPENPROJECT_PROJECT_ID,
                       help='OpenProject project ID')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without actually changing')
    args = parser.parse_args()
    
    print("=" * 80)
    print("OpenProject Work Package Update")
    print("=" * 80)
    print()
    
    # Validate configuration
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   OpenProject URL: {OPENPROJECT_URL}")
    print(f"   Project ID: {args.project_id}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    # Initialize client
    client = OpenProjectClient(OPENPROJECT_URL, OPENPROJECT_API_KEY, args.project_id)
    
    # Get all work packages
    print("📦 Fetching work packages...")
    work_packages = client.get_all_work_packages()
    print(f"✅ Found {len(work_packages)} work packages")
    print()
    
    # Categorize work packages
    epics = []
    features = []
    stories = []
    tasks = []
    others = []
    
    for wp in work_packages:
        wp_id = wp.get('id')
        subject = wp.get('subject', '')
        wp_type_id = wp.get('_embedded', {}).get('type', {}).get('id')
        wp_type_name = wp.get('_embedded', {}).get('type', {}).get('name', 'Unknown')
        
        identified_type = identify_work_package_type(subject)
        
        wp_info = {
            'id': wp_id,
            'subject': subject,
            'current_type_id': wp_type_id,
            'current_type_name': wp_type_name,
            'identified_type': identified_type
        }
        
        if identified_type == 'epic':
            epics.append(wp_info)
        elif identified_type == 'feature':
            features.append(wp_info)
        elif identified_type == 'story':
            stories.append(wp_info)
        elif identified_type == 'task':
            tasks.append(wp_info)
        else:
            others.append(wp_info)
    
    print(f"📊 Work Package Breakdown:")
    print(f"   Epics: {len(epics)}")
    print(f"   Features: {len(features)}")
    print(f"   Stories: {len(stories)}")
    print(f"   Tasks: {len(tasks)}")
    print(f"   Others: {len(others)}")
    print()
    
    # Update Epic types (should be type 40)
    print("🔄 Updating Epic work packages to Epic type (40)...")
    epic_updates = 0
    for epic in epics:
        if epic['current_type_id'] != 40:
            success, message = client.update_work_package_type(epic['id'], 40, args.dry_run)
            print(f"   {message}")
            if success and not args.dry_run:
                epic_updates += 1
    print()
    
    # Update Feature types (should be type 39)
    print("🔄 Updating Feature work packages to Feature type (39)...")
    feature_updates = 0
    for feature in features:
        if feature['current_type_id'] != 39:
            success, message = client.update_work_package_type(feature['id'], 39, args.dry_run)
            print(f"   {message}")
            if success and not args.dry_run:
                feature_updates += 1
    print()
    
    # Update Story types (should be type 41 - User Story)
    print("🔄 Updating Story work packages to User Story type (41)...")
    story_updates = 0
    for story in stories:
        if story['current_type_id'] != 41:
            success, message = client.update_work_package_type(story['id'], 41, args.dry_run)
            print(f"   {message}")
            if success and not args.dry_run:
                story_updates += 1
    print()
    
    # Create tasks under stories (if not dry run)
    if not args.dry_run and stories:
        print("📝 Creating tasks under stories based on acceptance criteria...")
        print("   (This feature will be enhanced to parse acceptance criteria)")
        print("   For now, tasks should be created manually or via story grooming")
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ Epic updates: {epic_updates}")
    print(f"✅ Feature updates: {feature_updates}")
    print(f"✅ Story updates: {story_updates}")
    print()
    
    if args.dry_run:
        print("🔨 This was a dry run. No changes were made.")
    else:
        print("✅ Update complete!")
        print(f"   View in OpenProject: {OPENPROJECT_URL}/projects/{args.project_id}/work_packages")


if __name__ == "__main__":
    main()















