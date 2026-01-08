"use client";

import React from 'react';

interface Document {
  document_id: string;
  title: string;
  type: string;
  created_at: string;
  updated_at?: string;
  status: string;
  size?: number;
  metadata?: Record<string, any>;
  versions?: Array<{
    version: string;
    created_at: string;
    notes?: string;
  }>;
}

interface DocumentMetadataProps {
  document: Document;
}

export default function DocumentMetadata({ document }: DocumentMetadataProps) {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };
  
  const formatSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };
  
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'indexed':
        return <span className="px-1 py-0.5 bg-green-100 text-green-800 text-xs rounded">✅ Indexed</span>;
      case 'processing':
        return <span className="px-1 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">⏳ Processing</span>;
      case 'error':
        return <span className="px-1 py-0.5 bg-red-100 text-red-800 text-xs rounded">❌ Error</span>;
      default:
        return <span className="px-1 py-0.5 bg-gray-100 text-gray-800 text-xs rounded">{status}</span>;
    }
  };
  
  return (
    <div className="rounded-lg border shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Document Information</h2>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Basic Information */}
        <div>
          <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>Basic Information</h3>
          <div className="space-y-1">
            <div>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Name:</span>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{document.title || document.document_id}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Type:</span>
              <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{document.type || 'Unknown'}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Size:</span>
              <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{formatSize(document.size)}</p>
            </div>
            <div>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Status:</span>
              <div className="mt-1">{getStatusBadge(document.status)}</div>
            </div>
          </div>
        </div>
        
        {/* Dates */}
        <div>
          <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>Dates</h3>
          <div className="space-y-1">
            <div>
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Created:</span>
              <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{formatDate(document.created_at)}</p>
            </div>
            {document.updated_at && (
              <div>
                <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>Updated:</span>
                <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{formatDate(document.updated_at)}</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Version History */}
        {document.versions && document.versions.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>Version History</h3>
            <div className="space-y-1">
              {document.versions.map((version, index) => (
                <div key={index} className="border rounded-md p-1" style={{ borderColor: 'var(--color-border)' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>v{version.version}</span>
                    <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{formatDate(version.created_at)}</span>
                  </div>
                  {version.notes && (
                    <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{version.notes}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Metadata */}
        {document.metadata && Object.keys(document.metadata).length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>Metadata</h3>
            <div className="space-y-1">
              {Object.entries(document.metadata).map(([key, value]) => (
                <div key={key}>
                  <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{key}:</span>
                  <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{String(value)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
