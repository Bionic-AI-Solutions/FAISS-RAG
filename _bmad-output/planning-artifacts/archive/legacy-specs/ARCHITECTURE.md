# Enterprise Multi-Modal RAG System - Architecture Specification

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Specifications](#component-specifications)
4. [Data Flow](#data-flow)
5. [Scalability Model](#scalability-model)
6. [Technology Stack](#technology-stack)

---

## 1. System Overview

### 1.1 Executive Summary

**Purpose**: Enterprise-grade, multi-tenant, multi-modal RAG system supporting 10,000 tenants with 1,000+ concurrent users each.

**Key Capabilities**:
- Multi-modal processing (text, images, audio, video, tables)
- Cross-modal search (text query → image results)
- Multi-agent orchestration with private memory scopes
- Session isolation with Redis-based caching
- Hybrid retrieval (vector + keyword + graph)
- HIPAA/SOC2/GDPR/FedRAMP compliant
- Hybrid cloud deployment (on-prem + cloud)

**Performance Targets**:
- Query Latency: p95 < 800ms
- Throughput: 10,000-50,000 QPS (distributed)
- Availability: 99.95%
- Document Ingestion: 1,000 docs/sec

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Edge Layer (HA Proxy)                         │
│              TLS 1.3 | DDoS Protection | CDN                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   API Gateway (Kong OSS)                         │
│    JWT/OAuth2 | RBAC | Rate Limiting | Tenant Routing          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
    ┌─────────▼────────┐              ┌────────▼─────────┐
    │ Ingestion Service│              │  Query Service   │
    │  (Kafka Workers) │              │    (FastAPI)     │
    └─────────┬────────┘              └────────┬─────────┘
              │                                 │
              └────────────┬────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │              Event Bus (Kafka)                    │
    │  Topics: ingestion, queries, audit, metrics      │
    └──────────────────────┬───────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │           Processing Pipeline Layer               │
    ├──────────┬─────────┬─────────┬─────────┬─────────┤
    │  Text    │ Image   │ Audio   │ Video   │ Table   │
    │ Pipeline │Pipeline │Pipeline │Pipeline │Pipeline │
    └──────────┴─────────┴─────────┴─────────┴─────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │              Memory & Cache Layer                 │
    │  ┌──────────────┐  ┌──────────────┐             │
    │  │ Redis Cluster│  │ FAISS Indices│             │
    │  │ (L1 Cache)   │  │ (L2/L3 Store)│             │
    │  └──────────────┘  └──────────────┘             │
    └───────────────────────────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │           Hybrid Retrieval Engine                 │
    ├──────────┬──────────────┬──────────────┬─────────┤
    │  FAISS   │Elasticsearch │    Neo4j     │Reranker │
    │ (Vector) │  (Keyword)   │   (Graph)    │(ColBERT)│
    └──────────┴──────────────┴──────────────┴─────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │      Multi-Agent Orchestration (LangGraph)        │
    │  Orchestrator | Retrieval | Domain | Tool Agents │
    └───────────────────────────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │             LLM Provider Layer                    │
    │  ┌─────────┐  ┌─────────┐  ┌──────────┐         │
    │  │ Claude  │  │ OpenAI  │  │  Ollama  │         │
    │  │ Sonnet  │  │   GPT   │  │ Llama3.1 │         │
    │  └─────────┘  └─────────┘  └──────────┘         │
    └───────────────────────────────────────────────────┘
                           │
    ┌──────────────────────▼───────────────────────────┐
    │              Data Storage Layer                   │
    ├─────────────┬──────────────┬──────────┬──────────┤
    │ PostgreSQL  │ MinIO/Ceph   │TimescaleDB│  Vault  │
    │ (Metadata)  │ (Objects)    │ (Metrics) │(Secrets)│
    │ + pgvector  │  Encrypted   │Audit Logs │   KMS   │
    └─────────────┴──────────────┴──────────┴──────────┘
```

---

## 2. Architecture Patterns

### 2.1 Multi-Tenancy Model

**Three-Tier Isolation Strategy**:

```python
class TenantTier(Enum):
    NAMESPACE = "namespace"      # Shared infra, metadata filtering
    INDEX = "dedicated_index"     # Dedicated indices, shared cluster
    CLUSTER = "dedicated_cluster" # Fully isolated infrastructure

# Tenant allocation logic
def allocate_tenant_tier(tenant_profile):
    if tenant_profile.security_level == "high" or \
       tenant_profile.data_volume > 100_GB:
        return TenantTier.CLUSTER
    
    elif tenant_profile.data_volume > 10_GB:
        return TenantTier.INDEX
    
    else:
        return TenantTier.NAMESPACE
```

**Isolation Mechanisms**:

| Tier | FAISS Index | Redis | Elasticsearch | PostgreSQL | Encryption |
|------|-------------|-------|---------------|------------|------------|
| Namespace | Shared with filters | Shared keyspace | Shared index | Shared schema | Tenant-level KEK |
| Index | Dedicated index | Dedicated DB | Dedicated index | Shared schema | Tenant-level KEK |
| Cluster | Dedicated cluster | Dedicated cluster | Dedicated cluster | Dedicated DB | Infrastructure-level |

### 2.2 Cache Strategy (Redis)

**Three-Level Caching**:

```
L1: Hot Embeddings (1h TTL)
├── Key: emb:{tenant_id}:{content_hash}
├── Size: ~10GB per cluster
└── Compression: float32 → float16

L2: Session Data (24h TTL)
├── Key: session:{tenant_id}:{user_id}:{session_id}
├── Chat history: List structure
└── User context: Hash structure

L3: Search Results (5min TTL)
├── Key: search:{tenant_id}:{query_hash}
├── Value: JSON serialized results
└── Invalidation: On document updates
```

**Redis Cluster Configuration**:
- 6 nodes (3 masters + 3 replicas)
- 8GB RAM per node
- Persistence: RDB + AOF
- Eviction: allkeys-lru

### 2.3 Scalability Patterns

**Horizontal Scaling**:
- Stateless query services (scale 1-1000 pods)
- Sharded FAISS indices (10M vectors/shard)
- Elasticsearch cluster (scale nodes dynamically)
- Redis cluster (scale nodes for cache)

**Auto-Scaling Rules**:
```yaml
autoscaling:
  query_service:
    metric: cpu_utilization
    target: 70%
    min_replicas: 10
    max_replicas: 500
  
  ingestion_workers:
    metric: kafka_lag
    target: 1000_messages
    min_replicas: 5
    max_replicas: 200
```

---

## 3. Component Specifications

### 3.1 Redis Cache Layer

**Purpose**: Session management, hot cache, rate limiting

**Architecture**:
- Redis Cluster: 6 nodes (3 masters + 3 replicas)
- Persistence: RDB snapshots + AOF
- Eviction: allkeys-lru policy
- Memory: 8GB per node (48GB total)

**Data Structures**:
```
Keys:
  session:{tenant_id}:{user_id}:{session_id}  → Hash
  chat:{tenant_id}:{user_id}:{session_id}      → List
  emb:{tenant_id}:{content_hash}               → String (binary)
  search:{tenant_id}:{query_hash}              → String (JSON)
  ratelimit:{tenant_id}:{user_id}              → Sorted Set
  user:{tenant_id}:{user_id}:sessions          → Set
```

**Cache Implementation**:
```python
class RedisCacheManager:
    async def cache_embedding(self, key: str, embedding: np.ndarray, ttl: int = 3600):
        """Cache embedding with compression"""
        cache_key = f"emb:{key}"
        compressed = embedding.astype(np.float16).tobytes()
        return await self.cluster.setex(cache_key, ttl, compressed)
    
    async def get_embedding(self, key: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding"""
        cache_key = f"emb:{key}"
        data = await self.cluster.get(cache_key)
        if data:
            return np.frombuffer(data, dtype=np.float16).astype(np.float32)
        return None
```

### 3.2 FAISS Vector Store

**Purpose**: High-performance vector similarity search

**Index Configuration**:
```python
# For datasets up to 100M vectors per tenant
index_config = {
    "type": "IVF4096,PQ64",
    "dimension": 768,  # Nomic embed dimension
    "metric": "cosine",
    "nprobe": 64,
    "on_disk": True,
    "mmap": True,
    "gpu_enabled": False  # Optional GPU acceleration
}
```

**Sharding Strategy**:
- Shard size: 10M vectors
- Shard distribution: Round-robin across nodes
- Query routing: Query all shards, merge results

**Index Types by Scale**:
| Vectors | Index Type | Memory | Disk |
|---------|-----------|--------|------|
| < 1M | IndexFlatIP | ~3GB | 0 |
| 1M-10M | IVF1024,Flat | ~4GB | 0 |
| 10M-100M | IVF4096,PQ64 | ~600MB | ~3GB |
| 100M+ | IndexShards(IVF4096,PQ64) | ~6GB | ~30GB |

### 3.3 Nomic Embedding Service

**Models**:
- Text: `nomic-embed-text-v1.5` (768d)
- Vision: `nomic-embed-vision-v1.5` (768d)

**Task Types**:
- `search_query`: For user queries
- `search_document`: For document chunks
- `clustering`: For document organization
- `classification`: For categorization

**Implementation**:
```python
class NomicEmbeddingService:
    def __init__(self):
        self.text_model = "nomic-embed-text-v1.5"
        self.vision_model = "nomic-embed-vision-v1.5"
        self.dimension = 768
        self.max_batch_size = 128
    
    async def embed_texts(
        self,
        texts: List[str],
        task_type: str = 'search_document'
    ) -> np.ndarray:
        """Embed text with task-specific optimization"""
        embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            result = embed.text(
                texts=batch,
                model=self.text_model,
                task_type=task_type,
                dimensionality=self.dimension
            )
            embeddings.extend(result['embeddings'])
        return np.array(embeddings, dtype=np.float32)
```

**Performance**:
- Batch size: 128 texts/images
- Throughput: 10,000 embeddings/sec
- Latency: p95 < 100ms for batch
- Cache hit ratio target: 80%

### 3.4 Hybrid Retrieval Engine

**Three-Stage Retrieval**:

```python
class HybridRetrievalEngine:
    async def retrieve(self, query: str, tenant_id: str, top_k: int = 20):
        # Stage 1: Parallel retrieval
        vector_results, keyword_results, graph_results = await asyncio.gather(
            self._vector_search(query, tenant_id, k=100),
            self._keyword_search(query, tenant_id, k=100),
            self._graph_search(query, tenant_id, k=50)
        )
        
        # Stage 2: Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion([
            vector_results,
            keyword_results,
            graph_results
        ], k=60)
        
        # Stage 3: Cross-encoder reranking
        reranked = await self.reranker.rerank(
            query=query,
            documents=fused_results,
            top_k=top_k
        )
        
        return reranked
```

**Reciprocal Rank Fusion**:
```python
def _reciprocal_rank_fusion(
    self,
    result_lists: List[List[Tuple[str, float]]],
    k: int = 60
) -> List[Dict]:
    """
    RRF score = sum(1 / (k + rank_i)) across all lists
    """
    doc_scores = {}
    
    for result_list in result_lists:
        for rank, (doc_id, _) in enumerate(result_list, 1):
            if doc_id not in doc_scores:
                doc_scores[doc_id] = 0
            doc_scores[doc_id] += 1 / (k + rank)
    
    # Sort by RRF score
    sorted_docs = sorted(
        doc_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return [{'doc_id': doc_id, 'rrf_score': score} 
            for doc_id, score in sorted_docs]
```

### 3.5 Multi-Agent System (LangGraph)

**Agent Types**:

1. **Orchestrator Agent**
   - Decomposes complex queries
   - Coordinates other agents
   - Synthesizes final response

2. **Retrieval Agents**
   - Document Retriever
   - Code Retriever
   - Image Retriever
   - Table Retriever

3. **Domain Expert Agents**
   - Finance Agent
   - Legal Agent
   - Technical Agent
   - Custom domain agents

4. **Tool Agents**
   - Calculator/Code Executor
   - Web Search Agent
   - API Integration Agent

**Agent Memory Scopes**:
```python
memory_scopes = {
    "agent_private": {
        # Each agent's working memory
        "storage": "redis",
        "ttl": 3600,
        "namespace": "agent:{agent_id}:memory"
    },
    "session": {
        # Current conversation
        "storage": "redis",
        "ttl": 86400,
        "namespace": "session:{session_id}"
    },
    "user": {
        # User-specific long-term memory
        "storage": "faiss_index",
        "namespace": "user:{tenant_id}:{user_id}"
    }
}
```

### 3.6 LLM Provider Integration

**Provider Configuration**:
```python
llm_config = {
    "providers": {
        "claude": {
            "endpoint": "https://api.anthropic.com",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 200000
        },
        "openai": {
            "endpoint": "https://api.openai.com/v1",
            "model": "gpt-4-turbo",
            "max_tokens": 128000
        },
        "ollama": {
            "endpoint": "http://ollama:11434",
            "model": "llama3.1:70b",
            "max_tokens": 128000,
            "cost": 0.0  # Self-hosted
        },
        "openrouter": {
            "endpoint": "https://openrouter.ai/api/v1",
            "api_key": "${OPENROUTER_API_KEY}",
            "default_model": "openai/gpt-4-turbo",
            "fallback_models": [
                "anthropic/claude-3.5-sonnet",
                "meta-llama/llama-3.1-70b-instruct"
            ],
            "cost_tracking": True,
            "auto_failover": True
        },
        "openai_compatible": {
            "endpoints": [
                {
                    "name": "vllm-local",
                    "url": "http://vllm-service:8000/v1",
                    "api_key": "${VLLM_API_KEY}",
                    "models": ["llama-3.1-70b", "mistral-7b"]
                },
                {
                    "name": "tensorrt-llm",
                    "url": "http://tensorrt-llm:8000/v1",
                    "api_key": "${TENSORRT_API_KEY}",
                    "models": ["llama-3.1-70b"]
                }
            ],
            "health_check_interval": 60,
            "auto_failover": True
        }
    },
    "routing": {
        "long_context": "claude",           # > 100K tokens
        "cost_optimized": "openrouter",     # Cost optimization
        "default": "openrouter",            # Default provider
        "self_hosted": "openai_compatible"  # Self-hosted models
    }
}
```

---

## 4. Data Flow

### 4.1 Document Ingestion Pipeline

```
User Upload
    ↓
API Gateway (validation)
    ↓
Kafka Topic (ingestion_requests)
    ↓
Worker Pool (auto-scaling)
    ↓
Multi-Modal Processing:
    ├─ Text Pipeline → Chunking → Embedding
    ├─ Image Pipeline → OCR → Vision Embedding
    ├─ Audio Pipeline → Transcription → Embedding
    ├─ Video Pipeline → Frame + Audio Extraction
    └─ Table Pipeline → Structure Extraction
    ↓
Parallel Storage:
    ├─ FAISS (vectors)
    ├─ Elasticsearch (keywords)
    ├─ Neo4j (graph)
    ├─ PostgreSQL (metadata)
    └─ MinIO (raw files)
    ↓
Kafka Topic (ingestion_complete)
    ↓
User Notification
```

### 4.2 Query Processing Pipeline

```
User Query
    ↓
API Gateway (auth + rate limit)
    ↓
Query Service
    ↓
Redis Cache Check
    ├─ Hit → Return cached result
    └─ Miss → Continue
        ↓
    Query Embedding (Nomic)
        ↓
    Parallel Retrieval:
        ├─ FAISS (vector search)
        ├─ Elasticsearch (keyword)
        └─ Neo4j (graph)
        ↓
    Reciprocal Rank Fusion
        ↓
    Reranking (ColBERT)
        ↓
    Multi-Agent Processing
        ↓
    LLM Generation (routed provider)
        ↓
    Cache Result (Redis)
        ↓
    Return to User
```

---

## 5. Scalability Model

### 5.1 Resource Requirements (10,000 Tenants)

**Distribution**:
- 80% Namespace tier (8,000 tenants)
- 15% Index tier (1,500 tenants)
- 5% Cluster tier (500 tenants)

**Storage Calculations**:

```
FAISS Vector Storage:
  Namespace: 8,000 × 650MB = 5.2TB
  Index: 1,500 × 6.5GB = 9.75TB
  Cluster: 500 × 65GB = 32.5TB
  Total: ~48TB (with 2x replication: 96TB)

Redis Cache:
  Active sessions: 1M concurrent × 1MB = 1TB
  Hot cache: 20% of vectors compressed = 9.6TB
  Total: ~11TB across cluster

Elasticsearch:
  Full-text index: ~50TB (with 2x replication: 100TB)

PostgreSQL:
  Metadata: ~5TB (with 2x replication: 10TB)

MinIO Object Storage:
  Raw documents: ~500TB (with 3x replication: 1.5PB)

Compute:
  Query Service: 200-500 pods × 4 vCPU = 800-2,000 vCPU
  Workers: 100-200 pods × 8 vCPU = 800-1,600 vCPU
  Vector Search: 50 pods × 16 vCPU = 800 vCPU
  Total: 2,400-4,400 vCPU cores
```

### 5.2 Performance Projections

**Query Performance**:
- Cold query (cache miss): 600-800ms (p95)
- Warm query (partial cache): 200-400ms (p95)
- Hot query (full cache): 50-100ms (p95)

**Throughput**:
- Per query service pod: 100-200 QPS
- Total cluster (500 pods): 50,000-100,000 QPS
- With caching (80% hit rate): 250,000 QPS effective

---

## 6. Technology Stack Summary

| Layer | Component | Technology | OSS | Purpose |
|-------|-----------|------------|-----|---------|
| **Edge** | Load Balancer | HA Proxy | ✓ | TLS termination, DDoS |
| **API** | Gateway | Kong OSS | ✓ | Auth, rate limiting |
| **API** | Framework | FastAPI | ✓ | REST endpoints |
| **Cache** | Session/Cache | Redis | ✓ | Hot cache, sessions |
| **Vector** | Vector Store | FAISS | ✓ | Similarity search |
| **Search** | Keyword | Elasticsearch | ✓ | BM25, filtering |
| **Graph** | Knowledge Graph | Neo4j | ✓ | Entity relationships |
| **Embedding** | Text/Vision | Nomic Embed | ✓ | 768d embeddings |
| **Reranker** | Reranking | ColBERTv2 | ✓ | Result reranking |
| **LLM** | Generation | Claude/OpenAI/Ollama | Partial | Response generation |
| **Agents** | Orchestration | LangGraph | ✓ | Multi-agent coord |
| **Queue** | Message Bus | Apache Kafka | ✓ | Event streaming |
| **DB** | Metadata | PostgreSQL + pgvector | ✓ | Structured data |
| **Storage** | Object Store | MinIO | ✓ | Document storage |
| **Metrics** | Time-series | TimescaleDB | ✓ | Metrics, audit |
| **Secrets** | Secret Mgmt | HashiCorp Vault | ✓ | Keys, certificates |
| **Container** | Orchestration | Kubernetes | ✓ | Container mgmt |
| **Monitoring** | Metrics | Prometheus + Grafana | ✓ | System monitoring |
| **Tracing** | Dist. Tracing | Jaeger | ✓ | Request tracing |
| **Logging** | Log Aggregation | ELK Stack | ✓ | Centralized logs |

---

## 7. Key Design Decisions

### 7.1 Why Redis Over Alternatives?

**Chosen**: Redis Cluster

**Rationale**:
- Industry standard with extensive tooling
- Rich data structures (strings, lists, sets, sorted sets, hashes)
- Cluster mode for horizontal scaling
- Persistence options (RDB + AOF)
- Proven at scale (10M+ ops/sec)
- Active community and extensive documentation

### 7.2 Why Nomic Embed?

**Chosen**: Nomic Embed v1.5

**Rationale**:
- Open source and self-hostable
- High quality (MTEB benchmarks competitive)
- 768 dimensions (smaller than 1536, faster)
- Task-specific optimization
- Vision model available
- Multilingual support
- No API costs for self-hosted
- Lower memory footprint

### 7.3 Why Multi-LLM Support?

**Rationale**:
- Flexibility: Different models for different tasks
- Cost optimization: Ollama for simple queries (free)
- Capability matching: Claude for long context (200K tokens)
- Vendor independence: No lock-in
- Compliance: On-prem option (Ollama)
- Redundancy: Failover capability
- Performance: Route by latency requirements

### 7.4 Why FAISS Over Managed Vector DBs?

**Chosen**: FAISS

**Rationale**:
- Highest performance (in-memory with mmap)
- On-disk persistence
- No vendor lock-in
- GPU acceleration option
- Mature and battle-tested (Meta)
- Fine-grained control
- Zero API costs
- Hybrid deployment friendly
- Production proven at billion-scale

---

## Appendix A: Component Communication Matrix

| From/To | Redis | FAISS | ES | Neo4j | Postgres | Kafka | MinIO |
|---------|-------|-------|----|----|----------|-------|-------|
| **Query Service** | R/W | R | R | R | R | W | R |
| **Ingestion Worker** | W | W | W | W | W | R/W | W |
| **FAISS Service** | R | R/W | - | - | R | - | - |
| **Agent System** | R/W | R | R | R | R | W | R |

R = Read, W = Write

---

## Appendix B: Failure Modes & Resilience

| Component | Failure Mode | Impact | Mitigation | Recovery Time |
|-----------|--------------|---------|-----------|---------------|
| Redis Node | Pod failure | Degraded cache | Replica promotion | < 1 min |
| FAISS Pod | Pod failure | Reduced QPS | Load balancing | < 5 min |
| ES Node | Node failure | Degraded search | Shard rebalancing | < 10 min |
| Kafka Broker | Broker failure | Event delay | Partition replicas | < 2 min |
| Query Service | Pod failure | Reduced capacity | Auto-scaling | < 2 min |
| LLM Provider | API failure | Generation fails | Fallback provider | < 30 sec |

**RTO (Recovery Time Objective)**: < 15 minutes
**RPO (Recovery Point Objective)**: < 5 minutes

---

**End of Architecture Document**

For deployment instructions, see: DEPLOYMENT.md
For API specifications, see: API_SPECIFICATION.md
For implementation guide, see: IMPLEMENTATION_ROADMAP.md
