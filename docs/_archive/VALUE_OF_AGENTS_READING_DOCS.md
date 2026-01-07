# Value Analysis: Should BMAD Agents Read from `docs/`?

**Date:** 2026-01-07  
**Purpose:** Analyze whether BMAD agents should read project-specific requirements from `docs/` directory

## The Question

**"Is there value in having BMAD agents read from `docs/` since all rules are expected to be part of BMAD core understanding already?"**

## Current Architecture

### BMAD Framework (`_bmad/`)
- ✅ **Generic methodology** - Reusable across projects
- ✅ **Configuration-driven** - `project-config.yaml` for project-specific settings
- ✅ **Integration rules** - `cursor-rules.mdc` (always applied)
- ✅ **Workflow patterns** - Standard processes

### Project Documentation (`docs/`)
- ✅ **Project-specific requirements** - Testing strategy, QA workflow
- ✅ **Human reference** - For developers, test team, PM
- ✅ **Historical records** - Verification documents, status reports
- ❌ **NOT automatically loaded** by agents

## Analysis: Where Should Project-Specific Rules Live?

### Option 1: Keep in `docs/` (Current State)

**Current Pattern:**
- `docs/TESTING_STRATEGY.md` - Project-specific testing requirements
- `docs/QA_TESTING_WORKFLOW.md` - Project-specific QA process
- Agents don't automatically load these
- Humans read them for understanding

**Pros:**
- ✅ **Flexible** - Can document complex requirements in natural language
- ✅ **Evolves naturally** - Easy to update as project matures
- ✅ **Human-readable** - Clear for team members
- ✅ **Separation of concerns** - Framework vs project-specific

**Cons:**
- ❌ **Not automatically enforced** - Agents don't know unless explicitly told
- ❌ **Requires explicit loading** - Workflow steps must say "read docs/X.md"
- ❌ **Easy to miss** - Requirements might not be followed if not loaded

### Option 2: Move to `project-config.yaml`

**Proposed Pattern:**
```yaml
# _bmad/_config/project-config.yaml
testing:
  require_unit_tests: true
  require_integration_tests: true
  unit_test_location: "tests/unit/"
  integration_test_location: "tests/integration/"
  
workflows:
  story_requirements:
    require_unit_tests: true
    require_integration_tests: true
    require_verification_docs: true
```

**Pros:**
- ✅ **Automatically loaded** - Agents read config.yaml during activation
- ✅ **Structured** - Easy to parse and enforce programmatically
- ✅ **Enforceable** - Agents can check requirements automatically
- ✅ **Version controlled** - Part of BMAD configuration

**Cons:**
- ❌ **Limited flexibility** - Complex requirements hard to express in YAML
- ❌ **Less readable** - Not as clear for humans
- ❌ **Config bloat** - Could make config.yaml very large

### Option 3: Hybrid Approach (Recommended)

**Pattern:**
- **Simple requirements** → `project-config.yaml` (automatically loaded)
- **Complex requirements** → `docs/` (explicitly loaded by workflow steps)
- **Universal best practices** → BMAD framework (always applied)

**Example:**

```yaml
# project-config.yaml - Simple, structured requirements
testing:
  require_unit_tests: true
  require_integration_tests: true
```

```markdown
# docs/TESTING_STRATEGY.md - Complex, detailed requirements
## Unit Tests (with Mocks)
- Test logic in isolation
- Mock external services (FAISS, Meilisearch, Redis)
- Test tenant isolation, error handling...

## Integration Tests (with Real Services)
- Test with real FAISS indices
- Verify performance requirements (<150ms p95)
- Test end-to-end workflows...
```

**Workflow Step:**
```markdown
## Step: Verify Testing Requirements

1. Read `project-config.yaml` → Check `testing.require_unit_tests`
2. Read `docs/TESTING_STRATEGY.md` → Understand detailed requirements
3. Verify unit tests exist in `tests/unit/`
4. Verify integration tests exist in `tests/integration/`
```

## Value Assessment

### ✅ Value in Agents Reading `docs/` for:

1. **Complex Project-Specific Requirements**
   - Testing strategies with detailed explanations
   - QA workflows with multiple steps
   - Project-specific architecture patterns
   - Domain-specific business rules

2. **Enforcement During Workflows**
   - When workflow step needs to verify requirements
   - When agent needs to understand project context
   - When requirements are too complex for config.yaml

3. **Project Evolution**
   - Requirements that change over time
   - Lessons learned documented in docs/
   - Project-specific best practices

### ❌ Less Value for:

1. **Simple Boolean Flags**
   - "Require unit tests: yes/no" → Better in config.yaml

2. **Universal Best Practices**
   - "Always write tests" → Should be in BMAD framework

3. **Historical Records**
   - Verification documents, status reports → Humans only

## Recommended Approach

### Tier 1: BMAD Framework (Always Applied)
**For:** Universal best practices, methodology patterns

**Example:**
- "Always write tests before implementation"
- "Follow red-green-refactor cycle"
- "Update work package status when starting/completing work"

### Tier 2: `project-config.yaml` (Automatically Loaded)
**For:** Simple, structured project-specific settings

**Example:**
```yaml
testing:
  require_unit_tests: true
  require_integration_tests: true
  
workflows:
  story_min_hours: 0.5
  story_max_hours: 4
```

### Tier 3: `docs/` (Explicitly Loaded When Needed)
**For:** Complex, detailed project-specific requirements

**Example:**
- `docs/TESTING_STRATEGY.md` - Detailed testing requirements
- `docs/QA_TESTING_WORKFLOW.md` - Complete QA process
- `docs/ARCHITECTURE_DECISIONS.md` - Project-specific architecture

**Loading Pattern:**
```markdown
## Workflow Step: Verify Testing

1. Check config.yaml: `testing.require_unit_tests` → Must be true
2. Read `docs/TESTING_STRATEGY.md` → Understand detailed requirements
3. Verify requirements met
```

## Implementation Recommendation

### For Testing Requirements (Current Example)

**1. Add to `project-config.yaml`:**
```yaml
testing:
  require_unit_tests: true
  require_integration_tests: true
  unit_test_location: "tests/unit/"
  integration_test_location: "tests/integration/"
```

**2. Keep `docs/TESTING_STRATEGY.md`:**
- Detailed explanations
- Examples and patterns
- Best practices
- Complex requirements

**3. Update Workflow Steps:**
```markdown
## Step: Verify Testing Requirements

1. Read `project-config.yaml` → Check `testing.require_unit_tests`
2. If true, read `docs/TESTING_STRATEGY.md` → Understand requirements
3. Verify unit tests exist in `{testing.unit_test_location}`
4. Verify integration tests exist in `{testing.integration_test_location}`
```

## Conclusion

### ✅ YES, There IS Value in Agents Reading `docs/`

**When:**
- Requirements are complex and need detailed explanation
- Requirements are project-specific (not universal)
- Requirements need to be enforced during workflows
- Requirements evolve over time

**How:**
- Use **hybrid approach**: Simple flags in config.yaml, complex details in docs/
- **Explicit loading**: Workflow steps say "read docs/X.md" when needed
- **Automatic checking**: Agents check config.yaml flags automatically

### Current State Assessment

**Current approach is good but could be enhanced:**

✅ **Good:**
- `docs/` serves as human reference
- Complex requirements documented clearly
- Flexible and evolvable

⚠️ **Could Improve:**
- Add simple flags to `project-config.yaml` for automatic checking
- Update workflow steps to explicitly load `docs/` when needed
- Make requirements enforceable, not just documented

### Final Recommendation

**Use Three-Tier Approach:**

1. **BMAD Framework** → Universal best practices (always applied)
2. **`project-config.yaml`** → Simple project settings (automatically loaded)
3. **`docs/`** → Complex project requirements (explicitly loaded when needed)

**This gives you:**
- ✅ Automatic enforcement (config.yaml)
- ✅ Detailed understanding (docs/)
- ✅ Universal patterns (BMAD framework)
- ✅ Flexibility for project evolution


