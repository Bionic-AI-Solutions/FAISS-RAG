# BMad Master Ongoing Tasks

**Date:** 2026-01-07  
**Status:** ACTIVE  
**Owner:** BMad Master

## Mandatory Ongoing Tasks

### 1. Behavioral Rules Sync to Template Repository ⚠️ CRITICAL

**Task:** Sync behavioral rules to virgin-devcontainer template whenever behavioral rules are updated.

**Trigger:** Any change to `_bmad/integrations/*.mdc` files

**Process:**
1. Run sync script: `./scripts/sync-behavioral-rules-to-template.sh --check-only`
2. If changes detected, review: `./scripts/sync-behavioral-rules-to-template.sh --dry-run`
3. Execute sync: `./scripts/sync-behavioral-rules-to-template.sh`
4. Verify changes in GitHub: https://github.com/Bionic-AI-Solutions/virgin-devcontainer.git

**Files to Sync:**
- `_bmad/integrations/cursor-rules.mdc`
- `_bmad/integrations/testing-strategy.mdc`
- `_bmad/integrations/qa-workflow.mdc`
- Any other `.mdc` files in `_bmad/integrations/`

**Documentation:** `docs/BEHAVIORAL_RULES_SYNC_PROCESS.md`

**Last Sync:** [Update after each sync]

**Next Review:** After next behavioral rule change

---

## Task History

### 2026-01-07: Behavioral Rules Sync Process Established

**Action:** Created sync script and documentation for keeping virgin-devcontainer template updated with behavioral rules.

**Files Created:**
- `scripts/sync-behavioral-rules-to-template.sh` - Automated sync script
- `docs/BEHAVIORAL_RULES_SYNC_PROCESS.md` - Complete sync process documentation
- `docs/BMAD_MASTER_TASKS.md` - This file (ongoing task tracking)

**Files Updated:**
- `_bmad/integrations/cursor-rules.mdc` - Added sync process reference

**Rationale:** Ensure all future projects benefit from learned best practices and process improvements.

---

## Future Tasks

*Tasks will be added here as they are identified*

