"use client";

import React, { useState, useRef } from 'react';
import { documentsApi } from '@/app/lib/api-client';

interface DocumentUploadProps {
  tenantId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'indexing' | 'complete' | 'error';
  error?: string;
}

export default function DocumentUpload({ tenantId, onSuccess, onCancel }: DocumentUploadProps) {
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    'application/msword', // .doc
    'text/plain',
    'image/jpeg',
    'image/png',
    'image/gif',
  ];
  
  const validateFile = (file: File): string | null => {
    // Check file type
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(pdf|docx?|txt|jpg|jpeg|png|gif)$/i)) {
      return `File type not supported: ${file.type || 'unknown'}`;
    }
    
    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return `File too large: ${(file.size / (1024 * 1024)).toFixed(2)}MB (max 50MB)`;
    }
    
    return null;
  };
  
  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;
    
    const newFiles: FileWithProgress[] = [];
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const error = validateFile(file);
      
      newFiles.push({
        file,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined,
      });
    }
    
    setFiles((prev) => [...prev, ...newFiles]);
  };
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };
  
  const handleUpload = async () => {
    const pendingFiles = files.filter((f) => f.status === 'pending' && !f.error);
    
    if (pendingFiles.length === 0) {
      alert('No valid files to upload');
      return;
    }
    
    // Upload files sequentially
    for (const fileWithProgress of pendingFiles) {
      try {
        // Update status to uploading
        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileWithProgress.file
              ? { ...f, status: 'uploading', progress: 10 }
              : f
          )
        );
        
        // Upload file
        const result = await documentsApi.uploadDocument(
          tenantId,
          fileWithProgress.file,
          fileWithProgress.file.name,
          null // user parameter not needed here, handled by auth token
        );
        
        // Update status to processing
        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileWithProgress.file
              ? { ...f, status: 'processing', progress: 50 }
              : f
          )
        );
        
        // Simulate processing and indexing
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.file === fileWithProgress.file
                ? { ...f, status: 'indexing', progress: 75 }
                : f
            )
          );
          
          setTimeout(() => {
            setFiles((prev) =>
              prev.map((f) =>
                f.file === fileWithProgress.file
                  ? { ...f, status: 'complete', progress: 100 }
                  : f
              )
            );
          }, 1000);
        }, 1000);
      } catch (error) {
        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileWithProgress.file
              ? {
                  ...f,
                  status: 'error',
                  error: error instanceof Error ? error.message : 'Upload failed',
                }
              : f
          )
        );
      }
    }
    
    // Call onSuccess after all files are processed
    setTimeout(() => {
      const allComplete = files.every((f) => f.status === 'complete' || f.status === 'error');
      if (allComplete) {
        onSuccess();
      }
    }, 3000);
  };
  
  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return '✅';
      case 'processing':
      case 'indexing':
        return '⏳';
      case 'error':
        return '❌';
      default:
        return '📄';
    }
  };
  
  return (
    <div className="rounded-lg border p-4 shadow-lg" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Upload Documents</h2>
        <button
          onClick={onCancel}
          className="hover:opacity-70"
          style={{ color: 'var(--color-text-primary)' }}
        >
          ✕
        </button>
      </div>
      
      {/* Drag and Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'bg-blue-50'
            : 'hover:bg-gray-50'
        }`}
        style={{
          borderColor: isDragging ? 'var(--color-primary)' : 'var(--color-border)',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif"
          onChange={(e) => handleFileSelect(e.target.files)}
          className="hidden"
        />
        <div className="space-y-2">
          <div className="text-4xl">📤</div>
          <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
            Drag and drop files here, or{' '}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="hover:underline"
              style={{ color: 'var(--color-primary)' }}
            >
              browse files
            </button>
          </p>
          <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
            Supported: PDF, DOCX, TXT, Images (max 50MB per file)
          </p>
        </div>
      </div>
      
      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Files to Upload</h3>
          {files.map((fileWithProgress, index) => (
            <div
              key={index}
              className="border rounded-md p-2 flex items-center justify-between"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span>{getStatusIcon(fileWithProgress.status)}</span>
                  <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                    {fileWithProgress.file.name}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                    ({(fileWithProgress.file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                {fileWithProgress.error && (
                  <p className="text-xs text-red-600">{fileWithProgress.error}</p>
                )}
                {fileWithProgress.status === 'uploading' ||
                fileWithProgress.status === 'processing' ||
                fileWithProgress.status === 'indexing' ? (
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{ width: `${fileWithProgress.progress}%`, backgroundColor: 'var(--color-primary)' }}
                    />
                  </div>
                ) : null}
              </div>
              {fileWithProgress.status !== 'uploading' &&
                fileWithProgress.status !== 'processing' &&
                fileWithProgress.status !== 'indexing' && (
                  <button
                    onClick={() => removeFile(fileWithProgress.file)}
                    className="text-red-600 hover:text-red-800 ml-2"
                  >
                    Remove
                  </button>
                )}
            </div>
          ))}
        </div>
      )}
      
      {/* Actions */}
      <div className="mt-4 flex items-center justify-end gap-2">
        <button
          onClick={onCancel}
          className="px-4 py-2 border rounded-md hover:bg-gray-50"
          style={{ borderColor: 'var(--color-border)' }}
        >
          Cancel
        </button>
        <button
          onClick={handleUpload}
          disabled={files.filter((f) => f.status === 'pending' && !f.error).length === 0}
          className="px-4 py-2 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          Upload {files.filter((f) => f.status === 'pending' && !f.error).length} File(s)
        </button>
      </div>
    </div>
  );
}
