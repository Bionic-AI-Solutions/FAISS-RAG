# Implementation Plan: Tenant-Specific MCP Server Configuration

## Overview
This feature enables tenant-specific MCP server configuration, allowing each tenant to have their own preconfigured MCP server endpoints for external dependencies (Postgres, MinIO, AI-MCP-Server, etc.).

## Requirements

### Functional Requirements

#### FR-MCP-001: Tenant MCP Configuration Storage
- System must store tenant-specific MCP server configurations in `TenantConfig` model
- Configuration must include endpoints, credentials, and connection parameters for each MCP server type
- Configuration must be stored as JSON in `mcp_server_config` field

#### FR-MCP-002: Tenant MCP Configuration Management
- System must provide MCP tools to register/update tenant-specific MCP server configurations
- System must validate MCP server endpoints before storing configuration
- System must support partial configuration updates (update only specific MCP server types)

#### FR-MCP-003: Dynamic MCP Client Initialization
- System must initialize tenant-specific MCP clients based on `tenant_id` from context
- System must fall back to global configuration if tenant-specific configuration is not available
- System must cache tenant-specific MCP clients for performance

#### FR-MCP-004: Service Integration
- Postgres service must use tenant-specific Postgres MCP client when available
- MinIO service must use tenant-specific MinIO MCP client when available
- AI-MCP-Server service must use tenant-specific AI-MCP-Server client when available
- All services must fall back to global clients if tenant-specific clients are not available

### Non-Functional Requirements

#### NFR-MCP-001: Performance
- Tenant-specific MCP client initialization must add <10ms overhead
- Connection pooling must be efficient for tenant-specific clients
- No performance degradation for tenants using global configuration

#### NFR-MCP-002: Security
- Tenant MCP credentials must be encrypted at rest
- Tenant MCP configurations must be isolated per tenant (RLS enforcement)
- Only Tenant Admin and Uber Admin can manage tenant MCP configurations

#### NFR-MCP-003: Reliability
- System must handle MCP server connection failures gracefully
- System must validate MCP server endpoints before storing configuration
- System must provide clear error messages for invalid configurations

#### NFR-MCP-004: Scalability
- System must support 200+ tenants with tenant-specific MCP configurations
- Connection pooling must scale efficiently with tenant count
- No memory leaks in tenant-specific MCP client caching

## Implementation Phases

### Phase 1: Configuration Storage & Management (Week 1)

#### 1.1 Database Schema Extension
- Add `mcp_server_config` JSON field to `tenant_configs` table
- Create database migration script
- Update `TenantConfig` model with new field

**Deliverables:**
- Database migration file
- Updated `TenantConfig` model
- Unit tests for model changes

#### 1.2 MCP Configuration Management Tools
- Create `rag_register_tenant_mcp_config` MCP tool
- Create `rag_update_tenant_mcp_config` MCP tool
- Create `rag_get_tenant_mcp_config` MCP tool
- Implement configuration validation logic

**Deliverables:**
- MCP tools in `app/mcp/tools/tenant_mcp_config.py`
- Configuration validation functions
- Unit tests for MCP tools

#### 1.3 Configuration Validation
- Implement MCP server endpoint validation
- Implement connection test for each MCP server type
- Add error handling for invalid configurations

**Deliverables:**
- Validation functions
- Connection test utilities
- Unit tests for validation

### Phase 2: MCP Client Factory (Week 2)

#### 2.1 Client Factory Design
- Design tenant-specific MCP client factory pattern
- Create base factory interface
- Implement factory registry for different MCP server types

**Deliverables:**
- Factory design document
- Base factory interface
- Factory registry implementation

#### 2.2 Postgres MCP Client Factory
- Implement tenant-specific Postgres MCP client factory
- Add connection pooling for tenant-specific clients
- Implement fallback to global Postgres client

**Deliverables:**
- Postgres MCP client factory
- Connection pooling implementation
- Unit tests for factory

#### 2.3 MinIO MCP Client Factory
- Implement tenant-specific MinIO MCP client factory
- Add connection pooling for tenant-specific clients
- Implement fallback to global MinIO client

**Deliverables:**
- MinIO MCP client factory
- Connection pooling implementation
- Unit tests for factory

#### 2.4 AI-MCP-Server Client Factory
- Implement tenant-specific AI-MCP-Server client factory
- Leverage AI-MCP-Server's native multi-tenant capabilities for tenant-specific endpoint routing
- Add connection pooling for tenant-specific clients
- Implement fallback to global AI-MCP-Server client

**Deliverables:**
- AI-MCP-Server client factory
- Connection pooling implementation
- Unit tests for factory

### Phase 3: Service Integration (Week 3)

#### 3.1 Postgres Service Integration
- Update Postgres service to use tenant-specific clients
- Implement tenant context extraction for client selection
- Add fallback logic to global client

**Deliverables:**
- Updated Postgres service
- Integration tests
- Performance benchmarks

#### 3.2 MinIO Service Integration
- Update MinIO service to use tenant-specific clients
- Implement tenant context extraction for client selection
- Add fallback logic to global client

**Deliverables:**
- Updated MinIO service
- Integration tests
- Performance benchmarks

#### 3.3 AI-MCP-Server Service Integration
- Update AI-MCP-Server service to use tenant-specific clients
- Leverage AI-MCP-Server's native multi-tenant setup for tenant-specific routing
- Implement tenant context extraction for client selection
- Add fallback logic to global client

**Deliverables:**
- Updated AI-MCP-Server service
- Integration tests
- Performance benchmarks

### Phase 4: Testing & Validation (Week 4)

#### 4.1 Unit Tests
- Unit tests for configuration management
- Unit tests for MCP client factory
- Unit tests for service integration

**Deliverables:**
- Complete unit test suite
- >80% code coverage
- All tests passing

#### 4.2 Integration Tests
- Integration tests for tenant-specific MCP connections
- Integration tests for fallback to global configuration
- Integration tests for configuration validation

**Deliverables:**
- Complete integration test suite
- All integration tests passing
- Test documentation

#### 4.3 Performance Tests
- Performance tests for connection initialization overhead
- Performance tests for connection pooling
- Performance tests for tenant-specific vs global clients

**Deliverables:**
- Performance test results
- Performance benchmarks
- Optimization recommendations

## Dependencies
- TenantConfig model extension
- MCP client service refactoring
- Database migration support
- Existing MCP client implementations (Postgres, MinIO, AI-MCP-Server)

## Testing Strategy

### Unit Testing
- Configuration management functions
- MCP client factory implementations
- Service integration logic
- Validation functions

### Integration Testing
- End-to-end tenant-specific MCP connections
- Fallback to global configuration
- Configuration validation workflows
- Multi-tenant scenarios

### Performance Testing
- Connection initialization overhead
- Connection pooling efficiency
- Tenant-specific vs global client performance
- Scalability with 200+ tenants

### Security Testing
- Tenant configuration isolation (RLS)
- Credential encryption
- Authorization checks
- Input validation

## Rollout Plan

### Development Environment
1. Deploy database migration
2. Deploy MCP configuration management tools
3. Deploy MCP client factories
4. Deploy service integrations
5. Run full test suite

### Staging Environment
1. Deploy all changes
2. Configure test tenant with tenant-specific MCP servers
3. Run integration tests
4. Performance validation
5. Security validation

### Production Environment
1. Deploy database migration (with rollback plan)
2. Deploy MCP configuration management tools
3. Deploy MCP client factories
4. Deploy service integrations
5. Monitor for issues
6. Gradual rollout to enterprise tenants

## Rollback Plan
- Database migration rollback script
- Feature flag to disable tenant-specific MCP configuration
- Fallback to global configuration for all tenants
- Monitoring and alerting for rollback triggers

## Monitoring and Alerting
- MCP client connection success rate
- Tenant-specific MCP configuration usage
- Performance metrics (connection initialization time)
- Error rates for tenant-specific MCP connections
