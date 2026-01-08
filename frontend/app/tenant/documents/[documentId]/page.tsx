"use client";

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '@/app/contexts/AuthContext';
import { useRole } from '@/app/contexts/RoleContext';
import { useTenant } from '@/app/contexts/TenantContext';
import { documentsApi } from '@/app/lib/api-client';
import DocumentViewer from '@/components/documents/DocumentViewer';
import DocumentMetadata from '@/components/documents/DocumentMetadata';
import DocumentActions from '@/components/documents/DocumentActions';
import DocumentUpdateDialog from '@/components/documents/DocumentUpdateDialog';

interface Document {
  document_id: string;
  title: string;
  type: string;
  created_at: string;
  updated_at?: string;
  status: string;
  size?: number;
  content?: string;
  metadata?: Record<string, any>;
  versions?: Array<{
    version: string;
    created_at: string;
    notes?: string;
  }>;
}

export default function DocumentViewerPage() {
  const router = useRouter();
  const params = useParams();
  const documentId = params?.documentId as string;
  
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { isTenantAdmin } = useRole();
  const { currentTenantId } = useTenant();
  
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpdateDialog, setShowUpdateDialog] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  const tenantId = currentTenantId || user?.tenant_id || null;
  
  useEffect(() => {
    // Redirect if not authenticated or not tenant admin
    if (!authLoading && (!isAuthenticated || !isTenantAdmin)) {
      router.push('/auth/login');
      return;
    }
    
    // Load document if authenticated and tenant ID available
    if (isAuthenticated && tenantId && documentId) {
      loadDocument();
    }
  }, [isAuthenticated, authLoading, isTenantAdmin, tenantId, documentId, router]);
  
  const loadDocument = async () => {
    if (!tenantId || !documentId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const doc = await documentsApi.getDocument(documentId, tenantId, user);
      setDocument(doc);
    } catch (err) {
      console.error('Failed to load document:', err);
      setError(err instanceof Error ? err.message : 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };
  
  const handleUpdate = async (file: File, versionNotes?: string) => {
    if (!tenantId || !documentId) return;
    
    try {
      // Upload new version
      await documentsApi.uploadDocument(tenantId, file, file.name, user);
      
      // Reload document to get updated version
      await loadDocument();
      setShowUpdateDialog(false);
    } catch (err) {
      console.error('Failed to update document:', err);
      alert(err instanceof Error ? err.message : 'Failed to update document');
    }
  };
  
  const handleDelete = async () => {
    if (!tenantId || !documentId) return;
    
    try {
      await documentsApi.deleteDocument(documentId, tenantId, user);
      router.push('/tenant/documents');
    } catch (err) {
      console.error('Failed to delete document:', err);
      alert(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };
  
  const handleDownload = () => {
    if (!document?.content) {
      alert('Document content not available for download');
      return;
    }
    
    // Create a blob and download
    const blob = new Blob([document.content], { type: document.type || 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = document.title || `document-${documentId}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="" style={{ color: 'var(--color-text-secondary)' }}>Loading document...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4">
        <div className="border rounded-md p-4" style={{ backgroundColor: 'rgba(244, 67, 54, 0.1)', borderColor: 'var(--color-error)' }}>
          <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-error)' }}>Error</h2>
          <p className="text-base mb-4" style={{ color: 'var(--color-text-secondary)' }}>{error}</p>
          <button
            onClick={loadDocument}
            className="mt-4 px-4 py-2 text-white rounded-md"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  if (!document) {
    return (
      <div className="p-4">
        <p className="" style={{ color: 'var(--color-text-secondary)' }}>Document not found</p>
      </div>
    );
  }
  
  return (
    <div className="p-4 space-y-4">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.push('/tenant/documents')}
            className="hover:underline mb-2"
            style={{ color: 'var(--color-primary)' }}
          >
            ← Back to Documents
          </button>
          <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>{document.title || documentId}</h1>
        </div>
        <DocumentActions
          onUpdate={() => setShowUpdateDialog(true)}
          onDelete={() => setShowDeleteConfirm(true)}
          onDownload={handleDownload}
        />
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Document Viewer (2/3 width) */}
        <div className="lg:col-span-2">
          <DocumentViewer document={document} />
        </div>
        
        {/* Metadata Panel (1/3 width) */}
        <div className="lg:col-span-1">
          <DocumentMetadata document={document} />
        </div>
      </div>
      
      {/* Update Dialog */}
      {showUpdateDialog && tenantId && (
        <DocumentUpdateDialog
          documentId={documentId}
          currentTitle={document.title}
          onUpdate={handleUpdate}
          onCancel={() => setShowUpdateDialog(false)}
        />
      )}
      
      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="rounded-lg border p-4 max-w-md w-full" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
            <h2 className="text-2xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>Delete Document</h2>
            <p className="text-base mb-4" style={{ color: 'var(--color-text-secondary)' }}>
              Are you sure you want to delete <strong>{document.title || documentId}</strong>?
              This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
                style={{ borderColor: 'var(--color-border)' }}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
