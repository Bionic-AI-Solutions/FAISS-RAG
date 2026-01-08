"use client";

import React from 'react';
import { useRouter } from 'next/navigation';

interface Document {
  document_id: string;
  title: string;
  type: string;
  created_at: string;
  status: string;
}

interface RecentDocumentsProps {
  documents: Document[];
}

export default function RecentDocuments({ documents }: RecentDocumentsProps) {
  const router = useRouter();
  
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'indexed':
        return <span className="px-xs py-0.5 bg-green-100 text-green-800 text-xs rounded">✅ Indexed</span>;
      case 'processing':
        return <span className="px-xs py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded">⏳ Processing</span>;
      case 'error':
        return <span className="px-xs py-0.5 bg-red-100 text-red-800 text-xs rounded">❌ Error</span>;
      default:
        return <span className="px-xs py-0.5 bg-gray-100 text-gray-800 text-xs rounded">{status}</span>;
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
  
  return (
    <div className="rounded-lg border p-4 shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Recent Documents</h2>
        <button
          onClick={() => router.push('/tenant/documents')}
          className="text-sm hover:underline"
          style={{ color: 'var(--color-primary)' }}
        >
          View All
        </button>
      </div>
      
      {documents.length === 0 ? (
        <div className="text-center py-8" style={{ color: 'var(--color-text-secondary)' }}>
          <p className="mb-2">No documents yet</p>
          <button
            onClick={() => router.push('/tenant/documents/upload')}
            className="px-4 py-2 rounded text-white font-medium"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            Upload Your First Document
          </button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--color-border)' }}>
                <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Name</th>
                <th className="text-left py-2 px-2 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Type</th>
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
                      onClick={() => router.push(`/tenant/documents/${doc.document_id}`)}
                      className="hover:underline font-medium"
                      style={{ color: 'var(--color-primary)' }}
                    >
                      {doc.title || doc.document_id}
                    </button>
                  </td>
                  <td className="py-2 px-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{doc.type || 'Unknown'}</td>
                  <td className="py-2 px-2 text-sm" style={{ color: 'var(--color-text-secondary)' }}>{formatDate(doc.created_at)}</td>
                  <td className="py-2 px-2">{getStatusBadge(doc.status)}</td>
                  <td className="py-2 px-2">
                    <button
                      onClick={() => router.push(`/tenant/documents/${doc.document_id}`)}
                      className="text-sm hover:underline"
                      style={{ color: 'var(--color-primary)' }}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
