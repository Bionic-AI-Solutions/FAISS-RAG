# Behavioral Rules Sync Process

**Date:** 2026-01-07  
**Status:** MANDATORY PROCESS  
**Owner:** BMad Master / Development Team

## Overview

**CRITICAL:** Whenever behavioral rules are updated in this project, they MUST be synced to the [virgin-devcontainer template repository](https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git) to ensure all future projects benefit from our learnings.

## What Gets Synced

**Behavioral Rules Files** (`_bmad/integrations/*.mdc`):
- `cursor-rules.mdc` - Core integration rules
- `testing-strategy.mdc` - Testing requirements (unit + integration tests)
- `qa-workflow.mdc` - QA testing and story closure workflow
- Any other `.mdc` files in `_bmad/integrations/`

**Why These Files:**
- These are **behavioral rules** that define HOW agents work
- They are **alwaysApply: true** - automatically loaded by all agents
- They represent **learned best practices** that should be in all projects from day one

## When to Sync

**Sync behavioral rules whenever:**
- ✅ New behavioral rule file is created (`_bmad/integrations/*.mdc`)
- ✅ Existing behavioral rule is updated (testing strategy, QA workflow, etc.)
- ✅ Process improvements are documented in behavioral rules
- ✅ After major architectural decisions are codified in rules

**Do NOT sync:**
- ❌ Project-specific configuration (`project-config.yaml`)
- ❌ Project-specific documentation (`docs/`)
- ❌ Implementation artifacts (`_bmad-output/`)
- ❌ Story files or verification documents

## Sync Process

### Option 1: Automated Sync Script (Recommended)

```bash
# Check if sync is needed (dry-run)
./scripts/sync-behavioral-rules-to-template.sh --check-only

# Preview changes (dry-run)
./scripts/sync-behavioral-rules-to-template.sh --dry-run

# Perform sync
./scripts/sync-behavioral-rules-to-template.sh
```

**What the script does:**
1. Finds all behavioral rule files (`_bmad/integrations/*.mdc`)
2. Clones/updates virgin-devcontainer repository
3. Copies updated files to template repository
4. Commits changes with descriptive message
5. Provides push instructions

### Option 2: Manual Sync

If script is unavailable, manually sync:

```bash
# 1. Clone/update virgin-devcontainer
cd ~/.bmad-cache
git clone https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
# OR if already cloned:
cd virgin-devcontainer
git pull origin main

# 2. Copy behavioral rules
cp /workspaces/mem0-rag/_bmad/integrations/*.mdc \
   ~/.bmad-cache/virgin-devcontainer/_bmad/integrations/

# 3. Review changes
cd ~/.bmad-cache/virgin-devcontainer
git diff

# 4. Commit and push
git add _bmad/integrations/*.mdc
git commit -m "chore: sync behavioral rules from mem0-rag project

Synced behavioral rules to ensure new projects get latest improvements."
git push origin main
```

## Verification Checklist

After syncing, verify:

- [ ] All `.mdc` files from `_bmad/integrations/` are in template
- [ ] File contents match exactly (no project-specific references)
- [ ] Commit message describes what changed and why
- [ ] Changes are pushed to `main` branch
- [ ] GitHub repository shows updated files

## Integration with Workflow

**BMad Master Responsibility:**
- Monitor for behavioral rule changes
- Execute sync process after significant updates
- Document sync in project notes

**Development Team Responsibility:**
- Notify BMad Master when behavioral rules are updated
- Review sync script output before pushing
- Verify template repository after sync

## Example Sync Scenarios

### Scenario 1: New Testing Strategy Added

**Change:** Created `testing-strategy.mdc` with unit + integration test requirements

**Sync Action:**
```bash
./scripts/sync-behavioral-rules-to-template.sh
# Review output
# Push to virgin-devcontainer
```

**Result:** All new projects get testing strategy from day one

### Scenario 2: QA Workflow Updated

**Change:** Updated `qa-workflow.mdc` with verification doc process

**Sync Action:**
```bash
./scripts/sync-behavioral-rules-to-template.sh --dry-run  # Preview
./scripts/sync-behavioral-rules-to-template.sh            # Execute
```

**Result:** All new projects get updated QA workflow

### Scenario 3: Integration Test Patterns Added

**Change:** Added integration test patterns section to `testing-strategy.mdc`

**Sync Action:**
```bash
./scripts/sync-behavioral-rules-to-template.sh
```

**Result:** All new projects get integration test pattern guidance

## Benefits

**For This Project:**
- ✅ Process improvements are preserved
- ✅ Knowledge is shared across projects
- ✅ Consistent behavior across all BMAD projects

**For Future Projects:**
- ✅ Start with latest best practices
- ✅ No need to rediscover process improvements
- ✅ Consistent agent behavior from day one

## Troubleshooting

### Script Fails: Repository Not Found

**Solution:** Script will auto-clone if repository doesn't exist

### Script Fails: Permission Denied

**Solution:** Ensure you have write access to virgin-devcontainer repository

### Files Don't Match After Sync

**Solution:** 
1. Check file paths are correct
2. Verify no project-specific content in behavioral rules
3. Re-run sync script

### Template Repository Has Conflicts

**Solution:**
1. Pull latest changes: `git pull origin main`
2. Resolve conflicts manually
3. Re-run sync script

## Related Documentation

- **Virgin DevContainer Repository:** https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git
- **BMAD Architecture:** `docs/BMAD_ARCHITECTURE_CLARIFICATION.md`
- **Behavioral Rules:** `_bmad/integrations/`

## Maintenance

**Review Frequency:** After each behavioral rule update

**Last Sync:** [Update this date after each sync]

**Next Review:** After next behavioral rule change

