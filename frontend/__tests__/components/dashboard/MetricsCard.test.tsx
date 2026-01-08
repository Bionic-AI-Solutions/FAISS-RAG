/**
 * Unit tests for MetricsCard component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricsCard from '@/components/dashboard/MetricsCard';

describe('MetricsCard', () => {
  it('should render with title and value', () => {
    render(<MetricsCard title="Total Documents" value={150} />);

    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('should render with string value', () => {
    render(<MetricsCard title="Status" value="Active" />);

    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('should render with subtitle', () => {
    render(
      <MetricsCard
        title="Total Documents"
        value={150}
        subtitle="Last 30 days"
      />
    );

    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('Last 30 days')).toBeInTheDocument();
  });

  it('should render with icon', () => {
    render(
      <MetricsCard
        title="Total Documents"
        value={150}
        icon="📄"
      />
    );

    expect(screen.getByText('📄')).toBeInTheDocument();
  });

  it('should render with positive trend', () => {
    render(
      <MetricsCard
        title="Growth"
        value={100}
        trend={{ value: 15, isPositive: true }}
      />
    );

    expect(screen.getByText('↑ 15%')).toBeInTheDocument();
  });

  it('should render with negative trend', () => {
    render(
      <MetricsCard
        title="Decline"
        value={100}
        trend={{ value: 10, isPositive: false }}
      />
    );

    expect(screen.getByText('↓ 10%')).toBeInTheDocument();
  });

  it('should format large numbers with commas', () => {
    render(<MetricsCard title="Total" value={1234567} />);

    expect(screen.getByText('1,234,567')).toBeInTheDocument();
  });

  it('should render all props together', () => {
    render(
      <MetricsCard
        title="Documents"
        value={250}
        subtitle="This month"
        icon="📄"
        trend={{ value: 20, isPositive: true }}
      />
    );

    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('250')).toBeInTheDocument();
    expect(screen.getByText('This month')).toBeInTheDocument();
    expect(screen.getByText('📄')).toBeInTheDocument();
    expect(screen.getByText('↑ 20%')).toBeInTheDocument();
  });
});
