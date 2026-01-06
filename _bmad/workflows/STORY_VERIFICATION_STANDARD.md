# Story Verification Standard

## Overview

**Every story MUST have a final verification task** that validates all acceptance criteria are met and the implementation works as expected.

## Standard Verification Task

### Task Name
**Task N: Verify Story Implementation (AC: All)**

### Standard Subtasks

The verification task should include subtasks that verify:

1. **Functional Verification**
   - Verify all acceptance criteria are met
   - Verify implementation works as expected
   - Verify integration with existing systems (if applicable)

2. **Technical Verification**
   - Verify code follows architecture patterns and constraints
   - Verify error handling works correctly
   - Verify performance requirements are met (if applicable)

3. **Testing Verification**
   - Verify unit tests pass (if applicable)
   - Verify integration tests pass (if applicable)
   - Verify manual testing confirms functionality

4. **Documentation Verification**
   - Verify code is properly documented
   - Verify README/guides are updated (if applicable)
   - Verify API documentation is updated (if applicable)

### Story-Specific Verification

Each story should also include story-specific verification items based on its acceptance criteria. For example:

- **Infrastructure stories**: Verify services start, health checks pass, network connectivity works
- **API stories**: Verify endpoints work, authentication/authorization works, error handling works
- **Database stories**: Verify schema migrations work, queries perform correctly, data integrity is maintained
- **Integration stories**: Verify external services connect, data flows correctly, error handling works

## Implementation Checklist

When implementing a story:

1. ✅ Create all implementation tasks
2. ✅ Add verification task as the **final task**
3. ✅ Include standard verification subtasks
4. ✅ Include story-specific verification subtasks
5. ✅ Mark verification task complete only after all acceptance criteria are verified
6. ✅ Update story status to "done" only after verification is complete

## Example

```markdown
- [x] Task 1: Implement Feature X
  - [x] Create feature implementation
  - [x] Add error handling
  - [x] Write unit tests

- [x] Task 2: Verify Story Implementation (AC: All)
  - [x] Verify all acceptance criteria are met
  - [x] Verify feature works as expected
  - [x] Verify integration with existing systems
  - [x] Verify code follows architecture patterns
  - [x] Verify unit tests pass
  - [x] Verify error handling works correctly
  - [x] Verify documentation is updated
```

## Workflow Integration

This standard should be applied:
- When creating new stories
- When breaking down stories into tasks
- When reviewing story completion
- When updating story templates

## Test Team Validation Process

**CRITICAL: Test team validation is required before story closure**

### Task Validation

**When:** Task is marked "In testing" (status 79)

**Test Team Actions:**
1. Review task implementation
2. Run test suite for task
3. Verify acceptance criteria met
4. Verify code quality standards
5. Update task status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bug

### Story Validation

**When:** All tasks are "Closed" (82) and story is "In testing" (79)

**Prerequisites:**
- ✅ All tasks "Closed" (82)
- ✅ All bugs "Closed" (82)
- ✅ Story marked "In testing" (79) by dev

**Test Team Actions:**
1. Review all task implementations
2. Run full story test suite
3. Verify all acceptance criteria met
4. Verify integration with other stories
5. Verify code follows architecture patterns
6. Update story status:
   - **"Closed" (82)** if validation passes
   - **"Test failed" (81)** if validation fails → Create bugs

### Bug Management

**When:** Task or story validation fails

**Test Team Actions:**
1. Create bug work package in OpenProject
2. Link bug to story (parent relationship)
3. Add detailed bug description (expected vs actual, steps to reproduce, acceptance criteria violated)
4. Set bug priority (High 74, Normal 73, Low 72)
5. Assign bug to dev
6. Set bug status to "New" (71)

**Bug Fix Iteration:**
1. Dev fixes bug → Bug status "In testing" (79)
2. Test team validates fix:
   - **"Closed" (82)** if fix validated
   - **"Test failed" (81)** if fix incomplete → Iterate
3. Repeat until bug is "Closed" (82)

**Only after all bugs closed:** Story can be re-validated and closed

### Epic Closure

**Prerequisites:**
- ✅ All stories "Closed" (82)
- ✅ All tasks in all stories "Closed" (82)
- ✅ All bugs in all stories "Closed" (82)

**Test Team Actions:**
1. Verify all prerequisites
2. Run epic-level integration tests
3. Close epic (status 82)

## Notes

- Verification should be the **last task** in every story
- Verification should not be marked complete until all acceptance criteria are verified
- Story status should remain "in-progress" until verification is complete
- **Story status should be updated to "done" only after:**
  - ✅ All tasks "Closed" (82)
  - ✅ All bugs "Closed" (82)
  - ✅ Test team validation passed
  - ✅ Verification task complete


