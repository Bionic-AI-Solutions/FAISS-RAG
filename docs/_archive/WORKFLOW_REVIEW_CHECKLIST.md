# Workflow Review Checklist

**Date:** 2026-01-06  
**Reviewers:** Scrum Master (SM), Product Manager (PM), Project Manager (PM)  
**Purpose:** Review the new BMAD workflow integration and ensure completeness

## Review Items

### 1. Epic-Story Lifecycle Workflow

**File:** `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`

**Checklist:**
- [ ] Epic requirements clearly defined (description, story breakdown, test story, design doc)
- [ ] Story requirements clearly defined (description, tasks, UI docs, test task)
- [ ] Task requirements clearly defined (duplicate prevention, test task naming)
- [ ] Status transitions clearly defined (immediate when conditions met)
- [ ] Document locations clearly specified
- [ ] Action owner responsibilities clearly defined
- [ ] MCP tool call examples are correct
- [ ] Integration with other workflows is clear

**Review Notes:**
- [ ] Any missing requirements?
- [ ] Any unclear instructions?
- [ ] Any conflicts with existing workflows?

### 2. Groom Story Workflow

**File:** `.cursor/rules/bmad/bmm/workflows/groom-story.mdc`

**Checklist:**
- [ ] Duplicate prevention step is clear
- [ ] Test task creation requirement is included
- [ ] Checklist includes duplicate checking
- [ ] References epic-story-lifecycle workflow
- [ ] MCP tool call examples are correct

**Review Notes:**
- [ ] Any missing steps?
- [ ] Any unclear instructions?

### 3. Dev Story with Tasks Workflow

**File:** `.cursor/rules/bmad/bmm/workflows/dev-story-with-tasks.mdc`

**Checklist:**
- [ ] Immediate status transition calls are included
- [ ] Status helper function calls are integrated
- [ ] Step-by-step workflow includes immediate parent updates
- [ ] References epic-story-lifecycle workflow
- [ ] MCP tool call examples are correct

**Review Notes:**
- [ ] Any missing steps?
- [ ] Any unclear instructions?

### 4. Status Helper Functions

**File:** `scripts/openproject_status_helpers.py`

**Checklist:**
- [ ] All required functions are present
- [ ] MCP tool call patterns are clear
- [ ] Function documentation is complete
- [ ] Status IDs are correctly defined
- [ ] Type IDs are correctly defined

**Review Notes:**
- [ ] Any missing functions?
- [ ] Any unclear implementations?

### 5. Integration Completeness

**Checklist:**
- [ ] BMAD index updated with new workflow
- [ ] All workflows reference epic-story-lifecycle where appropriate
- [ ] Supporting documentation is complete
- [ ] No conflicts with existing workflows

**Review Notes:**
- [ ] Any integration gaps?
- [ ] Any conflicts to resolve?

## Review Sign-off

**Scrum Master (SM):**
- [ ] Reviewed and approved
- [ ] Date: ___________
- [ ] Notes: ___________

**Product Manager (PM):**
- [ ] Reviewed and approved
- [ ] Date: ___________
- [ ] Notes: ___________

**Project Manager (PM):**
- [ ] Reviewed and approved
- [ ] Date: ___________
- [ ] Notes: ___________

## Action Items

After review, document any action items here:

1. _________________________________________________
2. _________________________________________________
3. _________________________________________________


