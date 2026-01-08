/**
 * Unit tests for DocumentList component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentList from '@/components/documents/DocumentList';

describe('DocumentList', () => {
  const mockDocuments = [
    {
      document_id: 'doc-1',
      title: 'Test Document 1',
      type: 'pdf',
      created_at: '2024-01-15T10:00:00Z',
      status: 'indexed',
      size: 1024 * 1024, // 1MB
    },
    {
      document_id: 'doc-2',
      title: 'Test Document 2',
      type: 'docx',
      created_at: '2024-01-14T15:30:00Z',
      status: 'processing',
      size: 512 * 1024, // 512KB
    },
  ];

  it('should render empty state when no documents', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={[]}
        total={0}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Documents (0)')).toBeInTheDocument();
    expect(screen.getByText('No documents found')).toBeInTheDocument();
  });

  it('should render documents list', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={2}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Documents (2)')).toBeInTheDocument();
    expect(screen.getByText('Test Document 1')).toBeInTheDocument();
    expect(screen.getByText('Test Document 2')).toBeInTheDocument();
  });

  it('should call onView when document title is clicked', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={2}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    const docLink = screen.getByText('Test Document 1');
    await user.click(docLink);

    expect(mockOnView).toHaveBeenCalledWith('doc-1');
  });

  it('should call onDelete when Delete button is clicked', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={2}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    const deleteButtons = screen.getAllByText('Delete');
    await user.click(deleteButtons[0]);

    expect(mockOnDelete).toHaveBeenCalledWith('doc-1');
  });

  it('should display pagination when total pages > 1', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={25}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('should call onPageChange when pagination buttons are clicked', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={25}
        page={2}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    expect(mockOnPageChange).toHaveBeenCalledWith(3);
  });

  it('should disable Previous button on first page', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={25}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeDisabled();
  });

  it('should format file sizes correctly', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={2}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
    expect(screen.getByText('512.00 KB')).toBeInTheDocument();
  });

  it('should display status badges correctly', () => {
    const mockOnPageChange = vi.fn();
    const mockOnView = vi.fn();
    const mockOnDelete = vi.fn();

    render(
      <DocumentList
        documents={mockDocuments}
        total={2}
        page={1}
        pageSize={10}
        onPageChange={mockOnPageChange}
        onView={mockOnView}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('✅ Indexed')).toBeInTheDocument();
    expect(screen.getByText('⏳ Processing')).toBeInTheDocument();
  });
});
