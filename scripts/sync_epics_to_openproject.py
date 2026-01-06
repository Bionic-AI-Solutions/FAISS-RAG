#!/usr/bin/env python3
"""
Sync Epics and Stories from epics.md to OpenProject

This script parses the epics.md file and creates/updates corresponding
work packages in OpenProject, maintaining the hierarchy:
Epic → Feature → Story

Usage:
    python scripts/sync_epics_to_openproject.py [--project-id PROJECT_ID] [--dry-run]

Environment Variables:
    OPENPROJECT_URL: Base URL of OpenProject instance
    OPENPROJECT_API_KEY: API key for authentication
    OPENPROJECT_PROJECT_ID: Project ID (default: 8 for Mem0-RAG)
"""

import os
import sys
import re
import json
import argparse
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from requests.auth import HTTPBasicAuth


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
EPICS_FILE = PROJECT_ROOT / "_bmad-output/planning-artifacts/epics.md"

OPENPROJECT_URL = os.getenv("OPENPROJECT_URL", "https://op.zippio.ai")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
OPENPROJECT_PROJECT_ID = int(os.getenv("OPENPROJECT_PROJECT_ID", "8"))


class EpicParser:
    """Parse epics.md file to extract epics, features, and stories"""
    
    def __init__(self, epics_file: Path):
        self.epics_file = epics_file
        self.content = ""
        if epics_file.exists():
            self.content = epics_file.read_text()
        else:
            raise FileNotFoundError(f"Epics file not found: {epics_file}")
    
    def parse(self) -> List[Dict]:
        """Parse epics.md and return structured data"""
        epics = []
        
        # Pattern for Epic: ### Epic {N}: {title}
        epic_pattern = r'^### Epic (\d+): (.+)$'
        # Pattern for Story: #### Story {N}.{M}: {title}
        story_pattern = r'^#### Story (\d+)\.(\d+): (.+)$'
        
        current_epic = None
        current_stories = []
        
        lines = self.content.split('\n')
        
        for i, line in enumerate(lines):
            # Check for Epic
            epic_match = re.match(epic_pattern, line)
            if epic_match:
                # Save previous epic if exists
                if current_epic:
                    current_epic['stories'] = current_stories
                    epics.append(current_epic)
                
                epic_num = int(epic_match.group(1))
                epic_title = epic_match.group(2).strip()
                
                # Get epic description (next few lines until next section)
                description_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].startswith('###') or lines[j].startswith('####'):
                        break
                    if lines[j].strip() and not lines[j].startswith('**'):
                        description_lines.append(lines[j].strip())
                
                current_epic = {
                    'number': epic_num,
                    'title': epic_title,
                    'description': ' '.join(description_lines[:3]),  # First few lines
                    'stories': []
                }
                current_stories = []
                continue
            
            # Check for Story
            story_match = re.match(story_pattern, line)
            if story_match:
                epic_num = int(story_match.group(1))
                story_num = int(story_match.group(2))
                story_title = story_match.group(3).strip()
                
                # Get story content (As a/I want/So that and Acceptance Criteria)
                story_content = self._extract_story_content(lines, i)
                
                story = {
                    'epic_number': epic_num,
                    'story_number': story_num,
                    'title': story_title,
                    'content': story_content
                }
                current_stories.append(story)
                continue
        
        # Don't forget the last epic
        if current_epic:
            current_epic['stories'] = current_stories
            epics.append(current_epic)
        
        return epics
    
    def _extract_story_content(self, lines: List[str], start_idx: int) -> str:
        """Extract story content including user story and acceptance criteria"""
        content_lines = []
        in_story = True
        found_ac = False
        
        for i in range(start_idx + 1, min(start_idx + 50, len(lines))):
            line = lines[i]
            
            # Stop at next story or epic
            if line.startswith('#### Story') or line.startswith('### Epic'):
                break
            
            # Collect content
            if line.strip():
                content_lines.append(line)
                if 'Acceptance Criteria' in line or '**Acceptance Criteria**' in line:
                    found_ac = True
        
        return '\n'.join(content_lines)


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
        
        # Cache for existing work packages
        self.work_package_cache = {}
        self._load_existing_work_packages()
    
    def _load_existing_work_packages(self):
        """Load existing work packages for the project"""
        url = f"{self.base_url}/api/v3/work_packages"
        params = {'filters': json.dumps([{'project': {'operator': '=', 'values': [str(self.project_id)]}}])}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for wp in data.get('_embedded', {}).get('elements', []):
                wp_id = wp.get('id')
                subject = wp.get('subject', '')
                self.work_package_cache[subject] = wp_id
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing work packages: {e}")
    
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
    
    def create_or_update_epic(self, epic: Dict, dry_run: bool = False) -> Optional[int]:
        """Create or update epic work package"""
        subject = f"Epic {epic['number']}: {epic['title']}"
        
        # Check if exists
        if subject in self.work_package_cache:
            wp_id = self.work_package_cache[subject]
            print(f"📝 Epic already exists: {subject} (ID: {wp_id})")
            if not dry_run:
                # Update if needed
                self._update_work_package(wp_id, epic['description'])
            return wp_id
        
        if dry_run:
            print(f"🔨 [DRY RUN] Would create epic: {subject}")
            return None
        
        # Create epic (use Epic type 40, fallback to Summary task 38 if not enabled)
        url = f"{self.base_url}/api/v3/work_packages"
        payload = {
            "subject": subject,
            "description": {
                "raw": epic['description'],
                "format": "markdown"
            },
            "_links": {
                "type": {"href": "/api/v3/types/40"},  # Epic (fallback to 38 if not enabled)
                "project": {"href": f"/api/v3/projects/{self.project_id}"}
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            wp = response.json()
            wp_id = wp.get('id')
            self.work_package_cache[subject] = wp_id
            print(f"✅ Created epic: {subject} (ID: {wp_id})")
            return wp_id
        except Exception as e:
            print(f"❌ Failed to create epic {subject}: {e}")
            return None
    
    def create_or_update_story(self, story: Dict, epic_id: int, dry_run: bool = False) -> Optional[int]:
        """Create or update story work package"""
        subject = f"Story {story['epic_number']}.{story['story_number']}: {story['title']}"
        
        # Check if exists
        if subject in self.work_package_cache:
            wp_id = self.work_package_cache[subject]
            print(f"📝 Story already exists: {subject} (ID: {wp_id})")
            if not dry_run:
                self._update_work_package(wp_id, story['content'], parent_id=epic_id)
            return wp_id
        
        if dry_run:
            print(f"🔨 [DRY RUN] Would create story: {subject}")
            return None
        
        # Create story (use User Story type 41)
        url = f"{self.base_url}/api/v3/work_packages"
        payload = {
            "subject": subject,
            "description": {
                "raw": story['content'],
                "format": "markdown"
            },
            "_links": {
                "type": {"href": "/api/v3/types/41"},  # User Story
                "project": {"href": f"/api/v3/projects/{self.project_id}"},
                "parent": {"href": f"/api/v3/work_packages/{epic_id}"}
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            wp = response.json()
            wp_id = wp.get('id')
            self.work_package_cache[subject] = wp_id
            print(f"✅ Created story: {subject} (ID: {wp_id})")
            return wp_id
        except Exception as e:
            print(f"❌ Failed to create story {subject}: {e}")
            return None
    
    def _update_work_package(self, wp_id: int, description: str, parent_id: Optional[int] = None):
        """Update work package description and optionally parent"""
        wp = self.get_work_package(wp_id)
        if not wp:
            return
        
        payload = {
            "lockVersion": wp.get('lockVersion', 0),
            "description": {
                "raw": description,
                "format": "markdown"
            }
        }
        
        if parent_id:
            payload["_links"] = {
                "parent": {"href": f"/api/v3/work_packages/{parent_id}"}
            }
        
        url = f"{self.base_url}/api/v3/work_packages/{wp_id}"
        try:
            response = self.session.patch(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"⚠️  Warning: Could not update work package {wp_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Sync epics.md to OpenProject')
    parser.add_argument('--project-id', type=int, default=OPENPROJECT_PROJECT_ID,
                       help='OpenProject project ID')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating')
    args = parser.parse_args()
    
    print("=" * 80)
    print("Epics.md to OpenProject Sync")
    print("=" * 80)
    print()
    
    # Validate configuration
    if not OPENPROJECT_API_KEY:
        print("❌ ERROR: OPENPROJECT_API_KEY environment variable is required")
        sys.exit(1)
    
    if not EPICS_FILE.exists():
        print(f"❌ ERROR: Epics file not found: {EPICS_FILE}")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"   Epics file: {EPICS_FILE}")
    print(f"   OpenProject URL: {OPENPROJECT_URL}")
    print(f"   Project ID: {args.project_id}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    # Parse epics.md
    print("📖 Parsing epics.md...")
    try:
        parser = EpicParser(EPICS_FILE)
        epics = parser.parse()
        print(f"✅ Found {len(epics)} epics with {sum(len(e['stories']) for e in epics)} stories")
        print()
    except Exception as e:
        print(f"❌ Failed to parse epics.md: {e}")
        sys.exit(1)
    
    # Initialize OpenProject client
    client = OpenProjectClient(OPENPROJECT_URL, OPENPROJECT_API_KEY, args.project_id)
    
    # Sync epics and stories
    print("🔄 Syncing to OpenProject...")
    print()
    
    created_epics = 0
    created_stories = 0
    updated_epics = 0
    updated_stories = 0
    
    for epic in epics:
        epic_id = client.create_or_update_epic(epic, dry_run=args.dry_run)
        if epic_id:
            if epic['title'] in [f"Epic {e['number']}: {e['title']}" for e in epics]:
                updated_epics += 1
            else:
                created_epics += 1
        
        for story in epic['stories']:
            if epic_id:
                story_id = client.create_or_update_story(story, epic_id, dry_run=args.dry_run)
                if story_id:
                    if story['title'] in [s['title'] for s in epic['stories']]:
                        updated_stories += 1
                    else:
                        created_stories += 1
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"📊 Epics: {created_epics} created, {updated_epics} updated")
    print(f"📊 Stories: {created_stories} created, {updated_stories} updated")
    print()
    
    if args.dry_run:
        print("🔨 This was a dry run. No changes were made.")
    else:
        print("✅ Sync complete!")
        print(f"   View in OpenProject: {OPENPROJECT_URL}/projects/{args.project_id}/work_packages")


if __name__ == "__main__":
    main()


