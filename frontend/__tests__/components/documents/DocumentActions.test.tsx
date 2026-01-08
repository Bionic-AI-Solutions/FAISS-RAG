/**
 * Unit tests for DocumentActions component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentActions from '@/components/documents/DocumentActions';

describe('DocumentActions', () => {
  it('should render all action buttons', () => {
    const mockUpdate = vi.fn();
    const mockDelete = vi.fn();
    const mockDownload = vi.fn();

    render(
      <DocumentActions
        onUpdate={mockUpdate}
        onDelete={mockDelete}
        onDownload={mockDownload}
      />
    );

    expect(screen.getByText('📝 Update')).toBeInTheDocument();
    expect(screen.getByText('⬇️ Download')).toBeInTheDocument();
    expect(screen.getByText('🗑️ Delete')).toBeInTheDocument();
  });

  it('should call onUpdate when Update button is clicked', async () => {
    const user = userEvent.setup();
    const mockUpdate = vi.fn();
    const mockDelete = vi.fn();
    const mockDownload = vi.fn();

    render(
      <DocumentActions
        onUpdate={mockUpdate}
        onDelete={mockDelete}
        onDownload={mockDownload}
      />
    );

    const updateButton = screen.getByText('📝 Update');
    await user.click(updateButton);

    expect(mockUpdate).toHaveBeenCalledTimes(1);
  });

  it('should call onDelete when Delete button is clicked', async () => {
    const user = userEvent.setup();
    const mockUpdate = vi.fn();
    const mockDelete = vi.fn();
    const mockDownload = vi.fn();

    render(
      <DocumentActions
        onUpdate={mockUpdate}
        onDelete={mockDelete}
        onDownload={mockDownload}
      />
    );

    const deleteButton = screen.getByText('🗑️ Delete');
    await user.click(deleteButton);

    expect(mockDelete).toHaveBeenCalledTimes(1);
  });

  it('should call onDownload when Download button is clicked', async () => {
    const user = userEvent.setup();
    const mockUpdate = vi.fn();
    const mockDelete = vi.fn();
    const mockDownload = vi.fn();

    render(
      <DocumentActions
        onUpdate={mockUpdate}
        onDelete={mockDelete}
        onDownload={mockDownload}
      />
    );

    const downloadButton = screen.getByText('⬇️ Download');
    await user.click(downloadButton);

    expect(mockDownload).toHaveBeenCalledTimes(1);
  });
});
