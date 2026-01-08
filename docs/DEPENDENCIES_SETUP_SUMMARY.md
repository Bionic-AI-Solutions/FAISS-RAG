# External Dependencies Setup Summary

## Quick Answer

**All external dependencies are fully configurable via environment variables. Nothing is hardcoded.**

You can connect to external instances of all services by setting environment variables in a `.env` file or system environment.

---

## External Dependencies List

### 1. **PostgreSQL** (Database)
- **Purpose:** Primary database for tenant data, configurations, audit logs
- **Config:** `app/config/database.py`
- **Env Prefix:** `DB_`
- **Docker Service:** `mem0-rag-postgres:5432`
- **External:** Set `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

### 2. **Redis** (Caching & Session Storage)
- **Purpose:** Caching, rate limiting, session storage, Mem0 fallback
- **Config:** `app/config/redis.py`
- **Env Prefix:** `REDIS_`
- **Docker Service:** `mem0-rag-redis:6379`
- **External:** Set `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- **Auto-detects:** Docker network name if running in container

### 3. **MinIO** (S3-Compatible Storage)
- **Purpose:** Object storage for documents, embeddings, files
- **Config:** `app/config/minio.py`
- **Env Prefix:** `MINIO_`
- **Docker Service:** `mem0-rag-minio:9000`
- **External:** Set `MINIO_ENDPOINT`, `MINIO_PORT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`
- **Supports:** AWS S3 (use S3 endpoint and credentials)

### 4. **Meilisearch** (Search Engine)
- **Purpose:** Keyword search and hybrid retrieval
- **Config:** `app/config/meilisearch.py`
- **Env Prefix:** `MEILISEARCH_`
- **Docker Service:** `mem0-rag-meilisearch:7700`
- **External:** Set `MEILISEARCH_HOST`, `MEILISEARCH_PORT`, `MEILISEARCH_API_KEY`

### 5. **Mem0** (Memory Management)
- **Purpose:** Long-term memory for conversational context
- **Config:** `app/config/mem0.py`
- **Env Prefix:** `MEM0_`
- **Docker Service:** Not included (uses Python SDK with Redis fallback)
- **External:** Set `MEM0_API_URL`, `MEM0_API_KEY`
- **Fallback:** Uses Redis if Mem0 unavailable (`MEM0_FALLBACK_TO_REDIS=true`)

### 6. **Langfuse** (Observability)
- **Purpose:** LLM observability, tool call tracking, analytics
- **Config:** `app/config/langfuse.py`
- **Env Prefix:** `LANGFUSE_`
- **Docker Service:** `mem0-rag-langfuse:3000`
- **External:** Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
- **Optional:** Can be disabled with `LANGFUSE_ENABLED=false`

### 7. **FAISS** (Vector Search)
- **Purpose:** Vector similarity search (in-process library)
- **Config:** `app/config/faiss.py`
- **Env Prefix:** `FAISS_`
- **No Service:** Python library, needs filesystem storage
- **Config:** Set `FAISS_INDEX_PATH` for index storage location

---

## Configuration Approach

### ✅ Fully Configurable
- All connections use **Pydantic Settings** with environment variable support
- No hardcoded connection strings in code
- Supports `.env` file or system environment variables

### ✅ Environment-Aware Defaults
- Auto-detects Docker vs host environment
- Uses Docker network names when running in containers
- Falls back to `localhost` for host environments

### ✅ Flexible Setup Options
1. **Docker Compose** (default): All services in `docker/docker-compose.yml`
2. **External Services**: Set environment variables to point to external instances
3. **Hybrid**: Mix Docker Compose services with external services

---

## Quick Setup Guide

### Option 1: Docker Compose (Development)

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Services available at:
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
# - MinIO: localhost:9000
# - Meilisearch: localhost:7700
# - Langfuse: localhost:3000
```

### Option 2: External Services

Create `.env` file:

```bash
# Database
DB_HOST=your-postgres-host.com
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSL=true

# Redis
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# MinIO / S3
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_PORT=443
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_USE_SSL=true

# Meilisearch
MEILISEARCH_HOST=https://your-meilisearch-host.com
MEILISEARCH_PORT=7700
MEILISEARCH_API_KEY=your_api_key

# Mem0 (optional)
MEM0_API_URL=https://your-mem0-api.com
MEM0_API_KEY=your_api_key

# Langfuse (optional)
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true

# FAISS
FAISS_INDEX_PATH=/data/faiss_indices
```

---

## Environment Variable Reference

### Database (DB_*)
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_SSL` - Enable SSL (default: false)
- `DB_POOL_MIN` - Min pool size (default: 5)
- `DB_POOL_MAX` - Max pool size (default: 50)
- `DATABASE_URL` - Full connection URL (alternative)

### Redis (REDIS_*)
- `REDIS_HOST` - Redis host (auto-detects Docker)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_PASSWORD` - Redis password
- `REDIS_DB` - Database number (default: 0)
- `REDIS_POOL_SIZE` - Pool size (default: 10)
- `REDIS_URL` - Full connection URL (alternative)

### MinIO (MINIO_*)
- `MINIO_ENDPOINT` - MinIO endpoint (auto-detects Docker)
- `MINIO_PORT` - MinIO port (default: 9000)
- `MINIO_ACCESS_KEY` - Access key
- `MINIO_SECRET_KEY` - Secret key
- `MINIO_USE_SSL` - Use SSL (default: false)
- `MINIO_BUCKET_NAME` - Default bucket name

### Meilisearch (MEILISEARCH_*)
- `MEILISEARCH_HOST` - Host URL (auto-detects Docker)
- `MEILISEARCH_PORT` - Port (default: 7700)
- `MEILISEARCH_API_KEY` - API key

### Mem0 (MEM0_*)
- `MEM0_API_URL` - Mem0 API URL
- `MEM0_API_KEY` - Mem0 API key
- `MEM0_FALLBACK_TO_REDIS` - Fallback to Redis (default: true)

### Langfuse (LANGFUSE_*)
- `LANGFUSE_PUBLIC_KEY` - Public key
- `LANGFUSE_SECRET_KEY` - Secret key
- `LANGFUSE_HOST` - Langfuse host
- `LANGFUSE_PROJECT_NAME` - Project name
- `LANGFUSE_ENABLED` - Enable/disable (default: true)

### FAISS (FAISS_*)
- `FAISS_INDEX_PATH` - Index storage path
- `FAISS_DIMENSION` - Vector dimension (default: 768)
- `FAISS_INDEX_TYPE` - Index type (default: IndexFlatL2)

---

## Configuration Files Location

All configuration is managed in `app/config/`:
- `database.py` - PostgreSQL configuration
- `redis.py` - Redis configuration
- `minio.py` - MinIO/S3 configuration
- `meilisearch.py` - Meilisearch configuration
- `mem0.py` - Mem0 configuration
- `langfuse.py` - Langfuse configuration
- `faiss.py` - FAISS configuration
- `settings.py` - Application settings
- `auth.py` - Authentication settings
- `authorization.py` - Authorization settings

---

## Verification

### Check Service Connectivity

```bash
# PostgreSQL
psql -h localhost -U postgres -d mem0_rag_db

# Redis
redis-cli -h localhost -p 6379 -a redis_password ping

# MinIO
curl http://localhost:9000/minio/health/live

# Meilisearch
curl http://localhost:7700/health

# Langfuse
curl http://localhost:3000/api/public/health
```

---

## Documentation

For detailed setup instructions, see:
- **`docs/EXTERNAL_DEPENDENCIES.md`** - Complete dependency setup guide
- **`docker/docker-compose.yml`** - Docker Compose service definitions
- **`app/config/`** - Configuration file implementations

---

## Summary

✅ **All dependencies are configurable** - No hardcoded connections  
✅ **Environment-aware** - Auto-detects Docker vs host  
✅ **Flexible** - Supports Docker Compose, external services, or hybrid  
✅ **Production-ready** - Supports SSL, connection pooling, timeouts  

You can connect to external instances of all services by simply setting environment variables.

