# OpenProject Integration for BMAD

This module provides the standard integration between BMAD methodology and OpenProject.

## Overview

OpenProject serves as the **PRIMARY system** for all BMAD projects:

### Work Management
- **Projects**: Top-level organization
- **Epics**: Business goals and major initiatives
- **Features**: Functional capabilities
- **User Stories**: User-centric requirements with acceptance criteria
- **Tasks**: Implementation work items

### Document Storage (Attachments)
**ALL project documents** are stored as attachments at the appropriate work package level:

| Level | Documents |
|-------|-----------|
| **Project** | Product briefs, project overview, high-level specs |
| **Epic** | Epic specifications, business cases |
| **Feature** | Feature architecture, technical designs, API specs |
| **Story** | Story specifications, acceptance criteria docs |
| **Task** | Implementation notes, technical details |

**⚠️ Important:** Do NOT store project documents in Archon. Archon is ONLY for searching external knowledge (library docs, research, etc.).

## Quick Setup

### 1. Get Your Project ID

```python
# Run this to find your OpenProject project
mcp_openproject_list_projects(active_only=True)
```

### 2. Get Type IDs

```python
# Run this to get work package types for your project
mcp_openproject_list_types(project_id=YOUR_PROJECT_ID)
```

### 3. Update Configuration

Edit `_bmad/_config/project-config.yaml`:

```yaml
openproject:
  enabled: true
  project_id: YOUR_PROJECT_ID  # ← Update this
  
  types:
    epic: 40           # ← Verify/update from list_types
    feature: 39
    user_story: 41
    task: 36
```

## Files in This Module

| File | Purpose |
|------|---------|
| `tools.md` | Complete MCP tool reference with all parameters |
| `workflow.md` | Work-driven development workflow and patterns |
| `README.md` | This setup guide |

## Integration with BMAD Agents

Each BMAD agent has specific OpenProject responsibilities:

| Agent | Work Management | Document Storage |
|-------|-----------------|------------------|
| **PM** | Create Epics, Features, User Stories | Product briefs (Project), PRDs (Epic) |
| **Dev** | Query/update Tasks, log time | Implementation notes (Task) |
| **SM** | Sprint planning, status reporting | Sprint reports (Project) |
| **Architect** | Create technical tasks | Architecture docs (Feature), System design (Project) |
| **TEA** | Create test tasks, update bugs | Test strategy (Feature), Test cases (Story) |

## Core Workflow

```
1. GET WORK    → mcp_openproject_list_work_packages(project_id, "open")
2. START       → mcp_openproject_update_work_package(id, status_id=77)
3. RESEARCH    → Search Archon for EXTERNAL knowledge (library docs, patterns)
4. IMPLEMENT   → Write code
5. DOCUMENT    → Attach implementation docs to Task in OpenProject
6. REVIEW      → mcp_openproject_update_work_package(id, status_id=79)
7. COMPLETE    → mcp_openproject_update_work_package(id, status_id=82)
8. NEXT        → Return to step 1
```

## Troubleshooting

### "Parameter must be integer, got string"

The OpenProject MCP server requires integer parameters. If using JSON-RPC, ensure proper type conversion.

### Can't Find Work Package Types

Run `mcp_openproject_list_types(project_id=YOUR_ID)` to get the correct type IDs for your OpenProject instance.

### Status Updates Failing

Check available statuses with `mcp_openproject_list_statuses()` and verify the status IDs in your config match.

## Related Documentation

- See `workflow.md` for detailed workflow patterns
- See `tools.md` for complete tool reference
- See `_bmad/integrations/archon/` for knowledge repository integration

