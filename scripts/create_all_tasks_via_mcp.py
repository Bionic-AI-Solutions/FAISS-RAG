#!/usr/bin/env python3
"""
Create all tasks in OpenProject using MCP tools.

This script creates tasks for Epic 3, 4, and 5 stories.
"""

import json
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from create_all_missing_tasks import create_epic3_tasks, create_epic4_tasks, create_epic5_tasks

def main():
    """Main execution function."""
    print("=" * 80)
    print("Creating All Tasks in OpenProject")
    print("=" * 80)
    
    # Get all tasks
    all_tasks = []
    all_tasks.extend(create_epic3_tasks())
    all_tasks.extend(create_epic4_tasks())
    all_tasks.extend(create_epic5_tasks())
    
    # Remove status_id from all tasks (not accepted during creation)
    for task in all_tasks:
        task.pop("status_id", None)
    
    print(f"\nTotal tasks to create: {len(all_tasks)}")
    
    # Split into batches of 20
    batches = []
    for i in range(0, len(all_tasks), 20):
        batches.append(all_tasks[i:i+20])
    
    print(f"Number of batches: {len(batches)}")
    
    # Output instructions for manual MCP tool calls
    print("\n" + "=" * 80)
    print("MCP Tool Call Instructions")
    print("=" * 80)
    print("\nUse mcp_openproject_bulk_create_work_packages with the following JSON strings:")
    
    for i, batch in enumerate(batches, 1):
        batch_json = json.dumps(batch)
        print(f"\n--- Batch {i} ({len(batch)} tasks) ---")
        print(f"work_packages: {batch_json[:200]}...")
        
        # Save to file for easy copy-paste
        with open(f"/tmp/batch_{i}.json", "w") as f:
            f.write(batch_json)
        print(f"Saved to /tmp/batch_{i}.json")
    
    print("\n" + "=" * 80)
    print("To create tasks, use:")
    print("mcp_openproject_bulk_create_work_packages(")
    print("    project_id=8,")
    print("    work_packages=<JSON_STRING_FROM_FILE>,")
    print("    continue_on_error=True")
    print(")")
    print("=" * 80)


if __name__ == "__main__":
    main()




