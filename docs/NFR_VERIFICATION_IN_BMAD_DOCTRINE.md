# NFR Verification in BMAD Doctrine

## Summary

NFR (Non-Functional Requirements) verification has been integrated into the core BMAD doctrine to ensure every Epic includes NFR verification as a mandatory story with tasks.

## Changes Made

### 1. Epic Story Lifecycle Workflow (`epic-story-lifecycle.mdc`)

**Added Requirements:**
- Every Epic MUST have a **Story X.NFR: Epic X NFR Verification**
- NFR verification story includes tasks for:
  - Connection pooling and resource management
  - Concurrent request handling
  - Fault tolerance and fallback mechanisms
  - Performance targets (latency, throughput)
  - NFR verification report creation

**Updated Epic Closure Criteria:**
- Epic can ONLY be closed after:
  - ✅ All stories closed (including Story X.NFR)
  - ✅ NFR verification complete with report
  - ✅ Integration tests pass

### 2. Story Grooming Workflow (`groom-story.mdc`)

**Added Requirements:**
- Every Story that affects NFRs MUST have a **Task X.Y.NFR: Story X.Y NFR Verification**
- NFR verification task includes:
  - Connection pooling verification (if applicable)
  - Concurrent request handling verification
  - Fault tolerance verification (if applicable)
  - Performance target verification (if applicable)
  - NFR compliance documentation

### 3. Test Validation Workflow (`test-validation.mdc`)

**Added Requirements:**
- Epic closure requires NFR verification completion
- NFR verification checklist:
  - Story X.NFR is closed
  - NFR verification report exists
  - Connection pooling meets targets
  - Concurrent request handling works
  - Fault tolerance mechanisms work
  - Performance targets met

## NFR Verification Story Template

### Story X.NFR: Epic X NFR Verification

**As a** Platform Operator,  
**I want** to verify that Epic X meets all Non-Functional Requirements,  
**So that** the system maintains high concurrency, high availability, high scalability, and high performance.

**Acceptance Criteria:**
- **Given** Epic X is implemented
- **When** NFR verification is performed
- **Then** All NFR targets are met:
  - Connection pooling configured correctly
  - Concurrent request handling verified
  - Fault tolerance mechanisms verified
  - Performance targets met (latency, throughput)

**Tasks:**
1. **Task X.NFR.1:** Verify connection pooling and resource management
2. **Task X.NFR.2:** Verify concurrent request handling
3. **Task X.NFR.3:** Verify fault tolerance and fallback mechanisms
4. **Task X.NFR.4:** Verify performance targets (latency, throughput)
5. **Task X.NFR.5:** Create NFR verification report

## NFR Verification Task Template

### Task X.Y.NFR: Story X.Y NFR Verification

**Description:**
```
**NFR Verification Task for Story X.Y**

**Activities:**
1. Verify connection pooling (if applicable)
2. Verify concurrent request handling
3. Verify fault tolerance (if applicable)
4. Verify performance targets (if applicable)
5. Document NFR compliance in story test document

**NFR Categories to Verify:**
- High Concurrency: Connection pooling, async operations
- High Availability: Fault tolerance, fallback mechanisms
- High Scalability: Resource management, horizontal scaling
- High Performance: Latency targets, throughput targets
```

## Integration with Epic Tests

NFR verification can be part of:
- **Epic Test Story (Story X.T):** Include NFR verification in epic-level tests
- **Feature Tests:** Include NFR verification in feature-level tests
- **Story Tests:** Include NFR verification in story-level tests (Task X.Y.NFR)

## NFR Verification Checklist

### For Every Epic:
- [ ] Story X.NFR created
- [ ] All NFR verification tasks created
- [ ] NFR verification report created
- [ ] Connection pooling verified
- [ ] Concurrent request handling verified
- [ ] Fault tolerance verified
- [ ] Performance targets verified
- [ ] Story X.NFR closed

### For Every Story (if affects NFRs):
- [ ] Task X.Y.NFR created
- [ ] NFR compliance verified
- [ ] NFR compliance documented
- [ ] Task X.Y.NFR closed

## References

- **NFR Verification Framework:** `docs/NFR_VERIFICATION_FRAMEWORK.md`
- **NFR Pool Size Calculations:** `docs/NFR_POOL_SIZE_CALCULATIONS.md`
- **NFR Audit Report:** `docs/NFR_AUDIT_REPORT.md`
- **NFR Compliance Summary:** `docs/NFR_COMPLIANCE_SUMMARY.md`

