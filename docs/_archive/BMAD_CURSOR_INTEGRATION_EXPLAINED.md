# BMAD Agent System - How It Works with Cursor

**Date:** 2026-01-07  
**Purpose:** Complete explanation of BMAD system architecture and how it integrates with Cursor

## Overview

The BMAD (Build, Manage, and Deploy) system is a methodology that provides structured agent personalities, workflows, and rules for AI-assisted development. It integrates with Cursor through a two-tier architecture:

1. **`.cursor/rules/bmad/`** - Cursor rules that activate BMAD agents and workflows
2. **`_bmad/`** - Complete BMAD doctrine containing agent definitions, workflows, and configurations

## System Architecture

### Two-Tier Structure

```
.cursor/rules/bmad/          ← Cursor Rules (Activation Layer)
├── index.mdc                ← Master index (always applied)
├── core/
│   └── agents/
│       └── bmad-master.mdc  ← References _bmad/core/agents/bmad-master.md
├── bmm/
│   └── agents/
│       └── pm.mdc          ← References _bmad/bmm/agents/pm.md
└── ...

_bmad/                       ← BMAD Doctrine (Source of Truth)
├── core/
│   └── agents/
│       └── bmad-master.md   ← Complete agent definition
├── bmm/
│   ├── agents/
│   │   └── pm.md           ← Complete PM agent definition
│   ├── workflows/
│   │   └── create-epics-and-stories/
│   │       └── workflow.md ← Complete workflow instructions
│   └── config.yaml         ← Agent configuration
└── integrations/
    └── cursor-rules.mdc     ← Integration rules (always applied)
```

## How It Works

### 1. Cursor Rules Layer (`.cursor/rules/bmad/`)

**Purpose:** Lightweight activation files that tell Cursor to load the full agent/workflow from `_bmad/`

**Structure:**

- Each `.mdc` file is a Cursor rule with frontmatter
- Contains activation instructions that reference `_bmad/` files
- Uses `alwaysApply: false` (manual activation) or `alwaysApply: true` (always active)

**Example: PM Agent Rule** (`.cursor/rules/bmad/bmm/agents/pm.mdc`):

```markdown
---
description: BMAD BMM Agent: pm
globs:
alwaysApply: false
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified.

<agent-activation CRITICAL="TRUE">
1. LOAD the FULL agent file from @_bmad/bmm/agents/pm.md
2. READ its entire contents - this contains the complete agent persona, menu, and instructions
3. Execute ALL activation steps exactly as written in the agent file
4. Follow the agent's persona and menu system precisely
5. Stay in character throughout the session
</agent-activation>
```

**Key Points:**

- The `.mdc` file is just a pointer/activator
- The actual agent definition is in `_bmad/bmm/agents/pm.md`
- When you reference `@bmad/bmm/agents/pm`, Cursor loads the `.mdc` file, which then loads the full agent from `_bmad/`

### 2. BMAD Doctrine Layer (`_bmad/`)

**Purpose:** Complete source of truth for all BMAD agents, workflows, tasks, and configurations

**Structure:**

#### Agent Definitions (`_bmad/{module}/agents/{agent-name}.md`)

Contains:

- **Persona:** Role, identity, communication style, principles
- **Activation Steps:** How to initialize the agent
- **Menu System:** Available commands and workflows
- **Menu Handlers:** How to execute menu items (workflows, scripts, etc.)
- **Configuration:** References to `config.yaml` for user settings

**Example Structure:**

```xml
<agent id="pm.agent.yaml" name="John" title="Product Manager">
  <activation>
    <step>Load config.yaml</step>
    <step>Show greeting</step>
    <step>Display menu</step>
  </activation>
  <persona>
    <role>Product Manager specializing in PRD creation</role>
    <identity>8+ years experience...</identity>
  </persona>
  <menu>
    <item cmd="PR" exec="workflow.md">Create PRD</item>
    <item cmd="ES" exec="workflow.md">Create Epics and Stories</item>
  </menu>
</agent>
```

#### Workflow Definitions (`_bmad/{module}/workflows/{workflow-name}/`)

Contains:

- **workflow.md** or **workflow.yaml** - Complete workflow instructions
- **steps/** - Individual workflow steps
- **templates/** - Output templates
- **checklist.md** - Workflow checklist
- **instructions.md** - Detailed instructions

**Workflow Types:**

- **Markdown workflows** (`.md`) - Step-by-step instructions
- **YAML workflows** (`.yaml`) - Structured workflow definitions executed by `workflow.xml`

#### Configuration Files (`_bmad/{module}/config.yaml`)

Contains:

- User name
- Communication language
- Output folders
- Project-specific settings

**Example:**

```yaml
user_name: "John"
communication_language: "English"
output_folder: "_bmad-output"
```

#### Integration Rules (`_bmad/integrations/cursor-rules.mdc`)

**Purpose:** Standard operating procedures for all BMAD agents

**Contains:**

- OpenProject integration rules (work management)
- Archon integration rules (external knowledge search)
- Document storage hierarchy
- Workflow patterns (Dev, Test, PM)
- Story verification standard

**Status:** `alwaysApply: true` - Always active for all agents

## How Agents Get Their Knowledge

### 1. Agent Personalities

**Source:** `_bmad/{module}/agents/{agent-name}.md`

**Loaded When:**

- User references `@bmad/{module}/agents/{agent-name}` in Cursor
- Cursor loads `.cursor/rules/bmad/{module}/agents/{agent-name}.mdc`
- The `.mdc` file instructs to load `_bmad/{module}/agents/{agent-name}.md`
- Agent persona, menu, and instructions are loaded

**Example:**

```
User: @bmad/bmm/agents/pm
  ↓
Cursor loads: .cursor/rules/bmad/bmm/agents/pm.mdc
  ↓
.mdc file says: "LOAD @_bmad/bmm/agents/pm.md"
  ↓
Full agent definition loaded from _bmad/
```

### 2. Rules and Workflows

**Source:** `_bmad/{module}/workflows/{workflow-name}/`

**Loaded When:**

- Agent menu item references a workflow
- Workflow handler loads the workflow file
- Workflow steps are executed

**Example:**

```
User selects: [PR] Create PRD
  ↓
Agent menu handler sees: exec="workflow.md"
  ↓
Loads: _bmad/bmm/workflows/2-plan-workflows/prd/workflow.md
  ↓
Executes workflow steps
```

### 3. Integration Rules

**Source:** `_bmad/integrations/cursor-rules.mdc`

**Loaded When:**

- Always loaded (`alwaysApply: true`)
- Provides standard operating procedures
- Defines OpenProject and Archon integration patterns

### 4. Configuration

**Source:** `_bmad/{module}/config.yaml`

**Loaded When:**

- Agent activation step 2 (mandatory)
- Provides user-specific settings
- Used throughout agent session

## Activation Flow

### Complete Agent Activation Sequence

```
1. User references: @bmad/bmm/agents/pm
   ↓
2. Cursor loads: .cursor/rules/bmad/bmm/agents/pm.mdc
   ↓
3. .mdc file contains activation instructions:
   - LOAD @_bmad/bmm/agents/pm.md
   - READ entire contents
   - Execute activation steps
   ↓
4. Agent activation begins:
   Step 1: Load persona (already in context)
   Step 2: Load config.yaml → Store as session variables
   Step 3: Remember user name
   Step 4: Show greeting + display menu
   Step 5: Wait for user input
   ↓
5. User selects menu item
   ↓
6. Menu handler executes:
   - If workflow: Load workflow.yaml → Execute via workflow.xml
   - If exec: Load file.md → Execute instructions
   ↓
7. Workflow/script references:
   - Integration rules (cursor-rules.mdc) - always available
   - Other workflows via @bmad references
   - Config values from config.yaml
```

## Key Files and Their Roles

### Always Applied Rules

1. **`.cursor/rules/bmad/index.mdc`**

   - `alwaysApply: true`
   - Master index of all BMAD agents/workflows
   - Provides reference guide

2. **`_bmad/integrations/cursor-rules.mdc`**
   - `alwaysApply: true`
   - Standard operating procedures
   - OpenProject/Archon integration rules

### Manual Activation Rules

All agent and workflow rules use `alwaysApply: false` - they must be explicitly referenced:

- `@bmad/bmm/agents/pm` - Activates PM agent
- `@bmad/bmm/workflows/create-epics-and-stories` - Activates workflow
- `@bmad/bmm/workflows/epic-story-lifecycle` - Activates lifecycle workflow

## Where Things Come From

### Agent Personalities

- **Source:** `_bmad/{module}/agents/{agent-name}.md`
- **Activated by:** `.cursor/rules/bmad/{module}/agents/{agent-name}.mdc`
- **Contains:** Persona, menu, activation steps, handlers

### Rules

- **Source:** `_bmad/integrations/cursor-rules.mdc` (always applied)
- **Also:** Individual workflow rules in `_bmad/{module}/workflows/`
- **Contains:** Integration patterns, workflow requirements, standards

### Tasks

- **Source:** `_bmad/{module}/tasks/{task-name}.md`
- **Activated by:** `.cursor/rules/bmad/{module}/tasks/{task-name}.mdc`
- **Contains:** Reusable task workflows

### Understanding/Knowledge

- **Source:** Multiple sources:
  1. **Agent definitions** - Built-in knowledge in agent persona
  2. **Workflow instructions** - Step-by-step guidance
  3. **Integration rules** - Standard patterns (OpenProject, Archon)
  4. **Config files** - Project-specific settings
  5. **External knowledge** - Archon RAG for external docs

## BMAD Doctrine Changes

### Recent Integration

**Question:** "Have you made the change to the BMAD doctrine as well?"

**Answer:** Yes, according to `docs/BMAD_DOCTRINE_INTEGRATION_SUMMARY.md`:

1. **New Workflow Created:** `epic-story-lifecycle` (mentioned but file not found - needs creation)
2. **Updated Workflows:**
   - `groom-story.mdc` - Added duplicate prevention
   - `dev-story-with-tasks.mdc` - Added immediate status transitions
3. **Integration Rules Updated:** `_bmad/integrations/cursor-rules.mdc` - Story verification standard

**Status:** Integration documented, but `epic-story-lifecycle.mdc` workflow file needs to be created in `.cursor/rules/bmad/bmm/workflows/`

## Summary

### The Two-Tier System

1. **`.cursor/rules/bmad/`** = **Activation Layer**

   - Lightweight pointers to BMAD doctrine
   - Tells Cursor what to load
   - Index and integration rules always applied

2. **`_bmad/`** = **Doctrine Layer (Source of Truth)**
   - Complete agent definitions
   - Full workflow instructions
   - Configuration files
   - Integration rules

### How Knowledge Flows

```
User Reference (@bmad/...)
  ↓
Cursor Rule (.mdc) - Activation
  ↓
BMAD Doctrine (_bmad/...) - Full Definition
  ↓
Agent/Workflow Execution
  ↓
Integration Rules (cursor-rules.mdc) - Always Available
  ↓
External Knowledge (Archon) - When Needed
```

### Key Takeaway

**Everything comes from `_bmad/` folder** - the `.cursor/rules/bmad/` folder is just the activation layer that tells Cursor to load the full definitions from `_bmad/`.

The BMAD system is designed so that:

- **Agents** get their personalities from `_bmad/{module}/agents/`
- **Rules** come from `_bmad/integrations/cursor-rules.mdc` and workflow files
- **Tasks** come from `_bmad/{module}/tasks/`
- **Understanding** comes from agent personas, workflow instructions, and external knowledge (Archon)

All of this is orchestrated through the `.cursor/rules/bmad/` activation layer, which provides the interface between Cursor and the BMAD doctrine.

