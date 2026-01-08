/**
 * Unit tests for DocumentUpdateDialog component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentUpdateDialog from '@/components/documents/DocumentUpdateDialog';

// Mock window.alert
const mockAlert = vi.fn();
global.alert = mockAlert;

describe('DocumentUpdateDialog', () => {
  const mockOnUpdate = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockAlert.mockClear();
  });

  it('should render dialog with current document title', () => {
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getAllByText('Update Document').length).toBeGreaterThan(0);
    expect(screen.getByText('Test Document')).toBeInTheDocument();
  });

  it('should call onCancel when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    const closeButton = screen.getByText('✕');
    await user.click(closeButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should call onCancel when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('should disable Update button when no file is selected', () => {
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    // Find the button by role and text
    const updateButton = screen.getByRole('button', { name: /Update Document/i });
    expect(updateButton).toBeDisabled();
  });

  it('should show file input', () => {
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput?.getAttribute('type')).toBe('file');
  });

  it('should show version notes textarea', () => {
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByPlaceholderText('Describe changes in this version...');
    expect(textarea).toBeInTheDocument();
  });

  it('should allow entering version notes', async () => {
    const user = userEvent.setup();
    render(
      <DocumentUpdateDialog
        documentId="doc-1"
        currentTitle="Test Document"
        onUpdate={mockOnUpdate}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByPlaceholderText('Describe changes in this version...');
    await user.type(textarea, 'Updated content');

    expect(textarea).toHaveValue('Updated content');
  });
});
