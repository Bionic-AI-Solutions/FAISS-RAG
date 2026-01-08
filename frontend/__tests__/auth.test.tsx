/**
 * Authentication Tests
 * 
 * Tests for OAuth 2.0 authentication, JWT token handling, and session management.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getToken, storeToken, removeToken, extractUserFromToken, isTokenExpired, getOAuthUrl } from '@/app/lib/auth';

// Mock window object for localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

describe('Authentication', () => {
  beforeEach(() => {
    // Clear mocks before each test
    vi.clearAllMocks();
    // Reset localStorage mock
    (localStorage.getItem as any).mockReturnValue(null);
  });

  describe('Token Management', () => {
    it('should store and retrieve token', () => {
      const token = 'test-token-123';
      storeToken(token);
      expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', token);
      (localStorage.getItem as any).mockReturnValue(token);
      expect(getToken()).toBe(token);
    });

    it('should remove token on logout', () => {
      (localStorage.getItem as any).mockReturnValue('test-token');
      removeToken();
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
      (localStorage.getItem as any).mockReturnValue(null);
      expect(getToken()).toBeNull();
    });

    it('should detect expired tokens', () => {
      // Create expired token (exp: past date)
      const expiredToken = createTestToken({ exp: Math.floor(Date.now() / 1000) - 3600 });
      expect(isTokenExpired(expiredToken)).toBe(true);
    });

    it('should detect valid tokens', () => {
      // Create valid token (exp: future date)
      const validToken = createTestToken({ exp: Math.floor(Date.now() / 1000) + 3600 });
      expect(isTokenExpired(validToken)).toBe(false);
    });
  });

  describe('User Extraction from Token', () => {
    it('should extract user from valid JWT token', () => {
      const token = createTestToken({
        sub: 'user-123',
        email: 'test@example.com',
        role: 'tenant_admin',
        tenant_id: 'tenant-456',
      });

      const user = extractUserFromToken(token);
      expect(user).toEqual({
        id: 'user-123',
        email: 'test@example.com',
        role: 'tenant_admin',
        tenant_id: 'tenant-456',
      });
    });

    it('should handle missing claims gracefully', () => {
      const token = createTestToken({ sub: 'user-123' });
      const user = extractUserFromToken(token);
      expect(user?.id).toBe('user-123');
      expect(user?.email).toBe('');
      expect(user?.role).toBe('end_user');
    });
  });

  describe('OAuth Flow', () => {
    it('should generate OAuth URL with correct parameters', () => {
      const url = new URL(getOAuthUrl());
      expect(url.searchParams.get('response_type')).toBe('code');
      expect(url.searchParams.get('scope')).toContain('openid');
      expect(url.searchParams.get('state')).toBeTruthy();
    });
  });
});

/**
 * Helper function to create test JWT tokens
 */
function createTestToken(payload: Record<string, any>): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const base64Header = btoa(JSON.stringify(header));
  const base64Payload = btoa(JSON.stringify(payload));
  return `${base64Header}.${base64Payload}.signature`;
}
