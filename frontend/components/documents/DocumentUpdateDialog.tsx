"use client";

import React, { useState, useRef } from 'react';
import { documentsApi } from '@/app/lib/api-client';

interface DocumentUpdateDialogProps {
  documentId: string;
  currentTitle: string;
  onUpdate: (file: File, versionNotes?: string) => void;
  onCancel: () => void;
}

export default function DocumentUpdateDialog({
  documentId,
  currentTitle,
  onUpdate,
  onCancel,
}: DocumentUpdateDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [versionNotes, setVersionNotes] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file
      const maxSize = 50 * 1024 * 1024; // 50MB
      if (selectedFile.size > maxSize) {
        alert(`File too large: ${(selectedFile.size / (1024 * 1024)).toFixed(2)}MB (max 50MB)`);
        return;
      }
      setFile(selectedFile);
    }
  };
  
  const handleSubmit = async () => {
    if (!file) {
      alert('Please select a file to upload');
      return;
    }
    
    setIsUploading(true);
    try {
      await onUpdate(file, versionNotes);
    } catch (error) {
      console.error('Update failed:', error);
      alert(error instanceof Error ? error.message : 'Failed to update document');
    } finally {
      setIsUploading(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="rounded-lg border p-4 max-w-lg w-full" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Update Document</h2>
          <button
            onClick={onCancel}
            className="hover:opacity-70"
            style={{ color: 'var(--color-text-primary)' }}
          >
            ✕
          </button>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              Current Document
            </label>
            <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{currentTitle}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              New File
            </label>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="w-full px-2 py-1 border rounded-md focus:outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)' }}
            />
            {file && (
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                Selected: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              Version Notes (Optional)
            </label>
            <textarea
              value={versionNotes}
              onChange={(e) => setVersionNotes(e.target.value)}
              placeholder="Describe changes in this version..."
              className="w-full px-2 py-1 border rounded-md focus:outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)' }}
              rows={3}
            />
          </div>
        </div>
        
        <div className="mt-4 flex items-center justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={isUploading}
            className="px-4 py-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
            style={{ borderColor: 'var(--color-border)' }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!file || isUploading}
            className="px-4 py-2 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            {isUploading ? 'Uploading...' : 'Update Document'}
          </button>
        </div>
      </div>
    </div>
  );
}
