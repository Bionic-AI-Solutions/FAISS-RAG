# Testing Procedures

This directory contains all core testing methodology procedures for BMAD projects.

## Purpose

These procedures define the fundamental testing requirements, responsibilities, and workflows that all BMAD agents must follow. They are part of the core development methodology (BMM), not external system integrations.

## Architecture

**Location:** `_bmad/bmm/testarch/procedures/`

**Why here?**
- Testing is core development methodology (BMM)
- BMM has dedicated test architecture (`testarch/`)
- Consistent with other test workflows in `_bmad/bmm/workflows/testarch/`
- Logically grouped with testing knowledge base in `_bmad/bmm/testarch/knowledge/`

**Cursor Rules:**
- Procedures are loaded via `_bmad/integrations/testing-methodology.mdc` (aggregator)
- Aggregator has `alwaysApply: true` to ensure procedures are always available
- Aggregator references procedures in this directory

## Procedures

### 1. Testing Strategy
**File:** `testing-strategy.md`

**Purpose:** Defines mandatory requirement for unit tests + integration tests.

**Key Points:**
- Every story MUST have both unit tests AND integration tests
- Unit tests: Fast, isolated, with mocks
- Integration tests: Real-world validation, with real services
- Agent responsibilities defined

### 2. QA Workflow
**File:** `qa-workflow.md`

**Purpose:** Complete workflow for task/story validation, bug management, and closure.

**Key Points:**
- Task → Story → Epic closure workflow
- Bug management and iteration cycle
- Status flows and role responsibilities
- Checklist templates

### 3. System Readiness
**File:** `system-readiness.md`

**Purpose:** Responsibility for ensuring dependency systems are running before integration tests.

**Key Points:**
- PRIMARY: Test Team / TEA Agent responsible
- SECONDARY: Dev Agent responsible during development
- Service startup procedures
- Failure scenarios and escalation

### 4. Test Data Responsibility
**File:** `test-data-responsibility.md`

**Purpose:** Responsibility for creating test data and fixtures.

**Key Points:**
- Mock fixtures (unit tests): Dev Agent
- Real test data (integration tests): Dev Agent creates, Test Team validates
- Shared fixtures: TEA Agent / Test Team
- Integration test patterns: Test Team / TEA
- Data factories: TEA (framework), Dev (story-specific)

### 5. Browser Testing
**File:** `browser-testing.md`

**Purpose:** Mandatory browser-based integration testing procedure for UI development.

**Key Points:**
- Pre-testing checklist
- Complete user journey testing
- Cross-browser and responsive design testing
- Documentation requirements
- Escalation process

## Templates

### Browser Testing Checklist
**File:** `templates/browser-testing-checklist.md`

**Purpose:** Reusable checklist template for browser testing sessions.

## Usage

### For Agents

**All agents should reference these procedures via:**
- `_bmad/integrations/testing-methodology.mdc` (quick reference)
- Direct file references in this directory (detailed procedures)

### For Developers

**When implementing:**
1. Read `testing-strategy.md` for test requirements
2. Read `test-data-responsibility.md` for fixture creation
3. Read `system-readiness.md` for service management

### For Test Team / TEA

**When validating:**
1. Read `qa-workflow.md` for validation workflow
2. Read `system-readiness.md` for service verification
3. Read `test-data-responsibility.md` for test data validation

### For QA / UX Teams

**When testing UI:**
1. Read `browser-testing.md` for testing procedure
2. Use `templates/browser-testing-checklist.md` for test sessions

## Integration

### With BMM Test Architecture

**Workflows:** `_bmad/bmm/workflows/testarch/`
- `testarch-framework` - Uses procedures for framework setup
- `testarch-atdd` - Uses procedures for test-first development
- `testarch-automate` - Uses procedures for test automation

**Knowledge Base:** `_bmad/bmm/testarch/knowledge/`
- `data-factories.md` - Referenced by test-data-responsibility.md
- `fixture-architecture.md` - Referenced by test-data-responsibility.md
- `test-levels-framework.md` - Referenced by testing-strategy.md

### With Integrations

**Cursor Rules:** `_bmad/integrations/testing-methodology.mdc`
- Aggregator that loads these procedures
- Provides quick reference
- Ensures procedures are always available

**OpenProject Integration:** `_bmad/integrations/openproject/`
- Procedures reference OpenProject for work management
- Status flows align with OpenProject status IDs

## Maintenance

### Updating Procedures

1. Edit procedure file in this directory
2. Update version number and last updated date
3. Update references in other procedures if needed
4. Update aggregator (`testing-methodology.mdc`) if structure changes

### Adding New Procedures

1. Create new `.md` file in this directory
2. Follow existing procedure format
3. Add reference to aggregator (`testing-methodology.mdc`)
4. Update this README

### Version Control

- Procedures are versioned (Document Version field)
- Last updated date tracked
- Review frequency specified (typically Quarterly)

## References

- **BMM Test Architecture:** `_bmad/bmm/testarch/`
- **Test Workflows:** `_bmad/bmm/workflows/testarch/`
- **Test Knowledge Base:** `_bmad/bmm/testarch/knowledge/`
- **Cursor Rules Aggregator:** `_bmad/integrations/testing-methodology.mdc`
- **Architecture Analysis:** `_bmad/ARCHITECTURE_ANALYSIS.md`

---

**Last Updated:** 2026-01-08  
**Maintained By:** Test Team / TEA Agent
