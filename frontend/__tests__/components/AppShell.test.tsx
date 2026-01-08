/**
 * AppShell Component Tests
 * 
 * Tests for base layout components: AppShell, Header, Sidebar, Breadcrumbs
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import AppShell from '@/components/AppShell';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import Breadcrumbs from '@/components/Breadcrumbs';

// Mock contexts
vi.mock('@/app/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '1', email: 'test@example.com', role: 'tenant_admin' },
    logout: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('@/app/contexts/RoleContext', () => ({
  useRole: () => ({
    role: 'tenant_admin',
    permissions: {
      canViewTenantDashboard: true,
      canManageDocuments: true,
      canViewPlatformDashboard: false,
      canManageTenants: false,
      canManageConfiguration: true,
      canViewAnalytics: true,
      canManageUsers: true,
      canSwitchTenantContext: false,
    },
    isUberAdmin: false,
    isTenantAdmin: true,
  }),
  RoleProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('@/app/contexts/TenantContext', () => ({
  useTenant: () => ({
    currentTenantId: 'tenant-123',
    currentTenantName: null,
    isInTenantContext: false,
    switchTenant: vi.fn(),
    exitTenantContext: vi.fn(),
  }),
  TenantProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('next/navigation', () => ({
  usePathname: () => '/tenant/dashboard',
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('AppShell', () => {
  it('should render with children', () => {
    render(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
});

describe('Header', () => {
  it('should display platform name', () => {
    render(<Header />);
    expect(screen.getByText('RAG Platform Admin')).toBeInTheDocument();
  });

  it('should display user email', () => {
    render(<Header />);
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('should display role badge for tenant_admin', () => {
    render(<Header />);
    expect(screen.getByText('Tenant Admin')).toBeInTheDocument();
  });
});

describe('Sidebar', () => {
  it('should render navigation items for tenant_admin', () => {
    render(<Sidebar />);
    expect(screen.getByText('Tenant Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Document Management')).toBeInTheDocument();
  });

  it('should not render platform dashboard for tenant_admin', () => {
    render(<Sidebar />);
    expect(screen.queryByText('Platform Dashboard')).not.toBeInTheDocument();
  });
});

describe('Breadcrumbs', () => {
  it('should render breadcrumb navigation', () => {
    render(<Breadcrumbs />);
    expect(screen.getByText('Home')).toBeInTheDocument();
  });
});
