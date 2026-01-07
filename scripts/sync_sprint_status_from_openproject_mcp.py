#!/usr/bin/env python3
"""
Sync sprint-status.yaml from OpenProject using MCP tools.
This script is designed to be called from within an MCP-enabled environment.
"""

import os
import sys
import re
import yaml
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# OpenProject status mapping to BMAD sprint status
OP_TO_BMAD_STATUS = {
    71: "backlog",      # New
    72: "backlog",      # In specification
    73: "backlog",      # Specified
    74: "backlog",      # Confirmed
    75: "backlog",      # To be scheduled
    76: "backlog",      # Scheduled
    77: "in-progress",  # In progress
    78: "ready-for-dev", # Developed
    79: "review",       # In testing
    80: "review",       # Tested
    81: "in-progress",  # Test failed
    82: "done",         # Closed
    83: "backlog",      # On hold
    84: "backlog",      # Rejected
}

def parse_story_key(subject):
    """Convert story subject to BMAD story key format"""
    match = re.match(r'Story (\d+)\.(\d+): (.+)', subject)
    if match:
        epic_num = match.group(1)
        story_num = match.group(2)
        title = match.group(3).lower().replace(' ', '-').replace('&', 'and')
        title = re.sub(r'[^a-z0-9-]', '', title)
        title = re.sub(r'-+', '-', title).strip('-')
        return f"{epic_num}-{story_num}-{title}"
    return None

def parse_epic_key(subject):
    """Convert epic subject to BMAD epic key format"""
    match = re.match(r'Epic (\d+): (.+)', subject)
    if match:
        return f"epic-{match.group(1)}"
    return None

def generate_sprint_status(work_packages, output_file):
    """Generate sprint-status.yaml from OpenProject work packages"""
    
    epics = {}
    stories = {}
    
    # Parse work packages
    for wp in work_packages:
        wp_id = wp.get("id")
        subject = wp.get("subject", "")
        
        # Get status ID - handle both dict and direct ID
        status_obj = wp.get("status", {})
        if isinstance(status_obj, dict):
            status_id = status_obj.get("id", 71)
        else:
            status_id = status_obj if status_obj else 71
        
        # Get type - handle both dict and direct name
        type_obj = wp.get("type", {})
        if isinstance(type_obj, dict):
            wp_type = type_obj.get("name", "")
        else:
            wp_type = type_obj if type_obj else ""
        
        # Skip test tasks and subtasks (tasks that are children of stories)
        if "Test Task" in subject or wp_id == 81:
            continue
        
        # Skip tasks that are children of stories (these are subtasks)
        # We only track epics and stories in sprint-status.yaml
        if wp_type == "Task" and wp.get("parent"):
            continue
        
        # Map OpenProject status to BMAD status
        bmad_status = OP_TO_BMAD_STATUS.get(status_id, "backlog")
        
        # Check if epic
        epic_key = parse_epic_key(subject)
        if epic_key:
            epics[epic_key] = {
                "id": wp_id,
                "subject": subject,
                "status": bmad_status,
                "op_status_id": status_id
            }
            continue
        
        # Check if story
        story_key = parse_story_key(subject)
        if story_key:
            epic_num = story_key.split('-')[0]
            stories[story_key] = {
                "id": wp_id,
                "subject": subject,
                "epic": f"epic-{epic_num}",
                "status": bmad_status,
                "op_status_id": status_id
            }
    
    # Build sprint status structure
    development_status = {}
    
    # Sort epics by number
    sorted_epics = sorted(epics.items(), key=lambda x: int(x[0].split('-')[1]))
    
    for epic_key, epic_data in sorted_epics:
        # Add epic entry
        development_status[epic_key] = epic_data["status"]
        
        # Add stories for this epic
        epic_num = epic_key.split('-')[1]
        epic_stories = [
            (k, v) for k, v in stories.items() 
            if k.startswith(f"{epic_num}-")
        ]
        # Sort stories by story number
        epic_stories.sort(key=lambda x: (int(x[0].split('-')[0]), int(x[0].split('-')[1])))
        
        for story_key, story_data in epic_stories:
            development_status[story_key] = story_data["status"]
        
        # Add retrospective entry
        development_status[f"{epic_key}-retrospective"] = "optional"
    
    # Generate YAML content
    sprint_status = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": "mem0-rag",
        "project_key": "op-8",
        "tracking_system": "openproject",
        "story_location": "_bmad-output/implementation-artifacts",
        "development_status": development_status
    }
    
    # Write YAML file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        # Write header comments
        f.write("# Sprint Status - Generated from OpenProject\n")
        f.write(f"# Generated: {sprint_status['generated']}\n")
        f.write(f"# Project: {sprint_status['project']}\n")
        f.write(f"# Project Key: {sprint_status['project_key']}\n")
        f.write(f"# Tracking System: {sprint_status['tracking_system']}\n")
        f.write(f"# Story Location: {sprint_status['story_location']}\n")
        f.write("\n")
        f.write("# STATUS DEFINITIONS:\n")
        f.write("# ==================\n")
        f.write("# Epic Status:\n")
        f.write("#   - backlog: Epic not yet started\n")
        f.write("#   - in-progress: Epic actively being worked on\n")
        f.write("#   - done: All stories in epic completed\n")
        f.write("#\n")
        f.write("# Story Status:\n")
        f.write("#   - backlog: Story only exists in epic file\n")
        f.write("#   - ready-for-dev: Story file created, ready for development\n")
        f.write("#   - in-progress: Developer actively working on implementation\n")
        f.write("#   - review: Implementation complete, ready for review\n")
        f.write("#   - done: Story completed\n")
        f.write("#\n")
        f.write("# Retrospective Status:\n")
        f.write("#   - optional: Can be completed but not required\n")
        f.write("#   - done: Retrospective has been completed\n")
        f.write("#\n")
        f.write("# WORKFLOW NOTES:\n")
        f.write("# ===============\n")
        f.write("# - Mark epic as 'in-progress' when starting work on its first story\n")
        f.write("# - SM typically creates next story ONLY after previous one is 'done' to incorporate learnings\n")
        f.write("# - Dev moves story to 'review', then Dev runs code-review (fresh context, ideally different LLM)\n")
        f.write("# - Status synced from OpenProject MCP (Project ID: 8)\n")
        f.write("\n")
        
        # Write YAML data
        yaml.dump(sprint_status, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    return sprint_status

if __name__ == "__main__":
    print("This script should be called via MCP tool integration")
    print("Use MCP tools to fetch OpenProject data and generate sprint-status.yaml")
    print("\nTo use this script:")
    print("1. Call mcp_openproject_list_work_packages(project_id=8, status='all', page_size=100)")
    print("2. Pass the work_packages array to generate_sprint_status()")
    print("3. The script will generate sprint-status.yaml with synced statuses")














