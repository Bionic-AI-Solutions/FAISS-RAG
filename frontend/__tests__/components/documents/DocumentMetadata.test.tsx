/**
 * Unit tests for DocumentMetadata component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DocumentMetadata from '@/components/documents/DocumentMetadata';

describe('DocumentMetadata', () => {
  const mockDocument = {
    document_id: 'doc-1',
    title: 'Test Document',
    type: 'pdf',
    created_at: '2024-01-15T10:00:00Z',
    status: 'indexed',
    size: 1024 * 1024, // 1MB
  };

  it('should render document information title', () => {
    render(<DocumentMetadata document={mockDocument} />);

    expect(screen.getByText('Document Information')).toBeInTheDocument();
  });

  it('should display basic information', () => {
    render(<DocumentMetadata document={mockDocument} />);

    expect(screen.getByText('Basic Information')).toBeInTheDocument();
    expect(screen.getByText('Test Document')).toBeInTheDocument();
    expect(screen.getByText('pdf')).toBeInTheDocument();
    expect(screen.getByText('1.00 MB')).toBeInTheDocument();
  });

  it('should display status badge', () => {
    render(<DocumentMetadata document={mockDocument} />);

    expect(screen.getByText('✅ Indexed')).toBeInTheDocument();
  });

  it('should display dates section', () => {
    render(<DocumentMetadata document={mockDocument} />);

    expect(screen.getByText('Dates')).toBeInTheDocument();
    expect(screen.getByText('Created:')).toBeInTheDocument();
  });

  it('should display updated date when available', () => {
    const docWithUpdate = {
      ...mockDocument,
      updated_at: '2024-01-16T10:00:00Z',
    };

    render(<DocumentMetadata document={docWithUpdate} />);

    expect(screen.getByText('Updated:')).toBeInTheDocument();
  });

  it('should display version history when available', () => {
    const docWithVersions = {
      ...mockDocument,
      versions: [
        {
          version: '1.0',
          created_at: '2024-01-15T10:00:00Z',
          notes: 'Initial version',
        },
        {
          version: '1.1',
          created_at: '2024-01-16T10:00:00Z',
          notes: 'Updated content',
        },
      ],
    };

    render(<DocumentMetadata document={docWithVersions} />);

    expect(screen.getByText('Version History')).toBeInTheDocument();
    expect(screen.getByText('v1.0')).toBeInTheDocument();
    expect(screen.getByText('v1.1')).toBeInTheDocument();
    expect(screen.getByText('Initial version')).toBeInTheDocument();
    expect(screen.getByText('Updated content')).toBeInTheDocument();
  });

  it('should display metadata when available', () => {
    const docWithMetadata = {
      ...mockDocument,
      metadata: {
        author: 'John Doe',
        pages: 10,
        language: 'en',
      },
    };

    render(<DocumentMetadata document={docWithMetadata} />);

    expect(screen.getByText('Metadata')).toBeInTheDocument();
    expect(screen.getByText('author:')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('pages:')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('should handle missing size gracefully', () => {
    const docWithoutSize = {
      ...mockDocument,
      size: undefined,
    };

    render(<DocumentMetadata document={docWithoutSize} />);

    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('should use document_id when title is missing', () => {
    const docWithoutTitle = {
      ...mockDocument,
      title: '',
    };

    render(<DocumentMetadata document={docWithoutTitle} />);

    expect(screen.getByText('doc-1')).toBeInTheDocument();
  });
});
