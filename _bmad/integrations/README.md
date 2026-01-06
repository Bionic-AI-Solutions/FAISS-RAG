# BMAD Integrations Package

This package provides standard integrations for OpenProject (work management + document storage) and Archon (external knowledge search).

## CRITICAL: System Responsibilities

| System | Responsibility |
|--------|----------------|
| **OpenProject** | Work management + ALL project documents (attachments) |
| **Archon** | Search EXTERNAL knowledge only (library docs, patterns) |

**⚠️ DO NOT store project documents in Archon. Archon is ONLY for searching external documentation.**

## Quick Start

### New Project Setup

```bash
# Run interactive setup
python scripts/bmad-setup.py init
```

This will:
1. Create `_bmad/_config/project-config.yaml` with your settings
2. Generate `CLAUDE.md` with configured IDs
3. Create output directories

### Existing Project

If you already have a config file:

```bash
# Validate configuration
python scripts/bmad-setup.py validate

# Regenerate CLAUDE.md after config changes
python scripts/bmad-setup.py generate-claude-md

# View current configuration
python scripts/bmad-setup.py show-config
```

## Package Structure

```
_bmad/
├── _config/
│   └── project-config.yaml      # ← EDIT THIS for each project
├── integrations/
│   ├── openproject/
│   │   ├── README.md            # OpenProject setup guide
│   │   ├── tools.md             # Complete tool reference
│   │   └── workflow.md          # Work + document storage workflow
│   ├── archon/
│   │   ├── README.md            # Archon setup guide
│   │   ├── tools.md             # External search reference
│   │   └── workflow.md          # External knowledge search workflow
│   ├── workflows/
│   │   └── project-init/
│   │       └── workflow.md      # Project initialization workflow
│   ├── agent-integration-mixin.md  # Agent enhancement definitions
│   ├── cursor-rules.mdc         # Cursor rules for integrations
│   └── README.md                # This file
├── templates/
│   └── CLAUDE.md.template       # Template for CLAUDE.md generation
└── ...existing BMAD modules...

scripts/
└── bmad-setup.py                # Setup and management script
```

## Document Storage Architecture

**ALL project documents are stored as OpenProject attachments at the appropriate level:**

| Work Package Level | Documents to Store |
|--------------------|-------------------|
| **Project** | Product briefs, project overview, high-level specs |
| **Epic** | Epic specifications, business cases |
| **Feature** | Feature architecture, technical designs, API specs |
| **Story** | Story specifications, acceptance criteria docs, test cases |
| **Task** | Implementation notes, technical details |

## Configuration

All project-specific settings are in `_bmad/_config/project-config.yaml`:

| Section | Purpose |
|---------|---------|
| `project` | Project identity (name, description, repo) |
| `team` | Team settings (user name, language) |
| `paths` | Output directories |
| `openproject` | OpenProject IDs and workflow settings |
| `archon` | RAG search settings (external knowledge only) |
| `testing` | TEA agent configuration |
| `workflows` | Story sizing, sprint settings |

### Minimum Required Configuration

```yaml
openproject:
  project_id: YOUR_PROJECT_ID  # From OpenProject

archon:
  enabled: true
  rag:
    default_match_count: 5
```

## How It Works

### 1. Configuration-Driven

All integration settings are centralized in `project-config.yaml`. When you:
- Change OpenProject project → Update config → Regenerate CLAUDE.md
- Add new type IDs → Update config → Agents use new IDs automatically

### 2. CLAUDE.md Generation

The `CLAUDE.md` file is generated from a template using your config values:

```bash
python scripts/bmad-setup.py generate-claude-md
```

This ensures:
- AI assistants have the correct project IDs
- Tool examples use your actual configuration
- No manual CLAUDE.md editing needed

### 3. Agent Integration

BMAD agents reference the integration modules:
- `_bmad/integrations/cursor-rules.mdc` - Always-on integration rules
- `_bmad/integrations/agent-integration-mixin.md` - Agent capabilities

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BMAD AGENTS                             │
│  (PM, Dev, Architect, SM, TEA, Tech Writer, UX Designer)   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ Integration │  │   CLAUDE.md │  │   Config    │
     │   Modules   │  │  (Generated)│  │   (YAML)    │
     └─────────────┘  └─────────────┘  └─────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     ┌─────────────────────┐     ┌─────────────────────┐
     │     OPENPROJECT     │     │       ARCHON        │
     │ (Work + Documents)  │     │ (External Search)   │
     │                     │     │                     │
     │  • Epics            │     │  • Library docs     │
     │  • Stories          │     │  • Framework refs   │
     │  • Tasks            │     │  • Code examples    │
     │  • Status           │     │  • Best practices   │
     │  • ALL Documents    │     │                     │
     │    (attachments)    │     │  ⚠️ Search only!   │
     └─────────────────────┘     └─────────────────────┘
```

## Reusing for New Projects

### Step 1: Copy Integration Package

Copy these folders to your new project:
- `_bmad/integrations/`
- `_bmad/templates/`
- `_bmad/_config/project-config.yaml` (as template)
- `scripts/bmad-setup.py`

### Step 2: Initialize

```bash
cd new-project
python scripts/bmad-setup.py init
```

### Step 3: Configure

1. Get OpenProject project ID
2. Update `project-config.yaml`
3. Regenerate CLAUDE.md

### Step 4: Verify

```bash
python scripts/bmad-setup.py validate
```

## Integration Rules

### Rule 1: OpenProject-First

**ALWAYS** use OpenProject for work management AND document storage:
- Create work packages before coding
- Update status when starting/completing work
- Attach project documents to appropriate work package level
- Never skip work package updates

### Rule 2: Documents in OpenProject

**ALWAYS** store project documents as OpenProject attachments:
- Product briefs → Project-level
- Architecture docs → Feature-level
- Implementation notes → Task-level

### Rule 3: Archon for External Search Only

**ONLY** use Archon for searching external knowledge:
- Search library documentation
- Find framework references
- Look up code patterns from external sources
- **DO NOT** store project documents in Archon

### Rule 4: Configuration Reference

**ALWAYS** use configured IDs:
- Don't hardcode type/status/priority IDs
- Read from `project-config.yaml`
- Use generated CLAUDE.md as reference

## Troubleshooting

### "project_id not configured"

Run setup or manually edit `project-config.yaml`:
```bash
python scripts/bmad-setup.py init
```

### "CLAUDE.md out of date"

Regenerate after config changes:
```bash
python scripts/bmad-setup.py generate-claude-md
```

### "Type/status ID not found"

Get correct IDs from OpenProject:
```python
mcp_openproject_list_types(project_id=YOUR_ID)
mcp_openproject_list_statuses()
```

Update `project-config.yaml` with correct values.

## Related Documentation

- [OpenProject Integration](openproject/README.md) - Work management + document storage
- [Archon Integration](archon/README.md) - External knowledge search only
- [Project Initialization Workflow](workflows/project-init/workflow.md)
- [Agent Integration Mixin](agent-integration-mixin.md)
