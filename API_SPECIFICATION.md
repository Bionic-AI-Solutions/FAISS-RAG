# Enterprise Multi-Modal RAG System - API Specification

## Version: 1.0
## Last Updated: 2025-12-26

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Request/Response Formats](#requestresponse-formats)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [SDK Examples](#sdk-examples)

---

## 1. API Overview

### 1.1 Base URL

```
Production: https://api.rag-system.com/v1
Staging: https://api-staging.rag-system.com/v1
```

### 1.2 API Principles

- RESTful design
- JSON request/response bodies
- JWT-based authentication
- Tenant isolation via headers
- Versioned endpoints
- Idempotent operations where applicable

### 1.3 Common Headers

```http
Authorization: Bearer <jwt_token>
X-Tenant-ID: <tenant_uuid>
X-Request-ID: <uuid>  # Optional, for tracing
Content-Type: application/json
```

---

## 2. Authentication

### 2.1 Obtain Access Token

**Endpoint:** `POST /auth/token`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "tenant_id": "tenant-uuid-here"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "tenant_id": "tenant-uuid"
  }
}
```

### 2.2 Refresh Token

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 3. Core Endpoints

### 3.1 Document Management

#### Upload Document

**Endpoint:** `POST /documents/upload`

**Request:**
```http
POST /v1/documents/upload HTTP/1.1
Host: api.rag-system.com
Authorization: Bearer <token>
X-Tenant-ID: <tenant-uuid>
Content-Type: multipart/form-data

file: <binary>
metadata: {
  "title": "Q4 Financial Report",
  "category": "finance",
  "tags": ["quarterly", "2024", "finance"],
  "permissions": {
    "read": ["group:finance", "user:alice@example.com"],
    "write": ["user:admin@example.com"]
  }
}
```

**Response:**
```json
{
  "document_id": "doc-uuid-123",
  "status": "processing",
  "filename": "q4_report.pdf",
  "file_size": 1048576,
  "modality": "text",
  "created_at": "2025-12-26T10:00:00Z",
  "estimated_processing_time": 30
}
```

#### Get Document Status

**Endpoint:** `GET /documents/{document_id}/status`

**Response:**
```json
{
  "document_id": "doc-uuid-123",
  "status": "completed",
  "progress": 100,
  "chunks_created": 152,
  "embeddings_generated": 152,
  "processing_time_ms": 28500,
  "errors": []
}
```

#### List Documents

**Endpoint:** `GET /documents`

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `modality` (string): Filter by modality (text, image, audio, video, table)
- `status` (string): Filter by status (processing, completed, failed)
- `sort_by` (string): Sort field (created_at, filename, file_size)
- `sort_order` (string): asc or desc

**Response:**
```json
{
  "documents": [
    {
      "document_id": "doc-uuid-123",
      "filename": "report.pdf",
      "file_size": 1048576,
      "modality": "text",
      "status": "completed",
      "created_at": "2025-12-26T10:00:00Z",
      "metadata": {
        "title": "Q4 Financial Report",
        "tags": ["quarterly", "2024"]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 156,
    "total_pages": 8
  }
}
```

#### Delete Document

**Endpoint:** `DELETE /documents/{document_id}`

**Response:**
```json
{
  "document_id": "doc-uuid-123",
  "status": "deleted",
  "deleted_at": "2025-12-26T11:00:00Z"
}
```

### 3.2 Query Operations

#### Basic Query

**Endpoint:** `POST /query`

**Request:**
```json
{
  "query": "What were the key findings in the Q4 financial report?",
  "filters": {
    "modality": ["text", "table"],
    "tags": ["finance", "quarterly"],
    "date_range": {
      "start": "2024-10-01",
      "end": "2024-12-31"
    }
  },
  "options": {
    "top_k": 10,
    "include_sources": true,
    "stream": false,
    "llm_provider": "openrouter",  # or "claude", "openai", "ollama", "openai_compatible"
    "llm_model": "anthropic/claude-3.5-sonnet",  # Optional: specific model for OpenRouter
    "cost_optimize": false  # Enable cost-optimized routing
  }
}
```

**Response:**
```json
{
  "query_id": "query-uuid-456",
  "response": "Based on the Q4 financial report, the key findings include:\n\n1. Revenue increased by 23% year-over-year\n2. Operating expenses were reduced by 15%\n3. Net profit margin improved to 18%...",
  "sources": [
    {
      "document_id": "doc-uuid-123",
      "chunk_id": "chunk-uuid-789",
      "filename": "q4_report.pdf",
      "page": 5,
      "relevance_score": 0.92,
      "text_preview": "Q4 revenue reached $45M, representing a 23% increase..."
    },
    {
      "document_id": "doc-uuid-124",
      "chunk_id": "chunk-uuid-790",
      "filename": "financial_summary.xlsx",
      "sheet": "Summary",
      "relevance_score": 0.87,
      "text_preview": "Operating expenses: $12M (15% reduction from Q3)"
    }
  ],
  "metadata": {
    "latency_ms": 650,
    "tokens_used": 1250,
    "llm_provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "cost_usd": 0.0025,
    "cache_hit": false
  }
}
```

#### Streaming Query

**Endpoint:** `POST /query/stream`

**Request:** Same as basic query with `"stream": true`

**Response:** Server-Sent Events (SSE)

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type":"start","query_id":"query-uuid-456"}

data: {"type":"chunk","content":"Based on the Q4"}

data: {"type":"chunk","content":" financial report,"}

data: {"type":"chunk","content":" the key findings"}

data: {"type":"source","source":{"document_id":"doc-uuid-123","relevance_score":0.92}}

data: {"type":"end","metadata":{"latency_ms":650,"tokens_used":1250}}
```

#### Multi-Modal Query

**Endpoint:** `POST /query/multimodal`

**Request:**
```json
{
  "query": "Find charts showing revenue trends",
  "modalities": ["text", "image", "table"],
  "cross_modal": true,
  "options": {
    "top_k_per_modality": 5,
    "fusion_strategy": "weighted",
    "weights": {
      "text": 0.4,
      "image": 0.3,
      "table": 0.3
    }
  }
}
```

**Response:**
```json
{
  "query_id": "query-uuid-457",
  "response": "I found several visualizations and data tables showing revenue trends...",
  "results_by_modality": {
    "image": [
      {
        "document_id": "doc-uuid-125",
        "image_url": "https://storage.rag-system.com/images/chart_123.png",
        "caption": "Q4 Revenue Growth Chart",
        "relevance_score": 0.94
      }
    ],
    "table": [
      {
        "document_id": "doc-uuid-124",
        "table_data": {
          "headers": ["Quarter", "Revenue", "Growth %"],
          "rows": [
            ["Q1", "$35M", "12%"],
            ["Q2", "$38M", "8.5%"],
            ["Q3", "$42M", "10.5%"],
            ["Q4", "$45M", "7.1%"]
          ]
        },
        "relevance_score": 0.91
      }
    ],
    "text": [
      {
        "document_id": "doc-uuid-123",
        "text": "Revenue trends show consistent growth...",
        "relevance_score": 0.88
      }
    ]
  }
}
```

### 3.3 Session Management

#### Create Session

**Endpoint:** `POST /sessions`

**Request:**
```json
{
  "title": "Q4 Analysis Discussion",
  "context": {
    "focus_area": "finance",
    "document_scope": ["doc-uuid-123", "doc-uuid-124"]
  }
}
```

**Response:**
```json
{
  "session_id": "session-uuid-789",
  "created_at": "2025-12-26T10:00:00Z",
  "expires_at": "2025-12-27T10:00:00Z",
  "title": "Q4 Analysis Discussion"
}
```

#### Query with Session

**Endpoint:** `POST /sessions/{session_id}/query`

**Request:**
```json
{
  "query": "What about the operating expenses?",
  "use_history": true
}
```

**Response:**
```json
{
  "query_id": "query-uuid-458",
  "session_id": "session-uuid-789",
  "response": "Following up on the Q4 financial report we discussed, operating expenses were $12M, which represents a 15% reduction from Q3...",
  "conversation_history": [
    {
      "role": "user",
      "content": "What were the key findings in the Q4 report?",
      "timestamp": "2025-12-26T10:01:00Z"
    },
    {
      "role": "assistant",
      "content": "Based on the Q4 financial report...",
      "timestamp": "2025-12-26T10:01:02Z"
    },
    {
      "role": "user",
      "content": "What about the operating expenses?",
      "timestamp": "2025-12-26T10:02:00Z"
    }
  ]
}
```

#### Get Session History

**Endpoint:** `GET /sessions/{session_id}/history`

**Response:**
```json
{
  "session_id": "session-uuid-789",
  "messages": [
    {
      "message_id": "msg-uuid-1",
      "role": "user",
      "content": "What were the key findings?",
      "timestamp": "2025-12-26T10:01:00Z"
    },
    {
      "message_id": "msg-uuid-2",
      "role": "assistant",
      "content": "Based on the Q4 financial report...",
      "sources": ["doc-uuid-123"],
      "timestamp": "2025-12-26T10:01:02Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_messages": 12
  }
}
```

### 3.4 Search Operations

#### Semantic Search

**Endpoint:** `POST /search`

**Request:**
```json
{
  "query": "revenue growth strategies",
  "search_type": "semantic",
  "filters": {
    "document_ids": ["doc-uuid-123", "doc-uuid-124"],
    "modality": ["text"]
  },
  "options": {
    "top_k": 20,
    "min_score": 0.7
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "chunk-uuid-789",
      "document_id": "doc-uuid-123",
      "score": 0.92,
      "text": "Our revenue growth strategy focuses on three key areas...",
      "metadata": {
        "page": 12,
        "section": "Strategic Initiatives"
      }
    }
  ],
  "total_results": 15,
  "search_time_ms": 45
}
```

#### Hybrid Search

**Endpoint:** `POST /search/hybrid`

**Request:**
```json
{
  "query": "revenue growth Q4 2024",
  "search_strategies": {
    "semantic": {
      "enabled": true,
      "weight": 0.5
    },
    "keyword": {
      "enabled": true,
      "weight": 0.3,
      "fields": ["text", "title"]
    },
    "graph": {
      "enabled": true,
      "weight": 0.2,
      "max_hops": 2
    }
  },
  "top_k": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "chunk-uuid-789",
      "document_id": "doc-uuid-123",
      "combined_score": 0.89,
      "score_breakdown": {
        "semantic": 0.92,
        "keyword": 0.85,
        "graph": 0.78
      },
      "text": "Q4 2024 revenue grew by 23%..."
    }
  ],
  "fusion_method": "reciprocal_rank_fusion",
  "search_time_ms": 120
}
```

### 3.5 Analytics & Monitoring

#### Get Usage Statistics

**Endpoint:** `GET /analytics/usage`

**Query Parameters:**
- `start_date` (ISO 8601)
- `end_date` (ISO 8601)
- `granularity` (hour, day, week, month)

**Response:**
```json
{
  "period": {
    "start": "2024-12-01T00:00:00Z",
    "end": "2024-12-31T23:59:59Z"
  },
  "metrics": {
    "total_queries": 15420,
    "total_documents": 1250,
    "storage_used_gb": 125.5,
    "cache_hit_rate": 0.78,
    "avg_query_latency_ms": 425,
    "p95_query_latency_ms": 780
  },
  "usage_by_day": [
    {
      "date": "2024-12-01",
      "queries": 520,
      "documents_uploaded": 45
    }
  ]
}
```

#### Get Query Analytics

**Endpoint:** `GET /analytics/queries`

**Response:**
```json
{
  "top_queries": [
    {
      "query": "revenue growth",
      "count": 145,
      "avg_latency_ms": 380
    }
  ],
  "query_volume_by_hour": [
    {
      "hour": "2024-12-26T10:00:00Z",
      "count": 85
    }
  ],
  "popular_documents": [
    {
      "document_id": "doc-uuid-123",
      "filename": "q4_report.pdf",
      "access_count": 234
    }
  ]
}
```

---

## 4. Request/Response Formats

### 4.1 Standard Response Format

All successful API responses follow this structure:

```json
{
  "success": true,
  "data": {
    // Response-specific data
  },
  "metadata": {
    "request_id": "req-uuid-123",
    "timestamp": "2025-12-26T10:00:00Z",
    "latency_ms": 150
  }
}
```

### 4.2 Pagination

For list endpoints:

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 156,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 5. Error Handling

### 5.1 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The query parameter is required",
    "details": {
      "field": "query",
      "constraint": "required"
    },
    "request_id": "req-uuid-123",
    "timestamp": "2025-12-26T10:00:00Z"
  }
}
```

### 5.2 Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing authentication token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_REQUEST` | 400 | Malformed request |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `DOCUMENT_TOO_LARGE` | 413 | Document exceeds size limit |
| `UNSUPPORTED_FORMAT` | 415 | File format not supported |

---

## 6. Rate Limiting

### 6.1 Rate Limit Headers

All responses include:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1640520000
```

### 6.2 Default Limits

| Tier | Requests/Hour | Concurrent Sessions | Max Document Size |
|------|---------------|---------------------|-------------------|
| Free | 100 | 1 | 10 MB |
| Basic | 1,000 | 5 | 50 MB |
| Pro | 10,000 | 20 | 500 MB |
| Enterprise | Custom | Custom | Custom |

### 6.3 Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 3600 seconds",
    "retry_after": 3600
  }
}
```

---

## 7. SDK Examples

### 7.1 Python SDK

```python
from rag_sdk import RAGClient

# Initialize client
client = RAGClient(
    api_key="your-api-key",
    tenant_id="tenant-uuid"
)

# Upload document
document = client.documents.upload(
    file_path="/path/to/document.pdf",
    metadata={
        "title": "Q4 Report",
        "tags": ["finance", "quarterly"]
    }
)

# Query
response = client.query(
    query="What were the key findings?",
    filters={"tags": ["finance"]},
    stream=False
)

print(response.text)
for source in response.sources:
    print(f"Source: {source.filename}, Score: {source.relevance_score}")

# Streaming query
for chunk in client.query_stream("Explain the revenue trends"):
    print(chunk.content, end="", flush=True)
```

### 7.2 JavaScript/TypeScript SDK

```typescript
import { RAGClient } from '@rag-system/sdk';

// Initialize client
const client = new RAGClient({
  apiKey: 'your-api-key',
  tenantId: 'tenant-uuid'
});

// Upload document
const document = await client.documents.upload({
  file: fileBuffer,
  metadata: {
    title: 'Q4 Report',
    tags: ['finance', 'quarterly']
  }
});

// Query
const response = await client.query({
  query: 'What were the key findings?',
  filters: {
    tags: ['finance']
  }
});

console.log(response.text);
response.sources.forEach(source => {
  console.log(`Source: ${source.filename}, Score: ${source.relevanceScore}`);
});

// Streaming query
const stream = await client.queryStream('Explain the revenue trends');
for await (const chunk of stream) {
  process.stdout.write(chunk.content);
}
```

### 7.3 cURL Examples

**Upload Document:**
```bash
curl -X POST https://api.rag-system.com/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: tenant-uuid" \
  -F "file=@/path/to/document.pdf" \
  -F 'metadata={"title":"Q4 Report","tags":["finance"]}'
```

**Query:**
```bash
curl -X POST https://api.rag-system.com/v1/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: tenant-uuid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were the key findings?",
    "filters": {"tags": ["finance"]},
    "options": {"top_k": 10}
  }'
```

---

## 8. Webhooks

### 8.1 Configure Webhook

**Endpoint:** `POST /webhooks`

**Request:**
```json
{
  "url": "https://your-domain.com/webhook",
  "events": ["document.completed", "document.failed"],
  "secret": "your-webhook-secret"
}
```

### 8.2 Webhook Events

**Document Completed:**
```json
{
  "event": "document.completed",
  "timestamp": "2025-12-26T10:00:00Z",
  "data": {
    "document_id": "doc-uuid-123",
    "filename": "report.pdf",
    "status": "completed",
    "chunks_created": 152
  }
}
```

**Document Failed:**
```json
{
  "event": "document.failed",
  "timestamp": "2025-12-26T10:00:00Z",
  "data": {
    "document_id": "doc-uuid-124",
    "filename": "corrupted.pdf",
    "error": "Unable to parse PDF"
  }
}
```

---

## Appendix: Complete OpenAPI Spec

See `openapi.yaml` for the complete OpenAPI 3.0 specification.

---

**End of API Specification**

For architecture details, see: ARCHITECTURE.md
For deployment instructions, see: DEPLOYMENT.md
For implementation guide, see: IMPLEMENTATION_ROADMAP.md
