#!/usr/bin/env python3
"""
Create all tasks in OpenProject using MCP tools.

This script reads task definitions from create_all_missing_tasks.py
and creates them in OpenProject using bulk_create_work_packages.
"""

import json
import sys
from create_all_missing_tasks import create_epic3_tasks, create_epic4_tasks, create_epic5_tasks

# Batch size for bulk creation
BATCH_SIZE = 20

def create_tasks_batch(tasks_batch: list, batch_num: int) -> dict:
    """Create a batch of tasks using MCP tool."""
    # Remove status_id from tasks (not accepted during creation)
    tasks_for_creation = []
    for task in tasks_batch:
        task_copy = task.copy()
        task_copy.pop("status_id", None)  # Remove status_id
        tasks_for_creation.append(task_copy)
    
    # Convert to JSON string for MCP tool
    tasks_json = json.dumps(tasks_for_creation)
    
    print(f"\nBatch {batch_num}: Creating {len(tasks_for_creation)} tasks...")
    print(f"First task: {tasks_for_creation[0]['subject']}")
    print(f"Last task: {tasks_for_creation[-1]['subject']}")
    
    # Note: This would need to be called via MCP tool
    # For now, we'll output the JSON for manual execution
    return {
        "batch_num": batch_num,
        "tasks": tasks_for_creation,
        "json": tasks_json
    }


def main():
    """Main execution function."""
    print("=" * 80)
    print("Preparing Tasks for OpenProject Creation")
    print("=" * 80)
    
    # Get all tasks
    all_tasks = []
    all_tasks.extend(create_epic3_tasks())
    all_tasks.extend(create_epic4_tasks())
    all_tasks.extend(create_epic5_tasks())
    
    print(f"\nTotal tasks: {len(all_tasks)}")
    
    # Split into batches
    batches = []
    for i in range(0, len(all_tasks), BATCH_SIZE):
        batch = all_tasks[i:i + BATCH_SIZE]
        batches.append(batch)
    
    print(f"Number of batches: {len(batches)}")
    print(f"Batch size: {BATCH_SIZE}")
    
    # Prepare batches for creation
    print("\n" + "=" * 80)
    print("Task Batches Ready for Creation")
    print("=" * 80)
    
    for i, batch in enumerate(batches, 1):
        batch_info = create_tasks_batch(batch, i)
        print(f"\nBatch {i} JSON (first 500 chars):")
        print(batch_info["json"][:500] + "..." if len(batch_info["json"]) > 500 else batch_info["json"])
    
    print("\n" + "=" * 80)
    print("To create these tasks, use mcp_openproject_bulk_create_work_packages")
    print("with each batch's JSON string.")
    print("=" * 80)
    
    # Output all batches as JSON for easy copy-paste
    all_batches_json = json.dumps([batch_info["json"] for batch_info in [create_tasks_batch(batch, i+1) for i, batch in enumerate(batches)]], indent=2)
    
    with open("/tmp/task_batches.json", "w") as f:
        f.write(all_batches_json)
    
    print(f"\nAll batches saved to /tmp/task_batches.json")
    print(f"Total tasks to create: {len(all_tasks)}")


if __name__ == "__main__":
    main()




