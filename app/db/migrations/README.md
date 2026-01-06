# Database Migrations

This directory contains Alembic database migrations for the application.

## Setup

Migrations are configured to work with async SQLAlchemy 2.0 and PostgreSQL using asyncpg.

## Running Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade -1  # Rollback one version
alembic downgrade base  # Rollback all migrations
```

### View current revision

```bash
alembic current
```

### View migration history

```bash
alembic history
```

## Configuration

- **Alembic config**: `alembic.ini` (root directory)
- **Environment config**: `app/db/migrations/env.py`
- **Migration template**: `app/db/migrations/script.py.mako`

## Notes

- All migrations use async SQLAlchemy 2.0
- Database URL is loaded from `app.config.database.db_settings`
- Models are automatically imported for autogenerate support
- Migrations are stored in `app/db/migrations/versions/`





