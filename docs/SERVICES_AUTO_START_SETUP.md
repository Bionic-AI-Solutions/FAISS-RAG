# Services Auto-Start Setup

**Date:** 2026-01-07  
**Status:** ✅ **IMPLEMENTED** - Services automatically start before integration tests

---

## Summary

Integration tests now automatically ensure all required services are running before test execution. This ensures that services that were part of previous Epics are always available for integration tests.

---

## Implementation

### 1. Service Management Script

**File:** `scripts/ensure_services_running.py`

This script:
- Checks if Docker is running
- Verifies each required service container is running
- Starts services if they're not running
- Performs health checks (when possible)
- Reports service status

**Required Services:**
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (port 9000)
- Meilisearch (port 7700)

**Usage:**
```bash
python scripts/ensure_services_running.py
```

### 2. Automatic Service Startup in Tests

**File:** `tests/integration/conftest.py`

Added `ensure_services_running` fixture that:
- Automatically runs before all integration tests
- Calls `ensure_services_running.py` script
- Ensures services are available before tests execute
- Provides warnings if services can't be started

**Fixture Order:**
1. `ensure_services_running` (session-scoped, autouse=True)
2. `event_loop` (session-scoped)
3. `test_db_engine` (session-scoped)
4. `setup_test_database_engine` (session-scoped, autouse=True)

---

## Docker Compose Configuration

**File:** `docker/docker-compose.yml`

**Changes:**
- Redis port mapping updated from `6380:6379` to `6379:6379`
- All services configured with health checks
- Services use consistent naming: `mem0-rag-{service}`

**Start Services:**
```bash
docker compose -f docker/docker-compose.yml up -d
```

**Stop Services:**
```bash
docker compose -f docker/docker-compose.yml down
```

---

## Service Configuration

### Redis

**Container:** `mem0-rag-redis`  
**Port:** 6379  
**Password:** `redis_password` (set via `REDIS_PASSWORD` env var)

**Configuration:**
- AOF (Append-Only File) persistence enabled
- Password required for connections
- Health check: `redis-cli -a redis_password ping`

**Environment Variable:**
```bash
REDIS_PASSWORD=redis_password
```

### PostgreSQL

**Container:** `mem0-rag-postgres`  
**Port:** 5432  
**Database:** `mem0_rag_db`  
**User:** `postgres`  
**Password:** `postgres_password`

### MinIO

**Container:** `mem0-rag-minio`  
**Ports:** 9000 (API), 9001 (Console)  
**Credentials:** `minioadmin` / `minioadmin123`

### Meilisearch

**Container:** `mem0-rag-meilisearch`  
**Port:** 7700  
**Master Key:** `masterKey`

---

## Integration Test Workflow

### Before Tests Run

1. **Service Check:** `ensure_services_running` fixture executes
2. **Service Startup:** Services are started if not running
3. **Health Verification:** Services are verified (when possible)
4. **Test Execution:** Integration tests run with live services

### During Tests

- Tests use real services (no mocks)
- Services are accessed via configured ports
- Connection pooling and timeouts are handled automatically

### After Tests

- Services remain running (for subsequent test runs)
- No cleanup of services (they persist across test sessions)

---

## Troubleshooting

### Services Not Starting

**Check Docker:**
```bash
docker ps
docker compose -f docker/docker-compose.yml ps
```

**Check Logs:**
```bash
docker compose -f docker/docker-compose.yml logs redis
docker compose -f docker/docker-compose.yml logs postgres
```

**Manual Start:**
```bash
docker compose -f docker/docker-compose.yml up -d
```

### Port Conflicts

If ports are already in use:
1. Check what's using the port: `lsof -i :6379`
2. Stop conflicting service or change port in `docker-compose.yml`
3. Restart services: `docker compose -f docker/docker-compose.yml restart`

### Redis Connection Issues

**Verify Redis is accessible:**
```bash
docker exec mem0-rag-redis redis-cli -a redis_password ping
```

**Check Redis configuration:**
```bash
python3 -c "from app.config.redis import redis_settings; print(redis_settings.url)"
```

**Set password in environment:**
```bash
export REDIS_PASSWORD=redis_password
```

---

## Best Practices

### For Development

1. **Always start services before running tests:**
   ```bash
   python scripts/ensure_services_running.py
   ```

2. **Use docker-compose for service management:**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

3. **Verify services are healthy:**
   ```bash
   docker compose -f docker/docker-compose.yml ps
   ```

### For CI/CD

1. **Start services in CI pipeline:**
   ```yaml
   - name: Start services
     run: docker compose -f docker/docker-compose.yml up -d
   ```

2. **Wait for services to be ready:**
   ```yaml
   - name: Wait for services
     run: python scripts/ensure_services_running.py
   ```

3. **Run integration tests:**
   ```yaml
   - name: Run integration tests
     run: pytest tests/integration/ -v
   ```

---

## Summary

✅ **Services automatically start before integration tests**  
✅ **Redis port fixed to 6379 (was 6380)**  
✅ **Service health checks implemented**  
✅ **Automatic service management in test fixtures**  
✅ **Documentation created**

**Status:** ✅ **SERVICES AUTO-START IMPLEMENTED**

