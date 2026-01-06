#!/usr/bin/env python3
"""
Comprehensive OpenProject Update Script

This script:
1. Lists all work packages for the project
2. Updates story types from Task (36) to User Story (41)
3. Updates feature types to Feature (39)
4. Updates epic types to Epic (40)
5. Creates tasks under stories based on implementation artifacts

Usage:
    python scripts/fix_and_update_openproject.py [--project-id PROJECT_ID] [--dry-run]
"""

import os
import sys
import json
import re
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from requests.auth import HTTPBasicAuth


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
IMPLEMENTATION_ARTIFACTS = PROJECT_ROOT / "_bmad-output/implementation-artifacts"
EPICS_FILE = PROJECT_ROOT / "_bmad-output/planning-artifacts/epics.md"

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
            return None
    
    def update_work_package_type(self, wp_id: int, new_type_id: int, dry_run: bool = False) -> Tuple[bool, str]:
        """Update work package type"""
        wp = self.get_work_package(wp_id)
        if not wp:
            return False, f"Could not fetch work package {wp_id}"
        
        current_type_id = wp.get('_embedded', {}).get('type', {}).get('id')
        if current_type_id == new_type_id:
            return True, f"Already correct type"
        
        subject = wp.get('subject', f'WP-{wp_id}')
        lock_version = wp.get('lockVersion', 0)
        
        if dry_run:
            type_names = {36: 'Task', 38: 'Summary task', 39: 'Feature', 40: 'Epic', 41: 'User story'}
            return True, f"[DRY RUN] Would update {subject} from {type_names.get(current_type_id, current_type_id)} to {type_names.get(new_type_id, new_type_id)}"
        
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
            return True, f"✅ Updated {subject}"
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return False, f"❌ Failed: {error_msg}"
    
    def create_task(self, parent_id: int, subject: str, description: str, dry_run: bool = False) -> Optional[int]:
        """Create a task work package under a parent"""
        if dry_run:
            print(f"   [DRY RUN] Would create: {subject}")
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
            return wp.get('id')
        except Exception as e:
            return None
    
    def list_tasks_under_parent(self, parent_id: int) -> List[Dict]:
        """List all tasks under a parent work package"""
        url = f"{self.base_url}/api/v3/work_packages"
        filters = json.dumps([
            {'project': {'operator': '=', 'values': [str(self.project_id)]}},
            {'parent': {'operator': '=', 'values': [str(parent_id)]}}
        ])
        params = {'filters': filters, 'pageSize': 100}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('_embedded', {}).get('elements', [])
        except:
            return []


def identify_work_package_type(subject: str) -> Optional[Tuple[str, int]]:
    """Identify work package type from subject and return (type_name, type_id)"""
    if re.match(r'^Epic \d+:', subject):
        return ('epic', 40)
    elif re.match(r'^Feature \d+\.\d+:', subject):
        return ('feature', 39)
    elif re.match(r'^Story \d+\.\d+:', subject):
        return ('story', 41)
    elif re.match(r'^Task \d+\.\d+\.\d+', subject) or 'Task' in subject:
        return ('task', 36)
    return None


def parse_implementation_artifact(artifact_file: Path) -> List[Dict]:
    """Parse implementation artifact to extract tasks"""
    if not artifact_file.exists():
        return []
    
    content = artifact_file.read_text()
    tasks = []
    
    # Pattern for tasks: "- [ ] Task N: ..." or "- [x] Task N: ..."
    task_pattern = r'^- \[[ x]\]\s*Task\s+(\d+):\s*(.+)$'
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        match = re.match(task_pattern, line)
        if match:
            task_num = match.group(1)
            task_title = match.group(2).strip()
            
            # Get task description (subtasks and details)
            description_lines = []
            for j in range(i + 1, min(i + 30, len(lines))):
                next_line = lines[j]
                if next_line.strip().startswith('- [') and not next_line.strip().startswith('  -'):
                    break
                if next_line.strip() and not next_line.startswith('##'):
                    description_lines.append(next_line)
            
            task = {
                'number': task_num,
                'subject': f"Task {task_num}: {task_title}",
                'description': '\n'.join(description_lines[:15]).strip()
            }
            tasks.append(task)
    
    return tasks


def find_story_artifact(story_subject: str) -> Optional[Path]:
    """Find implementation artifact for a story"""
    # Story 1.1 -> 1-1-*.md
    match = re.match(r'Story (\d+)\.(\d+):', story_subject)
    if not match:
        return None
    
    epic_num = match.group(1)
    story_num = match.group(2)
    pattern = f"{epic_num}-{story_num}-*.md"
    artifacts = list(IMPLEMENTATION_ARTIFACTS.glob(pattern))
    return artifacts[0] if artifacts else None


def main():
    parser = argparse.ArgumentParser(description='Fix and update OpenProject work packages')
    parser.add_argument('--project-id', type=int, default=OPENPROJECT_PROJECT_ID,
                       help='OpenProject project ID')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without actually changing')
    parser.add_argument('--create-tasks', action='store_true',
                       help='Create tasks under stories from implementation artifacts')
    args = parser.parse_args()
    
    print("=" * 80)
    print("OpenProject Work Package Fix & Update")
    print("=" * 80)
    print()
    
    # Validate configuration
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        print()
        print("Set it with:")
        print("  export OPENPROJECT_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   OpenProject URL: {OPENPROJECT_URL}")
    print(f"   Project ID: {args.project_id}")
    print(f"   Dry run: {args.dry_run}")
    print(f"   Create tasks: {args.create_tasks}")
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
    
    for wp in work_packages:
        wp_id = wp.get('id')
        subject = wp.get('subject', '')
        wp_type_id = wp.get('_embedded', {}).get('type', {}).get('id')
        
        identified = identify_work_package_type(subject)
        if identified:
            type_name, expected_type_id = identified
            wp_info = {
                'id': wp_id,
                'subject': subject,
                'current_type_id': wp_type_id,
                'expected_type_id': expected_type_id,
                'needs_update': wp_type_id != expected_type_id
            }
            
            if type_name == 'epic':
                epics.append(wp_info)
            elif type_name == 'feature':
                features.append(wp_info)
            elif type_name == 'story':
                stories.append(wp_info)
            elif type_name == 'task':
                tasks.append(wp_info)
    
    print(f"📊 Work Package Breakdown:")
    print(f"   Epics: {len(epics)} ({sum(1 for e in epics if e['needs_update'])} need type update)")
    print(f"   Features: {len(features)} ({sum(1 for f in features if f['needs_update'])} need type update)")
    print(f"   Stories: {len(stories)} ({sum(1 for s in stories if s['needs_update'])} need type update)")
    print(f"   Tasks: {len(tasks)}")
    print()
    
    # Update Epic types
    if epics:
        print("🔄 Updating Epic work packages to Epic type (40)...")
        epic_updates = 0
        for epic in epics:
            if epic['needs_update']:
                success, message = client.update_work_package_type(epic['id'], 40, args.dry_run)
                print(f"   {message}: {epic['subject']}")
                if success and not args.dry_run:
                    epic_updates += 1
        print(f"   ✅ Updated {epic_updates} epics")
        print()
    
    # Update Feature types
    if features:
        print("🔄 Updating Feature work packages to Feature type (39)...")
        feature_updates = 0
        for feature in features:
            if feature['needs_update']:
                success, message = client.update_work_package_type(feature['id'], 39, args.dry_run)
                print(f"   {message}: {feature['subject']}")
                if success and not args.dry_run:
                    feature_updates += 1
        print(f"   ✅ Updated {feature_updates} features")
        print()
    
    # Update Story types
    if stories:
        print("🔄 Updating Story work packages to User Story type (41)...")
        story_updates = 0
        for story in stories:
            if story['needs_update']:
                success, message = client.update_work_package_type(story['id'], 41, args.dry_run)
                print(f"   {message}: {story['subject']}")
                if success and not args.dry_run:
                    story_updates += 1
        print(f"   ✅ Updated {story_updates} stories")
        print()
    
    # Create tasks under stories
    if args.create_tasks and stories:
        print("📝 Creating tasks under stories from implementation artifacts...")
        tasks_created = 0
        
        for story in stories:
            story_id = story['id']
            story_subject = story['subject']
            
            # Check if tasks already exist
            existing_tasks = client.list_tasks_under_parent(story_id)
            if existing_tasks:
                print(f"   ⏭️  Story {story_subject} already has {len(existing_tasks)} tasks")
                continue
            
            # Find implementation artifact
            artifact_file = find_story_artifact(story_subject)
            if artifact_file:
                print(f"   📄 Found artifact: {artifact_file.name}")
                tasks = parse_implementation_artifact(artifact_file)
                
                if tasks:
                    print(f"   📋 Creating {len(tasks)} tasks for {story_subject}...")
                    for task in tasks:
                        task_id = client.create_task(story_id, task['subject'], task['description'], args.dry_run)
                        if task_id:
                            tasks_created += 1
                            print(f"      ✅ Created: {task['subject']}")
                else:
                    print(f"   ⚠️  No tasks found in artifact")
            else:
                print(f"   ⚠️  No artifact found for {story_subject}")
        
        print(f"   ✅ Created {tasks_created} tasks total")
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    if args.dry_run:
        print("🔨 This was a dry run. No changes were made.")
        print()
        print("To apply changes, run without --dry-run:")
        print("  python scripts/fix_and_update_openproject.py")
        if args.create_tasks:
            print("  python scripts/fix_and_update_openproject.py --create-tasks")
    else:
        print("✅ Update complete!")
        print(f"   View in OpenProject: {OPENPROJECT_URL}/projects/{args.project_id}/work_packages")


if __name__ == "__main__":
    main()








