/**
 * Unit tests for HealthStatus component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import HealthStatus from '@/components/dashboard/HealthStatus';

describe('HealthStatus', () => {
  it('should render healthy status correctly', () => {
    const components = {
      database: { status: true, message: 'Connected' },
      vector_store: { status: true, message: 'Operational' },
      api: { status: true, message: 'Running' },
    };

    render(<HealthStatus status="healthy" components={components} />);

    expect(screen.getByText('Health Status')).toBeInTheDocument();
    expect(screen.getByText('Healthy')).toBeInTheDocument();
    expect(screen.getByText('database')).toBeInTheDocument();
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('should render degraded status correctly', () => {
    const components = {
      database: { status: true, message: 'Connected' },
      vector_store: { status: false, message: 'Degraded performance' },
    };

    render(<HealthStatus status="degraded" components={components} />);

    expect(screen.getByText('Degraded')).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });

  it('should render unhealthy status correctly', () => {
    const components = {
      database: { status: false, message: 'Connection failed' },
    };

    render(<HealthStatus status="unhealthy" components={components} />);

    expect(screen.getByText('Unhealthy')).toBeInTheDocument();
    // Check for status icon in the status badge (first occurrence)
    const statusBadge = screen.getByText('Unhealthy').closest('div');
    expect(statusBadge).toHaveTextContent('❌');
  });

  it('should display all component statuses', () => {
    const components = {
      database: { status: true, message: 'Connected' },
      vector_store: { status: true, message: 'Operational' },
      api: { status: false, message: 'Error' },
      cache: { status: true, message: 'Active' },
    };

    render(<HealthStatus status="healthy" components={components} />);

    expect(screen.getByText('database')).toBeInTheDocument();
    expect(screen.getByText('vector_store')).toBeInTheDocument();
    expect(screen.getByText('api')).toBeInTheDocument();
    expect(screen.getByText('cache')).toBeInTheDocument();
  });

  it('should handle empty components object', () => {
    render(<HealthStatus status="healthy" components={{}} />);

    expect(screen.getByText('Health Status')).toBeInTheDocument();
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });
});
