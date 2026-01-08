# Virgin Repository Update - genImage Doctrine Integration

**Date**: 2026-01-04  
**Status**: Ready for Sync  
**Doctrine**: genImage MCP Server for UX Design

## Summary

BMAD doctrine has been updated to include mandatory use of genImage MCP server for generating visual mockups when creating wireframes, UI designs, or design direction mockups. These changes need to be pushed to the `virgin-devcontainer` repository.

## Changes to Virgin Repository

When updating the `virgin-devcontainer` repository, ensure these files are updated:

### BMAD Doctrine Files (Updated):

1. `_bmad/bmm/agents/ux-designer.md` - Updated with genImage principle (MANDATORY use)
2. `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md` - Updated with genImage step (Step 8)
3. `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md` - Updated with genImage usage

## Update Steps

### Option 1: Using Preparation Script (Recommended)

```bash
# Clone virgin-devcontainer if not already cloned
cd /workspaces
git clone https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
cd virgin-devcontainer

# Run preparation script from mem0-rag
cd /workspaces/mem0-rag
./scripts/prepare-virgin-devcontainer.sh /workspaces/virgin-devcontainer

# The script will copy all BMAD files including the updated doctrine
```

### Option 2: Manual Copy

```bash
# From mem0-rag project
cd /workspaces/mem0-rag

# Copy updated agent file
cp _bmad/bmm/agents/ux-designer.md /path/to/virgin-devcontainer/_bmad/bmm/agents/

# Copy updated workflow files
cp _bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md /path/to/virgin-devcontainer/_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/
cp _bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md /path/to/virgin-devcontainer/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/

# Copy documentation
cp docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md /path/to/virgin-devcontainer/docs/
```

### Commit and Push

```bash
cd /path/to/virgin-devcontainer

# Add updated agent and workflow files
git add _bmad/bmm/agents/ux-designer.md
git add _bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md
git add _bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md

# Add documentation
git add docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md

# Commit
git commit -m "Add genImage MCP server doctrine for UX design

- Add core doctrine: genImage for wireframes and UI mockups
- Update UX Designer agent: Mandatory genImage usage
- Update wireframe workflow: Generate visual mockups with genImage
- Update UX design workflow: Use genImage for design direction mockups
- Use tenant_id='fedfina' for all genImage calls
- All wireframe/mockup creation must include genImage-generated visuals"

# Push
git push origin main
```

## Verification

After updating virgin repository, verify:

1. ✅ `_bmad/bmm/agents/ux-designer.md` includes genImage principle (MANDATORY)
2. ✅ Wireframe workflow includes genImage step (Step 8)
3. ✅ UX design workflow step 9 includes genImage usage
4. ✅ Documentation file copied to `docs/`

## Impact

This doctrine ensures that:

- All UX design work includes high-quality visual mockups
- Wireframes are automatically visualized using genImage
- Design direction mockups are generated as realistic UI images
- Consistent use of "fedfina" tenant for all genImage calls
- Future projects using virgin-devcontainer will have this doctrine built-in

## Related Files

- UX Designer Agent: `_bmad/bmm/agents/ux-designer.md` (contains genImage doctrine in principles)
- Wireframe Workflow: `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md`
- UX Design Workflow: `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md`

---

**Status**: Ready for sync to virgin-devcontainer  
**Next Action**: Run preparation script or manual copy commands above
