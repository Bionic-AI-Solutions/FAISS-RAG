/**
 * Integration test setup file.
 * 
 * This file configures the test environment for integration tests that use live services.
 */

import { beforeAll, afterAll } from 'vitest';

// Test configuration
export const TEST_CONFIG = {
  // Backend API base URL (main RAG backend with MCP server)
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // REST Proxy Backend URL (for Admin UI API)
  REST_PROXY_URL: process.env.REST_PROXY_URL || 'http://localhost:8001',
  
  // MCP server base URL (mounted in main backend)
  MCP_BASE_URL: process.env.MCP_BASE_URL || 'http://localhost:8000/mcp',
  
  // OAuth configuration (for integration tests)
  OAUTH_CLIENT_ID: process.env.OAUTH_CLIENT_ID || 'test-client-id',
  OAUTH_REDIRECT_URI: process.env.OAUTH_REDIRECT_URI || 'http://localhost:3000/auth/callback',
  
  // Test tenant configuration
  TEST_TENANT_ID: 'test-integration-tenant',
  TEST_TENANT_NAME: 'Test Integration Tenant',
  
  // Performance thresholds
  API_RESPONSE_TIME_THRESHOLD_MS: 150, // p95 threshold
};

/**
 * Ensure backend services are running before integration tests.
 */
beforeAll(async () => {
  // Check if backend is accessible
  try {
    const response = await fetch(`${TEST_CONFIG.API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }
    const health = await response.json();
    console.log('✅ Backend is accessible', health);
  } catch (error) {
    console.warn('⚠️  Backend may not be running. Integration tests may fail.');
    console.warn('   Start backend with: cd backend && uvicorn app.main:app --reload');
    console.warn(`   Error: ${error}`);
  }
  
  // Check if MCP server is accessible
  try {
    // MCP server should be mounted at /mcp endpoint
    const response = await fetch(`${TEST_CONFIG.MCP_BASE_URL}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'initialize',
        params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'test', version: '1.0' } },
        id: 1,
      }),
    });
    if (!response.ok) {
      throw new Error(`MCP server check failed: ${response.status}`);
    }
    console.log('✅ MCP server is accessible');
  } catch (error) {
    console.warn('⚠️  MCP server may not be accessible. Some integration tests may fail.');
    console.warn(`   Error: ${error}`);
  }
});

/**
 * Cleanup after all integration tests.
 */
afterAll(async () => {
  // Cleanup test data if needed
  // For now, we'll leave test data for manual inspection
  console.log('Integration tests completed');
});
