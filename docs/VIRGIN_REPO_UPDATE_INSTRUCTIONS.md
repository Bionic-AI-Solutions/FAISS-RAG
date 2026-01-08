# Virgin Repository Update Instructions - NFR Verification

## Summary

BMAD doctrine has been updated to include mandatory NFR verification in every Epic. These changes need to be pushed to the `virgin-devcontainer` repository.

## Files to Update

### Core Doctrine Files:
1. `.cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc`
2. `.cursor/rules/bmad/bmm/workflows/groom-story.mdc`
3. `.cursor/rules/bmad/bmm/workflows/test-validation.mdc`

### Documentation Files:
4. `docs/NFR_VERIFICATION_IN_BMAD_DOCTRINE.md`
5. `docs/VIRGIN_REPO_NFR_UPDATE.md`
6. `docs/BMAD_DOCTRINE_NFR_UPDATE_COMPLETE.md`

## Update Steps

### Option 1: Using Preparation Script

```bash
# Clone virgin-devcontainer if not already cloned
cd /workspaces
git clone https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
cd virgin-devcontainer

# Run preparation script from mem0-rag
cd /workspaces/mem0-rag
./scripts/prepare-virgin-devcontainer.sh /workspaces/virgin-devcontainer

# The script will copy all BMAD files including the updated workflows
```

### Option 2: Manual Copy

```bash
# From mem0-rag project
cd /workspaces/mem0-rag

# Copy updated workflow files
cp .cursor/rules/bmad/bmm/workflows/epic-story-lifecycle.mdc /path/to/virgin-devcontainer/.cursor/rules/bmad/bmm/workflows/
cp .cursor/rules/bmad/bmm/workflows/groom-story.mdc /path/to/virgin-devcontainer/.cursor/rules/bmad/bmm/workflows/
cp .cursor/rules/bmad/bmm/workflows/test-validation.mdc /path/to/virgin-devcontainer/.cursor/rules/bmad/bmm/workflows/

# Copy documentation
cp docs/NFR_VERIFICATION_IN_BMAD_DOCTRINE.md /path/to/virgin-devcontainer/docs/
cp docs/VIRGIN_REPO_NFR_UPDATE.md /path/to/virgin-devcontainer/docs/
cp docs/BMAD_DOCTRINE_NFR_UPDATE_COMPLETE.md /path/to/virgin-devcontainer/docs/
```

### Commit and Push

```bash
cd /path/to/virgin-devcontainer
git add .cursor/rules/bmad/bmm/workflows/*.mdc docs/NFR_*.md docs/VIRGIN_REPO_*.md docs/BMAD_DOCTRINE_*.md
git commit -m "Add NFR verification to BMAD doctrine

- Update epic-story-lifecycle.mdc: Add Story X.NFR requirement
- Update groom-story.mdc: Add Task X.Y.NFR requirement
- Update test-validation.mdc: Add NFR verification to Epic closure
- Add NFR verification documentation
- Ensure every Epic includes NFR verification story with tasks"
git push origin main
```

## Verification

After updating, verify:
- [ ] Epic lifecycle workflow includes NFR verification story requirement
- [ ] Story grooming workflow includes NFR verification task requirement
- [ ] Test validation workflow includes NFR verification in Epic closure
- [ ] Documentation includes NFR verification guide

## Impact

**Before:** NFRs were documented but not systematically verified.

**After:** Every Epic MUST include:
- Story X.NFR for NFR verification
- Tasks to verify connection pooling, concurrency, availability, scalability, performance
- NFR verification report before Epic closure


