# genImage Doctrine Update - Complete

**Date**: 2026-01-04  
**Status**: ✅ Complete - Ready for Virgin Repository Sync  
**Doctrine**: genImage MCP Server for UX Design

---

## Summary

BMAD core doctrine has been updated to mandate the use of genImage MCP server for generating visual mockups when creating wireframes, UI designs, or design direction mockups. All UX design work must now include genImage-generated visual mockups using tenant_id="fedfina".

---

## Changes Made

### 1. UX Designer Agent Updated

**File**: `_bmad/bmm/agents/ux-designer.md`
- Added mandatory principle: Use genImage for wireframes and mocks
- Uses tenant_id="fedfina" for all genImage calls

### 3. Wireframe Workflow Updated

**File**: `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md`
- Added Step 8: Generate Visual Mockup with genImage (MANDATORY)
- Generates high-quality UI mockups after wireframe creation
- Saves mockup images alongside wireframe files

### 4. UX Design Workflow Updated

**File**: `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md`
- Updated Step 2: Generate Visual Mockups with genImage
- Replaces HTML-only approach with genImage-generated visual mockups
- Creates realistic UI design images for each design direction

### 5. Documentation Created

**File**: `docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md`
- Virgin repository update instructions
- Manual copy commands
- Verification checklist

---

## Files Changed

### New Files:
1. ✅ `docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md` - Virgin repo update guide
2. ✅ `docs/GENIMAGE_DOCTRINE_UPDATE_COMPLETE.md` - This summary document

### Updated Files (BMAD Doctrine):
1. ✅ `_bmad/bmm/agents/ux-designer.md` - Added genImage principle
2. ✅ `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md` - Added genImage step
3. ✅ `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md` - Updated with genImage

---

## Doctrine Requirements

### When to Use genImage

1. **Wireframe Creation**: After creating wireframe designs, ALWAYS generate visual UI mockups
2. **Design Direction Mockups**: When creating design direction variations, generate visual mockups
3. **UI Component Design**: When designing UI components, generate visual mockups
4. **User Journey Visualization**: When visualizing user journeys, generate mockup images
5. **Any UI/UX Visual Design Work**: Whenever visual representation is needed

### genImage Configuration

- **Tenant ID**: ALWAYS use `tenant_id="fedfina"` for all genImage calls
- **Prompt Quality**: Create detailed, descriptive prompts including layout, colors, typography, components
- **File Organization**: Save mockups in `{planning_artifacts}/ux-design-mockups/`
- **Naming**: `{design-type}-{description}-{timestamp}.png`

---

## Virgin Repository Sync

### Files to Sync

The following files need to be synced to `virgin-devcontainer`:

1. `_bmad/bmm/agents/ux-designer.md` (UPDATED - contains genImage doctrine)
2. `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md` (UPDATED - includes genImage step)
3. `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md` (UPDATED - uses genImage)
4. `docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md` (NEW)
5. `docs/GENIMAGE_DOCTRINE_UPDATE_COMPLETE.md` (NEW)

### Sync Method

**Option 1: Automated Script (Recommended)**
```bash
cd /workspaces/mem0-rag
./scripts/prepare-virgin-devcontainer.sh /path/to/virgin-devcontainer
```

The script will automatically copy all `_bmad/` files including the new doctrine directory.

**Option 2: Manual Copy**
See `docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md` for detailed manual copy commands.

### Verification Checklist

After syncing to virgin-devcontainer, verify:

- [ ] `_bmad/bmm/agents/ux-designer.md` includes genImage principle (MANDATORY)
- [ ] Wireframe workflow includes genImage step (Step 8)
- [ ] UX design workflow step 9 includes genImage usage
- [ ] Documentation files copied to `docs/`

---

## Impact

### Before This Doctrine

- Wireframes were created as ASCII/text diagrams only
- Design directions were HTML-based or text descriptions
- No standardized visual mockup generation
- Inconsistent visual design representation

### After This Doctrine

- ✅ All wireframes automatically get visual UI mockups via genImage
- ✅ Design direction mockups are high-quality generated images
- ✅ Consistent use of "fedfina" tenant for all genImage calls
- ✅ Standardized visual design representation
- ✅ Future projects using virgin-devcontainer will have this built-in

---

## Enforcement

This doctrine is enforced at multiple levels:

1. **Agent Level**: UX Designer agent principles include mandatory genImage usage
2. **Workflow Level**: Wireframe and UX design workflows include genImage steps
3. **Code Review**: All UX design outputs should include genImage-generated mockups

**No exceptions** - This is core doctrine and must be followed for all UX design work involving visual mockups or wireframes.

---

## Next Steps

1. ✅ Doctrine created and integrated
2. ✅ Agent and workflows updated
3. ✅ Documentation created
4. ⏭️ **Sync to virgin-devcontainer repository** (Pending)
5. ⏭️ Verify in virgin-devcontainer after sync

---

## Related Documents

- Virgin Repo Update Guide: `docs/VIRGIN_REPO_GENIMAGE_DOCTRINE_UPDATE.md`
- UX Designer Agent (Doctrine): `_bmad/bmm/agents/ux-designer.md` (contains genImage principle)
- Wireframe Workflow: `_bmad/bmm/workflows/excalidraw-diagrams/create-wireframe/instructions.md`
- UX Design Workflow: `_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md`

---

**Status**: ✅ Complete in mem0-rag repository  
**Next Action**: Sync to virgin-devcontainer repository  
**Ready for**: Virgin repository update
