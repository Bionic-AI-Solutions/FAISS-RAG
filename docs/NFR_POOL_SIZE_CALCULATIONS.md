# NFR Pool Size Calculations

## Overview

This document calculates connection pool sizes required to meet NFR targets for high concurrency, high availability, high scalability, and high performance.

## NFR Targets

### Concurrency Targets
- **NFR-SCALE-004**: 200 concurrent users per tenant
- **NFR-SCALE-006**: 40,000 requests per minute (MVP)
- **NFR-SCALE-007**: 200,000 requests per minute (Phase 2)

### Performance Targets
- **NFR-PERF-001**: <200ms p95 search latency
- **NFR-PERF-002**: <100ms p95 memory operations
- **NFR-PERF-003**: <500ms cold start

## Pool Size Calculations

### 1. Redis Connection Pool

**Target**: 40,000 requests/minute = ~667 requests/second

**Calculation**:
- Each Redis connection can handle 100,000+ ops/sec
- With 10 connections: 10 × 100,000 = 1,000,000 ops/sec capacity
- Required: 667 ops/sec
- **Utilization**: 667 / 1,000,000 = 0.067% (very low)

**Recommendation**:
- **Default**: 10 connections (sufficient for MVP)
- **Phase 2**: 20 connections (for 200K req/min)
- **Configurable**: Via `REDIS_POOL_SIZE` environment variable

**Current Setting**: `pool_size=10` ✅ **MEETS NFR**

### 2. Database Connection Pool

**Target**: 200 concurrent users per tenant × 200 tenants = 40,000 concurrent users

**Calculation**:
- Each database connection can handle ~100 concurrent queries (async)
- With 10 connections: 10 × 100 = 1,000 concurrent queries
- Required: 40,000 concurrent users (but not all query simultaneously)
- **Assumption**: 10% active queries = 4,000 concurrent queries
- **Gap**: 4,000 queries / 1,000 capacity = 4x over capacity

**Recommendation**:
- **Current**: `pool_max=10` ⚠️ **INSUFFICIENT**
- **Required**: `pool_max=50` (for 4,000 concurrent queries)
- **With overflow**: `pool_max=40, max_overflow=20` (total 60 connections)
- **Configurable**: Via `DB_POOL_MAX` environment variable

**Action Required**: Increase database pool size

### 3. Meilisearch Client

**Status**: Singleton client (HTTP-based, connection pooling handled by HTTP client)

**Analysis**:
- Meilisearch uses HTTP, not persistent connections
- HTTP client (requests/httpx) handles connection pooling internally
- No explicit pool configuration needed
- ✅ **MEETS NFR** (HTTP client handles concurrency)

### 4. MinIO Client

**Status**: Singleton client (HTTP-based, connection pooling handled by HTTP client)

**Analysis**:
- MinIO uses HTTP (S3-compatible API), not persistent connections
- HTTP client handles connection pooling internally
- No explicit pool configuration needed
- ✅ **MEETS NFR** (HTTP client handles concurrency)

### 5. FAISS Manager

**Status**: File-based indices (not connection-based)

**Analysis**:
- FAISS uses file I/O, not network connections
- Concurrent access handled by file locking
- **Issue**: File-based indices limit horizontal scaling
- ⚠️ **SCALABILITY CONCERN**: Cannot scale FAISS across multiple pods

**Recommendation**:
- **Short-term**: File locking for concurrent access safety
- **Long-term**: Distributed FAISS or shared storage (NFS/EBS)

## Summary

| Component | Current | Required | Status | Action |
|-----------|---------|----------|--------|--------|
| Redis | 10 | 10 | ✅ Meets NFR | None |
| Database | 10 | 50 | ⚠️ Insufficient | Increase to 50 |
| Meilisearch | N/A | N/A | ✅ Meets NFR | None |
| MinIO | N/A | N/A | ✅ Meets NFR | None |
| FAISS | File-based | Distributed | ⚠️ Scalability | Plan migration |

## Immediate Actions

1. **Database Pool Size**: Increase `DB_POOL_MAX` from 10 to 50
2. **Redis Pool Size**: Keep at 10 (sufficient), make configurable
3. **FAISS**: Document scalability limitation, plan distributed solution

## Configuration Updates

### Database Configuration
```python
# app/config/database.py
pool_max: int = Field(default=50, description="Maximum connection pool size (NFR: 200 concurrent users/tenant)")
```

### Redis Configuration
```python
# app/config/redis.py
pool_size: int = Field(default=10, description="Connection pool size (NFR: 40K req/min, sufficient)")
```

## Monitoring

Track these metrics to verify NFR compliance:
- Connection pool utilization (should be <80%)
- Connection wait time (should be <10ms)
- Request latency (p50, p95, p99)
- Error rates (should be <0.1%)

