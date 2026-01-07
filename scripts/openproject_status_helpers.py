#!/usr/bin/env python3
"""
OpenProject Status Transition Helper Functions

These functions help action owners update parent work package statuses
immediately when child work package statuses change.

**USAGE:** These functions are called by action owners (PM, Dev, Test Team) 
immediately after updating work package statuses using OpenProject MCP tools.

**MCP TOOL CALLS:** These functions use the following MCP tools:
- mcp_openproject_get_work_package_children
- mcp_openproject_get_work_package
- mcp_openproject_update_work_package
- mcp_openproject_get_work_package_hierarchy (for epic updates)

**STATUS TRANSITIONS:** All transitions are IMMEDIATE when conditions are met.
"""

# Status IDs
STATUS_NEW = 71
STATUS_IN_PROGRESS = 77
STATUS_IN_TESTING = 79
STATUS_CLOSED = 82

# Type IDs
TYPE_EPIC = 40
TYPE_FEATURE = 39
TYPE_USER_STORY = 41
TYPE_TASK = 36
TYPE_BUG = 42


def update_epic_status_based_on_stories(epic_id: int):
    """
    Update epic status based on story statuses.
    Call this IMMEDIATELY whenever a story status changes.
    
    Action Owner: Person updating story status (PM, Dev, or Test Team)
    
    Status Transitions:
    - Epic → "In progress" (77): When first story moves to "In progress" (77) - IMMEDIATE
    - Epic → "Closed" (82): When last story is closed (82) - IMMEDIATE
    
    Args:
        epic_id: OpenProject work package ID for the epic
    
    MCP Tool Calls:
        - mcp_openproject_get_work_package_children(parent_id=epic_id, status="all")
        - mcp_openproject_get_work_package(work_package_id=epic_id)
        - mcp_openproject_update_work_package(work_package_id=epic_id, status_id=...)
    """
    # Step 1: Get all stories for epic (including closed)
    # MCP call:
    # children = mcp_openproject_get_work_package_children(
    #     parent_id=epic_id,
    #     status="all"  # Include closed stories
    # )
    # stories = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_USER_STORY]
    
    # Step 2: Check if any story is in progress
    # any_in_progress = any(s["status"]["id"] == STATUS_IN_PROGRESS for s in stories)
    
    # Step 3: Get current epic status
    # epic = mcp_openproject_get_work_package(work_package_id=epic_id)
    # current_status_id = epic["work_package"]["status"]["id"]
    
    # Step 4: Update epic to "In progress" if first story started
    # if any_in_progress and current_status_id != STATUS_IN_PROGRESS:
    #     mcp_openproject_update_work_package(
    #         work_package_id=epic_id,
    #         status_id=STATUS_IN_PROGRESS,
    #         comment="Epic in progress: First story has started."
    #     )
    
    # Step 5: Check if all stories are closed
    # all_closed = all(s["status"]["id"] == STATUS_CLOSED for s in stories) if stories else False
    
    # Step 6: Update epic to "Closed" if all stories closed
    # if all_closed and current_status_id != STATUS_CLOSED:
    #     mcp_openproject_update_work_package(
    #         work_package_id=epic_id,
    #         status_id=STATUS_CLOSED,
    #         comment="Epic closed: All stories are closed."
    #     )
    
    print(f"⚠️  Template function - implement with MCP tools")
    print(f"   Epic ID: {epic_id}")
    print(f"   Action: Check story statuses and update epic status if conditions met")
    print(f"   See epic-story-lifecycle workflow for complete implementation")


def update_story_status_based_on_tasks(story_id: int):
    """
    Update story status based on task statuses.
    Call this IMMEDIATELY whenever a task status changes.
    
    Action Owner: Person updating task status (Dev)
    
    Status Transitions:
    - Story → "In progress" (77): When first task moves to "In progress" (77) - IMMEDIATE
    
    Args:
        story_id: OpenProject work package ID for the story
    
    MCP Tool Calls:
        - mcp_openproject_get_work_package_children(parent_id=story_id, status="all")
        - mcp_openproject_get_work_package(work_package_id=story_id)
        - mcp_openproject_update_work_package(work_package_id=story_id, status_id=...)
    """
    # Step 1: Get all tasks for story (including closed)
    # MCP call:
    # children = mcp_openproject_get_work_package_children(
    #     parent_id=story_id,
    #     status="all"  # Include closed tasks
    # )
    # tasks = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_TASK]
    
    # Step 2: Check if any task is in progress
    # any_in_progress = any(t["status"]["id"] == STATUS_IN_PROGRESS for t in tasks) if tasks else False
    
    # Step 3: Get current story status
    # story = mcp_openproject_get_work_package(work_package_id=story_id)
    # current_status_id = story["work_package"]["status"]["id"]
    
    # Step 4: Update story to "In progress" if first task started
    # if any_in_progress and current_status_id != STATUS_IN_PROGRESS:
    #     mcp_openproject_update_work_package(
    #         work_package_id=story_id,
    #         status_id=STATUS_IN_PROGRESS,
    #         comment="Story in progress: First task has started."
    #     )
    
    print(f"⚠️  Template function - implement with MCP tools")
    print(f"   Story ID: {story_id}")
    print(f"   Action: Check task statuses and update story status if conditions met")
    print(f"   See epic-story-lifecycle workflow for complete implementation")


def update_story_status_when_test_task_ready(story_id: int, test_task_id: int = None):
    """
    Update story status to "In testing" when test task is ready.
    Call this IMMEDIATELY when test task moves to "In testing" (79).
    
    Action Owner: Person updating test task status (Dev)
    
    Status Transitions:
    - Story → "In testing" (79): When test task moves to "In testing" (79) AND all other tasks closed - IMMEDIATE
    
    Args:
        story_id: OpenProject work package ID for the story
        test_task_id: Optional test task ID. If not provided, will search for task with ".T:" in subject
    
    MCP Tool Calls:
        - mcp_openproject_get_work_package_children(parent_id=story_id, status="all")
        - mcp_openproject_get_work_package(work_package_id=story_id)
        - mcp_openproject_get_work_package(work_package_id=test_task_id) if test_task_id provided
        - mcp_openproject_update_work_package(work_package_id=story_id, status_id=...)
    """
    # Step 1: Get all tasks for story
    # children = mcp_openproject_get_work_package_children(
    #     parent_id=story_id,
    #     status="all"
    # )
    # tasks = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_TASK]
    
    # Step 2: Find test task
    # if test_task_id:
    #     test_task = next((t for t in tasks if t["id"] == test_task_id), None)
    # else:
    #     # Search for task with ".T:" in subject or "Testing and Validation"
    #     test_task = next(
    #         (t for t in tasks if ".T:" in t["subject"] or "Testing and Validation" in t["subject"]),
    #         None
    #     )
    
    # Step 3: Check if test task is in testing
    # if not test_task or test_task["status"]["id"] != STATUS_IN_TESTING:
    #     return  # Test task not ready
    
    # Step 4: Check if all other tasks are closed
    # other_tasks = [t for t in tasks if t["id"] != test_task["id"]]
    # all_other_tasks_closed = all(t["status"]["id"] == STATUS_CLOSED for t in other_tasks)
    
    # Step 5: Get current story status
    # story = mcp_openproject_get_work_package(work_package_id=story_id)
    # current_status_id = story["work_package"]["status"]["id"]
    
    # Step 6: Update story to "In testing" if conditions met
    # if all_other_tasks_closed and current_status_id != STATUS_IN_TESTING:
    #     mcp_openproject_update_work_package(
    #         work_package_id=story_id,
    #         status_id=STATUS_IN_TESTING,
    #         comment="Story in testing: Test task ready and all other tasks closed."
    #     )
    
    print(f"⚠️  Template function - implement with MCP tools")
    print(f"   Story ID: {story_id}")
    print(f"   Test Task ID: {test_task_id}")
    print(f"   Action: Check test task status and update story status if conditions met")
    print(f"   See epic-story-lifecycle workflow for complete implementation")


def update_story_status_when_all_tasks_closed(story_id: int):
    """
    Update story status to "Closed" when all tasks are closed.
    Call this IMMEDIATELY whenever a task or bug is closed.
    
    Action Owner: Person closing task/bug (Dev or Test Team)
    
    Status Transitions:
    - Story → "Closed" (82): When all tasks and bugs closed - IMMEDIATE
    - Also triggers epic status update if all stories in epic are closed
    
    Args:
        story_id: OpenProject work package ID for the story
    
    MCP Tool Calls:
        - mcp_openproject_get_work_package_children(parent_id=story_id, status="all")
        - mcp_openproject_get_work_package(work_package_id=story_id)
        - mcp_openproject_get_work_package_hierarchy(work_package_id=story_id) to get epic
        - mcp_openproject_update_work_package(work_package_id=story_id, status_id=...)
        - mcp_openproject_update_work_package(work_package_id=epic_id, status_id=...) if epic should close
    """
    # Step 1: Get all tasks and bugs for story
    # children = mcp_openproject_get_work_package_children(
    #     parent_id=story_id,
    #     status="all"
    # )
    # tasks = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_TASK]
    # bugs = [c for c in children.get("children", []) if c["type"]["id"] == TYPE_BUG]
    
    # Step 2: Check if all tasks and bugs are closed
    # all_tasks_closed = all(t["status"]["id"] == STATUS_CLOSED for t in tasks) if tasks else True
    # all_bugs_closed = all(b["status"]["id"] == STATUS_CLOSED for b in bugs) if bugs else True
    
    # Step 3: Get current story status
    # story = mcp_openproject_get_work_package(work_package_id=story_id)
    # current_status_id = story["work_package"]["status"]["id"]
    
    # Step 4: Update story to "Closed" if all tasks and bugs closed
    # if all_tasks_closed and all_bugs_closed and current_status_id != STATUS_CLOSED:
    #     mcp_openproject_update_work_package(
    #         work_package_id=story_id,
    #         status_id=STATUS_CLOSED,
    #         comment="Story closed: All tasks and bugs are closed."
    #     )
    
    # Step 5: Trigger epic status update if story closed
    # if all_tasks_closed and all_bugs_closed:
    #     # Get epic from story hierarchy
    #     hierarchy = mcp_openproject_get_work_package_hierarchy(work_package_id=story_id)
    #     ancestors = hierarchy.get("ancestors", [])
    #     epic = next((a for a in ancestors if a["type"]["id"] == TYPE_EPIC), None)
    #     if epic:
    #         update_epic_status_based_on_stories(epic["id"])
    
    print(f"⚠️  Template function - implement with MCP tools")
    print(f"   Story ID: {story_id}")
    print(f"   Action: Check all tasks/bugs closed and update story status if conditions met")
    print(f"   See epic-story-lifecycle workflow for complete implementation")


if __name__ == "__main__":
    print("=" * 80)
    print("OpenProject Status Transition Helper Functions")
    print("=" * 80)
    print()
    print("These functions help action owners update parent work package statuses")
    print("immediately when child work package statuses change.")
    print()
    print("Usage:")
    print("  Call these functions IMMEDIATELY after updating work package statuses")
    print("  using OpenProject MCP tools.")
    print()
    print("Functions:")
    print("  - update_epic_status_based_on_stories(epic_id)")
    print("  - update_story_status_based_on_tasks(story_id)")
    print("  - update_story_status_when_test_task_ready(story_id, test_task_id)")
    print("  - update_story_status_when_all_tasks_closed(story_id)")
    print()
    print("Implementation:")
    print("  These functions contain pseudocode showing the MCP tool calls needed.")
    print("  See .cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc")
    print("  for complete implementation details.")
    print()
    print("=" * 80)
