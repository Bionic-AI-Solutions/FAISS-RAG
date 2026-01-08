"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/contexts/AuthContext';
import { useRole } from '@/app/contexts/RoleContext';
import { useTenant } from '@/app/contexts/TenantContext';
import { documentsApi } from '@/app/lib/api-client';
import DocumentList from '@/components/documents/DocumentList';
import DocumentUpload from '@/components/documents/DocumentUpload';

interface Document {
  document_id: string;
  title: string;
  type: string;
  created_at: string;
  status: string;
  size?: number;
}

export default function DocumentsPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { isTenantAdmin } = useRole();
  const { currentTenantId } = useTenant();
  const router = useRouter();
  
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  const pageSize = 50;
  const tenantId = currentTenantId || user?.tenant_id || null;
  
  useEffect(() => {
    // Redirect if not authenticated or not tenant admin
    if (!authLoading && (!isAuthenticated || !isTenantAdmin)) {
      router.push('/auth/login');
      return;
    }
    
    // Load documents if authenticated and tenant ID available
    if (isAuthenticated && tenantId) {
      loadDocuments();
    }
  }, [isAuthenticated, authLoading, isTenantAdmin, tenantId, page, router]);
  
  const loadDocuments = async () => {
    if (!tenantId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await documentsApi.listDocuments(tenantId, page, pageSize, user);
      setDocuments(response.documents || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };
  
  const handleUploadSuccess = () => {
    setShowUpload(false);
    loadDocuments(); // Reload documents after upload
  };
  
  const handleDelete = async (documentId: string) => {
    if (!tenantId) return;
    
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      await documentsApi.deleteDocument(documentId, tenantId, user);
      await loadDocuments(); // Reload documents after deletion
    } catch (err) {
      console.error('Failed to delete document:', err);
      alert(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };
  
  // Filter documents based on search query, type, and status
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = !searchQuery || 
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.document_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || doc.type === filterType;
    const matchesStatus = filterStatus === 'all' || doc.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesSearch && matchesType && matchesStatus;
  });
  
  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div style={{ color: 'var(--color-text-secondary)' }}>Loading documents...</div>
      </div>
    );
  }
  
  return (
    <div className="p-4 space-y-4">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Document Management</h1>
          <p className="text-base mt-2" style={{ color: 'var(--color-text-secondary)' }}>
            Manage your knowledge base documents
          </p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="px-4 py-2 rounded text-white font-medium"
          style={{ backgroundColor: 'var(--color-primary)' }}
        >
          📤 Upload Document
        </button>
      </div>
      
      {/* Upload Dialog */}
      {showUpload && tenantId && (
        <DocumentUpload
          tenantId={tenantId}
          onSuccess={handleUploadSuccess}
          onCancel={() => setShowUpload(false)}
        />
      )}
      
      {/* Search and Filters */}
      <div className="rounded-lg border p-4" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              Search
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full px-2 py-1 border rounded-md focus:outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)' }}
            />
          </div>
          
          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              Type
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-2 py-1 border rounded-md focus:outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <option value="all">All Types</option>
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
              <option value="txt">TXT</option>
              <option value="image">Image</option>
            </select>
          </div>
          
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-2 py-1 border rounded-md focus:outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <option value="all">All Statuses</option>
              <option value="indexed">Indexed</option>
              <option value="processing">Processing</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="border rounded-md p-4" style={{ backgroundColor: 'rgba(244, 67, 54, 0.1)', borderColor: 'var(--color-error)' }}>
          <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-error)' }}>Error</h2>
          <p className="text-base mb-4" style={{ color: 'var(--color-text-secondary)' }}>{error}</p>
          <button
            onClick={loadDocuments}
            className="mt-4 px-4 py-2 rounded text-white font-medium"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            Retry
          </button>
        </div>
      )}
      
      {/* Document List */}
      <DocumentList
        documents={filteredDocuments}
        total={total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onView={(documentId) => router.push(`/tenant/documents/${documentId}`)}
        onDelete={handleDelete}
      />
    </div>
  );
}
