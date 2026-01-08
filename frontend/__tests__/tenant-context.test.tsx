/**
 * Tenant Context Tests
 * 
 * Tests for tenant context switching, session persistence, and context management.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { TenantProvider, useTenant } from '@/app/contexts/TenantContext';

// Mock window.sessionStorage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
});

// Mock dependencies
vi.mock('@/app/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'uber@example.com', role: 'uber_admin' },
  }),
}));

vi.mock('@/app/contexts/RoleContext', () => ({
  useRole: () => ({
    isUberAdmin: true,
  }),
}));

describe('Tenant Context', () => {
  beforeEach(() => {
    sessionStorageMock.clear();
  });

  describe('Tenant Context Switching (Uber Admin)', () => {
    it('should switch to tenant context', () => {
      const { result } = renderHook(() => useTenant(), {
        wrapper: TenantProvider,
      });

      act(() => {
        result.current.switchTenant('tenant-123', 'Test Tenant');
      });

      expect(result.current.currentTenantId).toBe('tenant-123');
      expect(result.current.currentTenantName).toBe('Test Tenant');
      expect(result.current.isInTenantContext).toBe(true);
    });

    it('should persist tenant context in session storage', () => {
      const { result } = renderHook(() => useTenant(), {
        wrapper: TenantProvider,
      });

      act(() => {
        result.current.switchTenant('tenant-123', 'Test Tenant');
      });

      expect(sessionStorage.getItem('current_tenant_id')).toBe('tenant-123');
      expect(sessionStorage.getItem('current_tenant_name')).toBe('Test Tenant');
    });

    it('should exit tenant context', () => {
      const { result } = renderHook(() => useTenant(), {
        wrapper: TenantProvider,
      });

      act(() => {
        result.current.switchTenant('tenant-123', 'Test Tenant');
      });

      act(() => {
        result.current.exitTenantContext();
      });

      expect(result.current.currentTenantId).toBeNull();
      expect(result.current.currentTenantName).toBeNull();
      expect(result.current.isInTenantContext).toBe(false);
    });

    it('should restore tenant context from session storage', async () => {
      sessionStorageMock.setItem('current_tenant_id', 'tenant-456');
      sessionStorageMock.setItem('current_tenant_name', 'Restored Tenant');

      const { result } = renderHook(() => useTenant(), {
        wrapper: TenantProvider,
      });

      // Wait for useEffect to run
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(result.current.currentTenantId).toBe('tenant-456');
      expect(result.current.currentTenantName).toBe('Restored Tenant');
    });
  });
});
