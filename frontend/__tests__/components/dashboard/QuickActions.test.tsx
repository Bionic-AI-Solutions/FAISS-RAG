/**
 * Unit tests for QuickActions component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import QuickActions from '@/components/dashboard/QuickActions';

// Mock Next.js router
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('QuickActions', () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it('should render all quick action buttons', () => {
    render(<QuickActions tenantId="test-tenant-123" />);

    expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    expect(screen.getByText('Upload Document')).toBeInTheDocument();
    expect(screen.getByText('View Analytics')).toBeInTheDocument();
    expect(screen.getByText('Manage Documents')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
  });

  it('should navigate to upload page when Upload Document is clicked', async () => {
    const user = userEvent.setup();
    render(<QuickActions tenantId="test-tenant-123" />);

    const uploadButton = screen.getByText('Upload Document').closest('button');
    expect(uploadButton).toBeInTheDocument();
    
    await user.click(uploadButton!);
    expect(mockPush).toHaveBeenCalledWith('/tenant/documents/upload');
  });

  it('should navigate to analytics page when View Analytics is clicked', async () => {
    const user = userEvent.setup();
    render(<QuickActions tenantId="test-tenant-123" />);

    const analyticsButton = screen.getByText('View Analytics').closest('button');
    expect(analyticsButton).toBeInTheDocument();
    
    await user.click(analyticsButton!);
    expect(mockPush).toHaveBeenCalledWith('/tenant/analytics');
  });

  it('should navigate to documents page when Manage Documents is clicked', async () => {
    const user = userEvent.setup();
    render(<QuickActions tenantId="test-tenant-123" />);

    const documentsButton = screen.getByText('Manage Documents').closest('button');
    expect(documentsButton).toBeInTheDocument();
    
    await user.click(documentsButton!);
    expect(mockPush).toHaveBeenCalledWith('/tenant/documents');
  });

  it('should navigate to configuration page when Configuration is clicked', async () => {
    const user = userEvent.setup();
    render(<QuickActions tenantId="test-tenant-123" />);

    const configButton = screen.getByText('Configuration').closest('button');
    expect(configButton).toBeInTheDocument();
    
    await user.click(configButton!);
    expect(mockPush).toHaveBeenCalledWith('/tenant/configuration');
  });

  it('should display action descriptions', () => {
    render(<QuickActions tenantId="test-tenant-123" />);

    expect(screen.getByText('Add new documents to your knowledge base')).toBeInTheDocument();
    expect(screen.getByText('View detailed analytics and reports')).toBeInTheDocument();
    expect(screen.getByText('View and manage all documents')).toBeInTheDocument();
    expect(screen.getByText('Configure tenant settings')).toBeInTheDocument();
  });

  it('should display action icons', () => {
    render(<QuickActions tenantId="test-tenant-123" />);

    expect(screen.getByText('📤')).toBeInTheDocument();
    expect(screen.getByText('📊')).toBeInTheDocument();
    expect(screen.getByText('📄')).toBeInTheDocument();
    expect(screen.getByText('⚙️')).toBeInTheDocument();
  });
});
