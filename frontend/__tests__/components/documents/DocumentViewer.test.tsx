/**
 * Unit tests for DocumentViewer component
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DocumentViewer from '@/components/documents/DocumentViewer';

describe('DocumentViewer', () => {
  it('should render document preview title', () => {
    const mockDocument = {
      document_id: 'doc-1',
      title: 'Test Document',
      type: 'pdf',
      status: 'indexed',
    };

    render(<DocumentViewer document={mockDocument} />);

    expect(screen.getByText('Document Preview')).toBeInTheDocument();
  });

  it('should display message when content is not available', () => {
    const mockDocument = {
      document_id: 'doc-1',
      title: 'Test Document',
      type: 'pdf',
      status: 'indexed',
    };

    render(<DocumentViewer document={mockDocument} />);

    expect(screen.getByText('Document content not available')).toBeInTheDocument();
  });

  it('should render text content', () => {
    const mockDocument = {
      document_id: 'doc-1',
      title: 'Test Document',
      type: 'text/plain',
      content: 'This is test content',
      status: 'indexed',
    };

    render(<DocumentViewer document={mockDocument} />);

    expect(screen.getByText('This is test content')).toBeInTheDocument();
  });

  it('should render PDF viewer for PDF documents', () => {
    const mockDocument = {
      document_id: 'doc-1',
      title: 'Test PDF',
      type: 'application/pdf',
      content: 'base64encodedcontent',
      status: 'indexed',
    };

    render(<DocumentViewer document={mockDocument} />);

    const iframe = screen.getByTitle('Test PDF');
    expect(iframe).toBeInTheDocument();
    expect(iframe.tagName).toBe('IFRAME');
  });

  it('should render image viewer for image documents', () => {
    const mockDocument = {
      document_id: 'doc-1',
      title: 'Test Image',
      type: 'image/jpeg',
      content: 'base64encodedcontent',
      status: 'indexed',
    };

    render(<DocumentViewer document={mockDocument} />);

    const img = screen.getByAltText('Test Image');
    expect(img).toBeInTheDocument();
    expect(img.tagName).toBe('IMG');
  });
});
