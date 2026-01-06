# Development Testing Rule

**CRITICAL RULE: Always test before proceeding. No exceptions.**

## Rule

**ALWAYS run tests before proceeding to the next task or story. No exceptions.**

## When to Test

1. **After implementing a task** - Run tests before marking task complete
2. **Before moving to next task** - Verify current implementation works
3. **After fixing bugs** - Run tests to ensure fix works
4. **Before marking story ready for test** - Run full test suite

## Test Command

```bash
# Run all tests
python3 -m pytest tests/ -v --tb=short

# Run specific test categories
python3 -m pytest tests/unit/ -v  # Unit tests
python3 -m pytest tests/integration/ -v  # Integration tests (require services)
python3 -m pytest tests/test_authorization.py -v  # Specific test file
```

## What to Verify

- ✅ All imports work (no circular imports)
- ✅ Unit tests pass
- ✅ No linting errors
- ✅ Code compiles and runs
- ✅ Integration tests pass (if services available)

## Test Failures

- **Fix implementation issues** - Don't change tests to pass broken code
- **Document pre-existing failures** - Note if failures are not related to current work
- **Skip integration tests** - If services not available (document in comments)

## Exception

**There are no exceptions to this rule.**

Always test before proceeding.



