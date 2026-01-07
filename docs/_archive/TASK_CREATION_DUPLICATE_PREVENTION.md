# Task Creation: Duplicate Prevention Guide

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW REQUIREMENT

## ⚠️ CRITICAL REMINDER

**Some stories may be in closed state and won't appear in default views. Always check for existing tasks before creating new ones to avoid duplicates.**

## Why This Matters

1. **Closed Stories Hidden**: Stories with status "Closed" won't appear in `status="open"` queries
2. **Existing Tasks**: Tasks may already exist under closed stories
3. **Duplicate Confusion**: Creating duplicates causes tracking issues and confusion
4. **Data Integrity**: Prevents duplicate task entries in OpenProject

## How to Check for Existing Tasks

### Step 1: Always Use `status="all"`

When querying OpenProject, **always use `status="all"`** to include closed stories and tasks:

```python
# ✅ CORRECT: Includes closed stories/tasks
mcp_openproject_get_work_package_children(
    parent_id=story_id,
    status="all"  # Includes closed tasks
)

# ✅ CORRECT: Includes closed work packages
mcp_openproject_list_work_packages(
    project_id=8,
    status="all"  # Includes closed stories
)

# ❌ WRONG: Will miss closed stories/tasks
mcp_openproject_get_work_package_children(
    parent_id=story_id,
    status="open"  # Will miss closed items!
)
```

### Step 2: Check by Task Subject

Before creating tasks, check if tasks with the same subject already exist:

```python
def check_existing_tasks(story_id: int, proposed_tasks: list[dict]) -> tuple:
    """
    Check for existing tasks and filter out duplicates.
    
    Returns:
        (new_tasks, existing_tasks)
    """
    # Get ALL children (including closed)
    existing_children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    
    # Extract existing task subjects
    existing_subjects = {
        task["subject"] 
        for task in existing_children.get("children", [])
    }
    
    # Separate new and existing tasks
    new_tasks = [
        task for task in proposed_tasks 
        if task["subject"] not in existing_subjects
    ]
    
    existing_tasks = [
        task for task in proposed_tasks 
        if task["subject"] in existing_subjects
    ]
    
    return new_tasks, existing_tasks
```

### Step 3: Create Only New Tasks

Only create tasks that don't already exist:

```python
def safe_create_story_tasks(story_id: int, tasks: list[dict]):
    """
    Safely create tasks, checking for duplicates first.
    """
    # Check for existing tasks
    new_tasks, existing_tasks = check_existing_tasks(story_id, tasks)
    
    if existing_tasks:
        print(f"⚠️  Found {len(existing_tasks)} existing tasks (skipping):")
        for task in existing_tasks:
            print(f"   - {task['subject']}")
    
    if not new_tasks:
        print(f"✅ All {len(tasks)} tasks already exist for story {story_id}")
        return {"created": [], "skipped": existing_tasks}
    
    print(f"📝 Creating {len(new_tasks)} new tasks")
    
    # Create only new tasks
    result = mcp_openproject_bulk_create_work_packages(
        project_id=8,
        work_packages=new_tasks,
        continue_on_error=True
    )
    
    # Set parent relationships
    for task in result.get("created", []):
        mcp_openproject_set_work_package_parent(
            work_package_id=task["id"],
            parent_id=story_id
        )
    
    return result
```

## Complete Workflow

### Before Creating Tasks

1. **Query with `status="all"`**:
   ```python
   existing = mcp_openproject_get_work_package_children(
       parent_id=story_id,
       status="all"
   )
   ```

2. **Extract existing subjects**:
   ```python
   existing_subjects = {task["subject"] for task in existing["children"]}
   ```

3. **Filter proposed tasks**:
   ```python
   new_tasks = [
       task for task in proposed_tasks 
       if task["subject"] not in existing_subjects
   ]
   ```

4. **Create only new tasks**:
   ```python
   if new_tasks:
       mcp_openproject_bulk_create_work_packages(
           project_id=8,
           work_packages=new_tasks
       )
   ```

## Helper Script

Use `scripts/check_existing_tasks.py` for reference implementation:

```bash
python3 scripts/check_existing_tasks.py
```

## Common Mistakes to Avoid

### ❌ Mistake 1: Using Default Status

```python
# ❌ WRONG: Default status may be "open"
mcp_openproject_get_work_package_children(parent_id=story_id)
```

**Fix:**
```python
# ✅ CORRECT: Explicitly use "all"
mcp_openproject_get_work_package_children(
    parent_id=story_id,
    status="all"
)
```

### ❌ Mistake 2: Not Checking Before Creation

```python
# ❌ WRONG: Creates duplicates
mcp_openproject_bulk_create_work_packages(
    project_id=8,
    work_packages=tasks  # May include duplicates!
)
```

**Fix:**
```python
# ✅ CORRECT: Check first, then create
new_tasks, existing = check_existing_tasks(story_id, tasks)
if new_tasks:
    mcp_openproject_bulk_create_work_packages(
        project_id=8,
        work_packages=new_tasks
    )
```

### ❌ Mistake 3: Assuming Story is Open

```python
# ❌ WRONG: Assumes story is open
mcp_openproject_list_work_packages(
    project_id=8,
    status="open"  # Misses closed stories!
)
```

**Fix:**
```python
# ✅ CORRECT: Check all statuses
mcp_openproject_list_work_packages(
    project_id=8,
    status="all"  # Includes closed stories
)
```

## Verification Checklist

Before creating tasks for a story:

- [ ] Query story children with `status="all"`
- [ ] Extract existing task subjects
- [ ] Compare proposed tasks with existing tasks
- [ ] Filter out duplicates
- [ ] Create only new tasks
- [ ] Verify parent relationships are set
- [ ] Confirm no duplicates were created

## Related Documentation

- **Workflow Requirement:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **PM Instructions:** `docs/PM_AGENT_INSTRUCTIONS.md`
- **Helper Script:** `scripts/check_existing_tasks.py`

## Summary

**Key Points:**

1. ⚠️ **Always use `status="all"`** when querying OpenProject
2. ⚠️ **Check for existing tasks** before creating new ones
3. ⚠️ **Filter duplicates** by task subject
4. ⚠️ **Create only new tasks** that don't already exist
5. ⚠️ **Some stories may be closed** and won't appear in default views

**Remember:** Closed stories won't appear in default views. Always check for existing tasks (including closed stories) before creating new ones to avoid duplicates.



