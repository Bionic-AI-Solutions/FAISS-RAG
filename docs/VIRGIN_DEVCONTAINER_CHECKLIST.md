# Virgin DevContainer - BMAD Integration Checklist

**Date:** 2026-01-07  
**Purpose:** Complete checklist of all files and folders that must be checked into `virgin-devcontainer` repository to replicate the BMAD methodology setup

## Overview

To replicate all BMAD rules, processes, and workflows in new projects, the following components must be included in the `virgin-devcontainer` template repository.

---

## ✅ Required Components

### 1. Complete BMAD Doctrine (`_bmad/` folder)

**Purpose:** Source of truth for all agents, workflows, and integrations

**Required Structure:**

```
_bmad/
├── _config/
│   ├── project-config.yaml              # ← Template (user edits for each project)
│   ├── manifest.yaml
│   ├── agent-manifest.csv
│   ├── workflow-manifest.csv
│   ├── task-manifest.csv
│   ├── tool-manifest.csv
│   ├── files-manifest.csv
│   └── agents/                           # Agent customization files
│       ├── core-bmad-master.customize.yaml
│       ├── bmm-pm.customize.yaml
│       ├── bmm-dev.customize.yaml
│       └── ... (all agent customize files)
│
├── core/
│   ├── agents/
│   │   └── bmad-master.md               # Core master agent
│   ├── config.yaml                      # Core module config template
│   ├── tasks/
│   │   ├── workflow.xml                 # Core workflow execution engine
│   │   ├── index-docs.xml
│   │   ├── shard-doc.xml
│   │   └── validate-workflow.xml
│   └── workflows/
│       ├── brainstorming/
│       └── party-mode/
│
├── bmm/                                  # Build, Manage, Maintain module
│   ├── agents/
│   │   ├── analyst.md
│   │   ├── architect.md
│   │   ├── dev.md
│   │   ├── pm.md
│   │   ├── sm.md
│   │   ├── tea.md
│   │   ├── tech-writer.md
│   │   ├── ux-designer.md
│   │   └── quick-flow-solo-dev.md
│   ├── config.yaml                      # BMM module config template
│   ├── workflows/
│   │   ├── 1-analysis/
│   │   │   ├── create-product-brief/
│   │   │   └── research/
│   │   ├── 2-plan-workflows/
│   │   │   ├── create-ux-design/
│   │   │   └── prd/
│   │   ├── 3-solutioning/
│   │   │   ├── check-implementation-readiness/
│   │   │   ├── create-architecture/
│   │   │   └── create-epics-and-stories/
│   │   ├── 4-implementation/
│   │   │   ├── bug-management/
│   │   │   ├── code-review/
│   │   │   ├── correct-course/
│   │   │   ├── create-story/
│   │   │   ├── dev-story/
│   │   │   ├── retrospective/
│   │   │   ├── sprint-planning/
│   │   │   ├── sprint-status/
│   │   │   └── test-validation/
│   │   ├── bmad-quick-flow/
│   │   ├── document-project/
│   │   ├── excalidraw-diagrams/
│   │   ├── generate-project-context/
│   │   ├── testarch/
│   │   └── workflow-status/
│   └── data/
│       └── documentation-standards.md
│
├── bmb/                                  # Build, Manage, Build module
│   ├── agents/
│   │   ├── agent-builder.md
│   │   ├── module-builder.md
│   │   └── workflow-builder.md
│   ├── config.yaml                      # BMB module config template
│   ├── workflows/
│   │   ├── agent/
│   │   ├── create-module/
│   │   ├── create-workflow/
│   │   ├── edit-workflow/
│   │   └── workflow-compliance-check/
│   └── docs/
│       └── workflows/
│
├── integrations/                         # Integration rules and docs
│   ├── cursor-rules.mdc                  # ← CRITICAL: Always-applied integration rules
│   ├── agent-integration-mixin.md
│   ├── README.md
│   ├── openproject/
│   │   ├── README.md
│   │   ├── tools.md                     # Complete OpenProject MCP tool reference
│   │   └── workflow.md                  # Work-driven development workflow
│   ├── archon/
│   │   ├── README.md
│   │   ├── tools.md                     # Complete Archon MCP tool reference
│   │   └── workflow.md                  # Research-driven workflow
│   └── workflows/
│       └── project-init/                 # Project initialization workflow
│
├── templates/
│   └── CLAUDE.md.template               # Template for CLAUDE.md generation
│
└── workflows/
    └── STORY_VERIFICATION_STANDARD.md   # Story verification requirements
```

**Critical Files:**

- ✅ `_bmad/integrations/cursor-rules.mdc` - **MUST BE INCLUDED** (always-applied integration rules)
- ✅ `_bmad/_config/project-config.yaml` - Template for user to customize
- ✅ All agent `.md` files - Complete agent definitions
- ✅ All workflow folders - Complete workflow instructions

---

### 2. Cursor Rules Activation Layer (`.cursor/rules/bmad/` folder)

**Purpose:** Lightweight activation files that tell Cursor to load full definitions from `_bmad/`

**Required Structure:**

```
.cursor/
└── rules/
    └── bmad/
        ├── index.mdc                    # ← Master index (always applied)
        │
        ├── core/
        │   ├── agents/
        │   │   └── bmad-master.mdc
        │   ├── tasks/
        │   │   ├── index-docs.mdc
        │   │   └── shard-doc.mdc
        │   └── workflows/
        │       ├── brainstorming.mdc
        │       └── party-mode.mdc
        │
        ├── bmm/
        │   ├── agents/
        │   │   ├── analyst.mdc
        │   │   ├── architect.mdc
        │   │   ├── dev.mdc
        │   │   ├── pm.mdc
        │   │   ├── sm.mdc
        │   │   ├── tea.mdc
        │   │   ├── tech-writer.mdc
        │   │   ├── ux-designer.mdc
        │   │   └── quick-flow-solo-dev.mdc
        │   └── workflows/
        │       ├── create-product-brief.mdc
        │       ├── research.mdc
        │       ├── create-ux-design.mdc
        │       ├── create-prd.mdc
        │       ├── check-implementation-readiness.mdc
        │       ├── create-architecture.mdc
        │       ├── create-epics-and-stories.mdc
        │       ├── epic-story-lifecycle.mdc        # ← CRITICAL: Lifecycle workflow
        │       ├── code-review.mdc
        │       ├── correct-course.mdc
        │       ├── create-story.mdc
        │       ├── dev-story.mdc
        │       ├── dev-story-with-tasks.mdc        # ← CRITICAL: Dev workflow
        │       ├── groom-story.mdc                 # ← CRITICAL: Story grooming
        │       ├── test-validation.mdc
        │       ├── bug-management.mdc
        │       ├── retrospective.mdc
        │       ├── sprint-planning.mdc
        │       ├── sprint-status.mdc
        │       ├── create-tech-spec.mdc
        │       ├── quick-dev.mdc
        │       ├── document-project.mdc
        │       ├── create-excalidraw-dataflow.mdc
        │       ├── create-excalidraw-diagram.mdc
        │       ├── create-excalidraw-flowchart.mdc
        │       ├── create-excalidraw-wireframe.mdc
        │       ├── generate-project-context.mdc
        │       ├── testarch-atdd.mdc
        │       ├── testarch-automate.mdc
        │       ├── testarch-ci.mdc
        │       ├── testarch-framework.mdc
        │       ├── testarch-nfr.mdc
        │       ├── testarch-test-design.mdc
        │       ├── testarch-test-review.mdc
        │       ├── testarch-trace.mdc
        │       ├── workflow-init.mdc
        │       └── workflow-status.mdc
        │
        └── bmb/
            ├── agents/
            │   ├── agent-builder.mdc
            │   ├── module-builder.mdc
            │   └── workflow-builder.mdc
            └── workflows/
                ├── agent.mdc
                ├── create-module.mdc
                ├── create-workflow.mdc
                ├── edit-workflow.mdc
                └── workflow-compliance-check.mdc
```

**Critical Files:**

- ✅ `.cursor/rules/bmad/index.mdc` - Master index (always applied)
- ✅ All `.mdc` activation files - Pointers to `_bmad/` definitions
- ✅ `epic-story-lifecycle.mdc` - Lifecycle management workflow
- ✅ `groom-story.mdc` - Story grooming with duplicate prevention
- ✅ `dev-story-with-tasks.mdc` - Dev workflow with status transitions

---

### 3. Setup and Management Scripts

**Purpose:** Scripts for initializing and managing BMAD in new projects

**Required Files:**

```
scripts/
└── bmad-setup.py                         # ← BMAD setup and management script
```

**Script Capabilities:**

- Interactive project initialization
- Generate CLAUDE.md from template
- Validate configuration
- Show current configuration
- Update project settings

---

### 4. Documentation Files

**Purpose:** Key documentation explaining the BMAD system

**Required Files:**

```
docs/
├── BMAD_CURSOR_INTEGRATION_EXPLAINED.md  # ← How BMAD works with Cursor
├── BMAD_DOCTRINE_INTEGRATION_SUMMARY.md  # Integration summary
└── VIRGIN_DEVCONTAINER_CHECKLIST.md      # This file
```

**Optional but Recommended:**

- `BMAD_COMPLETE_WORKFLOW_REQUIREMENTS.md` - Detailed workflow requirements
- `BMAD_WORKFLOW_QUICK_REFERENCE.md` - Quick reference guide
- `WORKFLOW_TASK_CREATION_REQUIREMENT.md` - Task creation details
- `TASK_CREATION_DUPLICATE_PREVENTION.md` - Duplicate prevention guide

---

### 5. Project Configuration Template

**Purpose:** Template configuration file for new projects

**Required File:**

```
_bmad/_config/project-config.yaml.template
```

**Note:** This should be a template with placeholder values that users customize for their project.

---

### 6. README Updates

**Purpose:** Update virgin-devcontainer README with BMAD information

**Required Updates to `README.md`:**

- Add BMAD methodology section
- Document the two-tier architecture (`.cursor/rules/bmad/` + `_bmad/`)
- Explain how to initialize BMAD in a new project
- Link to integration documentation
- Document required MCP servers (OpenProject, Archon)

---

## 📋 Complete File Checklist

### Critical Files (MUST BE INCLUDED)

- [ ] `_bmad/integrations/cursor-rules.mdc` - Integration rules (always applied)
- [ ] `_bmad/_config/project-config.yaml` - Configuration template
- [ ] `.cursor/rules/bmad/index.mdc` - Master index
- [ ] `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc` - Lifecycle workflow
- [ ] `.cursor/rules/bmad/bmm/workflows/groom-story.mdc` - Story grooming
- [ ] `.cursor/rules/bmad/bmm/workflows/dev-story-with-tasks.mdc` - Dev workflow
- [ ] `scripts/bmad-setup.py` - Setup script
- [ ] `docs/BMAD_CURSOR_INTEGRATION_EXPLAINED.md` - System explanation

### Complete Folder Structure

- [ ] `_bmad/` - Complete BMAD doctrine (all subfolders and files)
- [ ] `.cursor/rules/bmad/` - Complete Cursor rules (all subfolders and files)
- [ ] `scripts/bmad-setup.py` - Setup script
- [ ] `docs/` - Documentation files

---

## 🚀 Setup Instructions for New Projects

### Step 1: Copy BMAD Components

```bash
# From virgin-devcontainer template
cp -r _bmad/ /path/to/new-project/
cp -r .cursor/rules/bmad/ /path/to/new-project/.cursor/rules/
cp scripts/bmad-setup.py /path/to/new-project/scripts/
```

### Step 2: Initialize Project Configuration

```bash
cd /path/to/new-project
python scripts/bmad-setup.py init
```

This will:

- Prompt for project name, OpenProject project ID, etc.
- Generate `_bmad/_config/project-config.yaml` with your settings
- Validate configuration

### Step 3: Configure MCP Servers

Ensure your `~/.cursor/mcp.json` includes:

- OpenProject MCP server (for work management)
- Archon MCP server (for knowledge repository)

### Step 4: Verify Setup

```bash
python scripts/bmad-setup.py validate
python scripts/bmad-setup.py show-config
```

### Step 5: Generate CLAUDE.md (Optional)

```bash
python scripts/bmad-setup.py generate-claude-md
```

---

## 🔍 Verification Checklist

After checking in all files, verify:

- [ ] All `_bmad/` folders and files are present
- [ ] All `.cursor/rules/bmad/` files are present
- [ ] `bmad-setup.py` script is executable
- [ ] `project-config.yaml` is a template (not project-specific)
- [ ] README.md includes BMAD documentation
- [ ] All agent `.mdc` files reference correct `_bmad/` paths
- [ ] Integration rules (`cursor-rules.mdc`) are included
- [ ] Lifecycle workflow (`epic-story-lifecycle.mdc`) is included

---

## 📝 Notes

### What NOT to Include

- ❌ Project-specific `project-config.yaml` values (use template)
- ❌ Project-specific documentation in `docs/` (only include system docs)
- ❌ `_bmad-output/` folder (generated per project)
- ❌ `.cursorrules` file (user manages separately)

### Template vs. Project-Specific

**Template Files (Include in virgin-devcontainer):**

- `_bmad/_config/project-config.yaml` - Template with placeholders
- All agent/workflow definitions - Generic, reusable
- Integration rules - Standard operating procedures

**Project-Specific Files (User Creates):**

- `_bmad/_config/project-config.yaml` - User customizes for their project
- `_bmad-output/` - Generated artifacts
- Project documentation in `docs/`

---

## 🎯 Summary

To replicate the complete BMAD methodology in new projects, the `virgin-devcontainer` repository must include:

1. **Complete `_bmad/` folder** - All agents, workflows, integrations, config templates
2. **Complete `.cursor/rules/bmad/` folder** - All activation rules
3. **Setup script** - `scripts/bmad-setup.py`
4. **Documentation** - Key system documentation files
5. **Updated README** - BMAD integration instructions

The template should be **generic and reusable**, with users customizing `project-config.yaml` for their specific project needs.

---

## 🔗 References

- [BMAD Cursor Integration Explained](./BMAD_CURSOR_INTEGRATION_EXPLAINED.md)
- [BMAD Doctrine Integration Summary](./BMAD_DOCTRINE_INTEGRATION_SUMMARY.md)
- [Virgin DevContainer Repository](https://github.com/Bionic-AI-Solutions/virgin-devcontainer)
