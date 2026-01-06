# OpenProject Sync Responsibility & Workflow

## Responsibility Assignment

### Primary Owner: **Product Manager (PM)**

The **Product Manager** is responsible for ensuring that all epics, features, and stories from `epics.md` are accurately compiled and synchronized to OpenProject using MCP tools.

**PM Responsibilities:**
- ✅ Verify completeness: Ensure all epics from `epics.md` are created in OpenProject
- ✅ Maintain accuracy: Keep OpenProject structure aligned with `epics.md`
- ✅ Coordinate sync: Execute or oversee the sync process after epic/story updates
- ✅ Validate hierarchy: Ensure parent-child relationships are correctly established
- ✅ Quality check: Verify that all stories have complete acceptance criteria in OpenProject

### Supporting Role: **Scrum Master (SM)**

The **Scrum Master** supports the PM by:
- ✅ Assisting with story breakdown and acceptance criteria
- ✅ Ensuring stories are properly sized and ready for development
- ✅ Validating that OpenProject work packages align with sprint planning needs
- ✅ Coordinating with development team on story readiness

### When Sync Should Occur

1. **After Epic Creation Workflow**: When `create-epics-and-stories` workflow completes
2. **After Epic Updates**: When epics are modified in `epics.md`
3. **After Story Updates**: When stories are added, modified, or removed
4. **Before Sprint Planning**: Ensure OpenProject is up-to-date for sprint planning
5. **After PRD/Architecture Changes**: When requirements change significantly

## Sync Workflow

### Step 1: Verify Source Document

```bash
# Check epics.md for completeness
cat _bmad-output/planning-artifacts/epics.md | grep -E "^### Epic|^#### Story"
```

### Step 2: Run Sync Script

```bash
# Sync epics.md to OpenProject
python scripts/sync_epics_to_openproject.py
```

### Step 3: Verify in OpenProject

1. Open project in OpenProject UI
2. Verify all epics are present
3. Verify all features are present
4. Verify all stories are present
5. Check parent-child relationships

### Step 4: Store Documentation in Archon (Optional - Knowledge Repository)

After OpenProject sync, optionally store project documentation in Archon (knowledge repository):

```python
# Use Archon MCP tools to store project documents, specs, research
# Archon is ONLY for knowledge/document management, NOT task management
# See CLAUDE.md for workflow
```

## Sync Process Details

### What Gets Synced

1. **Epics**: All epics from `epics.md` → OpenProject Epic work packages
2. **Features**: All features (if explicitly defined) → OpenProject Feature work packages
3. **Stories**: All user stories → OpenProject User Story work packages
4. **Acceptance Criteria**: Full acceptance criteria from stories
5. **Parent-Child Relationships**: Epic → Feature → Story hierarchy

### Sync Rules

- **Idempotent**: Running sync multiple times should be safe (updates existing, creates missing)
- **Non-destructive**: Never delete work packages unless explicitly requested
- **Incremental**: Only sync what's changed or missing
- **Validation**: Verify work package IDs match between runs

## Tools & Scripts

### Available Scripts

1. **`scripts/sync_epics_to_openproject.py`** (to be created)
   - Parses `epics.md`
   - Creates/updates epics, features, stories in OpenProject
   - Sets parent-child relationships

2. **`scripts/set_openproject_parents.py`** (existing)
   - Sets parent-child relationships for existing work packages
   - Use when structure exists but relationships are missing

### MCP Tools Used

- `mcp_openproject_create_project()` - Create project
- `mcp_openproject_create_work_package()` - Create epics, features, stories
- `mcp_openproject_update_work_package()` - Update existing work packages
- `mcp_openproject_list_work_packages()` - Verify what exists
- `mcp_openproject_get_work_package()` - Get details for updates

## Quality Checklist

Before considering sync complete, verify:

- [ ] All epics from `epics.md` exist in OpenProject
- [ ] All stories from `epics.md` exist in OpenProject
- [ ] All acceptance criteria are present and complete
- [ ] Parent-child relationships are correctly established
- [ ] Work package types are correct (Epic, Feature, User Story)
- [ ] Project ID matches expected project
- [ ] No duplicate work packages created

## Troubleshooting

### Missing Epics/Stories

**Symptom**: Some epics or stories from `epics.md` are missing in OpenProject

**Solution**:
1. Check if they were filtered out (e.g., Phase 2 items)
2. Verify sync script ran completely
3. Check for errors in sync script output
4. Manually create missing items if needed

### Incorrect Parent Relationships

**Symptom**: Parent-child relationships are wrong or missing

**Solution**:
1. Run `scripts/set_openproject_parents.py`
2. Or manually set in OpenProject UI
3. Verify work package IDs are correct

### Duplicate Work Packages

**Symptom**: Same epic/story appears multiple times

**Solution**:
1. Check sync script for duplicate detection
2. Manually delete duplicates in OpenProject
3. Update sync script to check for existing work packages before creating

## Integration with BMAD Workflows

### Workflow: `create-epics-and-stories`

**Output**: `_bmad-output/planning-artifacts/epics.md`

**Next Step**: Sync to OpenProject

```bash
# After workflow completes
python scripts/sync_epics_to_openproject.py
```

### Workflow: `sprint-planning`

**Prerequisite**: OpenProject must be up-to-date

**Action**: PM ensures sync is complete before sprint planning begins

## Reporting

PM should report sync status:

- ✅ **Complete**: All epics/stories synced successfully
- ⚠️ **Partial**: Some items synced, some failed (list failures)
- ❌ **Failed**: Sync failed (provide error details)

## Escalation

If sync issues persist:

1. **PM** documents the issue
2. **PM** attempts manual sync via OpenProject UI
3. **PM** escalates to **Dev** team if script issues
4. **PM** escalates to **Architect** if structural issues

## Best Practices

1. **Regular Syncs**: Don't let `epics.md` and OpenProject drift apart
2. **Version Control**: Commit `epics.md` changes before syncing
3. **Validation**: Always verify sync results in OpenProject UI
4. **Documentation**: Document any manual changes made in OpenProject
5. **Communication**: Notify team when major syncs occur



