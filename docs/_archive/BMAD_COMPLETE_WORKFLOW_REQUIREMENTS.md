# BMAD Complete Workflow Requirements

**Last Updated:** 2026-01-06  
**Status:** MANDATORY WORKFLOW  
**Review Required By:** Scrum Master, Product Manager, Project Manager

## Overview

This document defines the complete BMAD workflow requirements for Epic and Story management in OpenProject, ensuring comprehensive documentation, proper status transitions, and quality gates at every level.

## Work Package Hierarchy

```
Project
└── Epic (type_id=40)
    └── Feature (type_id=39, if present) [OPTIONAL but RECOMMENDED]
        └── User Story (type_id=41)
            └── Task (type_id=36) / Bug (type_id=42)
```

**CRITICAL:** Maintain this hierarchy using OpenProject parent-child relationships.

**Note on Features:**
- Features are **recommended** for breaking down epics into sizable, testable chunks
- For **new epics going forward**, use Features when appropriate
- For **existing epics**, do NOT retroactively create Features (to avoid wasting time)
- Features help organize stories and provide intermediate validation points

---

## EPIC Requirements

### 1. High-Level Description and Important Aspects

**Requirement:** Every Epic MUST have a comprehensive description in OpenProject that includes:

- **Business Goal:** What business value does this epic deliver?
- **Scope:** What is included and excluded?
- **Success Criteria:** How do we know the epic is successful?
- **Dependencies:** What other epics or systems does this depend on?
- **Technical Considerations:** High-level technical approach
- **Timeline:** Expected duration and milestones

**Implementation:**

```python
epic = mcp_openproject_create_work_package(
    project_id=8,
    subject="Epic X: [Epic Name]",
    type_id=40,  # Epic
    description="""
    ## Business Goal
    [Clear statement of business value]
    
    ## Scope
    **Included:**
    - [Feature/functionality included]
    
    **Excluded:**
    - [Feature/functionality explicitly excluded]
    
    ## Success Criteria
    - [Measurable success criteria]
    
    ## Dependencies
    - [List of dependencies]
    
    ## Technical Considerations
    - [High-level technical approach]
    
    ## Timeline
    - Start: [Date]
    - Expected Completion: [Date]
    """,
    priority_id=74  # High
)
```

### 2. Story Breakdown Detailing Complete Functionality

**Requirement:** Epic description MUST include a complete story breakdown that details:

- **All Stories:** List of all stories in the epic
- **Story Goals:** What each story accomplishes
- **Story Dependencies:** Order and dependencies between stories
- **Complete Functionality:** How stories combine to deliver epic goals

**Implementation:**

```python
# Update epic description with story breakdown
mcp_openproject_update_work_package(
    work_package_id=epic_id,
    description=f"""
    {existing_description}
    
    ## Story Breakdown
    
    ### Story X.1: [Story Name]
    **Goal:** [What this story accomplishes]
    **Dependencies:** [None or list of prerequisite stories]
    **Functionality:** [What functionality this story delivers]
    
    ### Story X.2: [Story Name]
    **Goal:** [What this story accomplishes]
    **Dependencies:** [Story X.1]
    **Functionality:** [What functionality this story delivers]
    
    ...
    
    ## Complete Epic Functionality
    
    When all stories are complete, this epic delivers:
    - [Complete functionality 1]
    - [Complete functionality 2]
    - [Complete functionality 3]
    """
)
```

### 3. Epic Status Automation

**Requirement:** Epic status MUST automatically transition based on story statuses:

- **Epic → "In progress" (77):** When first story moves to "In progress" (77) - **IMMEDIATE**
- **Epic → "Closed" (82):** When last story is closed (82) - **IMMEDIATE**

**Implementation:**

**Action Owner Responsibility:** The person updating the story status MUST call this function immediately after updating story status.

```python
def update_epic_status_based_on_stories(epic_id: int):
    """
    Update epic status based on story statuses.
    Call this IMMEDIATELY whenever a story status changes.
    
    Action Owner: Person updating story status (PM, Dev, or Test Team)
    """
    # Get all stories for epic
    children = mcp_openproject_get_work_package_children(
        parent_id=epic_id,
        status="all"
    )
    stories = [c for c in children["children"] if c["type"] == "User story"]
    
    if not stories:
        return
    
    # Check if any story is "In progress"
    any_in_progress = any(
        story["status"] == "In progress" 
        for story in stories
    )
    
    # Check if all stories are "Closed"
    all_closed = all(
        story["status"] == "Closed" 
        for story in stories
    )
    
    epic = mcp_openproject_get_work_package(work_package_id=epic_id)
    current_status = epic["work_package"]["status"]["name"]
    
    # Update epic status IMMEDIATELY when conditions are met
    if all_closed and current_status != "Closed":
        # Epic closes when last story closes - IMMEDIATE
        mcp_openproject_update_work_package(
            work_package_id=epic_id,
            status_id=82,  # Closed
            comment="Epic closed: All stories are closed."
        )
    elif any_in_progress and current_status == "New":
        # Epic moves to "In progress" when first story moves to "In progress" - IMMEDIATE
        mcp_openproject_update_work_package(
            work_package_id=epic_id,
            status_id=77,  # In progress
            comment="Epic in progress: First story has started."
        )
```

**When to Call (Action Owner Responsibility):**
- **PM/Dev:** After updating story status to "In progress" (77) → Call immediately
- **Test Team:** After closing story (82) → Call immediately
- **Any Status Change:** After any story status change → Check and update epic status if needed

### 4. Epic Test Story

**Requirement:** Every Epic MUST have a dedicated test story for validating the complete epic functionality.

**Test Story Requirements:**
- **Subject:** "Test Story X: Epic X Validation"
- **Type:** User Story (type_id=41)
- **Description:** Comprehensive test plan for epic validation
- **Parent:** Epic (not a feature)
- **Tasks:** Include tasks for:
  - Epic integration testing
  - End-to-end scenario validation
  - Performance validation
  - Security validation
  - Documentation validation

**Implementation:**

```python
# Create epic test story
test_story = mcp_openproject_create_work_package(
    project_id=8,
    subject="Test Story X: Epic X Validation",
    type_id=41,  # User Story
    description="""
    As a **Test Team**,
    I want **to validate the complete Epic X functionality**,
    So that **I can ensure all epic goals are met and the epic is ready for production**.
    
    **Acceptance Criteria:**
    
    **Given** All stories in Epic X are complete
    **When** I run epic-level integration tests
    **Then** All integration tests pass
    **And** All end-to-end scenarios pass
    **And** Performance requirements are met
    **And** Security requirements are met
    **And** Documentation is complete
    **And** Epic verification document is created and attached
    
    **Test Scenarios:**
    1. [End-to-end scenario 1]
    2. [End-to-end scenario 2]
    3. [Performance scenario]
    4. [Security scenario]
    
    **Validation Checklist:**
    - [ ] All stories closed
    - [ ] All tasks in all stories closed
    - [ ] All bugs in all stories closed
    - [ ] Integration tests pass
    - [ ] End-to-end tests pass
    - [ ] Performance tests pass
    - [ ] Security tests pass
    - [ ] Documentation complete
    - [ ] Epic verification document attached
    """,
    priority_id=74  # High
)

# Link to epic
mcp_openproject_set_work_package_parent(
    work_package_id=test_story["work_package"]["id"],
    parent_id=epic_id
)

# Create test story tasks
test_tasks = [
    {
        "subject": "Task X.T.1: Epic Integration Testing",
        "type_id": 36,
        "description": "Run integration tests across all stories in epic..."
    },
    {
        "subject": "Task X.T.2: End-to-End Scenario Validation",
        "type_id": 36,
        "description": "Validate end-to-end user scenarios..."
    },
    {
        "subject": "Task X.T.3: Performance Validation",
        "type_id": 36,
        "description": "Validate performance requirements..."
    },
    {
        "subject": "Task X.T.4: Security Validation",
        "type_id": 36,
        "description": "Validate security requirements..."
    },
    {
        "subject": "Task X.T.5: Create Epic Verification Document",
        "type_id": 36,
        "description": "Create and attach epic verification document..."
    }
]

# Create tasks
for task in test_tasks:
    created_task = mcp_openproject_create_work_package(
        project_id=8,
        **task
    )
    mcp_openproject_set_work_package_parent(
        work_package_id=created_task["work_package"]["id"],
        parent_id=test_story["work_package"]["id"]
    )
```

### 5. High-Level Design and Implementation Document

**Requirement:** Every Epic MUST have a high-level design and implementation document attached to the Epic work package in OpenProject.

**Document Requirements:**
- **Location:** `_bmad-output/planning-artifacts/epic-X-design.md` or `_bmad-output/epic-X-design.md`
- **Content:**
  - Architecture overview
  - Component design
  - Data flow diagrams
  - API design (if applicable)
  - Database schema (if applicable)
  - Integration points
  - Security considerations
  - Performance considerations
- **Attachment:** Document MUST be attached to Epic work package in OpenProject
- **CRITICAL:** Never create duplicate documentation - use existing documents in `_bmad-output/` and attach as needed

**Implementation:**

```python
import base64
from pathlib import Path

# Create design document
design_doc_path = Path("_bmad-output/planning-artifacts/epic-X-design.md")
design_doc_path.write_text("""
# Epic X: Design and Implementation Document

## Architecture Overview
[Architecture description]

## Component Design
[Component descriptions]

## Data Flow
[Data flow diagrams]

## API Design
[API specifications]

## Database Schema
[Schema design]

## Integration Points
[Integration details]

## Security Considerations
[Security design]

## Performance Considerations
[Performance design]
""")

# Attach to epic
with open(design_doc_path, "rb") as f:
    doc_content = base64.b64encode(f.read()).decode("utf-8")

mcp_openproject_add_work_package_attachment(
    work_package_id=epic_id,
    file_data=doc_content,
    filename="epic-X-design.md",
    content_type="text/markdown",
    description="High-level design and implementation document for Epic X"
)
```

---

## STORY Requirements

### 1. Well-Written Description and Acceptance Criteria

**Requirement:** Every Story MUST have:

- **User Story Format:** "As a [persona], I want [goal], So that [benefit]"
- **Detailed Acceptance Criteria:** Using Given/When/Then format
- **Technical Details:** Implementation notes and technical requirements
- **Dependencies:** Prerequisite stories or tasks

**Implementation:**

```python
story = mcp_openproject_create_work_package(
    project_id=8,
    subject="Story X.Y: [Story Name]",
    type_id=41,  # User Story
    description="""
    As a **[Persona]**,
    I want **[Goal]**,
    So that **[Benefit]**.
    
    **Acceptance Criteria:**
    
    **Given** [Context]
    **When** [Action]
    **Then** [Expected Result]
    **And** [Additional Result]
    
    **Given** [Another Context]
    **When** [Another Action]
    **Then** [Another Expected Result]
    
    **Technical Details:**
    - [Technical requirement 1]
    - [Technical requirement 2]
    
    **Dependencies:**
    - [Prerequisite story or task]
    """,
    priority_id=73  # Normal
)
```

### 2. Tasks Articulated and Detailed

**Requirement:** Every Story MUST have all tasks created in OpenProject during grooming phase, BEFORE implementation starts.

**Task Requirements:**
- **Created During Grooming:** All tasks MUST be created before story moves to "In progress"
- **Detailed Descriptions:** Each task must have:
  - Clear description of work
  - Acceptance criteria for the task
  - Technical implementation notes
  - Estimated effort (30 min - 4 hours)
- **Linked to Story:** All tasks MUST be linked to story via parent relationship
- **Test Task:** MUST include a test task (see requirement 5)

**Implementation:**

See `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md` for complete task creation workflow.

### 3. UI Story: Wireframe or UI Document

**Requirement:** For UI stories, a wireframe or UI design document MUST be attached to the Story work package.

**Document Requirements:**
- **Location:** `_bmad-output/planning-artifacts/story-X-Y-ui-design.md` or `_bmad-output/story-X-Y-ui-design.md`
- **Content:**
  - Wireframes or mockups
  - UI component specifications
  - User interaction flows
  - Responsive design considerations
  - Accessibility requirements
- **Attachment:** Document MUST be attached to Story work package
- **CRITICAL:** Never create duplicate documentation - use existing documents in `_bmad-output/` and attach as needed

**Implementation:**

```python
# For UI stories only
if is_ui_story:
    ui_doc_path = Path("_bmad-output/planning-artifacts/story-X-Y-ui-design.md")
    ui_doc_path.write_text("""
    # Story X.Y: UI Design Document
    
    ## Wireframes
    [Wireframe descriptions or links]
    
    ## UI Components
    [Component specifications]
    
    ## User Interaction Flows
    [Interaction flow descriptions]
    
    ## Responsive Design
    [Responsive design considerations]
    
    ## Accessibility
    [Accessibility requirements]
    """)
    
    # Attach to story
    with open(ui_doc_path, "rb") as f:
        ui_content = base64.b64encode(f.read()).decode("utf-8")
    
    mcp_openproject_add_work_package_attachment(
        work_package_id=story_id,
        file_data=ui_content,
        filename="story-X-Y-ui-design.md",
        content_type="text/markdown",
        description="UI design document for Story X.Y"
    )
```

### 4. Story Status Automation: "In progress" When First Task Starts

**Requirement:** Story status MUST automatically move to "In progress" (77) when the first task moves to "In progress" (77) - **IMMEDIATE**.

**Implementation:**

**Action Owner Responsibility:** The person updating the task status MUST call this function immediately after updating task status.

```python
def update_story_status_based_on_tasks(story_id: int):
    """
    Update story status based on task statuses.
    Call this IMMEDIATELY whenever a task status changes.
    
    Action Owner: Person updating task status (Dev)
    """
    # Get all tasks for story
    children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    tasks = [c for c in children["children"] if c["type"] == "Task"]
    
    if not tasks:
        return
    
    # Check if any task is "In progress"
    any_in_progress = any(
        task["status"] == "In progress" 
        for task in tasks
    )
    
    story = mcp_openproject_get_work_package(work_package_id=story_id)
    current_status = story["work_package"]["status"]["name"]
    
    # Update story status IMMEDIATELY when conditions are met
    if any_in_progress and current_status == "New":
        # Story moves to "In progress" when first task moves to "In progress" - IMMEDIATE
        mcp_openproject_update_work_package(
            work_package_id=story_id,
            status_id=77,  # In progress
            comment="Story in progress: First task has started."
        )
```

**When to Call (Action Owner Responsibility):**
- **Dev:** After updating task status to "In progress" (77) → Call immediately

### 5. Test Story Task with Document Creation

**Requirement:** Every Story MUST have a test task that includes:

- **Task Subject:** "Task X.Y.T: Story X.Y Testing and Validation" (using X.Y.T naming convention)
- **Task Description:** Comprehensive test plan
- **Activities:**
  1. Run story test suite
  2. Validate all acceptance criteria
  3. Create Story Test Document (if not already exists)
  4. Attach Story Test Document to Story work package
  5. Story status automatically moves to "In testing" (79) when test task moves to "In testing" and all other tasks closed

**Story Test Document Requirements:**
- **Location:** `_bmad-output/planning-artifacts/story-X-Y-test-document.md` or `_bmad-output/story-X-Y-test-document.md`
- **Content:**
  - Test plan
  - Test results
  - Acceptance criteria validation
  - Test coverage summary
  - Issues found and resolution
- **Attachment:** Document MUST be attached to Story work package
- **CRITICAL:** Never create duplicate documentation - use existing documents in `_bmad-output/` and attach as needed

**Implementation:**

```python
# Create test task during story grooming
test_task = mcp_openproject_create_work_package(
    project_id=8,
    subject="Task X.Y.T: Story X.Y Testing and Validation",
    type_id=36,  # Task
    description="""
    **Test Task for Story X.Y**
    
    **Activities:**
    1. Run story test suite (unit + integration)
    2. Validate all acceptance criteria
    3. Create Story Test Document
    4. Attach Story Test Document to Story work package
    5. Update story status to "In testing" (79) if all other tasks complete
    
    **Test Plan:**
    - [ ] Unit tests for all components
    - [ ] Integration tests for story functionality
    - [ ] Acceptance criteria validation
    - [ ] Performance validation (if applicable)
    - [ ] Security validation (if applicable)
    
    **Story Test Document:**
    - Create `docs/STORY_X_Y_TEST_DOCUMENT.md`
    - Include test plan, results, and validation
    - Attach to Story work package
    """,
    priority_id=73  # Normal
)

# Link to story
mcp_openproject_set_work_package_parent(
    work_package_id=test_task["work_package"]["id"],
    parent_id=story_id
)

# When test task is complete, create and attach test document
def complete_story_test_task(story_id: int, test_task_id: int):
    """
    Complete story test task and create/attach test document.
    """
    # Create test document
    test_doc_path = Path(f"docs/STORY_{story_id}_TEST_DOCUMENT.md")
    test_doc_path.write_text(f"""
    # Story Test Document: Story {story_id}
    
    ## Test Plan
    [Test plan details]
    
    ## Test Results
    [Test results]
    
    ## Acceptance Criteria Validation
    [Validation results]
    
    ## Test Coverage Summary
    [Coverage details]
    
    ## Issues Found and Resolution
    [Issues and resolutions]
    """)
    
    # Attach to story
    with open(test_doc_path, "rb") as f:
        doc_content = base64.b64encode(f.read()).decode("utf-8")
    
    mcp_openproject_add_work_package_attachment(
        work_package_id=story_id,
        file_data=doc_content,
        filename=f"STORY_{story_id}_TEST_DOCUMENT.md",
        content_type="text/markdown",
        description="Story test document with test plan, results, and validation"
    )
    
    # Check if all other tasks are complete
    children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    tasks = [c for c in children["children"] if c["type"] == "Task" and c["id"] != test_task_id]
    
    all_other_tasks_closed = all(
        task["status"] == "Closed" 
        for task in tasks
    )
    
    if all_other_tasks_closed:
        # Update story status to "In testing"
        mcp_openproject_update_work_package(
            work_package_id=story_id,
            status_id=79,  # In testing
            comment="All tasks complete. Story ready for test team validation."
        )
```

### 6. Story Status Automation: "In testing" When Test Task Moves to "In testing"

**Requirement:** Story status MUST automatically move to "In testing" (79) when the test task moves to "In testing" (79) AND all other tasks are closed - **IMMEDIATE**.

**Implementation:**

**Action Owner Responsibility:** The person updating the test task status MUST call this function immediately after updating test task status.

```python
def update_story_status_when_test_task_ready(story_id: int, test_task_id: int):
    """
    Update story status to "In testing" when test task is ready.
    Call this IMMEDIATELY when test task moves to "In testing" (79).
    
    Action Owner: Person updating test task status (Dev)
    """
    # Get all tasks for story
    children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    tasks = [c for c in children["children"] if c["type"] == "Task"]
    
    # Find test task (by subject pattern "Task X.Y.T" or by ID)
    test_task = next((t for t in tasks if t["id"] == test_task_id), None)
    if not test_task:
        # Try to find by subject pattern
        test_task = next((t for t in tasks if ".T:" in t["subject"] or "Testing and Validation" in t["subject"]), None)
    
    if not test_task:
        return
    
    # Check if test task is "In testing"
    if test_task["status"] != "In testing":
        return
    
    # Check if all other tasks are closed
    other_tasks = [t for t in tasks if t["id"] != test_task["id"]]
    all_other_tasks_closed = all(
        task["status"] == "Closed" 
        for task in other_tasks
    )
    
    if all_other_tasks_closed:
        # Update story status to "In testing" - IMMEDIATE
        mcp_openproject_update_work_package(
            work_package_id=story_id,
            status_id=79,  # In testing
            comment="Story in testing: Test task ready and all other tasks closed."
        )
```

**When to Call (Action Owner Responsibility):**
- **Dev:** After updating test task status to "In testing" (79) → Call immediately

### 7. Story Closure: When Last Task Closes

**Requirement:** Story MUST automatically close (82) when the last task (ideally the test task) is closed (82) - **IMMEDIATE**.

**Implementation:**

**Action Owner Responsibility:** The person closing the task/bug MUST call this function immediately after closing.

```python
def update_story_status_when_all_tasks_closed(story_id: int):
    """
    Update story status to "Closed" when all tasks are closed.
    Call this IMMEDIATELY whenever a task or bug is closed.
    
    Action Owner: Person closing task/bug (Dev or Test Team)
    """
    # Get all tasks and bugs for story
    children = mcp_openproject_get_work_package_children(
        parent_id=story_id,
        status="all"
    )
    tasks = [c for c in children["children"] if c["type"] == "Task"]
    bugs = [c for c in children["children"] if c["type"] == "Bug"]
    
    # Check if all tasks are closed
    all_tasks_closed = all(
        task["status"] == "Closed" 
        for task in tasks
    )
    
    # Check if all bugs are closed
    all_bugs_closed = all(
        bug["status"] == "Closed" 
        for bug in bugs
    )
    
    if all_tasks_closed and all_bugs_closed:
        # Update story status to "Closed" - IMMEDIATE
        mcp_openproject_update_work_package(
            work_package_id=story_id,
            status_id=82,  # Closed
            comment="Story closed: All tasks and bugs are closed."
        )
        
        # Trigger epic status update IMMEDIATELY
        story = mcp_openproject_get_work_package(work_package_id=story_id)
        parent = story["work_package"].get("parent", {})
        if parent:
            epic_id = parent.get("id")
            if epic_id:
                update_epic_status_based_on_stories(epic_id)
```

**When to Call (Action Owner Responsibility):**
- **Dev/Test Team:** After closing any task (82) → Call immediately
- **Test Team:** After closing any bug (82) → Call immediately

---

## Role Responsibilities

### Product Manager (PM)

**Epic Responsibilities:**
- Create epic with comprehensive description
- Add story breakdown to epic description
- Create epic test story
- Create and attach epic design document
- Monitor epic status transitions

**Story Responsibilities:**
- Create story with detailed description and acceptance criteria
- Groom story: create all tasks (including test task) during grooming phase
- For UI stories: create and attach UI design document
- Verify all tasks created before marking story "In progress"
- Monitor story status transitions

### Developer (Dev)

**Story Responsibilities:**
- Verify tasks exist before starting implementation
- Update task status as work progresses
- Mark test task "In testing" when ready
- Create story test document when test task completes
- Attach story test document to story work package

### Test Team

**Story Responsibilities:**
- Validate tasks when marked "In testing"
- Validate story when marked "In testing"
- Create bugs for validation failures
- Close story when all tasks and bugs closed

**Epic Responsibilities:**
- Validate epic test story
- Run epic-level integration tests
- Close epic when all stories closed

### Scrum Master (SM)

**Responsibilities:**
- Review workflow compliance
- Ensure status transitions are followed
- Facilitate workflow improvements
- Monitor epic and story progress

### Project Manager (PM)

**Responsibilities:**
- Review overall project progress
- Ensure epic and story documentation is complete
- Monitor quality gates
- Coordinate cross-epic dependencies

---

## Automation vs Manual Processes

### Status Transitions (Manual via MCP Tools)

The following status transitions are **MANUAL** but **IMMEDIATE** - action owners MUST call helper functions using OpenProject MCP tools:

1. **Epic → "In progress":** When first story moves to "In progress" - **Action Owner calls immediately**
2. **Epic → "Closed":** When last story closes - **Action Owner calls immediately**
3. **Story → "In progress":** When first task moves to "In progress" - **Action Owner calls immediately**
4. **Story → "In testing":** When test task moves to "In testing" and all other tasks closed - **Action Owner calls immediately**
5. **Story → "Closed":** When all tasks and bugs closed - **Action Owner calls immediately**

**Implementation:**
- **Action owners** (PM, Dev, Test Team) use OpenProject MCP tools to:
  1. Update work package status
  2. **IMMEDIATELY** call helper function to update parent status if conditions are met
- Helper functions are provided in `scripts/openproject_status_helpers.py`
- All operations use OpenProject MCP server tools

### Manual Processes (Using OpenProject MCP)

The following processes are **MANUAL** and require explicit action using OpenProject MCP tools:

1. **Epic Creation:** PM creates epic with description using `mcp_openproject_create_work_package()`
2. **Story Creation:** PM creates story with acceptance criteria using `mcp_openproject_create_work_package()`
3. **Task Creation:** PM creates tasks during grooming using `mcp_openproject_bulk_create_work_packages()`
4. **Document Creation:** PM/Dev creates design and test documents in `_bmad-output/`
5. **Document Attachment:** PM/Dev attaches documents using `mcp_openproject_add_work_package_attachment()`
6. **Task Implementation:** Dev implements tasks and updates status using `mcp_openproject_update_work_package()`
7. **Task/Story Validation:** Test team validates work and updates status using `mcp_openproject_update_work_package()`
8. **Status Transitions:** Action owners call helper functions immediately after status changes

---

## Checklists

### Epic Creation Checklist (PM)

- [ ] Epic created with comprehensive description
- [ ] Story breakdown added to epic description
- [ ] Epic test story created
- [ ] Epic test story tasks created
- [ ] Epic design document created
- [ ] Epic design document attached to epic work package
- [ ] All stories created under epic
- [ ] Parent relationships set correctly

### Story Grooming Checklist (PM)

- [ ] Story created with detailed description and acceptance criteria
- [ ] All tasks created (including test task)
- [ ] All tasks linked to story (parent relationships)
- [ ] Task descriptions include acceptance criteria
- [ ] For UI stories: UI design document created and attached
- [ ] Story file created in `_bmad-output/implementation-artifacts/`
- [ ] Story ready for implementation

### Story Implementation Checklist (Dev)

- [ ] Verify all tasks exist in OpenProject
- [ ] Start first task → Story automatically moves to "In progress"
- [ ] Implement tasks
- [ ] Mark tasks "In testing" when complete
- [ ] Complete test task
- [ ] Create story test document
- [ ] Attach story test document to story work package
- [ ] Story automatically moves to "In testing" when test task ready

### Story Validation Checklist (Test Team)

- [ ] All tasks closed
- [ ] All bugs closed
- [ ] Story test document reviewed
- [ ] Story validation passed
- [ ] Story automatically closes when all tasks/bugs closed

### Epic Validation Checklist (Test Team)

- [ ] All stories closed
- [ ] All tasks in all stories closed
- [ ] All bugs in all stories closed
- [ ] Epic test story validated
- [ ] Epic-level integration tests passed
- [ ] Epic automatically closes when last story closes

---

## OpenProject MCP Server Integration

All workflow operations MUST use OpenProject MCP server tools:

- `mcp_openproject_create_work_package()` - Create epics, stories, tasks
- `mcp_openproject_update_work_package()` - Update statuses and descriptions
- `mcp_openproject_get_work_package()` - Get work package details
- `mcp_openproject_get_work_package_children()` - Get children (stories, tasks)
- `mcp_openproject_set_work_package_parent()` - Set parent relationships
- `mcp_openproject_add_work_package_attachment()` - Attach documents
- `mcp_openproject_add_work_package_comment()` - Add comments

---

## Document Locations

**CRITICAL:** Never create duplicate documentation. Use existing documents in `_bmad-output/` and attach as needed.

**Document Storage:**
- **Primary Location:** `_bmad-output/planning-artifacts/` or `_bmad-output/`
- **Attachments:** Attach parts or whole documents to Epics/Features/Stories in OpenProject as needed
- **No Duplicates:** Do NOT create duplicate documentation in `docs/` if it already exists in `_bmad-output/`

**Document Types:**
- Epic Design Documents: `_bmad-output/planning-artifacts/epic-X-design.md` or `_bmad-output/epic-X-design.md`
- Story UI Designs: `_bmad-output/planning-artifacts/story-X-Y-ui-design.md` or `_bmad-output/story-X-Y-ui-design.md`
- Story Test Documents: `_bmad-output/planning-artifacts/story-X-Y-test-document.md` or `_bmad-output/story-X-Y-test-document.md`

---

## Next Steps

1. **Review by SM, PM, PM:** Review this document and provide feedback
2. **Create Helper Functions:** Create reusable helper functions in `scripts/openproject_status_helpers.py`
3. **Update Existing Epics/Stories:** Retroactively update existing epics and stories to meet requirements (where applicable)
4. **Documentation:** Update all related workflow documentation to reference this document
5. **Training:** Ensure all action owners understand their responsibilities for immediate status transitions

---

## References

- **Task Creation Workflow:** `docs/WORKFLOW_TASK_CREATION_REQUIREMENT.md`
- **Complete Agile Workflow:** `docs/COMPLETE_AGILE_WORKFLOW.md`
- **QA Testing Workflow:** `docs/QA_TESTING_WORKFLOW.md`
- **Task Management Process:** `docs/TASK_MANAGEMENT_PROCESS.md`
- **PM Agent Instructions:** `docs/PM_AGENT_INSTRUCTIONS.md`

