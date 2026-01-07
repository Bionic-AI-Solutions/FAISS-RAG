# How BMAD Agents Use `docs/` Directory

**Date:** 2026-01-07  
**Purpose:** Clarify whether BMAD agents automatically read `docs/` files or if they're only for human reference

## Answer: Primarily Human Reference, Can Be Explicitly Loaded

### TL;DR

- ❌ **BMAD agents do NOT automatically load `docs/` files**
- ✅ **`docs/` files are primarily for human reference and record keeping**
- ✅ **Agents CAN load `docs/` files IF workflow step explicitly instructs them to**
- ✅ **Workflow references to `docs/` are documentation links for humans**

## Evidence from BMAD Framework

### Agent Loading Rules

**From all BMAD agents (`_bmad/bmm/agents/*.md`):**

```xml
<rules>
  <r>Load files ONLY when executing a user chosen workflow or a command requires it,
     EXCEPTION: agent activation step 2 config.yaml</r>
</rules>
```

**This means:**

- ✅ `_bmad/bmm/config.yaml` - Automatically loaded during agent activation
- ❌ `docs/TESTING_STRATEGY.md` - NOT automatically loaded
- ✅ `docs/TESTING_STRATEGY.md` - CAN be loaded if workflow step says to read it

### What Agents Automatically Load

**During Agent Activation:**

1. ✅ Agent persona (from `_bmad/bmm/agents/{agent}.md`)
2. ✅ Config file (`_bmad/bmm/config.yaml`) - **MANDATORY**
3. ✅ Project context (`**/project-context.md`) - If exists
4. ✅ Documentation standards (`_bmad/bmm/data/documentation-standards.md`) - For tech writer

**During Workflow Execution:**

1. ✅ Workflow files (`_bmad/bmm/workflows/{workflow}/workflow.yaml`)
2. ✅ Step files (`_bmad/bmm/workflows/{workflow}/steps/step-*.md`)
3. ✅ Templates (`_bmad/bmb/docs/workflows/templates/*.md`)
4. ✅ Data files (if specified in workflow)

**NOT Automatically Loaded:**

- ❌ Files from `docs/` directory
- ❌ Verification documents (`docs/STORY_*_VERIFICATION.md`)
- ❌ Project status documents (`docs/PROJECT_STATUS_*.md`)
- ❌ Testing strategy (`docs/TESTING_STRATEGY.md`)

### How `docs/` Files Are Referenced

#### Pattern 1: Workflow References Section

**In workflow YAML files:**

```yaml
## REFERENCES

- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
```

**Purpose:** Documentation links for **humans** reading the workflow

**Not:** Automatic loading instructions for agents

#### Pattern 2: Explicit Workflow Instructions

**If a workflow step explicitly says:**

```markdown
## Step 5: Review Testing Requirements

1. Read `docs/TESTING_STRATEGY.md`
2. Verify unit tests and integration tests are created
3. ...
```

**Then:** Agent WILL load and read the file

**But:** This is explicit instruction, not automatic

#### Pattern 3: Cursor Rules References

**In `.cursor/rules/bmad/bmm/workflows/*.mdc` files:**

```markdown
## References

- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
```

**Purpose:** Documentation links for **humans** using Cursor

**Not:** Automatic loading instructions

## Examples from Codebase

### Example 1: Test Validation Workflow

**File:** `_bmad/bmm/workflows/4-implementation/test-validation/workflow.yaml`

```yaml
## REFERENCES

- **Story Verification Standard:** `_bmad/workflows/STORY_VERIFICATION_STANDARD.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **Task Management:** `docs/TASK_MANAGEMENT_PROCESS.md`
```

**Analysis:**

- `_bmad/workflows/STORY_VERIFICATION_STANDARD.md` - Framework file (can be loaded)
- `docs/QA_TESTING_WORKFLOW.md` - Project doc (reference for humans)

### Example 2: Dev Agent Activation

**File:** `_bmad/bmm/agents/dev.md`

```xml
<step n="4">READ the entire story file BEFORE any implementation</step>
<step n="5">Load project-context.md if available for coding standards only</step>
```

**Analysis:**

- Story file - Explicitly instructed to read
- `project-context.md` - Explicitly instructed to load (if exists)
- `docs/TESTING_STRATEGY.md` - NOT mentioned, so NOT loaded

### Example 3: Workflow Step That Could Load docs/

**Hypothetical workflow step:**

```markdown
## Step 3: Verify Testing Requirements

1. Read `docs/TESTING_STRATEGY.md` to understand project testing requirements
2. Verify unit tests exist in `tests/unit/`
3. Verify integration tests exist in `tests/integration/`
```

**If this exists:** Agent WOULD load `docs/TESTING_STRATEGY.md`

**Current state:** No workflow steps explicitly instruct loading `docs/` files

## Impact on Recent Documentation

### Testing Documentation Created

**Files:**

- `docs/TESTING_STRATEGY.md`
- `docs/TESTING_PRINCIPLES.md` (updated)
- `docs/QA_TESTING_WORKFLOW.md` (updated)
- `docs/COMPLETE_AGILE_WORKFLOW.md` (updated)

### How They're Used

**Primary Usage:**

1. ✅ **Human reference** - Developers, test team, PM read these
2. ✅ **Record keeping** - Project requirements documented
3. ✅ **Workflow references** - Listed in workflow YAML "REFERENCES" sections
4. ✅ **OpenProject attachments** - Attached to work packages for traceability

**Agent Usage:**

- ❌ **NOT automatically loaded** by BMAD agents
- ✅ **CAN be loaded** if workflow step explicitly says to read them
- ✅ **Referenced** in workflow documentation for human guidance

## Recommendations

### For Maximum Agent Usage

**If you want agents to read `docs/` files:**

1. **Add explicit workflow steps:**

   ```markdown
   ## Step: Verify Testing Requirements

   Read `docs/TESTING_STRATEGY.md` and verify:

   - Unit tests exist
   - Integration tests exist
   ```

2. **Update workflow YAML:**

   ```yaml
   steps:
     - file: steps/step-verify-testing.md
       instructions:
         - Read docs/TESTING_STRATEGY.md
         - Verify requirements met
   ```

3. **Add to agent activation:**
   ```xml
   <step n="X">Load docs/TESTING_STRATEGY.md for project testing requirements</step>
   ```

### Current State (No Changes Needed)

**Current usage is appropriate:**

- ✅ `docs/` files serve as human reference
- ✅ Workflow references guide humans
- ✅ Agents follow BMAD framework patterns
- ✅ Project-specific requirements documented for humans

## Conclusion

**`docs/` directory is primarily for:**

- ✅ Human reference and understanding
- ✅ Record keeping and traceability
- ✅ Project-specific requirements documentation
- ✅ Workflow documentation references

**`docs/` directory is NOT:**

- ❌ Automatically loaded by BMAD agents
- ❌ Part of the BMAD framework
- ❌ Required for agent execution

**Agents CAN read `docs/` files:**

- ✅ If workflow step explicitly instructs
- ✅ If agent activation step explicitly instructs
- ✅ If user explicitly requests

**This is the correct pattern** - `docs/` serves as project documentation for humans, while `_bmad/` serves as the executable framework for agents.

