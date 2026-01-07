# BMAD Doctrine Integration Summary

**Date:** 2026-01-06  
**Status:** ✅ Complete  
**Purpose:** Integration of workflow requirements into BMAD doctrine

## Overview

The workflow requirements for Epic and Story lifecycle management have been integrated into the BMAD doctrine as proper workflow files, rather than standalone documentation. This ensures these rules are part of the core BMAD methodology and are automatically referenced by agents.

## What Was Integrated

### 1. New BMAD Workflow: `epic-story-lifecycle`

**Location:** `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`

**Purpose:** Defines the complete lifecycle management for Epics, Features, Stories, and Tasks in OpenProject, including:
- Epic requirements (description, story breakdown, test story, design documents)
- Story requirements (description, tasks, UI documents, test task)
- Task requirements (duplicate prevention, test task naming)
- Status transitions (immediate when conditions are met)
- Document locations
- Action owner responsibilities

**Key Features:**
- Complete MCP tool call examples
- Status transition rules with immediate execution
- Duplicate prevention for task creation
- Test story/task requirements
- Document attachment guidelines

### 2. Updated Workflow: `groom-story`

**Location:** `.cursor/rules/bmad/bmm/workflows/groom-story.mdc`

**Updates:**
- Added duplicate prevention step (check existing tasks with `status="all"`)
- Added test task creation requirement
- Updated checklist to include duplicate checking
- Added reference to `epic-story-lifecycle` workflow

### 3. Updated Workflow: `dev-story-with-tasks`

**Location:** `.cursor/rules/bmad/bmm/workflows/dev-story-with-tasks.mdc`

**Updates:**
- Added immediate status transition calls after task updates
- Integrated status helper function calls
- Updated step-by-step workflow to include immediate parent updates
- Added reference to `epic-story-lifecycle` workflow

### 4. Status Helper Functions

**Location:** `scripts/openproject_status_helpers.py`

**Purpose:** Provides template functions for action owners to update parent work package statuses immediately when child statuses change.

**Functions:**
- `update_epic_status_based_on_stories(epic_id)` - Epic status transitions
- `update_story_status_based_on_tasks(story_id)` - Story status when first task starts
- `update_story_status_when_test_task_ready(story_id, test_task_id)` - Story status when test task ready
- `update_story_status_when_all_tasks_closed(story_id)` - Story status when all tasks closed

**Note:** These functions contain pseudocode showing the MCP tool calls needed. The actual implementation uses MCP tools directly.

## Why This Approach?

### Before (Standalone Docs)
- Workflow rules in `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md`
- Quick reference in `docs/BMAD_WORKFLOW_QUICK_REFERENCE.md`
- Not automatically referenced by BMAD agents
- Had to manually reference these docs

### After (BMAD Doctrine)
- Workflow rules in `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`
- Automatically available to BMAD agents via `@bmad/bmm/workflows/epic-story-lifecycle`
- Integrated with existing workflows (`groom-story`, `dev-story-with-tasks`)
- Part of core BMAD methodology

## How to Use

### For Agents

**Reference the workflow:**
```
@bmad/bmm/workflows/epic-story-lifecycle
```

**In workflow steps:**
- PM agents creating epics/stories → Follow `epic-story-lifecycle` requirements
- PM agents grooming stories → Follow `groom-story` (which references `epic-story-lifecycle`)
- Dev agents implementing stories → Follow `dev-story-with-tasks` (which references `epic-story-lifecycle`)

### For Action Owners

**Status Transitions:**
- Call helper functions immediately after updating work package statuses
- Helper functions are in `scripts/openproject_status_helpers.py`
- See `epic-story-lifecycle` workflow for complete implementation details

**Task Creation:**
- Always check for existing tasks using `status="all"`
- Filter by subject to prevent duplicates
- See `groom-story` workflow for complete process

## Integration Points

### Workflows That Reference This

1. **create-epics-and-stories** → Should follow `epic-story-lifecycle` for epic creation
2. **groom-story** → References `epic-story-lifecycle` for task creation rules
3. **dev-story-with-tasks** → References `epic-story-lifecycle` for status transitions
4. **test-validation** → Should follow `epic-story-lifecycle` for story/epic closure

### Supporting Documentation

These docs remain for detailed reference but are now secondary to the BMAD doctrine:

- `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md` - Detailed requirements (reference)
- `docs/BMAD_WORKFLOW_QUICK_REFERENCE.md` - Quick reference guide (reference)
- `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md` - Task creation details (reference)
- `docs/TASK_CREATION_DUPLICATE_PREVENTION.md` - Duplicate prevention guide (reference)

## Next Steps

1. ✅ **Integration Complete** - Workflow rules integrated into BMAD doctrine
2. ⏳ **Review by SM, PM, PM** - Review the new workflow files
3. ⏳ **Update Existing Epics/Stories** - Apply requirements where applicable (without retroactively creating Features)
4. ⏳ **Train Action Owners** - Ensure everyone understands immediate status transition responsibilities

## Benefits

1. **Automatic Reference** - BMAD agents automatically have access to these rules
2. **Consistency** - All workflows follow the same lifecycle rules
3. **Maintainability** - Single source of truth in BMAD doctrine
4. **Integration** - Works seamlessly with existing BMAD workflows
5. **Discoverability** - Part of BMAD index and workflow system

## Files Changed

### New Files
- `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc` - Core lifecycle workflow

### Updated Files
- `.cursor/rules/bmad/bmm/workflows/groom-story.mdc` - Added duplicate prevention
- `.cursor/rules/bmad/bmm/workflows/dev-story-with-tasks.mdc` - Added immediate status transitions
- `scripts/openproject_status_helpers.py` - Updated with MCP tool call patterns

### Reference Files (Unchanged)
- `docs/BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md` - Detailed reference
- `docs/BMAD_WORKFLOW_QUICK_REFERENCE.md` - Quick reference
- `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md` - Task creation details
- `docs/TASK_CREATION_DUPLICATE_PREVENTION.md` - Duplicate prevention

---

**Summary:** Workflow requirements are now part of the BMAD doctrine, ensuring they're automatically available to all BMAD agents and integrated with existing workflows.


