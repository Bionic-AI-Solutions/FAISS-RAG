"use client";

import React from 'react';

interface DocumentActionsProps {
  onUpdate: () => void;
  onDelete: () => void;
  onDownload: () => void;
}

export default function DocumentActions({ onUpdate, onDelete, onDownload }: DocumentActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onUpdate}
        className="px-4 py-2 text-white rounded-md font-medium"
        style={{ backgroundColor: 'var(--color-primary)' }}
      >
        📝 Update
      </button>
      <button
        onClick={onDownload}
        className="px-4 py-2 border rounded-md hover:bg-gray-50 font-medium"
        style={{ borderColor: 'var(--color-border)' }}
      >
        ⬇️ Download
      </button>
      <button
        onClick={onDelete}
        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
      >
        🗑️ Delete
      </button>
    </div>
  );
}
