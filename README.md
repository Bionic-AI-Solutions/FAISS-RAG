# Mem0-RAG: Multi-Tenant RAG System with Mem0 Integration

Enterprise-grade, highly performant **Agentic RAG (Retrieval Augmented Generation) Infrastructure Platform** designed to serve as the short-term and long-term memory layer for multi-tenant chat client platforms.

## Overview

**Mem0-RAG** combines **Mem0's memory management capabilities** with **FAISS vector search** to deliver personalized, context-aware chatbot experiences across multiple domains including fintech, healthcare, retail, and customer service.

**Primary Interface**: The system exposes all capabilities via **Model Context Protocol (MCP)**, making it a standardized infrastructure service that chatbots, voice bots, and other LLM-powered systems can consume natively without custom API integration.

## Features

- **Multi-Tenant Architecture**: Complete data isolation with tenant-scoped resources
- **Vector Search**: FAISS-based vector search with tenant-partitioned indices
- **Keyword Search**: Meilisearch integration for hybrid retrieval
- **Memory Management**: Mem0 integration with Redis fallback
- **MCP-Native Interface**: All capabilities exposed via Model Context Protocol tools
- **Observability**: Langfuse integration for comprehensive tool call tracking
- **Compliance**: Built-in support for HIPAA, PCI DSS, SOC 2, GDPR
- **Performance**: Sub-200ms latency (p95) with multi-level caching

## Technology Stack

- **Python 3.11+** with FastAPI and FastMCP
- **PostgreSQL** with Row-Level Security (RLS) for multi-tenant data isolation
- **Redis** for caching, rate limiting, and session storage
- **FAISS** for vector search
- **Meilisearch** for keyword search
- **Mem0** for memory management (self-hosted containerized)
- **MinIO** for S3-compatible object storage
- **Langfuse** for observability and tool call tracking

## Project Structure

```
mem0-rag/
├── app/                    # Application code
│   ├── mcp/               # MCP Server Layer (Primary Interface)
│   ├── api/               # Optional REST API Endpoints
│   ├── services/          # Business Logic Layer
│   ├── models/            # Pydantic Models
│   ├── db/                # Database Layer
│   ├── config/            # Configuration Management
│   └── utils/             # Utility Functions
├── tests/                 # Test Suite
├── docker/                # Docker Configuration
├── kubernetes/            # Kubernetes Manifests
└── scripts/               # Utility Scripts
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL, Redis, MinIO, Meilisearch, Mem0, Langfuse services

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Bionic-AI-Solutions/mem0-rag.git
   cd mem0-rag
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start development environment:**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Development Environment Setup

The project includes a complete Docker Compose setup for local development with all prerequisite services:

- **PostgreSQL**: Database for tenant data, configurations, audit logs
- **Redis**: Caching, rate limiting, session storage
- **MinIO**: S3-compatible object storage
- **Meilisearch**: Keyword search engine
- **Mem0**: Memory management service (self-hosted)
- **Langfuse**: Observability and tool call tracking

Start all services:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

Verify services are running:
```bash
docker-compose -f docker/docker-compose.yml ps
```

## Configuration

All configuration is managed via environment variables. See `.env.example` for a complete list of configuration options.

Key configuration areas:
- **Database**: PostgreSQL connection settings
- **Redis**: Caching and session storage
- **MinIO**: Object storage configuration
- **Meilisearch**: Search engine configuration
- **Mem0**: Memory management service
- **Langfuse**: Observability configuration
- **Security**: JWT secrets, encryption keys
- **Rate Limiting**: Per-tenant rate limits

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py
```

### Code Quality

```bash
# Format code
black app tests

# Lint code
flake8 app tests

# Type checking
mypy app

# Security scanning
bandit -r app
```

## Architecture

The system follows a multi-tenant, MCP-first architecture:

- **MCP Server Layer**: Primary interface via Model Context Protocol
- **Service Layer**: Business logic for knowledge, memory, search operations
- **Data Layer**: PostgreSQL, Redis, MinIO, FAISS, Meilisearch
- **Middleware Stack**: Authentication, authorization, audit logging, observability

See `_bmad-output/planning-artifacts/architecture.md` for detailed architecture documentation.

## API Documentation

The system exposes capabilities via MCP tools. MCP tools include:

- **Knowledge Base Operations**: `rag_search`, `rag_ingest_document`, `rag_list_documents`
- **Memory Operations**: `rag_get_memory`, `rag_update_memory`, `rag_search_memory`
- **Tenant Management**: `rag_register_tenant`, `rag_configure_tenant`
- **Session Management**: `rag_get_session_context`, `rag_update_session_context`

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.
