# Story 2.2: Template Discovery MCP Tool

**Status:** Done  
**Epic:** Epic 2: Tenant Onboarding & Configuration  
**OpenProject ID:** 124

## Story Description

As a **Tenant Admin**,
I want **to discover available domain templates**,
So that **I can select the most appropriate template for my tenant**.

## Acceptance Criteria

### ✅ Task 1: Implement rag_list_templates MCP Tool

**Given** Template listing is required  
**When** I implement rag_list_templates MCP tool  
**Then** Tool returns list of available templates with descriptions (FR-TENANT-002)  
**And** Tool supports optional domain filter parameter  
**And** Each template includes: template_id, template_name, domain_type, description, compliance_checklist, configuration_options  
**And** Tool is accessible to all authenticated users (for discovery)  
**And** Response time is <100ms (p95)

**Implementation:**
- ✅ Created `app/mcp/tools/templates.py` with `rag_list_templates` tool
- ✅ Tool supports optional `domain_type` filter parameter
- ✅ Tool returns all template fields including compliance_checklist and customization_options
- ✅ Tool accessible to all authenticated users (no RBAC restrictions)
- ✅ Updated `app/mcp/tools/__init__.py` to import templates module

### ✅ Task 2: Implement rag_get_template MCP Tool

**Given** Template details retrieval is required  
**When** I implement rag_get_template MCP tool  
**Then** Tool returns complete template details for given template_id (FR-TENANT-003)  
**And** Details include: configuration options, compliance requirements, customization guide, example configurations  
**And** Tool is accessible to all authenticated users  
**And** Response time is <100ms (p95)

**Implementation:**
- ✅ Created `rag_get_template` tool in `app/mcp/tools/templates.py`
- ✅ Tool accepts `template_id` parameter (UUID string)
- ✅ Tool returns complete template details including all fields
- ✅ Tool raises `ResourceNotFoundError` if template not found
- ✅ Tool validates UUID format

### ✅ Task 3: Add Template Tool Tests

**Given** Template tools need to be tested  
**When** I create tests  
**Then** Tests verify rag_list_templates with and without domain filter  
**And** Tests verify rag_get_template success and error cases  
**And** All tests pass

**Implementation:**
- ✅ Created `tests/unit/test_template_tools.py` with comprehensive tests
- ✅ Tests cover: listing all templates, filtering by domain, getting template by ID, error cases

### ⏳ Task 4: Verify Story Implementation

**Given** Story implementation is complete  
**When** I verify all acceptance criteria  
**Then** All acceptance criteria are met  
**And** All tests pass  
**And** Tools are registered and discoverable via rag_list_tools

## Files Created/Modified

- ✅ `app/mcp/tools/templates.py` - Template discovery MCP tools
- ✅ `app/mcp/tools/__init__.py` - Added templates import
- ✅ `tests/unit/test_template_tools.py` - Template tool tests

## Notes

- Tools are accessible to all authenticated users (no RBAC restrictions) for template discovery
- Tools use TemplateRepository for database access
- Error handling uses ResourceNotFoundError for consistency
- Tools follow FastMCP tool decorator pattern with async functions

