# External Dependencies Setup Guide

This document provides a comprehensive overview of all external dependencies required for the Mem0-RAG system, how they are configured, and setup instructions.

## Overview

All external dependencies are **fully configurable** via environment variables. The application uses Pydantic Settings with environment variable support, allowing you to connect to external services without modifying code.

**Configuration Approach:**

- ✅ **All connections are configurable** via environment variables
- ✅ **No hardcoded connection strings** in application code
- ✅ **Environment-aware defaults** (auto-detects Docker vs host environment)
- ✅ **Supports both Docker Compose services and external services**

---

## External Dependencies List

### 1. PostgreSQL (Database)

**Purpose:** Primary database for tenant data, configurations, audit logs, and application state.

**Configuration File:** `app/config/database.py`

**Environment Variables:**

```bash
# Database Connection (prefix: DB_)
DB_HOST=localhost              # Database host (default: localhost)
DB_PORT=5432                   # Database port (default: 5432)
DB_NAME=mem0_rag_db           # Database name (default: mem0_rag_db)
DB_USER=postgres              # Database user (default: postgres)
DB_PASSWORD=postgres_password # Database password (default: postgres_password)
DB_SSL=false                   # Enable SSL/TLS (default: false)

# Connection Pooling
DB_POOL_MIN=5                  # Minimum pool size (default: 5)
DB_POOL_MAX=50                 # Maximum pool size (default: 50, NFR: 200 concurrent users/tenant)
DB_CONNECTION_TIMEOUT=60000    # Connection timeout in milliseconds (default: 60000)

# Alternative: Full Database URL
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
```

**Docker Compose Service:**

- Container: `mem0-rag-postgres`
- Port: `5432`
- Network: `mem0-rag-network`

**External Setup:**
To use an external PostgreSQL instance, set these environment variables:

```bash
DB_HOST=your-postgres-host.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSL=true  # Recommended for external connections
```

**Connection String Format:**

- Uses `asyncpg` driver: `postgresql+asyncpg://user:password@host:port/dbname`
- Supports connection pooling with configurable min/max pool sizes

---

### 2. Redis (Caching & Session Storage)

**Purpose:** Caching, rate limiting, session storage, and Mem0 fallback storage.

**Configuration File:** `app/config/redis.py`

**Environment Variables:**

```bash
# Redis Connection (prefix: REDIS_)
REDIS_HOST=localhost           # Redis host (auto-detects Docker: mem0-rag-redis)
REDIS_PORT=6379                # Redis port (default: 6379)
REDIS_PASSWORD=redis_password  # Redis password (default: None)
REDIS_DB=0                     # Redis database number (default: 0)

# Connection Pool
REDIS_POOL_SIZE=10             # Connection pool size (default: 10)
REDIS_CONNECT_TIMEOUT=10000     # Connection timeout in milliseconds (default: 10000)
REDIS_COMMAND_TIMEOUT=5000      # Command timeout in milliseconds (default: 5000)

# Redis Cluster (optional)
REDIS_CLUSTER_ENABLED=false    # Enable cluster mode (default: false)
REDIS_CLUSTER_NODES=node1:6379,node2:6379,node3:6379  # Comma-separated nodes

# Alternative: Full Redis URL
REDIS_URL=redis://:password@host:port/db
```

**Docker Compose Service:**

- Container: `mem0-rag-redis`
- Port: `6379`
- Network: `mem0-rag-network`
- Password: `redis_password` (configured in docker-compose.yml)

**External Setup:**
To use an external Redis instance:

```bash
REDIS_HOST=your-redis-host.com
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
```

**Auto-Detection:**
The application automatically detects if it's running in a Docker container and uses the Docker network name (`mem0-rag-redis`) if available. Otherwise, it falls back to `localhost` or the explicitly set `REDIS_HOST`.

---

### 3. MinIO (S3-Compatible Object Storage)

**Purpose:** Object storage for documents, embeddings, and file uploads.

**Configuration File:** `app/config/minio.py`

**Environment Variables:**

```bash
# MinIO Connection (prefix: MINIO_)
MINIO_ENDPOINT=localhost       # MinIO endpoint (auto-detects Docker: mem0-rag-minio)
MINIO_PORT=9000                # MinIO port (default: 9000)
MINIO_ACCESS_KEY=minioadmin    # MinIO access key (default: minioadmin)
MINIO_SECRET_KEY=minioadmin123 # MinIO secret key (default: minioadmin123)
MINIO_USE_SSL=false            # Use SSL/TLS (default: false)
MINIO_REGION=us-east-1         # MinIO region (default: us-east-1)

# Bucket Configuration
MINIO_BUCKET_NAME=mem0-rag-storage  # Default bucket name (default: mem0-rag-storage)
MINIO_BUCKET_REGION=us-east-1        # Bucket region (default: us-east-1)

# Console (optional)
MINIO_CONSOLE_PORT=9001        # MinIO console port (default: 9001)
```

**Docker Compose Service:**

- Container: `mem0-rag-minio`
- Port: `9000` (API), `9001` (Console)
- Network: `mem0-rag-network`
- Credentials: `minioadmin` / `minioadmin123`

**External Setup:**
To use an external MinIO or AWS S3-compatible service:

```bash
MINIO_ENDPOINT=s3.amazonaws.com  # or your MinIO host
MINIO_PORT=443
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_USE_SSL=true
MINIO_REGION=us-east-1
```

**Endpoint URL:**

- Constructed as: `http://endpoint:port` or `https://endpoint:port` (if SSL enabled)

---

### 4. Meilisearch (Search Engine)

**Purpose:** Keyword search and hybrid retrieval (combines with FAISS vector search).

**Configuration File:** `app/config/meilisearch.py`

**Environment Variables:**

```bash
# Meilisearch Connection (prefix: MEILISEARCH_)
MEILISEARCH_HOST=http://localhost  # Meilisearch host (auto-detects Docker: http://mem0-rag-meilisearch)
MEILISEARCH_PORT=7700               # Meilisearch port (default: 7700)
MEILISEARCH_API_KEY=masterKey       # Meilisearch API key (default: masterKey)
MEILISEARCH_TIMEOUT=5000            # Request timeout in milliseconds (default: 5000)
```

**Docker Compose Service:**

- Container: `mem0-rag-meilisearch`
- Port: `7700`
- Network: `mem0-rag-network`
- Master Key: `masterKey`

**External Setup:**
To use an external Meilisearch instance:

```bash
MEILISEARCH_HOST=https://your-meilisearch-host.com
MEILISEARCH_PORT=7700
MEILISEARCH_API_KEY=your_api_key
```

**URL Format:**

- Constructed as: `{host}:{port}` (e.g., `http://localhost:7700`)

---

### 5. Mem0 (Memory Management)

**Purpose:** Long-term memory management for conversational context and user memories.

**Configuration File:** `app/config/mem0.py`

**Environment Variables:**

```bash
# Mem0 Connection (prefix: MEM0_)
MEM0_API_URL=http://localhost:8001  # Mem0 API URL (default: http://localhost:8001)
MEM0_API_KEY=mem0_api_key            # Mem0 API key (default: mem0_api_key)
MEM0_TIMEOUT=30000                   # Request timeout in milliseconds (default: 30000)

# Fallback Configuration
MEM0_FALLBACK_TO_REDIS=true          # Fallback to Redis if Mem0 unavailable (default: true)
```

**Docker Compose Service:**

- **Note:** Mem0 service is commented out in docker-compose.yml due to image availability issues
- The application uses the Mem0 Python SDK with Redis fallback instead
- If you have a Mem0 API server, configure it via environment variables

**External Setup:**
To use an external Mem0 API server:

```bash
MEM0_API_URL=https://your-mem0-api.com
MEM0_API_KEY=your_api_key
MEM0_TIMEOUT=30000
```

**Fallback Behavior:**

- If Mem0 is unavailable and `MEM0_FALLBACK_TO_REDIS=true`, the application uses Redis for memory storage
- This ensures the system continues to function even if Mem0 is down

---

### 6. Langfuse (Observability)

**Purpose:** LLM observability, tool call tracking, and analytics.

**Configuration File:** `app/config/langfuse.py`

**Environment Variables:**

```bash
# Langfuse Connection (prefix: LANGFUSE_)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx        # Langfuse public key (default: pk-lf-xxx)
LANGFUSE_SECRET_KEY=sk-lf-xxx        # Langfuse secret key (default: sk-lf-xxx)
LANGFUSE_HOST=https://cloud.langfuse.com  # Langfuse host (default: https://cloud.langfuse.com)
LANGFUSE_PROJECT_NAME=mem0-rag       # Langfuse project name (default: mem0-rag)
LANGFUSE_TIMEOUT=5000                # Request timeout in milliseconds (default: 5000)

# Feature Flag
LANGFUSE_ENABLED=true                # Enable Langfuse observability (default: true)
```

**Docker Compose Service:**

- Container: `mem0-rag-langfuse`
- Port: `3000`
- Network: `mem0-rag-network`
- Uses PostgreSQL for its own database

**External Setup:**
To use Langfuse Cloud or external instance:

```bash
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PROJECT_NAME=your_project_name
LANGFUSE_ENABLED=true
```

**Note:** Langfuse can be disabled by setting `LANGFUSE_ENABLED=false` if you don't need observability.

---

### 7. FAISS (Vector Search)

**Purpose:** Vector similarity search for embeddings.

**Configuration File:** `app/config/faiss.py`

**Environment Variables:**

```bash
# FAISS Configuration (prefix: FAISS_)
FAISS_INDEX_PATH=/data/faiss_indices  # FAISS index storage path (default: /data/faiss_indices)
FAISS_INDEX_TYPE=IndexFlatL2          # FAISS index type (default: IndexFlatL2)
FAISS_DIMENSION=768                    # Vector dimension (default: 768)
FAISS_USE_MMAP=true                    # Use memory-mapped files (default: true)
```

**Note:** FAISS is a Python library that runs in-process. It doesn't require a separate service, but needs:

- Storage path for index files (can be local filesystem or mounted volume)
- Vector dimension configuration matching your embedding model

**Setup:**

- FAISS indices are stored on the filesystem
- In Docker, mount a volume to persist indices: `-v /path/to/indices:/data/faiss_indices`
- Ensure the path is writable by the application

---

## Configuration Summary

### All Dependencies Are Configurable

✅ **No hardcoded connections** - All service connections are configured via environment variables

✅ **Environment-aware defaults** - Automatically detects Docker vs host environment

✅ **Supports external services** - Can connect to external instances of all services

✅ **Flexible configuration** - Supports both individual settings and full connection URLs

### Configuration Priority

1. **Environment Variables** (highest priority)
2. **`.env` file** (loaded automatically by Pydantic Settings)
3. **Default values** (fallback if not set)

### Environment Variable Prefixes

Each service has a prefix for its environment variables:

- Database: `DB_`
- Redis: `REDIS_`
- MinIO: `MINIO_`
- Meilisearch: `MEILISEARCH_`
- Mem0: `MEM0_`
- Langfuse: `LANGFUSE_`
- FAISS: `FAISS_`

---

## Setup Instructions

### Option 1: Using Docker Compose (Recommended for Development)

All services are pre-configured in `docker/docker-compose.yml`:

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Verify services are running
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

**Default Configuration:**

- PostgreSQL: `localhost:5432` (user: `postgres`, password: `postgres_password`)
- Redis: `localhost:6379` (password: `redis_password`)
- MinIO: `localhost:9000` (credentials: `minioadmin` / `minioadmin123`)
- Meilisearch: `localhost:7700` (key: `masterKey`)
- Langfuse: `localhost:3000`

### Option 2: Using External Services

Create a `.env` file in the project root:

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
FAISS_DIMENSION=768
```

### Option 3: Hybrid Setup (Some Docker, Some External)

You can mix Docker Compose services with external services:

```bash
# Start only some services via Docker Compose
docker-compose -f docker/docker-compose.yml up -d postgres redis

# Configure external services in .env
MINIO_ENDPOINT=s3.amazonaws.com
MEILISEARCH_HOST=https://your-meilisearch-host.com
```

---

## Verification

### Check Service Connectivity

The application includes health checks and connection validation. You can verify services are accessible:

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

### Application Startup

The application will log connection status on startup. Check logs for:

- ✅ Successful connections
- ❌ Connection failures (with error messages)

---

## Troubleshooting

### Connection Issues

1. **Check environment variables are set:**

   ```bash
   env | grep -E "DB_|REDIS_|MINIO_|MEILISEARCH_"
   ```

2. **Verify service is accessible:**

   ```bash
   # Test network connectivity
   telnet your-host.com 5432
   ```

3. **Check Docker network (if using Docker Compose):**
   ```bash
   docker network inspect mem0-rag-network
   ```

### Auto-Detection Issues

If auto-detection isn't working correctly:

- Explicitly set the host via environment variable (e.g., `REDIS_HOST=your-host`)
- The application will use the explicitly set value over auto-detection

### SSL/TLS Issues

For external services requiring SSL:

- Set `DB_SSL=true` for PostgreSQL
- Set `MINIO_USE_SSL=true` for MinIO
- Use `https://` in URLs for Meilisearch and Mem0

---

## Summary

✅ **All dependencies are configurable** - No hardcoded connections  
✅ **Environment-aware** - Auto-detects Docker vs host environment  
✅ **Flexible setup** - Supports Docker Compose, external services, or hybrid  
✅ **Production-ready** - Supports SSL, connection pooling, and timeouts

You can connect to external instances of all services by simply setting the appropriate environment variables in your `.env` file or system environment.
