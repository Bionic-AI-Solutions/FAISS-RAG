# Project Dependencies

This document lists all dependencies required for the Mem0-RAG system.

## Core Dependencies (Already in pyproject.toml)

All dependencies are already defined in `pyproject.toml`. They just need to be installed.

### MCP Server Framework Dependencies

These are the dependencies specifically needed for Story 1.4 (MCP Server Framework):

1. **fastapi>=0.104.0** - Web framework for FastAPI application
2. **fastmcp>=0.9.0** - FastMCP server for MCP protocol implementation
3. **structlog>=23.2.0** - Structured logging library
4. **uvicorn[standard]>=0.24.0** - ASGI server for running FastAPI
5. **pydantic>=2.5.0** - Data validation using Python type annotations
6. **pydantic-settings>=2.1.0** - Settings management using Pydantic

### Full Application Dependencies

The complete list from `pyproject.toml` includes:

**Web Framework:**
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`

**MCP Server:**
- `fastmcp>=0.9.0`

**Data Validation & Settings:**
- `pydantic>=2.5.0`
- `pydantic-settings>=2.1.0`

**Database:**
- `sqlalchemy[asyncio]>=2.0.23` - Async SQLAlchemy ORM
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `alembic>=1.12.0` - Database migrations

**Caching & Storage:**
- `redis>=5.0.0` - Redis client
- `aioredis>=2.0.1` - Async Redis client
- `minio>=7.2.0` - S3-compatible object storage

**Search:**
- `meilisearch>=0.33.0` - Search engine
- `faiss-cpu>=1.7.4` - Vector similarity search

**Memory & Observability:**
- `mem0ai>=1.0.0` - Mem0 Python SDK
- `langfuse>=2.0.0` - LLM observability

**Utilities:**
- `structlog>=23.2.0` - Structured logging
- `python-multipart>=0.0.6` - Multipart form data
- `python-jose[cryptography]>=3.3.0` - JWT handling
- `passlib[bcrypt]>=1.7.4` - Password hashing
- `slowapi>=0.1.9` - Rate limiting
- `httpx>=0.25.0` - HTTP client

## Installation

To install all dependencies:

```bash
# Install the package and all dependencies
pip install -e .

# Or install just the dependencies
pip install -r requirements.txt  # if requirements.txt exists
# or
pip install $(grep -E '^\s*"[^"]+>=' pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/' | tr '\n' ' ')
```

## Development Dependencies

For development and testing:

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking support
- `black>=23.11.0` - Code formatting
- `flake8>=6.1.0` - Linting
- `mypy>=1.7.0` - Type checking
- `isort>=5.12.0` - Import sorting
- `bandit>=1.7.5` - Security linting

## Runtime Testing Requirements

For runtime testing of the MCP server (Story 1.4), you need:

1. **Python Dependencies** (install via `pip install -e .`):
   - All dependencies listed above

2. **Infrastructure Services** (from Story 1.2):
   - PostgreSQL (running and accessible)
   - Redis (running and accessible)
   - MinIO (running and accessible)
   - Meilisearch (running and accessible)
   - Langfuse (optional, for observability)

3. **Environment Variables**:
   - Database connection strings
   - Service endpoints and credentials
   - (See `.env.example` or configuration files)

## Current Status

**Dependencies Status:**
- ✅ All dependencies are **defined** in `pyproject.toml`
- ⚠️ Dependencies are **not yet installed** in the current environment
- ⚠️ This is why import tests fail with `ModuleNotFoundError`

**To Resolve:**
Run `pip install -e .` to install all dependencies, then runtime tests can be executed.





