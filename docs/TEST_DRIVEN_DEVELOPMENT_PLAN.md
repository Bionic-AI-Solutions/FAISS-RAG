# Enterprise Multi-Modal RAG System - Test-Driven Development Plan

## Version: 2.0 (Updated with OpenRouter & OpenAI-Compatible Support)

## Last Updated: 2025-12-26

---

## Overview

This plan implements an enterprise-grade, multi-modal RAG system following **Test-Driven Development (TDD)** principles. All features will be developed with tests written first, ensuring comprehensive coverage and quality.

**Key Requirements:**

- Support 10,000 tenants with 1,000+ concurrent users each
- Multi-modal processing (text, images, audio, video, tables)
- Hybrid retrieval (FAISS + Elasticsearch + Neo4j)
- Multi-agent orchestration with LangGraph
- Redis-based caching
- Nomic embeddings (768d)
- **Multi-LLM support: Claude, OpenAI, Ollama, OpenRouter, OpenAI-Compatible** ⭐ UPDATED
- Full compliance (HIPAA, SOC2, GDPR, FedRAMP)

**Performance Targets:**

- Query Latency (p95): < 800ms
- Throughput: 10,000-50,000 QPS
- Availability: 99.95%
- Document Ingestion: 1,000 docs/sec

---

## Part 1: Comprehensive Test Plan

### 1.1 Test Strategy

**Testing Pyramid:**

```
        /\
       /E2E\        (10%) - End-to-end tests
      /------\
     /Integration\  (30%) - Service integration tests
    /------------\
   /   Unit Tests  \ (60%) - Component unit tests
  /----------------\
```

**Test Categories:**

1. **Unit Tests**: Fast, isolated, mock dependencies
2. **Integration Tests**: Test service interactions with live dependencies
3. **End-to-End Tests**: Full user workflows
4. **Performance Tests**: Load, stress, latency
5. **Security Tests**: Authentication, authorization, encryption
6. **Compliance Tests**: HIPAA, GDPR, SOC2 requirements

### 1.2 Unit Test Suite

#### 1.2.1 Embedding Service Tests

**Location:** `tests/unit/services/embedding/`

**Test Cases:**

- `test_nomic_text_embedding_generation()` - Generate text embeddings
- `test_nomic_vision_embedding_generation()` - Generate image embeddings
- `test_embedding_batch_processing()` - Batch embedding generation
- `test_embedding_caching()` - Redis cache hit/miss
- `test_embedding_dimension_validation()` - Verify 768d output
- `test_task_type_optimization()` - search_query vs search_document
- `test_embedding_error_handling()` - Invalid input handling
- `test_concurrent_embedding_requests()` - Thread safety

**Coverage Target:** 95%

#### 1.2.2 FAISS Vector Store Tests

**Location:** `tests/unit/services/vector_store/`

**Test Cases:**

- `test_index_creation()` - Create IVF4096,PQ64 index
- `test_vector_addition()` - Add vectors to index
- `test_vector_search()` - Similarity search
- `test_index_persistence()` - Save/load from disk
- `test_multi_tenant_isolation()` - Tenant index separation
- `test_index_sharding()` - Shard creation and routing
- `test_index_training()` - Index training with sample data
- `test_search_parameter_tuning()` - nprobe optimization
- `test_index_compression()` - PQ64 quantization
- `test_concurrent_index_updates()` - Thread safety

**Coverage Target:** 90%

#### 1.2.3 Hybrid Retrieval Engine Tests

**Location:** `tests/unit/services/retrieval/`

**Test Cases:**

- `test_vector_search()` - FAISS search
- `test_keyword_search()` - Elasticsearch BM25
- `test_graph_search()` - Neo4j relationship traversal
- `test_reciprocal_rank_fusion()` - RRF algorithm
- `test_result_reranking()` - ColBERT reranking
- `test_parallel_retrieval()` - Concurrent search execution
- `test_result_deduplication()` - Remove duplicate chunks
- `test_score_normalization()` - Score range validation
- `test_retrieval_caching()` - Cache search results
- `test_retrieval_error_handling()` - Service failure handling

**Coverage Target:** 90%

#### 1.2.4 Document Processing Pipeline Tests

**Location:** `tests/unit/services/ingestion/pipelines/`

**Text Pipeline:**

- `test_pdf_extraction()` - Extract text from PDF
- `test_docx_extraction()` - Extract from DOCX
- `test_text_chunking()` - RecursiveCharacterTextSplitter
- `test_chunk_overlap()` - Verify overlap handling
- `test_metadata_preservation()` - Preserve document metadata

**Image Pipeline:**

- `test_image_ocr()` - Extract text from images
- `test_vision_embedding()` - Generate image embeddings
- `test_image_format_support()` - JPG, PNG, WEBP
- `test_image_resizing()` - Max dimension handling

**Audio Pipeline:**

- `test_audio_transcription()` - Whisper transcription
- `test_speaker_diarization()` - Speaker identification
- `test_audio_format_support()` - MP3, WAV, M4A

**Video Pipeline:**

- `test_frame_extraction()` - Extract frames at 1fps
- `test_scene_detection()` - Scene change detection
- `test_video_audio_extraction()` - Separate audio track

**Table Pipeline:**

- `test_table_extraction()` - Camelot table extraction
- `test_structure_preservation()` - Maintain table structure
- `test_csv_parsing()` - CSV file handling

**Coverage Target:** 85%

#### 1.2.5 Multi-Agent System Tests

**Location:** `tests/unit/services/agents/`

**Test Cases:**

- `test_agent_orchestration()` - LangGraph workflow
- `test_query_analyzer_agent()` - Query decomposition
- `test_retrieval_agent()` - Document retrieval
- `test_domain_agent()` - Domain-specific processing
- `test_tool_agent()` - Calculator, code execution
- `test_agent_memory_isolation()` - Private memory scopes
- `test_agent_state_management()` - State transitions
- `test_agent_error_recovery()` - Failure handling
- `test_concurrent_agent_execution()` - Parallel agents
- `test_agent_with_openrouter()` - Agent using OpenRouter ⭐ NEW
- `test_agent_with_openai_compatible()` - Agent using compatible endpoint ⭐ NEW

**Coverage Target:** 85%

#### 1.2.6 LLM Router Tests ⭐ UPDATED

**Location:** `tests/unit/services/llm/`

**Test Cases:**

- `test_claude_provider()` - Claude API integration
- `test_openai_provider()` - OpenAI API integration
- `test_ollama_provider()` - Ollama local integration
- `test_openrouter_provider()` - OpenRouter API integration ⭐ NEW
- `test_openrouter_model_selection()` - Model routing logic ⭐ NEW
- `test_openrouter_failover()` - Automatic model failover ⭐ NEW
- `test_openrouter_cost_tracking()` - Cost per model tracking ⭐ NEW
- `test_openai_compatible_provider()` - Generic OpenAI-compatible provider ⭐ NEW
- `test_openai_compatible_custom_endpoint()` - Custom endpoint configuration ⭐ NEW
- `test_openai_compatible_authentication()` - API key and header configuration ⭐ NEW
- `test_provider_routing()` - Route by context length
- `test_provider_routing_with_openrouter()` - Routing including OpenRouter ⭐ NEW
- `test_provider_fallback()` - Failover mechanism
- `test_provider_fallback_chain()` - Fallback: OpenRouter → OpenAI → Ollama ⭐ NEW
- `test_prompt_building()` - Context-aware prompts
- `test_token_counting()` - Token limit validation
- `test_streaming_response()` - SSE streaming
- `test_rate_limiting()` - Provider rate limits
- `test_multi_provider_cost_comparison()` - Cost comparison across providers ⭐ NEW

**Coverage Target:** 90%

#### 1.2.7 Session Management Tests

**Location:** `tests/unit/services/session/`

**Test Cases:**

- `test_session_creation()` - Create new session
- `test_session_retrieval()` - Get session data
- `test_conversation_history()` - Message storage
- `test_session_expiry()` - TTL handling
- `test_context_window_management()` - Truncate old messages
- `test_multi_user_sessions()` - User isolation
- `test_session_cleanup()` - Expired session removal

**Coverage Target:** 90%

#### 1.2.8 Authentication & Authorization Tests

**Location:** `tests/unit/services/auth/`

**Test Cases:**

- `test_jwt_generation()` - Token creation
- `test_jwt_validation()` - Token verification
- `test_jwt_expiry()` - Expiration handling
- `test_password_hashing()` - bcrypt hashing
- `test_mfa_setup()` - TOTP configuration
- `test_mfa_verification()` - TOTP validation
- `test_rbac_permissions()` - Role-based access
- `test_tenant_isolation()` - Tenant context filtering
- `test_token_refresh()` - Refresh token flow

**Coverage Target:** 95%

#### 1.2.9 Cache Manager Tests

**Location:** `tests/unit/services/cache/`

**Test Cases:**

- `test_embedding_cache()` - Cache embeddings
- `test_search_result_cache()` - Cache search results
- `test_session_cache()` - Cache session data
- `test_cache_ttl()` - Time-to-live handling
- `test_cache_eviction()` - LRU eviction policy
- `test_cache_compression()` - Float32 to float16
- `test_cache_cluster()` - Redis cluster operations
- `test_cache_invalidation()` - Invalidate on update

**Coverage Target:** 90%

### 1.3 Integration Test Suite

#### 1.3.1 Document Ingestion Integration Tests

**Location:** `tests/integration/ingestion/`

**Test Cases:**

- `test_end_to_end_document_upload()` - Upload → Process → Index
- `test_kafka_message_processing()` - Kafka consumer integration
- `test_multi_modal_processing()` - Process all modalities
- `test_concurrent_document_processing()` - Parallel processing
- `test_large_document_handling()` - 100MB+ documents
- `test_processing_error_recovery()` - Retry on failure
- `test_processing_status_tracking()` - Status updates
- `test_storage_integration()` - MinIO, FAISS, ES, Neo4j, PostgreSQL

**Test Environment:** Live services (Redis, Kafka, PostgreSQL, etc.)

#### 1.3.2 Query Service Integration Tests ⭐ UPDATED

**Location:** `tests/integration/query/`

**Test Cases:**

- `test_full_query_pipeline()` - Query → Retrieve → Generate
- `test_hybrid_retrieval_integration()` - All retrieval methods
- `test_caching_integration()` - Cache hit/miss scenarios
- `test_multi_llm_provider_integration()` - All LLM providers
- `test_openrouter_integration()` - Full OpenRouter integration ⭐ NEW
- `test_openrouter_streaming()` - Streaming response from OpenRouter ⭐ NEW
- `test_openai_compatible_integration()` - Generic provider integration ⭐ NEW
- `test_openai_compatible_streaming()` - Streaming from compatible endpoint ⭐ NEW
- `test_session_based_queries()` - Context-aware queries
- `test_concurrent_query_handling()` - 100+ concurrent queries
- `test_query_with_filters()` - Modality, date, tag filters
- `test_streaming_query_response()` - SSE streaming
- `test_provider_switching()` - Dynamic provider switching ⭐ NEW
- `test_cost_optimization_routing()` - Route by cost optimization ⭐ NEW

**Test Environment:** Live services

#### 1.3.3 Multi-Agent Integration Tests ⭐ UPDATED

**Location:** `tests/integration/agents/`

**Test Cases:**

- `test_agent_workflow_execution()` - Full agent pipeline
- `test_agent_memory_persistence()` - Redis memory storage
- `test_agent_tool_execution()` - Calculator, code execution
- `test_multi_agent_coordination()` - Agent collaboration
- `test_agent_error_handling()` - Failure recovery
- `test_agent_with_openrouter()` - Agent using OpenRouter ⭐ NEW
- `test_agent_with_openai_compatible()` - Agent using compatible endpoint ⭐ NEW

**Test Environment:** Live services

#### 1.3.4 API Integration Tests

**Location:** `tests/integration/api/`

**Test Cases:**

- `test_document_upload_api()` - POST /documents/upload
- `test_document_list_api()` - GET /documents
- `test_query_api()` - POST /query
- `test_query_api_with_openrouter()` - Query with OpenRouter provider ⭐ NEW
- `test_query_api_with_openai_compatible()` - Query with compatible endpoint ⭐ NEW
- `test_session_api()` - POST /sessions, GET /sessions/{id}/history
- `test_authentication_api()` - POST /auth/token
- `test_rate_limiting()` - Rate limit enforcement
- `test_error_responses()` - Error handling
- `test_api_versioning()` - Version compatibility

**Test Environment:** Live API server

### 1.4 End-to-End Test Suite

**Location:** `tests/e2e/`

**Test Scenarios:**

- `test_complete_user_workflow()` - Register → Upload → Query → Delete
- `test_multi_tenant_isolation()` - Tenant data separation
- `test_multi_modal_search()` - Cross-modal retrieval
- `test_session_conversation()` - Multi-turn dialogue
- `test_document_lifecycle()` - Upload → Process → Query → Delete
- `test_performance_under_load()` - 1000 concurrent users
- `test_disaster_recovery()` - Service failure and recovery
- `test_openrouter_workflow()` - Complete workflow with OpenRouter ⭐ NEW
- `test_openai_compatible_workflow()` - Complete workflow with compatible endpoint ⭐ NEW

**Test Environment:** Full production-like environment

### 1.5 Performance Test Suite ⭐ UPDATED

**Location:** `tests/performance/`

**Test Scenarios:**

- `test_query_latency_p95()` - Verify < 800ms p95 latency
- `test_query_throughput()` - 10,000-50,000 QPS
- `test_document_ingestion_rate()` - 1,000 docs/sec
- `test_cache_hit_rate()` - > 80% hit rate
- `test_concurrent_user_load()` - 1M concurrent sessions
- `test_database_connection_pooling()` - Connection efficiency
- `test_memory_usage()` - Memory leak detection
- `test_index_search_performance()` - FAISS search speed
- `test_openrouter_latency()` - OpenRouter response latency ⭐ NEW
- `test_openrouter_throughput()` - Requests per second ⭐ NEW
- `test_openai_compatible_latency()` - Compatible endpoint latency ⭐ NEW
- `test_provider_comparison()` - Compare all providers (latency, cost, quality) ⭐ NEW

**Tools:** k6, Locust, Apache JMeter

### 1.6 Security Test Suite

**Location:** `tests/security/`

**Test Cases:**

- `test_authentication_bypass()` - Unauthorized access attempts
- `test_sql_injection()` - SQL injection prevention
- `test_xss_attacks()` - Cross-site scripting prevention
- `test_csrf_protection()` - CSRF token validation
- `test_encryption_at_rest()` - Data encryption verification
- `test_encryption_in_transit()` - TLS verification
- `test_tenant_isolation()` - Cross-tenant access prevention
- `test_rate_limiting_bypass()` - Rate limit circumvention
- `test_secret_management()` - Secrets in Vault
- `test_audit_logging()` - Security event logging
- `test_api_key_security()` - OpenRouter/Compatible API key security ⭐ NEW

**Tools:** OWASP ZAP, Trivy, kube-bench

### 1.7 Compliance Test Suite

**Location:** `tests/compliance/`

**HIPAA Tests:**

- `test_phi_access_logging()` - PHI access audit logs
- `test_encryption_requirements()` - Encryption compliance
- `test_access_controls()` - Access control verification
- `test_data_retention()` - 7-year retention

**GDPR Tests:**

- `test_data_export()` - Right to access (Article 15)
- `test_data_deletion()` - Right to erasure (Article 17)
- `test_data_portability()` - Right to portability (Article 20)
- `test_consent_management()` - Consent tracking

**SOC2 Tests:**

- `test_access_controls()` - Logical access (CC6.1)
- `test_encryption()` - Encryption controls (CC6.6)
- `test_monitoring()` - Monitoring controls (CC7.2)
- `test_change_management()` - Change controls (CC8.1)

---

## Part 2: Test-Driven Implementation Plan

### Phase 1: Foundation & Infrastructure (Weeks 1-4)

#### Week 1: Project Setup & Infrastructure Tests

**Day 1-2: Repository Setup**

- [ ] Create GitHub repo: `Bionic-AI-Solutions/new-rag`
- [ ] Initialize project structure
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Configure test environments

**Day 3-5: Infrastructure Test Suite**

- [ ] Write tests for Kubernetes cluster setup
- [ ] Write tests for storage classes
- [ ] Write tests for network policies
- [ ] Write tests for secrets management
- [ ] **Implement infrastructure** (TDD: tests first)
- [ ] Verify all infrastructure tests pass

**Deliverables:**

- ✅ Repository created and configured
- ✅ CI/CD pipeline operational
- ✅ Infrastructure test suite (100% passing)
- ✅ Kubernetes cluster ready

#### Week 2: Core Data Stores & Tests

**Day 1-2: Redis Cluster**

- [ ] Write unit tests for Redis cache manager
- [ ] Write integration tests for Redis cluster
- [ ] **Implement Redis cache manager** (TDD)
- [ ] Deploy Redis cluster
- [ ] Verify all tests pass

**Day 3: PostgreSQL**

- [ ] Write tests for database schema
- [ ] Write tests for pgvector extension
- [ ] **Implement database setup** (TDD)
- [ ] Deploy PostgreSQL
- [ ] Verify all tests pass

**Day 4: Elasticsearch**

- [ ] Write tests for index creation
- [ ] Write tests for document indexing
- [ ] **Implement Elasticsearch integration** (TDD)
- [ ] Deploy Elasticsearch
- [ ] Verify all tests pass

**Day 5: Neo4j & Kafka**

- [ ] Write tests for graph operations
- [ ] Write tests for Kafka producers/consumers
- [ ] **Implement Neo4j and Kafka integration** (TDD)
- [ ] Deploy services
- [ ] Verify all tests pass

**Deliverables:**

- ✅ All data stores deployed
- ✅ Test suites for all stores (100% passing)
- ✅ Integration tests passing

#### Week 3: Security & Monitoring Tests

**Day 1-2: Security Test Suite**

- [ ] Write authentication tests
- [ ] Write authorization tests
- [ ] Write encryption tests
- [ ] Write tenant isolation tests
- [ ] **Implement security features** (TDD)
- [ ] Deploy Vault
- [ ] Verify all security tests pass

**Day 3-5: Monitoring Test Suite**

- [ ] Write tests for metrics collection
- [ ] Write tests for log aggregation
- [ ] Write tests for distributed tracing
- [ ] **Implement monitoring stack** (TDD)
- [ ] Deploy Prometheus, Grafana, Jaeger, ELK
- [ ] Verify all monitoring tests pass

**Deliverables:**

- ✅ Security test suite (100% passing)
- ✅ Monitoring test suite (100% passing)
- ✅ Vault operational
- ✅ Monitoring stack deployed

#### Week 4: Embedding Service & Vector Store Tests

**Day 1-3: Embedding Service**

- [ ] Write unit tests for Nomic embedding service
- [ ] Write integration tests with Redis caching
- [ ] **Implement embedding service** (TDD)
- [ ] Deploy embedding service
- [ ] Verify all tests pass

**Day 4-5: FAISS Vector Store**

- [ ] Write unit tests for FAISS index manager
- [ ] Write integration tests for index operations
- [ ] Write performance tests for search
- [ ] **Implement FAISS service** (TDD)
- [ ] Deploy FAISS service
- [ ] Verify all tests pass

**Deliverables:**

- ✅ Embedding service test suite (95% coverage)
- ✅ FAISS service test suite (90% coverage)
- ✅ Both services deployed and tested

---

### Phase 2: Core Services (Weeks 5-8)

#### Week 5: Document Ingestion Pipeline Tests

**Day 1: Text Pipeline Tests**

- [ ] Write unit tests for text extraction
- [ ] Write unit tests for text chunking
- [ ] Write integration tests for text processing
- [ ] **Implement text pipeline** (TDD)
- [ ] Verify all tests pass

**Day 2: Image Pipeline Tests**

- [ ] Write unit tests for OCR
- [ ] Write unit tests for vision embeddings
- [ ] Write integration tests for image processing
- [ ] **Implement image pipeline** (TDD)
- [ ] Verify all tests pass

**Day 3: Audio & Video Pipeline Tests**

- [ ] Write unit tests for audio transcription
- [ ] Write unit tests for video processing
- [ ] Write integration tests
- [ ] **Implement audio/video pipelines** (TDD)
- [ ] Verify all tests pass

**Day 4: Table Pipeline Tests**

- [ ] Write unit tests for table extraction
- [ ] Write integration tests
- [ ] **Implement table pipeline** (TDD)
- [ ] Verify all tests pass

**Day 5: Kafka Consumer Tests**

- [ ] Write integration tests for Kafka consumer
- [ ] Write tests for error handling and retries
- [ ] **Implement ingestion workers** (TDD)
- [ ] Deploy workers
- [ ] Verify all tests pass

**Deliverables:**

- ✅ All pipeline test suites (85% coverage)
- ✅ All pipelines implemented
- ✅ End-to-end ingestion tested

#### Week 6: Hybrid Retrieval Engine Tests

**Day 1-2: Retrieval Component Tests**

- [ ] Write unit tests for vector search
- [ ] Write unit tests for keyword search
- [ ] Write unit tests for graph search
- [ ] Write unit tests for RRF fusion
- [ ] Write unit tests for reranking
- [ ] **Implement retrieval engine** (TDD)
- [ ] Verify all tests pass

**Day 3-4: Integration Tests**

- [ ] Write integration tests for hybrid retrieval
- [ ] Write performance tests
- [ ] **Optimize retrieval** (TDD)
- [ ] Verify p95 latency < 200ms

**Day 5: Caching Tests**

- [ ] Write tests for retrieval result caching
- [ ] **Implement caching layer** (TDD)
- [ ] Verify cache hit rate > 80%

**Deliverables:**

- ✅ Retrieval engine test suite (90% coverage)
- ✅ Hybrid retrieval operational
- ✅ Performance targets met

#### Week 7: Query Service & LLM Integration Tests ⭐ UPDATED

**Day 1-2: Query Service Tests**

- [ ] Write unit tests for query processing
- [ ] Write integration tests for full query flow
- [ ] Write tests for streaming responses
- [ ] **Implement query service** (TDD)
- [ ] Deploy query service
- [ ] Verify all tests pass

**Day 3-4: LLM Router Tests (Extended)** ⭐ UPDATED

- [ ] Write unit tests for Claude provider
- [ ] Write unit tests for OpenAI provider
- [ ] Write unit tests for Ollama provider
- [ ] **Write unit tests for OpenRouter provider** ⭐ NEW
- [ ] **Write unit tests for OpenAI-Compatible provider** ⭐ NEW
- [ ] **Implement OpenRouter provider** (TDD) ⭐ NEW
- [ ] **Implement OpenAI-Compatible provider** (TDD) ⭐ NEW
- [ ] Write integration tests for provider routing
- [ ] Write tests for provider fallback
- [ ] Write tests for cost optimization
- [ ] **Update LLM router to include new providers** (TDD) ⭐ NEW
- [ ] **Add cost tracking for OpenRouter** (TDD) ⭐ NEW
- [ ] **Update provider routing logic** (TDD) ⭐ NEW
- [ ] Test with all providers
- [ ] Verify all tests pass

**Day 5: End-to-End Query Tests**

- [ ] Write E2E tests for complete query flow
- [ ] Write E2E tests with OpenRouter ⭐ NEW
- [ ] Write E2E tests with OpenAI-Compatible ⭐ NEW
- [ ] Write performance tests
- [ ] **Optimize query service** (TDD)
- [ ] Verify p95 latency < 800ms

**Deliverables:**

- ✅ Query service test suite (90% coverage)
- ✅ LLM integration test suite (90% coverage)
- ✅ **OpenRouter provider implemented and tested** ⭐ NEW
- ✅ **OpenAI-Compatible provider implemented and tested** ⭐ NEW
- ✅ Query service deployed
- ✅ Performance targets met

#### Week 8: API Gateway & Authentication Tests

**Day 1-2: Authentication Service Tests**

- [ ] Write unit tests for JWT generation/validation
- [ ] Write unit tests for MFA
- [ ] Write integration tests for auth flow
- [ ] **Implement authentication service** (TDD)
- [ ] Deploy auth service
- [ ] Verify all tests pass

**Day 3-4: API Gateway Tests**

- [ ] Write tests for Kong configuration
- [ ] Write tests for rate limiting
- [ ] Write tests for routing
- [ ] **Deploy Kong API Gateway** (TDD)
- [ ] Verify all tests pass

**Day 5: API Integration Tests**

- [ ] Write integration tests for all API endpoints
- [ ] Write tests for error handling
- [ ] Write tests for OpenRouter provider in API ⭐ NEW
- [ ] Write tests for OpenAI-Compatible provider in API ⭐ NEW
- [ ] **Verify complete API** (TDD)
- [ ] All API tests passing

**Deliverables:**

- ✅ Authentication test suite (95% coverage)
- ✅ API Gateway test suite (90% coverage)
- ✅ Complete API operational

---

### Phase 3: Advanced Features (Weeks 9-12)

#### Week 9: Multi-Agent System Tests

**Day 1-3: Agent Framework Tests**

- [ ] Write unit tests for agent orchestration
- [ ] Write unit tests for each agent type
- [ ] Write unit tests for agent memory
- [ ] **Implement agent system** (TDD)
- [ ] Verify all tests pass

**Day 4-5: Agent Integration Tests**

- [ ] Write integration tests for agent workflows
- [ ] Write E2E tests for complex queries
- [ ] Write tests for agents with OpenRouter ⭐ NEW
- [ ] Write tests for agents with OpenAI-Compatible ⭐ NEW
- [ ] **Deploy agent system** (TDD)
- [ ] Verify all tests pass

**Deliverables:**

- ✅ Agent system test suite (85% coverage)
- ✅ Multi-agent system operational

#### Week 10: Session Management Tests

**Day 1-2: Session Service Tests**

- [ ] Write unit tests for session creation
- [ ] Write unit tests for conversation history
- [ ] Write integration tests
- [ ] **Implement session management** (TDD)
- [ ] Verify all tests pass

**Day 3-5: Context-Aware Query Tests**

- [ ] Write tests for session-based queries
- [ ] Write tests for context window management
- [ ] **Integrate sessions with query service** (TDD)
- [ ] Verify all tests pass

**Deliverables:**

- ✅ Session management test suite (90% coverage)
- ✅ Context-aware queries operational

#### Week 11: Advanced Search & Analytics Tests

**Day 1-2: Advanced Search Tests**

- [ ] Write tests for multimodal search
- [ ] Write tests for cross-modal fusion
- [ ] **Implement advanced search** (TDD)
- [ ] Verify all tests pass

**Day 3-5: Analytics Service Tests**

- [ ] Write tests for usage statistics
- [ ] Write tests for query analytics
- [ ] Write tests for provider cost analytics ⭐ NEW
- [ ] **Implement analytics service** (TDD)
- [ ] Deploy analytics
- [ ] Verify all tests pass

**Deliverables:**

- ✅ Advanced search test suite (85% coverage)
- ✅ Analytics test suite (90% coverage)

#### Week 12: Performance Optimization Tests

**Day 1-5: Performance Test Suite**

- [ ] Write performance tests for query latency
- [ ] Write load tests for throughput
- [ ] Write stress tests
- [ ] Write provider comparison tests ⭐ NEW
- [ ] **Optimize based on test results** (TDD)
- [ ] Verify all performance targets met

**Deliverables:**

- ✅ Performance test suite
- ✅ All performance targets achieved

---

### Phase 4: Production Hardening (Weeks 13-16)

#### Week 13: Security & Compliance Tests

**Day 1-3: Security Test Suite**

- [ ] Write security tests (OWASP Top 10)
- [ ] Write penetration tests
- [ ] Write API key security tests ⭐ NEW
- [ ] **Fix security issues** (TDD)
- [ ] Verify all security tests pass

**Day 4-5: Compliance Test Suite**

- [ ] Write HIPAA compliance tests
- [ ] Write GDPR compliance tests
- [ ] Write SOC2 compliance tests
- [ ] **Implement compliance features** (TDD)
- [ ] Verify all compliance tests pass

**Deliverables:**

- ✅ Security test suite (100% passing)
- ✅ Compliance test suite (100% passing)

#### Week 14: Disaster Recovery Tests

**Day 1-3: Backup & Recovery Tests**

- [ ] Write tests for backup procedures
- [ ] Write tests for recovery procedures
- [ ] **Implement backup strategy** (TDD)
- [ ] Test disaster recovery scenarios
- [ ] Verify RTO/RPO targets

**Day 4-5: Chaos Engineering Tests**

- [ ] Write chaos tests (pod failures, network partitions)
- [ ] **Run chaos experiments** (TDD)
- [ ] Verify auto-recovery

**Deliverables:**

- ✅ Disaster recovery test suite
- ✅ RTO/RPO targets met

#### Week 15: Production Deployment Tests

**Day 1-3: Blue-Green Deployment Tests**

- [ ] Write tests for deployment process
- [ ] Write smoke tests
- [ ] **Deploy to production** (TDD)
- [ ] Verify all production tests pass

**Day 4-5: Production Validation Tests**

- [ ] Write validation tests
- [ ] **Run full validation** (TDD)
- [ ] Monitor for 48 hours

**Deliverables:**

- ✅ Production deployment successful
- ✅ All validation tests passing

#### Week 16: Documentation & Test Coverage Review

**Day 1-3: Test Coverage Analysis**

- [ ] Generate coverage reports
- [ ] Identify gaps
- [ ] **Add missing tests** (TDD)
- [ ] Achieve > 85% overall coverage

**Day 4-5: Documentation**

- [ ] Document test procedures
- [ ] Create test runbooks
- [ ] Document OpenRouter integration ⭐ NEW
- [ ] Document OpenAI-Compatible integration ⭐ NEW
- [ ] Final review

**Deliverables:**

- ✅ Test coverage > 85%
- ✅ Complete test documentation

---

## Implementation Details: OpenRouter & OpenAI-Compatible Providers

### OpenRouter Provider Implementation

**File:** `services/query/providers/openrouter.py`

```python
import httpx
from typing import Optional, AsyncIterator

class OpenRouterProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://rag-system.com",
                "X-Title": "Enterprise RAG System"
            },
            timeout=60.0
        )

    async def generate(
        self,
        prompt: str,
        model: str = "openai/gpt-4-turbo",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response using OpenRouter"""

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if stream:
            return self._generate_stream(payload)

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def list_models(self) -> list:
        """List available models from OpenRouter"""
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()["data"]

    async def get_model_info(self, model: str) -> dict:
        """Get information about a specific model"""
        models = await self.list_models()
        for m in models:
            if m["id"] == model:
                return m
        raise ValueError(f"Model {model} not found")

    def select_best_model(
        self,
        token_count: int,
        max_cost: Optional[float] = None
    ) -> str:
        """Select best model based on requirements"""
        # Implementation for intelligent model selection
        # Consider: cost, latency, context length, quality
        pass
```

### OpenAI-Compatible Provider Implementation

**File:** `services/query/providers/openai_compatible.py`

```python
import httpx
from typing import Optional, Dict

class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={
                **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
                **(custom_headers or {})
            },
            timeout=60.0
        )

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response using OpenAI-compatible endpoint"""

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Support both /v1/chat/completions and /chat/completions
        endpoints = [
            f"{self.base_url}/v1/chat/completions",
            f"{self.base_url}/chat/completions"
        ]

        for endpoint in endpoints:
            try:
                response = await self.client.post(
                    endpoint,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPError:
                continue

        raise ValueError("OpenAI-compatible endpoint not available")

    async def health_check(self) -> bool:
        """Check if the endpoint is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
```

### Updated LLM Router

**File:** `services/query/llm_router.py` (Updated)

```python
class LLMRouter:
    def __init__(self):
        self.providers = {
            'claude': ClaudeProvider(),
            'openai': OpenAIProvider(),
            'ollama': OllamaProvider(),
            'openrouter': OpenRouterProvider(),  # NEW
            'openai_compatible': OpenAICompatibleProvider()  # NEW
        }

    async def generate(
        self,
        query: str,
        context: List,
        provider: str = None,
        model: str = None,
        cost_optimize: bool = False
    ):
        """Route to appropriate LLM with enhanced routing"""

        # Build prompt
        prompt = self.build_prompt(query, context)
        token_count = self.count_tokens(prompt)

        # Auto-select provider if not specified
        if not provider:
            provider = self.select_provider(
                token_count=token_count,
                cost_optimize=cost_optimize
            )

        # Select model for OpenRouter if needed
        if provider == 'openrouter' and not model:
            model = self.select_openrouter_model(token_count)

        # Get provider instance
        llm = self.providers[provider]

        # Generate with model selection
        response = await llm.generate(
            prompt=prompt,
            model=model,
            stream=False
        )

        # Track cost
        await self.track_cost(provider, model, token_count, response)

        return response

    def select_provider(
        self,
        token_count: int,
        cost_optimize: bool = False
    ) -> str:
        """Intelligent provider selection"""

        if cost_optimize:
            # Use OpenRouter for cost optimization
            return 'openrouter'

        if token_count > 100000:
            return 'claude'  # Long context
        elif token_count < 1000:
            return 'ollama'  # Simple queries
        else:
            return 'openrouter'  # Default to OpenRouter for flexibility
```

### Configuration Updates

**File:** `config/llm.yaml` (Updated)

```yaml
llm:
  default_provider: openrouter # Updated default

  providers:
    claude:
      endpoint: "https://api.anthropic.com"
      model: "claude-sonnet-4-20250514"
      max_tokens: 200000
      temperature: 0.7

    openai:
      endpoint: "https://api.openai.com/v1"
      model: "gpt-4-turbo"
      max_tokens: 128000
      temperature: 0.7

    ollama:
      endpoint: "http://ollama:11434"
      model: "llama3.1:70b"
      max_tokens: 128000
      temperature: 0.7
      cost: 0.0

    openrouter: # NEW
      endpoint: "https://openrouter.ai/api/v1"
      api_key: "${OPENROUTER_API_KEY}"
      default_model: "openai/gpt-4-turbo"
      fallback_models:
        - "anthropic/claude-3.5-sonnet"
        - "meta-llama/llama-3.1-70b-instruct"
      cost_tracking: true
      auto_failover: true

    openai_compatible: # NEW
      endpoints:
        - name: "vllm-local"
          url: "http://vllm-service:8000/v1"
          api_key: "${VLLM_API_KEY}"
          models: ["llama-3.1-70b", "mistral-7b"]
        - name: "tensorrt-llm"
          url: "http://tensorrt-llm:8000/v1"
          api_key: "${TENSORRT_API_KEY}"
          models: ["llama-3.1-70b"]
      health_check_interval: 60
      auto_failover: true

  routing:
    long_context: "claude" # > 100K tokens
    cost_optimized: "openrouter" # Updated
    default: "openrouter" # Updated
    self_hosted: "openai_compatible" # NEW
```

---

## Test Execution Strategy

### Continuous Integration

**Pre-commit:**

- Run unit tests (fast)
- Run linters
- Check code coverage

**Pull Request:**

- Run full unit test suite
- Run integration tests
- Run security tests
- Generate coverage report

**Merge to Main:**

- Run all test suites
- Run performance tests
- Run compliance tests
- Deploy to staging

**Production Deployment:**

- Run full E2E test suite
- Run smoke tests
- Verify monitoring

### Test Environments

1. **Local Development**: Docker Compose
2. **CI Environment**: GitHub Actions runners
3. **Staging**: Kubernetes cluster (production-like)
4. **Production**: Full production environment

### Test Data Management

- **Unit Tests**: Mock data, fixtures
- **Integration Tests**: Test database with sample data
- **E2E Tests**: Production-like data
- **Performance Tests**: Synthetic load data

---

## Success Criteria

### Test Coverage

- Overall coverage: > 85%
- Critical components: > 90%
- Security components: > 95%
- **LLM Providers: > 90%** ⭐ UPDATED

### Test Execution

- Unit tests: < 5 minutes
- Integration tests: < 30 minutes
- E2E tests: < 2 hours
- Full suite: < 3 hours

### Quality Gates

- All tests must pass before merge
- No decrease in coverage
- Performance tests must meet targets
- Security tests must pass

---

## Risk Mitigation

### Test Maintenance

- Regular test reviews
- Update tests with code changes
- Remove flaky tests
- Optimize slow tests

### Test Environment Stability

- Isolated test databases
- Cleanup between test runs
- Stable test data
- Reliable test infrastructure

### Provider-Specific Risks ⭐ NEW

- **OpenRouter**: API key security, rate limiting, cost tracking
- **OpenAI-Compatible**: Endpoint availability, health checks, failover
- **Multi-Provider**: Provider selection logic, fallback chains

---

## Next Steps

1. **Review and approve this plan**
2. **Set up repository and CI/CD**
3. **Begin Phase 1, Week 1 implementation**
4. **Follow TDD: Write tests first, then implement**
5. **Iterate based on test results**

This plan ensures comprehensive test coverage and quality through Test-Driven Development, with all features developed test-first, including full support for OpenRouter and OpenAI-Compatible LLM providers.
