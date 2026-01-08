"use client";

import React from 'react';

interface Document {
  document_id: string;
  title: string;
  type: string;
  created_at: string;
  status: string;
  size?: number;
}

interface DocumentListProps {
  documents: Document[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onView: (documentId: string) => void;
  onDelete: (documentId: string) => void;
}

export default function DocumentList({
  documents,
  total,
  page,
  pageSize,
  onPageChange,
  onView,
  onDelete,
}: DocumentListProps) {
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
  
  const totalPages = Math.ceil(total / pageSize);
  
  return (
    <div className="rounded-lg border shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            Documents ({total})
          </h2>
        </div>
      </div>
      
      {documents.length === 0 ? (
        <div className="text-center py-8" style={{ color: 'var(--color-text-secondary)' }}>
          <p className="mb-2">No documents found</p>
          <p className="text-sm">Upload your first document to get started</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50" style={{ borderColor: 'var(--color-border)' }}>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Name</th>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Type</th>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Size</th>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Date</th>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Status</th>
                  <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="border-b hover:bg-gray-50" style={{ borderColor: 'var(--color-border)' }}>
                    <td className="py-2 px-2">
                      <button
                        onClick={() => onView(doc.document_id)}
                        className="hover:underline font-medium"
                        style={{ color: 'var(--color-primary)' }}
                      >
                        {doc.title || doc.document_id}
                      </button>
                    </td>
                    <td className="py-2 px-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{doc.type || 'Unknown'}</td>
                    <td className="py-2 px-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{formatSize(doc.size)}</td>
                    <td className="py-2 px-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{formatDate(doc.created_at)}</td>
                    <td className="py-2 px-2">{getStatusBadge(doc.status)}</td>
                    <td className="py-2 px-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => onView(doc.document_id)}
                          className="text-sm hover:underline"
                          style={{ color: 'var(--color-primary)' }}
                        >
                          View
                        </button>
                        <button
                          onClick={() => onDelete(doc.document_id)}
                          className="text-sm text-red-600 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-4 border-t flex items-center justify-between" style={{ borderColor: 'var(--color-border)' }}>
              <div className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} documents
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onPageChange(page - 1)}
                  disabled={page === 1}
                  className="px-2 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  Previous
                </button>
                <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => onPageChange(page + 1)}
                  disabled={page >= totalPages}
                  className="px-2 py-1 border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  style={{ borderColor: 'var(--color-border)' }}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
