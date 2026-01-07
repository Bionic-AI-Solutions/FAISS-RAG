# Virgin DevContainer - Setup Instructions

**Date:** 2026-01-07  
**Purpose:** Step-by-step instructions to prepare the virgin-devcontainer repository with complete BMAD integration

## Quick Setup

### Option 1: Automated Script (Recommended)

```bash
# From mem0-rag project root
cd /workspaces/mem0-rag
./scripts/prepare-virgin-devcontainer.sh /path/to/virgin-devcontainer
```

This script will:
- Copy all `_bmad/` files (excluding `_bmad-output/`)
- Copy all `.cursor/rules/bmad/` files
- Copy `scripts/bmad-setup.py`
- Copy key documentation files
- Ensure `project-config.yaml` is a template (not project-specific)
- Update `.gitignore` if needed

### Option 2: Manual Copy

```bash
# Clone virgin-devcontainer if not already cloned
git clone https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
cd virgin-devcontainer

# From mem0-rag project, copy files
# Copy BMAD doctrine
cp -r /workspaces/mem0-rag/_bmad/ .

# Copy Cursor rules
mkdir -p .cursor/rules
cp -r /workspaces/mem0-rag/.cursor/rules/bmad/ .cursor/rules/

# Copy setup script
mkdir -p scripts
cp /workspaces/mem0-rag/scripts/bmad-setup.py scripts/
chmod +x scripts/bmad-setup.py

# Copy documentation
mkdir -p docs
cp /workspaces/mem0-rag/docs/BMAD_CURSOR_INTEGRATION_EXPLAINED.md docs/
cp /workspaces/mem0-rag/docs/BMAD_DOCTRINE_INTEGRATION_SUMMARY.md docs/
cp /workspaces/mem0-rag/docs/VIRGIN_DEVCONTAINER_CHECKLIST.md docs/
cp /workspaces/mem0-rag/docs/VIRGIN_DEVCONTAINER_QUICK_REFERENCE.md docs/
```

## Post-Copy Steps

### 1. Clean Up Project-Specific Values

Edit `_bmad/_config/project-config.yaml` and ensure it has template values:

```yaml
project:
  name: "your-project-name"           # NOT "mem0-rag"
  display_name: "Your Project Name"   # NOT project-specific

openproject:
  project_id: null                    # NOT 8 (project-specific)

team:
  user_name: "TeamLead"               # NOT project-specific name
```

### 2. Update .gitignore

Ensure `.gitignore` includes:

```
# BMAD generated output
_bmad-output/
```

### 3. Update README.md

Add BMAD section to README.md (see template below).

### 4. Verify Structure

Check that these folders/files exist:

```
✅ _bmad/
✅ .cursor/rules/bmad/
✅ scripts/bmad-setup.py
✅ docs/BMAD_*.md
✅ .gitignore (with _bmad-output/)
```

### 5. Commit and Push

```bash
cd /path/to/virgin-devcontainer
git add .
git commit -m "Add complete BMAD methodology integration

- Add complete _bmad/ doctrine (agents, workflows, integrations)
- Add .cursor/rules/bmad/ activation layer
- Add bmad-setup.py for project initialization
- Add BMAD documentation
- Update README with BMAD integration instructions"
git push origin main
```

## README.md Template Addition

Add this section to `virgin-devcontainer/README.md`:

```markdown
## BMAD Methodology Integration

This template includes the complete **BMAD (Build, Manage, and Deploy) Methodology** integration for AI-assisted development with structured agent personalities, workflows, and rules.

### What's Included

- **Complete BMAD Doctrine** (`_bmad/`) - All agents, workflows, and integrations
- **Cursor Rules** (`.cursor/rules/bmad/`) - Activation layer for Cursor IDE
- **Setup Script** (`scripts/bmad-setup.py`) - Project initialization tool
- **Integration Rules** - OpenProject (work management) + Archon (knowledge repository)

### Quick Start

1. **Copy BMAD components** (already included in this template)
2. **Initialize your project:**
   ```bash
   python scripts/bmad-setup.py init
   ```
3. **Configure your project:**
   Edit `_bmad/_config/project-config.yaml` with your:
   - Project name and details
   - OpenProject project ID
   - Archon project ID (optional)
   - Team settings

4. **Start using BMAD agents:**
   - Reference agents: `@bmad/bmm/agents/pm` (Product Manager)
   - Reference workflows: `@bmad/bmm/workflows/create-epics-and-stories`
   - See `.cursor/rules/bmad/index.mdc` for complete list

### Documentation

- [BMAD Cursor Integration Explained](docs/BMAD_CURSOR_INTEGRATION_EXPLAINED.md)
- [BMAD Doctrine Integration Summary](docs/BMAD_DOCTRINE_INTEGRATION_SUMMARY.md)
- [Complete Checklist](docs/VIRGIN_DEVCONTAINER_CHECKLIST.md)

### Architecture

BMAD uses a two-tier architecture:

1. **`.cursor/rules/bmad/`** - Activation layer (lightweight pointers)
2. **`_bmad/`** - Doctrine layer (complete source of truth)

When you reference `@bmad/bmm/agents/pm`, Cursor loads the activation file which then loads the complete agent definition from `_bmad/bmm/agents/pm.md`.

### Integration Points

- **OpenProject** - Primary work management (Epics, Stories, Tasks)
- **Archon** - Knowledge repository (external documentation search)
- **MCP Servers** - Required: OpenProject MCP, Archon MCP

See `_bmad/integrations/` for detailed integration documentation.
```

## Verification Checklist

Before committing, verify:

- [ ] All `_bmad/` files copied (excluding `_bmad-output/`)
- [ ] All `.cursor/rules/bmad/` files copied
- [ ] `scripts/bmad-setup.py` is executable
- [ ] `project-config.yaml` has template values (not project-specific)
- [ ] `.gitignore` includes `_bmad-output/`
- [ ] README.md updated with BMAD section
- [ ] Documentation files copied to `docs/`
- [ ] No project-specific values in config files
- [ ] Git repository initialized (if new)

## Testing the Template

After setup, test with a new project:

```bash
# Create test project
mkdir test-project
cd test-project

# Copy from virgin-devcontainer
cp -r /path/to/virgin-devcontainer/_bmad/ .
cp -r /path/to/virgin-devcontainer/.cursor/rules/bmad/ .cursor/rules/
cp /path/to/virgin-devcontainer/scripts/bmad-setup.py scripts/

# Initialize
python scripts/bmad-setup.py init

# Verify
python scripts/bmad-setup.py validate
python scripts/bmad-setup.py show-config
```

## Troubleshooting

### Issue: Script fails with permission errors

**Solution:** Ensure you have write permissions to the target directory:
```bash
chmod -R u+w /path/to/virgin-devcontainer
```

### Issue: project-config.yaml has project-specific values

**Solution:** Manually edit and replace with template values (see "Clean Up Project-Specific Values" above)

### Issue: Files not copying correctly

**Solution:** Use manual copy method (Option 2) and verify each folder

### Issue: Git repository not initialized

**Solution:**
```bash
cd /path/to/virgin-devcontainer
git init
git remote add origin https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
```

## Next Steps After Setup

1. **Review the repository structure**
2. **Test the template** with a new project
3. **Update documentation** if needed
4. **Tag a release** (e.g., `v1.0.0-bmad-integration`)
5. **Announce** the updated template to your team

---

**Reference:** See `docs/VIRGIN_DEVCONTAINER_CHECKLIST.md` for complete file-by-file checklist.



