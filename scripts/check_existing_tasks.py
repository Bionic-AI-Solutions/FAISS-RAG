#!/usr/bin/env python3
"""
Check for existing tasks in OpenProject before creating new ones.

This script helps avoid duplicate task creation by checking for existing
tasks, including those under closed stories.
"""

import sys
from typing import List, Dict, Any, Set

# MCP tool imports would go here in actual usage
# For now, this is a reference implementation


def check_existing_tasks_for_story(story_id: int) -> List[Dict[str, Any]]:
    """
    Check for existing tasks for a story, including closed stories.
    
    Args:
        story_id: OpenProject work package ID for the story
    
    Returns:
        List of existing tasks (if any)
    """
    # Get ALL children (including closed tasks)
    # In actual usage, this would call:
    # children = mcp_openproject_get_work_package_children(
    #     parent_id=story_id,
    #     status="all"  # Include closed tasks
    # )
    
    # For reference:
    print(f"Checking for existing tasks under story {story_id}...")
    print("Use: mcp_openproject_get_work_package_children(parent_id={story_id}, status='all')")
    
    return []


def filter_existing_tasks(
    story_id: int, 
    proposed_tasks: List[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out tasks that already exist for a story.
    
    Args:
        story_id: OpenProject work package ID for the story
        proposed_tasks: List of tasks to create
    
    Returns:
        Tuple of (new_tasks, existing_tasks)
    """
    # Check for existing tasks
    existing_tasks = check_existing_tasks_for_story(story_id)
    existing_subjects: Set[str] = {task["subject"] for task in existing_tasks}
    
    # Separate new and existing tasks
    new_tasks = [
        task for task in proposed_tasks 
        if task["subject"] not in existing_subjects
    ]
    
    existing_proposed = [
        task for task in proposed_tasks 
        if task["subject"] in existing_subjects
    ]
    
    return new_tasks, existing_proposed


def safe_create_story_tasks(
    story_id: int, 
    tasks: List[Dict[str, Any]],
    project_id: int = 8
) -> Dict[str, Any]:
    """
    Safely create tasks for a story, checking for duplicates first.
    
    Args:
        story_id: OpenProject work package ID for the story
        tasks: List of task definitions
        project_id: OpenProject project ID
    
    Returns:
        Result dictionary with created and skipped tasks
    """
    # Step 1: Check for existing tasks
    new_tasks, existing_tasks = filter_existing_tasks(story_id, tasks)
    
    if existing_tasks:
        print(f"⚠️  Found {len(existing_tasks)} existing tasks (skipping):")
        for task in existing_tasks:
            print(f"   - {task['subject']}")
    
    if not new_tasks:
        print(f"✅ All {len(tasks)} tasks already exist for story {story_id}")
        return {
            "created": [],
            "skipped": existing_tasks,
            "total_existing": len(existing_tasks)
        }
    
    print(f"📝 Creating {len(new_tasks)} new tasks (skipping {len(existing_tasks)} existing)")
    
    # Step 2: Create only new tasks
    # In actual usage, this would call:
    # result = mcp_openproject_bulk_create_work_packages(
    #     project_id=project_id,
    #     work_packages=new_tasks,
    #     continue_on_error=True
    # )
    
    # Step 3: Set parent relationships
    # for task in result.get("created", []):
    #     mcp_openproject_set_work_package_parent(
    #         work_package_id=task["id"],
    #         parent_id=story_id
    #     )
    
    return {
        "created": new_tasks,
        "skipped": existing_tasks,
        "total_new": len(new_tasks),
        "total_existing": len(existing_tasks)
    }


def main():
    """Example usage."""
    print("=" * 80)
    print("Check Existing Tasks Before Creation")
    print("=" * 80)
    print()
    print("This script demonstrates how to check for existing tasks")
    print("before creating new ones to avoid duplicates.")
    print()
    print("Key points:")
    print("1. Always use status='all' when querying OpenProject")
    print("2. Check for existing tasks by subject (title)")
    print("3. Only create tasks that don't already exist")
    print("4. Some stories may be closed and won't appear in default views")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()




