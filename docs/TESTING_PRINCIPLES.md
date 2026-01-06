# Testing Principles

## Core Principle: Tests Must Align with Desired Functionality

**CRITICAL RULE**: Tests must validate the desired functionality as specified in Story/Task acceptance criteria. Tests should NOT be changed to pass broken functionality.

## Testing Workflow

### 1. Test-Driven Development (TDD) Approach

1. **Read Acceptance Criteria**: Understand what the story/task requires
2. **Write Tests First**: Create tests that validate the acceptance criteria
3. **Implement Functionality**: Write code to make tests pass
4. **Refactor**: Improve code while keeping tests passing

### 2. When Tests Fail

**DO:**

- ✅ Fix the implementation to match the acceptance criteria
- ✅ Verify the implementation meets all acceptance criteria
- ✅ Ensure tests validate the correct behavior

**DON'T:**

- ❌ Change tests to pass broken functionality
- ❌ Lower test expectations to match incorrect implementation
- ❌ Remove test assertions to make tests pass
- ❌ Mock away real functionality that should be tested

### 3. Test Alignment Verification

Before marking tests as complete, verify:

1. **Acceptance Criteria Coverage**: Each acceptance criterion has corresponding tests
2. **Test Assertions**: Tests assert the correct behavior, not just that code runs
3. **Edge Cases**: Tests cover error cases, boundary conditions, and failure scenarios
4. **Performance Requirements**: Tests validate performance requirements (e.g., <50ms)
5. **Error Handling**: Tests verify proper error responses (e.g., 401 Unauthorized, FR-ERROR-003)

### 4. Test Update Scenarios

**Valid Test Updates:**

- ✅ Updating outdated tests when functionality changes (e.g., feature is now implemented)
- ✅ Adding new tests for newly discovered edge cases
- ✅ Refactoring test code for clarity without changing assertions
- ✅ Fixing test setup/mocking to properly test implementation

**Invalid Test Updates:**

- ❌ Changing assertions to match incorrect implementation
- ❌ Removing test cases because implementation doesn't support them
- ❌ Mocking away functionality that should be tested
- ❌ Lowering expectations (e.g., changing <50ms to <500ms)

## Example: Story 1.5 Authentication Middleware

### Acceptance Criteria

- OAuth 2.0 token validation
- API key authentication
- Performance <50ms
- 401 Unauthorized with FR-ERROR-003 for invalid auth

### Test Alignment

**✅ Correct Approach:**

- Tests validate OAuth token extraction from Authorization header
- Tests validate API key extraction from X-API-Key header
- Tests validate performance monitoring (<50ms)
- Tests validate error responses (401, FR-ERROR-003)
- Tests validate audit logging for all authentication attempts

**❌ Incorrect Approach:**

- Changing performance test from <50ms to <500ms because implementation is slow
- Removing error handling tests because implementation doesn't return proper errors
- Mocking away OAuth validation to make tests pass

### Test Update Example

**Scenario**: Test `test_authenticate_api_key_not_implemented` fails because API key authentication IS implemented.

**✅ Correct Fix:**

- Update test to `test_authenticate_api_key_fallback_when_oauth_disabled`
- Test validates that API key auth works when OAuth is disabled
- Test aligns with actual implemented functionality

**❌ Incorrect Fix:**

- Remove the test entirely
- Change test to expect API key auth to fail
- Mock away API key validation

## Verification Checklist

Before marking tests as complete:

- [ ] All acceptance criteria have corresponding tests
- [ ] Tests validate correct behavior, not just that code runs
- [ ] Error cases are tested (invalid tokens, expired keys, etc.)
- [ ] Performance requirements are tested
- [ ] Error responses match requirements (status codes, error codes)
- [ ] No tests were changed to pass broken functionality
- [ ] Implementation fixes were made when tests failed
- [ ] Test assertions match acceptance criteria

## Story Verification Documents

**Practice**: When a story is complete, create verification documents and attach them to the OpenProject story work package:

1. **Story Verification Report** (`docs/STORY_X_Y_VERIFICATION.md`)

   - Acceptance criteria verification
   - Implementation verification
   - Test coverage summary
   - Files created/modified

2. **Test Alignment Verification** (`docs/STORY_X_Y_TEST_ALIGNMENT_VERIFICATION.md`)
   - Test alignment matrix with acceptance criteria
   - Test change analysis
   - Error code and performance verification
   - Recommendations

**Attach to OpenProject**:

- Use `mcp_openproject_add_work_package_attachment()` to add verification documents
- This provides traceability and supports test team validation
- Documents remain linked to the story for future reference

## Related Documentation

- `docs/DEV_AGENT_INSTRUCTIONS.md` - Development workflow (includes attachment process)
- `docs/TEST_TEAM_INSTRUCTIONS.md` - Test team validation process
- `docs/QA_TESTING_WORKFLOW.md` - Complete QA workflow
