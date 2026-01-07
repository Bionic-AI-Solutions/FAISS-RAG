# Virgin DevContainer - Quick Reference

**Quick checklist for what to check into `virgin-devcontainer` repository**

## ✅ Must Include (Complete Folders)

```
✅ _bmad/                    # Complete BMAD doctrine
✅ .cursor/rules/bmad/        # Complete Cursor activation rules
✅ scripts/bmad-setup.py      # Setup script
✅ docs/BMAD_*.md             # Key documentation files
```

## 🔑 Critical Files

1. **`_bmad/integrations/cursor-rules.mdc`** - Always-applied integration rules
2. **`_bmad/_config/project-config.yaml`** - Template (user customizes)
3. **`.cursor/rules/bmad/index.mdc`** - Master index
4. **`.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`** - Lifecycle workflow
5. **`.cursor/rules/bmad/bmm/workflows/groom-story.mdc`** - Story grooming
6. **`.cursor/rules/bmad/bmm/workflows/dev-story-with-tasks.mdc`** - Dev workflow

## 📋 Copy Command

```bash
# From mem0-rag project to virgin-devcontainer
cp -r _bmad/ /path/to/virgin-devcontainer/
cp -r .cursor/rules/bmad/ /path/to/virgin-devcontainer/.cursor/rules/
cp scripts/bmad-setup.py /path/to/virgin-devcontainer/scripts/
cp docs/BMAD_*.md /path/to/virgin-devcontainer/docs/
```

## 🚫 Don't Include

- ❌ `_bmad-output/` (generated per project)
- ❌ Project-specific config values
- ❌ `.cursorrules` (user manages)

## 📖 Full Details

See `docs/VIRGIN_DEVCONTAINER_CHECKLIST.md` for complete details.



