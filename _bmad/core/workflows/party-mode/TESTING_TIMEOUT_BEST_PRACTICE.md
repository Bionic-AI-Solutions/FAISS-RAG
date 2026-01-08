# Testing Command Timeout Best Practice

**Date**: 2026-01-08  
**Status**: Active Best Practice  
**Category**: Testing & Development Workflow

---

## Rule

**ALWAYS use timeout for test commands and other potentially long-running activities.**

### Rationale

Test commands, build processes, and other development activities can:
- Hang indefinitely if there are configuration issues
- Run longer than expected
- Block terminal sessions
- Consume resources unnecessarily

### Implementation

**Use `timeout` command for:**
- Test execution (`npm test`, `pytest`, etc.)
- Build processes that might hang
- Long-running development commands
- Any command where completion time is uncertain

### Examples

**✅ CORRECT:**
```bash
timeout 30 npm test -- --run
timeout 60 npm run build
timeout 120 python -m pytest
```

**❌ WRONG:**
```bash
npm test  # Can hang indefinitely
npm run build  # No timeout protection
```

### Timeout Values

| Activity | Recommended Timeout | Notes |
|----------|-------------------|-------|
| Unit tests | 30-60 seconds | Should complete quickly |
| Integration tests | 60-120 seconds | May take longer |
| Build processes | 60-180 seconds | Depends on project size |
| E2E tests | 120-300 seconds | Can be lengthy |

### Error Handling

When timeout is reached:
- Command returns exit code 124 (timeout)
- Process is terminated
- Partial output is still available
- Can be used to detect hanging processes

### Integration with BMAD Workflows

**For all BMAD agents and workflows:**
- Always wrap test commands with `timeout`
- Use appropriate timeout values based on activity
- Document timeout values in workflow instructions
- Include timeout in CI/CD pipelines

---

## Enforcement

This is a **MANDATORY** best practice for:
- All test execution commands
- Build processes
- Long-running development tasks
- CI/CD pipeline commands

**Violation Impact**: Can cause terminal sessions to hang, waste resources, and block development workflow.

---

## Related Documentation

- BMAD Testing Workflows
- CI/CD Best Practices
- Development Workflow Guidelines
