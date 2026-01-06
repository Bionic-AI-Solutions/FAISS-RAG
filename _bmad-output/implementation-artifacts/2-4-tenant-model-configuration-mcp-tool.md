# Story 2.4: Tenant Model Configuration MCP Tool

**Status:** Done  
**Epic:** Epic 2: Tenant Onboarding & Configuration  
**OpenProject ID:** 126

## Story Description

As a **Tenant Admin**,
I want **to configure tenant-specific AI models**,
So that **my tenant can use domain-appropriate models for embeddings and LLM operations**.

## Acceptance Criteria

### ✅ Task 1: Create Model Validation Service

**Given** Model validation is required  
**When** I create model validation service  
**Then** Service validates embedding models (text-embedding-3-large, text-embedding-3-small, etc.)  
**And** Service validates LLM models (gpt-4-turbo-preview, gpt-4, claude-3-5-sonnet, etc.)  
**And** Service validates domain-specific models  
**And** Service returns structured errors with suggestions for invalid models  
**And** Service provides fuzzy matching for similar model names

**Implementation:**
- ✅ Created `app/services/model_validator.py` with `ModelValidator` class
- ✅ Added `validate_embedding_model` method with supported models list
- ✅ Added `validate_llm_model` method with supported models list
- ✅ Added `validate_model_configuration` method for complete config validation
- ✅ Added `_find_similar_models` helper for fuzzy matching
- ✅ Returns structured `ValidationError` with recovery suggestions
- ✅ Case-insensitive model validation

### ✅ Task 2: Implement rag_configure_tenant_models MCP Tool

**Given** Model configuration is required  
**When** I implement rag_configure_tenant_models MCP tool  
**Then** Tool accepts: tenant_id, model_configuration (embedding_model, llm_model, domain-specific models) (FR-TENANT-006)  
**And** Tool validates model configuration (model availability, compatibility)  
**And** Tool stores configuration in tenant_config table  
**And** Tool updates tenant model settings for all operations  
**And** Access is restricted to Tenant Admin role only  
**And** Configuration update completes within <200ms

**Implementation:**
- ✅ Created `app/mcp/tools/tenant_configuration.py` with `rag_configure_tenant_models` tool
- ✅ Tool validates tenant_id format (UUID)
- ✅ Tool checks authorization (Tenant Admin only)
- ✅ Tool verifies tenant admin is configuring their own tenant
- ✅ Tool validates tenant exists
- ✅ Tool validates tenant_config exists
- ✅ Tool validates model configuration using ModelValidator
- ✅ Tool merges new configuration with existing configuration
- ✅ Tool updates tenant_config.model_configuration
- ✅ Tool registered in `app/mcp/tools/__init__.py`

### ✅ Task 3: Add Model Configuration Tests

**Given** Model configuration tool needs to be tested  
**When** I create tests  
**Then** Tests verify authorization checks (Tenant Admin only)  
**And** Tests verify tenant admin can only configure their own tenant  
**And** Tests verify successful configuration flow  
**And** Tests verify invalid model validation  
**And** Tests verify tenant not found error  
**And** Tests verify config not found error  
**And** All tests pass

**Implementation:**
- ✅ Created `tests/unit/test_model_validator.py` with 15 tests (all passing)
- ✅ Created `tests/unit/test_tenant_configuration_tool.py` with 7 tests (all passing)
- ✅ Tests cover all scenarios including authorization, validation, and error handling
- ✅ 100% test pass rate

### ✅ Task 4: Verify Story Implementation

**Given** Story implementation is complete  
**When** I verify all acceptance criteria  
**Then** All acceptance criteria are met  
**And** All tests pass  
**And** Tool is registered and discoverable via rag_list_tools  
**And** Configuration update completes within <200ms (performance requirement)

## Files Created/Modified

- ✅ `app/services/model_validator.py` - Model validation service
- ✅ `app/mcp/tools/tenant_configuration.py` - Tenant model configuration MCP tool
- ✅ `app/mcp/tools/__init__.py` - Added tenant_configuration import
- ✅ `tests/unit/test_model_validator.py` - Model validator tests (15 tests)
- ✅ `tests/unit/test_tenant_configuration_tool.py` - Configuration tool tests (7 tests)

## Notes

- Tool is restricted to Tenant Admin role only (as per FR-TENANT-006)
- Tenant Admin can only configure models for their own tenant (tenant isolation)
- Model validation provides fuzzy matching and suggestions for invalid models
- Configuration is merged with existing settings (partial updates supported)
- All model names are normalized to lowercase for consistency
- Supported models include OpenAI (GPT-4, GPT-3.5, embeddings) and Anthropic (Claude) models

