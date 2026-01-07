# Task Creation: Duplicate Issue Report

**Date:** 2026-01-06  
**Status:** ⚠️ DUPLICATES DETECTED

## Issue Summary

During bulk task creation for Epic 5 stories, duplicates were created because existing tasks were not checked first. The stories were in "In testing" status, which may not appear in default views.

## Affected Stories

### Story 5.2: User Memory Retrieval MCP Tool (ID: 141)
- **Status:** "In testing" (79)
- **Existing Tasks:** 7 tasks (IDs: 334-340)
- **New Tasks Created:** 8 tasks (IDs: 473-480)
- **Total:** 15 tasks (should be 8)
- **Duplicates:** 7 duplicate tasks created

### Story 5.3: User Memory Update MCP Tool (ID: 142)
- **Status:** Unknown (needs verification)
- **Existing Tasks:** 8 tasks (IDs: 341-348)
- **New Tasks Created:** 8 tasks (IDs: 481-488)
- **Total:** 16 tasks (should be 8)
- **Duplicates:** 8 duplicate tasks created

### Story 5.4: User Memory Search MCP Tool (ID: 143)
- **Status:** Unknown (needs verification)
- **Existing Tasks:** 8 tasks (IDs: 349-356)
- **New Tasks Created:** 8 tasks (IDs: 489-496)
- **Total:** 16 tasks (should be 8)
- **Duplicates:** 8 duplicate tasks created

## Root Cause

1. **Didn't check for existing tasks** before creating new ones
2. **Stories were in "In testing" status** - may not appear in default "open" views
3. **Didn't use `status="all"`** when checking for existing tasks
4. **Bulk creation script** didn't include duplicate checking logic

## Resolution Required

### Option 1: Delete Duplicate Tasks (Recommended)

Delete the newly created duplicate tasks (IDs: 473-480, 481-488, 489-496) and keep the original tasks (IDs: 334-340, 341-348, 349-356).

**Rationale:** Original tasks may have been worked on or have comments/history.

### Option 2: Keep New Tasks, Delete Old Ones

If the new tasks have better descriptions or are more complete, delete the old tasks and keep the new ones.

**Rationale:** New tasks may have more detailed descriptions matching current requirements.

### Option 3: Merge Tasks

Manually review and merge task information, keeping the best version of each task.

**Rationale:** Preserve any work/comments from original tasks while keeping updated descriptions.

## Prevention Measures Implemented

1. ✅ Updated workflow documentation to always check for existing tasks
2. ✅ Created `docs/TASK_CREATION_DUPLICATE_PREVENTION.md` guide
3. ✅ Created `scripts/check_existing_tasks.py` helper script
4. ✅ Updated all workflow docs to emphasize using `status="all"`

## Lessons Learned

1. **Always check for existing tasks first** - even if story appears to have no tasks
2. **Use `status="all"`** when querying OpenProject to include closed/in-testing stories
3. **Check by task subject** before creating to avoid duplicates
4. **Stories in "In testing" or "Closed" status** won't appear in default views

## Action Items

- [ ] Review duplicate tasks for Stories 5.2, 5.3, 5.4
- [ ] Decide which set of tasks to keep (old vs new)
- [ ] Delete duplicate tasks from OpenProject
- [ ] Verify no other stories have duplicate tasks
- [ ] Update task creation scripts to always check first

## Verification

To verify other stories don't have duplicates:

```python
# Check all stories we created tasks for
stories_to_check = [
    389, 390, 391, 392, 393,  # Epic 3
    394, 395, 396, 398,       # Epic 4
    141, 142, 143,            # Epic 5 (known duplicates)
    150, 151, 152, 153,       # Epic 7
    155, 156, 157, 158, 159,  # Epic 8
    161, 162, 163, 164, 165, 166, 167, 168, 169  # Epic 9
]

for story_id in stories_to_check:
    children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    # Check for duplicate subjects
    subjects = [task["subject"] for task in children["children"]]
    duplicates = [s for s in subjects if subjects.count(s) > 1]
    if duplicates:
        print(f"⚠️  Story {story_id} has duplicate tasks: {duplicates}")
```



