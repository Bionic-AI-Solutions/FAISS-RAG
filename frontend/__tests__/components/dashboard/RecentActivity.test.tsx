/**
 * Unit tests for RecentActivity component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import RecentActivity from '@/components/dashboard/RecentActivity';
import { analyticsApi } from '@/app/lib/api-client';

// Mock API client
vi.mock('@/app/lib/api-client', () => ({
  analyticsApi: {
    getUsageStats: vi.fn(),
  },
}));

describe('RecentActivity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(analyticsApi.getUsageStats).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<RecentActivity tenantId="test-tenant-123" />);

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Loading activity...')).toBeInTheDocument();
  });

  it('should render empty state when no activity', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 0,
      total_memory_operations: 0,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      expect(screen.getByText('No recent activity')).toBeInTheDocument();
    });
  });

  it('should display search activity', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 10,
      total_memory_operations: 0,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      expect(screen.getByText(/10 search operations performed/)).toBeInTheDocument();
      expect(screen.getByText('🔍')).toBeInTheDocument();
    });
  });

  it('should display memory activity', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 0,
      total_memory_operations: 5,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      expect(screen.getByText(/5 memory operations performed/)).toBeInTheDocument();
      expect(screen.getByText('💾')).toBeInTheDocument();
    });
  });

  it('should display multiple activities', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 10,
      total_memory_operations: 5,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      expect(screen.getByText(/10 search operations performed/)).toBeInTheDocument();
      expect(screen.getByText(/5 memory operations performed/)).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockRejectedValue(new Error('API Error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      expect(screen.getByText('No recent activity')).toBeInTheDocument();
    });

    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('should format timestamps correctly', async () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 1,
      total_memory_operations: 0,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="test-tenant-123" />);

    await waitFor(() => {
      // Should display relative time (e.g., "Just now", "1m ago")
      const timeElement = screen.getByText(/ago|Just now/);
      expect(timeElement).toBeInTheDocument();
    });
  });

  it('should not load activity when tenantId is empty', () => {
    vi.mocked(analyticsApi.getUsageStats).mockResolvedValue({
      total_searches: 0,
      total_memory_operations: 0,
      total_documents: 0,
      period_start: new Date().toISOString(),
      period_end: new Date().toISOString(),
    });

    render(<RecentActivity tenantId="" />);

    // Should not call API when tenantId is empty
    expect(analyticsApi.getUsageStats).not.toHaveBeenCalled();
  });
});
