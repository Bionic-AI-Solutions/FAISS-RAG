# Enterprise Multi-Modal RAG System - Configuration Reference

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Core Services Configuration](#core-services-configuration)
3. [Application Configuration](#application-configuration)
4. [Environment Variables](#environment-variables)
5. [Tuning Parameters](#tuning-parameters)

---

## 1. Configuration Overview

### 1.1 Configuration Management

All configurations are managed through:
- **Kubernetes ConfigMaps**: Non-sensitive configuration
- **Kubernetes Secrets**: Sensitive data (passwords, API keys)
- **HashiCorp Vault**: Encryption keys, certificates
- **Environment Variables**: Runtime configuration

### 1.2 Configuration Hierarchy

```
1. Default values (in code)
2. ConfigMap values (cluster-wide)
3. Environment variables (pod-specific)
4. Vault secrets (dynamic)
```

---

## 2. Core Services Configuration

### 2.1 Redis Configuration

```yaml
# redis-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: rag-system
data:
  redis.conf: |
    # Network
    bind 0.0.0.0
    port 6379
    protected-mode yes
    tcp-backlog 511
    timeout 0
    tcp-keepalive 300
    
    # General
    daemonize no
    supervised no
    databases 16
    
    # Persistence
    save 900 1        # Save after 900 sec if 1 key changed
    save 300 10       # Save after 300 sec if 10 keys changed
    save 60 10000     # Save after 60 sec if 10000 keys changed
    stop-writes-on-bgsave-error yes
    rdbcompression yes
    rdbchecksum yes
    dbfilename dump.rdb
    dir /data
    
    # AOF
    appendonly yes
    appendfilename "appendonly.aof"
    appendfsync everysec
    no-appendfsync-on-rewrite no
    auto-aof-rewrite-percentage 100
    auto-aof-rewrite-min-size 64mb
    
    # Memory Management
    maxmemory 8gb
    maxmemory-policy allkeys-lru
    maxmemory-samples 5
    
    # Performance
    slowlog-log-slower-than 10000  # microseconds
    slowlog-max-len 128
    latency-monitor-threshold 100
    
    # Cluster
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    cluster-require-full-coverage yes
```

**Key Parameters:**

| Parameter | Default | Description | Tuning Guidance |
|-----------|---------|-------------|-----------------|
| `maxmemory` | 8GB | Max memory per node | Set to 75% of available RAM |
| `maxmemory-policy` | allkeys-lru | Eviction policy | Use allkeys-lru for cache |
| `save` | Multiple | RDB save triggers | Adjust for write frequency |
| `appendfsync` | everysec | AOF sync frequency | everysec for balance |

### 2.2 PostgreSQL Configuration

```yaml
# postgres-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: rag-system
data:
  postgresql.conf: |
    # Connection Settings
    listen_addresses = '*'
    max_connections = 1000
    superuser_reserved_connections = 3
    
    # Memory
    shared_buffers = 16GB          # 25% of RAM
    effective_cache_size = 48GB    # 75% of RAM
    maintenance_work_mem = 2GB
    work_mem = 16MB
    
    # Checkpoint
    checkpoint_completion_target = 0.9
    wal_buffers = 16MB
    min_wal_size = 1GB
    max_wal_size = 4GB
    
    # Planner
    default_statistics_target = 100
    random_page_cost = 1.1  # SSD
    effective_io_concurrency = 200
    
    # Parallelism
    max_worker_processes = 16
    max_parallel_workers_per_gather = 4
    max_parallel_workers = 16
    max_parallel_maintenance_workers = 4
    
    # Logging
    log_destination = 'stderr'
    logging_collector = on
    log_directory = 'log'
    log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
    log_rotation_age = 1d
    log_rotation_size = 1GB
    log_min_duration_statement = 1000  # Log queries > 1s
    log_checkpoints = on
    log_connections = on
    log_disconnections = on
    log_lock_waits = on
    
    # Replication
    wal_level = replica
    max_wal_senders = 10
    max_replication_slots = 10
    hot_standby = on
    
    # Extensions
    shared_preload_libraries = 'pg_stat_statements,pgvector'
```

**Key Parameters:**

| Parameter | Default | Description | Tuning Guidance |
|-----------|---------|-------------|-----------------|
| `shared_buffers` | 16GB | Shared memory buffer | 25% of RAM for dedicated server |
| `effective_cache_size` | 48GB | Planner's assumption | 75% of RAM |
| `work_mem` | 16MB | Per-operation memory | Increase for complex queries |
| `max_connections` | 1000 | Max client connections | Based on application needs |

### 2.3 Elasticsearch Configuration

```yaml
# elasticsearch-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elasticsearch-config
  namespace: rag-system
data:
  elasticsearch.yml: |
    # Cluster
    cluster.name: rag-system-es
    node.name: ${HOSTNAME}
    network.host: 0.0.0.0
    
    # Discovery
    discovery.seed_hosts:
      - elasticsearch-0.elasticsearch
      - elasticsearch-1.elasticsearch
      - elasticsearch-2.elasticsearch
    cluster.initial_master_nodes:
      - elasticsearch-0
      - elasticsearch-1
      - elasticsearch-2
    
    # Performance
    indices.memory.index_buffer_size: 30%
    indices.queries.cache.size: 15%
    thread_pool.write.queue_size: 1000
    thread_pool.search.queue_size: 1000
    
    # Circuit Breakers
    indices.breaker.total.limit: 70%
    indices.breaker.request.limit: 40%
    indices.breaker.fielddata.limit: 40%
```

**JVM Options:**

```
# jvm.options
-Xms8g
-Xmx8g  # Set to 50% of RAM, max 32GB
-XX:+UseG1GC
-XX:G1ReservePercent=25
-XX:InitiatingHeapOccupancyPercent=30
```

### 2.4 FAISS Configuration

```python
# faiss_config.py
FAISS_CONFIG = {
    "index_type": "IVF4096,PQ64",
    "dimension": 768,
    "metric": "cosine",
    
    # Training parameters
    "training_size": 100000,  # Vectors to train on
    "nlist": 4096,            # Number of clusters
    
    # Search parameters
    "nprobe": 64,             # Clusters to search
    
    # Quantization
    "m": 64,                  # Subquantizers
    "nbits": 8,               # Bits per subquantizer
    
    # Storage
    "on_disk": True,
    "mmap": True,
    "use_gpu": False,
    
    # Sharding
    "shard_size": 10000000,   # 10M vectors per shard
    "auto_shard": True
}

# Performance tuning by scale
FAISS_CONFIGS_BY_SCALE = {
    "small": {  # < 1M vectors
        "index_type": "IndexFlatIP",
        "nprobe": None
    },
    "medium": {  # 1M-10M vectors
        "index_type": "IVF1024,Flat",
        "nprobe": 32
    },
    "large": {  # 10M-100M vectors
        "index_type": "IVF4096,PQ64",
        "nprobe": 64
    },
    "xlarge": {  # > 100M vectors
        "index_type": "IndexShards",
        "nprobe": 128
    }
}
```

### 2.5 Kafka Configuration

```yaml
# kafka-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-config
  namespace: rag-system
data:
  server.properties: |
    # Broker
    broker.id.generation.enable=true
    listeners=PLAINTEXT://:9092,CONTROLLER://:9093
    
    # Storage
    log.dirs=/var/lib/kafka/data
    num.partitions=10
    default.replication.factor=3
    min.insync.replicas=2
    
    # Performance
    num.network.threads=8
    num.io.threads=16
    socket.send.buffer.bytes=102400
    socket.receive.buffer.bytes=102400
    socket.request.max.bytes=104857600
    
    # Retention
    log.retention.hours=168  # 7 days
    log.segment.bytes=1073741824  # 1GB
    log.retention.check.interval.ms=300000
    
    # Replication
    replica.lag.time.max.ms=30000
    replica.fetch.min.bytes=1
    replica.fetch.wait.max.ms=500
```

---

## 3. Application Configuration

### 3.1 Query Service Configuration

```yaml
# query-service-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: query-service-config
  namespace: rag-system
data:
  config.yaml: |
    server:
      host: 0.0.0.0
      port: 8000
      workers: 4
      timeout: 30
    
    embedding:
      provider: nomic
      model: nomic-embed-text-v1.5
      dimension: 768
      batch_size: 128
      cache_ttl: 3600
    
    retrieval:
      top_k: 20
      min_score: 0.7
      
      vector_search:
        enabled: true
        weight: 0.5
        nprobe: 64
      
      keyword_search:
        enabled: true
        weight: 0.3
        fields: ["text", "title"]
      
      graph_search:
        enabled: true
        weight: 0.2
        max_hops: 2
      
      fusion:
        method: reciprocal_rank_fusion
        k: 60
      
      reranking:
        enabled: true
        model: BAAI/bge-reranker-v2-m3
        batch_size: 32
    
    llm:
      default_provider: openrouter
      
      providers:
        claude:
          model: claude-sonnet-4-20250514
          max_tokens: 200000
          temperature: 0.7
        
        openai:
          model: gpt-4-turbo
          max_tokens: 128000
          temperature: 0.7
        
        ollama:
          endpoint: http://ollama:11434
          model: llama3.1:70b
          max_tokens: 128000
          temperature: 0.7
        
        openrouter:
          endpoint: https://openrouter.ai/api/v1
          api_key: ${OPENROUTER_API_KEY}
          default_model: openai/gpt-4-turbo
          fallback_models:
            - anthropic/claude-3.5-sonnet
            - meta-llama/llama-3.1-70b-instruct
          cost_tracking: true
          auto_failover: true
        
        openai_compatible:
          endpoints:
            - name: vllm-local
              url: http://vllm-service:8000/v1
              api_key: ${VLLM_API_KEY}
              models: [llama-3.1-70b, mistral-7b]
            - name: tensorrt-llm
              url: http://tensorrt-llm:8000/v1
              api_key: ${TENSORRT_API_KEY}
              models: [llama-3.1-70b]
          health_check_interval: 60
          auto_failover: true
      
      routing:
        long_context_threshold: 100000
        simple_query_threshold: 1000
        long_context: claude
        cost_optimized: openrouter
        default: openrouter
        self_hosted: openai_compatible
    
    cache:
      enabled: true
      ttl:
        embeddings: 3600
        search_results: 300
        llm_responses: 600
      max_size: 10000
    
    monitoring:
      metrics_enabled: true
      tracing_enabled: true
      log_level: INFO
```

### 3.2 Ingestion Worker Configuration

```yaml
# ingestion-worker-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingestion-worker-config
  namespace: rag-ingestion
data:
  config.yaml: |
    kafka:
      brokers:
        - kafka-0.kafka:9092
        - kafka-1.kafka:9092
        - kafka-2.kafka:9092
      group_id: ingestion-workers
      topics:
        - ingestion_requests
      auto_offset_reset: earliest
      max_poll_records: 10
    
    processing:
      text:
        enabled: true
        chunk_size: 512
        chunk_overlap: 128
        supported_formats:
          - pdf
          - docx
          - txt
          - md
          - html
      
      image:
        enabled: true
        max_dimension: 2048
        ocr_enabled: true
        supported_formats:
          - jpg
          - jpeg
          - png
          - webp
      
      audio:
        enabled: true
        transcription_model: whisper-large-v3
        diarization_enabled: true
        supported_formats:
          - mp3
          - wav
          - m4a
      
      video:
        enabled: true
        frame_extraction_fps: 1
        scene_detection_threshold: 27.0
        supported_formats:
          - mp4
          - avi
          - mov
      
      table:
        enabled: true
        extraction_library: camelot
        supported_formats:
          - pdf
          - xlsx
          - csv
    
    storage:
      vectors:
        backend: faiss
        batch_size: 1000
      
      metadata:
        backend: postgresql
        batch_size: 100
      
      files:
        backend: minio
        bucket: documents
    
    concurrency:
      max_workers: 10
      timeout: 300
```

---

## 4. Environment Variables

### 4.1 Query Service Environment Variables

```bash
# Core settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database connections
POSTGRES_HOST=postgres.rag-system.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DB=rag_system
POSTGRES_USER=rag_admin
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}  # From secret

REDIS_HOST=redis-cluster.rag-system.svc.cluster.local
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}  # From secret
REDIS_DB=0

ELASTICSEARCH_HOST=elasticsearch.rag-system.svc.cluster.local
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=${ELASTICSEARCH_PASSWORD}  # From secret

NEO4J_URI=bolt://neo4j.rag-system.svc.cluster.local:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${NEO4J_PASSWORD}  # From secret

# Object storage
MINIO_ENDPOINT=minio.rag-system.svc.cluster.local:9000
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}  # From secret
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}  # From secret
MINIO_SECURE=false

# LLM providers
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}  # From secret
OPENAI_API_KEY=${OPENAI_API_KEY}  # From secret
OLLAMA_HOST=http://ollama.rag-system.svc.cluster.local:11434
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}  # From secret
VLLM_API_KEY=${VLLM_API_KEY}  # From secret (if using vLLM)
TENSORRT_LLM_API_KEY=${TENSORRT_LLM_API_KEY}  # From secret (if using TensorRT-LLM)

# JWT
JWT_SECRET=${JWT_SECRET}  # From secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Feature flags
ENABLE_CACHING=true
ENABLE_TRACING=true
ENABLE_METRICS=true

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=30
MAX_UPLOAD_SIZE=104857600  # 100MB

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
```

### 4.2 Ingestion Worker Environment Variables

```bash
# Kafka
KAFKA_BROKERS=kafka-0.kafka:9092,kafka-1.kafka:9092,kafka-2.kafka:9092
KAFKA_GROUP_ID=ingestion-workers
KAFKA_AUTO_OFFSET_RESET=earliest

# Processing
MAX_CONCURRENT_JOBS=10
PROCESSING_TIMEOUT=300
CHUNK_SIZE=512
CHUNK_OVERLAP=128

# Embedding
EMBEDDING_PROVIDER=nomic
EMBEDDING_MODEL=nomic-embed-text-v1.5
EMBEDDING_BATCH_SIZE=128

# Storage backends (same as query service)
POSTGRES_HOST=...
REDIS_HOST=...
MINIO_ENDPOINT=...
```

---

## 5. Tuning Parameters

### 5.1 Performance Tuning Guide

#### Query Latency Optimization

```yaml
targets:
  p50: < 200ms
  p95: < 800ms
  p99: < 1.5s

tuning_parameters:
  # FAISS search
  faiss_nprobe:
    default: 64
    low_latency: 32      # Faster, less accurate
    high_accuracy: 128   # Slower, more accurate
  
  # Cache settings
  cache_hit_rate_target: 0.80
  cache_ttl:
    hot_queries: 600    # 10 minutes
    normal_queries: 300 # 5 minutes
  
  # Retrieval
  top_k:
    initial_retrieval: 100
    after_fusion: 60
    final_results: 20
  
  # LLM
  max_context_tokens: 8000
  max_completion_tokens: 2000
  temperature: 0.7
  
  # Concurrency
  max_concurrent_requests: 1000
  connection_pool_size: 100
```

#### Throughput Optimization

```yaml
targets:
  queries_per_second: 10000-50000
  documents_per_second: 1000

tuning_parameters:
  # Horizontal scaling
  query_service_replicas:
    min: 10
    max: 500
    target_cpu: 70%
  
  ingestion_workers:
    min: 20
    max: 200
    target_kafka_lag: 1000
  
  # Batch processing
  embedding_batch_size: 128
  database_batch_size: 1000
  
  # Connection pooling
  postgres_pool_size: 100
  redis_pool_size: 50
```

#### Memory Optimization

```yaml
# Redis memory tuning
redis:
  maxmemory_policy: allkeys-lru
  maxmemory_samples: 5
  
  # Reduce memory usage
  hash_max_ziplist_entries: 512
  hash_max_ziplist_value: 64
  list_max_ziplist_size: -2
  
# FAISS memory tuning
faiss:
  # Use PQ for compression
  quantization: PQ64
  
  # Memory-mapped files
  use_mmap: true
  
  # GPU offloading (optional)
  use_gpu: false

# PostgreSQL memory tuning
postgresql:
  shared_buffers: 16GB  # 25% of RAM
  work_mem: 16MB        # Per operation
  maintenance_work_mem: 2GB
```

### 5.2 Resource Allocation by Tenant Tier

```yaml
tenant_tiers:
  namespace:
    storage_limit: 10GB
    vector_limit: 1000000
    qps_limit: 100
    resources:
      cpu: shared
      memory: shared
      cache: shared
  
  index:
    storage_limit: 100GB
    vector_limit: 10000000
    qps_limit: 1000
    resources:
      cpu: 8_cores
      memory: 32GB
      cache: 2GB
  
  cluster:
    storage_limit: 1TB
    vector_limit: 100000000
    qps_limit: 10000
    resources:
      cpu: 32_cores
      memory: 128GB
      cache: 10GB
      dedicated_nodes: true
```

### 5.3 Cost Optimization

```yaml
cost_optimization:
  compute:
    # Use spot instances for workers
    ingestion_workers:
      spot_percentage: 80%
      on_demand_minimum: 20%
    
    # Auto-scale based on load
    query_service:
      scale_down_after: 15m
      scale_up_threshold: 70%
  
  storage:
    # Tiered storage
    hot_data:
      storage_class: fast-ssd
      retention: 30_days
    
    cold_data:
      storage_class: standard
      retention: 1_year
    
    archive:
      storage_class: glacier
      retention: 7_years
  
  llm:
    # Route by cost
    simple_queries: ollama      # $0/1K tokens
    complex_queries: openai     # $0.01/1K tokens
    long_context: claude        # $0.015/1K tokens
  
  cache:
    # Aggressive caching
    enable_cdn: true
    cache_ttl_multiplier: 2.0
    cache_size_target: 20GB
```

---

## Appendix A: Complete Configuration Template

```yaml
# complete-config.yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-system-config
  namespace: rag-system
data:
  # Application Configuration
  app.yaml: |
    # Insert complete app config here
  
  # Infrastructure Configuration
  infrastructure.yaml: |
    # Redis, PostgreSQL, ES, etc.
  
  # Feature Flags
  features.yaml: |
    enable_multimodal: true
    enable_graph_search: true
    enable_agents: true
    enable_streaming: true
  
  # Monitoring
  monitoring.yaml: |
    prometheus:
      scrape_interval: 15s
      retention: 15d
    
    grafana:
      datasources: [prometheus, elasticsearch]
    
    jaeger:
      sampling_rate: 0.1
```

---

## Appendix B: Configuration Validation

```python
# config_validator.py
from pydantic import BaseModel, validator
from typing import Optional, List

class RedisConfig(BaseModel):
    host: str
    port: int = 6379
    password: Optional[str]
    db: int = 0
    maxmemory: str = "8gb"
    
    @validator('maxmemory')
    def validate_memory(cls, v):
        # Validate memory format
        assert v.endswith(('gb', 'mb'))
        return v

class FAISSConfig(BaseModel):
    dimension: int = 768
    index_type: str = "IVF4096,PQ64"
    nprobe: int = 64
    
    @validator('dimension')
    def validate_dimension(cls, v):
        assert v in [768, 1536], "Dimension must be 768 or 1536"
        return v

class SystemConfig(BaseModel):
    redis: RedisConfig
    faiss: FAISSConfig
    # ... other configs

# Usage
config = SystemConfig.parse_file("config.yaml")
```

---

**End of Configuration Reference**

For architecture details, see: ARCHITECTURE.md
For deployment instructions, see: DEPLOYMENT.md
For operations procedures, see: OPERATIONS.md
