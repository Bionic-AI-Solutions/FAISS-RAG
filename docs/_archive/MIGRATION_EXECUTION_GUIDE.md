# Database Migration Execution Guide

**Purpose:** Execute Alembic database migrations to initialize the database schema.

## Prerequisites

1. **Docker Services Running:**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

2. **Verify Services:**
   ```bash
   docker compose -f docker/docker-compose.yml ps
   ```
   
   All services should show "Up (healthy)" status.

3. **Dependencies Installed:**
   ```bash
   pip install -r requirements.txt
   ```

## Migration Execution Methods

### Method 1: Docker Exec (Recommended)

If direct database connection fails (common in containerized environments):

```bash
./scripts/run_migrations_docker.sh
```

This script:
- Checks if Docker services are running
- Executes migrations via Docker exec
- Verifies tables are created

### Method 2: Direct Connection

If database is accessible from host:

```bash
python scripts/run_migrations.py upgrade head
```

Or using Alembic directly:

```bash
alembic upgrade head
```

### Method 3: Manual Docker Exec

```bash
docker compose -f docker/docker-compose.yml exec postgres \
    bash -c "cd /workspaces/mem0-rag && alembic upgrade head"
```

## Verification

### Check Current Migration Version

```bash
alembic current
```

### List All Tables

```bash
docker compose -f docker/docker-compose.yml exec postgres \
    psql -U postgres -d mem0_rag_db -c "\dt"
```

Expected tables:
- `tenants`
- `users`
- `documents`
- `audit_logs`
- `tenant_api_keys`
- `templates` (from migration 003)
- `tenant_configs` (from migration 004)
- `alembic_version` (Alembic tracking table)

### Verify RLS Policies

```bash
docker compose -f docker/docker-compose.yml exec postgres \
    psql -U postgres -d mem0_rag_db -c "
    SELECT tablename, policyname, permissive, roles, cmd, qual 
    FROM pg_policies 
    WHERE schemaname = 'public';
    "
```

## Migration Rollback

If you need to rollback migrations:

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Troubleshooting

### Connection Refused

**Error:** `Connection refused` or `Connect call failed`

**Solution:** Use Docker exec method:
```bash
./scripts/run_migrations_docker.sh
```

### Migration Already Applied

**Error:** `Target database is not up to date`

**Solution:** Check current version:
```bash
alembic current
```

If migrations are ahead, you may need to:
1. Check migration files match database state
2. Manually update `alembic_version` table if needed
3. Re-run migrations

### Tables Not Created

**Error:** Migrations run but tables don't exist

**Solution:**
1. Check migration files are correct
2. Verify database connection
3. Check Alembic version table:
   ```bash
   docker compose -f docker/docker-compose.yml exec postgres \
       psql -U postgres -d mem0_rag_db -c "SELECT * FROM alembic_version;"
   ```

## Migration Files

Current migrations:
- `001_initial_schema.py` - Core tables (tenants, users, documents, audit_logs, tenant_api_keys)
- `002_enable_rls.py` - Row Level Security policies
- `003_add_templates_table.py` - Template management
- `004_add_tenant_configs_table.py` - Tenant configuration

## Next Steps

After migrations are executed:

1. **Run Integration Tests:**
   ```bash
   pytest tests/integration/test_repositories.py -v
   ```

2. **Verify RLS Policies:**
   ```bash
   pytest tests/integration/test_rls_policies.py -v
   ```

3. **Test Tenant Isolation:**
   ```bash
   pytest tests/test_tenant_isolation.py -v
   ```

## Notes

- Migrations use async SQLAlchemy but Alembic requires sync connections
- `psycopg2-binary` is included in requirements.txt for sync migrations
- Docker exec method works when direct connection fails
- Always verify migrations before proceeding with development







