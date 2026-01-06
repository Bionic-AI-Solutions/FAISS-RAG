#!/usr/bin/env python3
"""
Create Tasks Under Stories in OpenProject

This script reads implementation artifacts or epics.md and creates tasks
under story work packages in OpenProject.

Usage:
    python scripts/create_tasks_from_stories.py [--project-id PROJECT_ID] [--story-id STORY_ID] [--dry-run]
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
    
    def create_task(self, parent_id: int, subject: str, description: str, dry_run: bool = False) -> Optional[int]:
        """Create a task work package under a parent"""
        if dry_run:
            print(f"🔨 [DRY RUN] Would create task: {subject} under parent {parent_id}")
            return None
        
        # Get parent to ensure it exists
        parent = self.get_work_package(parent_id)
        if not parent:
            print(f"❌ Parent work package {parent_id} not found")
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
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            print(f"❌ Failed to create task {subject}: {error_msg}")
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
        except Exception as e:
            print(f"⚠️  Warning: Could not list tasks under {parent_id}: {e}")
            return []


def parse_implementation_artifact(artifact_file: Path) -> List[Dict]:
    """Parse implementation artifact to extract tasks"""
    if not artifact_file.exists():
        return []
    
    content = artifact_file.read_text()
    tasks = []
    
    # Pattern for tasks: "- [ ] Task N: ..." or "- [x] Task N: ..."
    task_pattern = r'^- \[[ x]\]\s*Task\s+(\d+):\s*(.+)$'
    
    lines = content.split('\n')
    current_task = None
    
    for i, line in enumerate(lines):
        match = re.match(task_pattern, line)
        if match:
            task_num = match.group(1)
            task_title = match.group(2).strip()
            
            # Get task description (subtasks and details)
            description_lines = []
            for j in range(i + 1, min(i + 20, len(lines))):
                next_line = lines[j]
                if next_line.strip().startswith('- [') and not next_line.strip().startswith('  -'):
                    break
                if next_line.strip() and not next_line.startswith('##'):
                    description_lines.append(next_line)
            
            task = {
                'number': task_num,
                'subject': f"Task {task_num}: {task_title}",
                'description': '\n'.join(description_lines[:10])  # First 10 lines
            }
            tasks.append(task)
    
    return tasks


def parse_story_tasks_from_epics(epics_file: Path, story_pattern: str) -> List[Dict]:
    """Parse tasks from epics.md for a specific story"""
    if not epics_file.exists():
        return []
    
    content = epics_file.read_text()
    tasks = []
    
    # Find the story section
    story_section = None
    lines = content.split('\n')
    in_story = False
    story_lines = []
    
    for i, line in enumerate(lines):
        if re.match(story_pattern, line):
            in_story = True
            story_lines = [line]
            continue
        
        if in_story:
            if line.startswith('#### Story') or line.startswith('### Epic'):
                break
            story_lines.append(line)
    
    if not story_lines:
        return []
    
    # Extract tasks from acceptance criteria
    # Look for "Given" blocks that can become tasks
    story_content = '\n'.join(story_lines)
    
    # Simple heuristic: Each "Given" block can be a task
    given_blocks = re.split(r'\*\*Given\*\*', story_content)
    
    for i, block in enumerate(given_blocks[1:], 1):  # Skip first empty split
        lines = block.split('\n')
        if not lines:
            continue
        
        # Extract the "Given" statement
        given_text = lines[0].strip()
        if not given_text:
            continue
        
        # Get related When/Then statements
        related_lines = []
        for line in lines[1:10]:  # Next 10 lines
            if line.strip() and (line.startswith('**When**') or line.startswith('**Then**') or line.startswith('**And**')):
                related_lines.append(line.strip())
        
        task = {
            'number': str(i),
            'subject': f"Task: {given_text[:60]}...",
            'description': f"**Given** {given_text}\n" + '\n'.join(related_lines)
        }
        tasks.append(task)
    
    return tasks


def main():
    parser = argparse.ArgumentParser(description='Create tasks under stories in OpenProject')
    parser.add_argument('--project-id', type=int, default=OPENPROJECT_PROJECT_ID,
                       help='OpenProject project ID')
    parser.add_argument('--story-id', type=int, default=None,
                       help='Specific story work package ID to create tasks under')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating')
    args = parser.parse_args()
    
    print("=" * 80)
    print("Create Tasks Under Stories in OpenProject")
    print("=" * 80)
    print()
    
    # Validate configuration
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   OpenProject URL: {OPENPROJECT_URL}")
    print(f"   Project ID: {args.project_id}")
    print(f"   Story ID: {args.story_id or 'All stories'}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    # Initialize client
    client = OpenProjectClient(OPENPROJECT_URL, OPENPROJECT_API_KEY, args.project_id)
    
    # If specific story ID provided, work with that
    if args.story_id:
        story = client.get_work_package(args.story_id)
        if not story:
            print(f"❌ Story {args.story_id} not found")
            sys.exit(1)
        
        subject = story.get('subject', '')
        print(f"📖 Working with story: {subject}")
        print()
        
        # Check if tasks already exist
        existing_tasks = client.list_tasks_under_parent(args.story_id)
        print(f"📊 Existing tasks under this story: {len(existing_tasks)}")
        
        # Try to find implementation artifact
        # Story 1.1 -> 1-1-project-structure-and-development-environment-setup.md
        story_match = re.match(r'Story (\d+)\.(\d+):', subject)
        if story_match:
            epic_num = story_match.group(1)
            story_num = story_match.group(2)
            artifact_name = f"{epic_num}-{story_num}-*.md"
            artifact_files = list(IMPLEMENTATION_ARTIFACTS.glob(artifact_name))
            
            if artifact_files:
                print(f"📄 Found implementation artifact: {artifact_files[0].name}")
                tasks = parse_implementation_artifact(artifact_files[0])
                print(f"📋 Parsed {len(tasks)} tasks from artifact")
                print()
                
                # Create tasks
                created = 0
                for task in tasks:
                    # Check if task already exists
                    existing = [t for t in existing_tasks if task['subject'] in t.get('subject', '')]
                    if existing:
                        print(f"⏭️  Task already exists: {task['subject']}")
                        continue
                    
                    task_id = client.create_task(args.story_id, task['subject'], task['description'], args.dry_run)
                    if task_id:
                        created += 1
                
                print()
                print(f"✅ Created {created} new tasks")
            else:
                print("⚠️  No implementation artifact found. Creating tasks from acceptance criteria...")
                # Parse from epics.md
                epics_file = PROJECT_ROOT / "_bmad-output/planning-artifacts/epics.md"
                story_pattern = f"^#### Story {epic_num}\\.{story_num}:"
                tasks = parse_story_tasks_from_epics(epics_file, story_pattern)
                
                if tasks:
                    print(f"📋 Parsed {len(tasks)} tasks from acceptance criteria")
                    created = 0
                    for task in tasks:
                        task_id = client.create_task(args.story_id, task['subject'], task['description'], args.dry_run)
                        if task_id:
                            created += 1
                    print(f"✅ Created {created} new tasks")
                else:
                    print("⚠️  Could not extract tasks. Please create tasks manually.")
    else:
        print("ℹ️  Use --story-id to specify which story to create tasks under")
        print("   Example: python scripts/create_tasks_from_stories.py --story-id 94")
    
    print()
    if args.dry_run:
        print("🔨 This was a dry run. No changes were made.")


if __name__ == "__main__":
    main()








