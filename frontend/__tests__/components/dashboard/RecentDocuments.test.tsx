/**
 * Unit tests for RecentDocuments component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RecentDocuments from '@/components/dashboard/RecentDocuments';

// Mock Next.js router
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('RecentDocuments', () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  const mockDocuments = [
    {
      document_id: 'doc-1',
      title: 'Test Document 1',
      type: 'pdf',
      created_at: '2024-01-15T10:00:00Z',
      status: 'indexed',
    },
    {
      document_id: 'doc-2',
      title: 'Test Document 2',
      type: 'docx',
      created_at: '2024-01-14T15:30:00Z',
      status: 'processing',
    },
  ];

  it('should render empty state when no documents', () => {
    render(<RecentDocuments documents={[]} />);

    expect(screen.getByText('Recent Documents')).toBeInTheDocument();
    expect(screen.getByText('No documents yet')).toBeInTheDocument();
    expect(screen.getByText('Upload Your First Document')).toBeInTheDocument();
  });

  it('should render documents list', () => {
    render(<RecentDocuments documents={mockDocuments} />);

    expect(screen.getByText('Recent Documents')).toBeInTheDocument();
    expect(screen.getByText('View All')).toBeInTheDocument();
    expect(screen.getByText('Test Document 1')).toBeInTheDocument();
    expect(screen.getByText('Test Document 2')).toBeInTheDocument();
  });

  it('should display document types', () => {
    render(<RecentDocuments documents={mockDocuments} />);

    expect(screen.getByText('pdf')).toBeInTheDocument();
    expect(screen.getByText('docx')).toBeInTheDocument();
  });

  it('should display status badges', () => {
    render(<RecentDocuments documents={mockDocuments} />);

    expect(screen.getByText('✅ Indexed')).toBeInTheDocument();
    expect(screen.getByText('⏳ Processing')).toBeInTheDocument();
  });

  it('should navigate to documents page when View All is clicked', async () => {
    const user = userEvent.setup();
    render(<RecentDocuments documents={mockDocuments} />);

    const viewAllButton = screen.getByText('View All');
    await user.click(viewAllButton);

    expect(mockPush).toHaveBeenCalledWith('/tenant/documents');
  });

  it('should navigate to document detail when document title is clicked', async () => {
    const user = userEvent.setup();
    render(<RecentDocuments documents={mockDocuments} />);

    const docLink = screen.getByText('Test Document 1');
    await user.click(docLink);

    expect(mockPush).toHaveBeenCalledWith('/tenant/documents/doc-1');
  });

  it('should navigate to document detail when View button is clicked', async () => {
    const user = userEvent.setup();
    render(<RecentDocuments documents={mockDocuments} />);

    const viewButtons = screen.getAllByText('View');
    await user.click(viewButtons[0]);

    expect(mockPush).toHaveBeenCalledWith('/tenant/documents/doc-1');
  });

  it('should navigate to upload page when Upload button is clicked in empty state', async () => {
    const user = userEvent.setup();
    render(<RecentDocuments documents={[]} />);

    const uploadButton = screen.getByText('Upload Your First Document');
    await user.click(uploadButton);

    expect(mockPush).toHaveBeenCalledWith('/tenant/documents/upload');
  });

  it('should format dates correctly', () => {
    render(<RecentDocuments documents={mockDocuments} />);

    // Check that dates are rendered (exact format may vary)
    const dateElements = screen.getAllByText(/Jan|2024/);
    expect(dateElements.length).toBeGreaterThan(0);
  });

  it('should handle documents without title', () => {
    const docsWithoutTitle = [
      {
        document_id: 'doc-3',
        title: '',
        type: 'txt',
        created_at: '2024-01-15T10:00:00Z',
        status: 'indexed',
      },
    ];

    render(<RecentDocuments documents={docsWithoutTitle} />);

    // Should display document_id when title is missing
    expect(screen.getByText('doc-3')).toBeInTheDocument();
  });
});
