"use client";

import React from 'react';

interface Document {
  document_id: string;
  title: string;
  type: string;
  content?: string;
  status: string;
}

interface DocumentViewerProps {
  document: Document;
}

export default function DocumentViewer({ document }: DocumentViewerProps) {
  const renderContent = () => {
    if (!document.content) {
      return (
        <div className="flex items-center justify-center h-64 " style={{ color: 'var(--color-text-secondary)' }}>
          <p>Document content not available</p>
        </div>
      );
    }
    
    // Determine document type and render accordingly
    const contentType = document.type?.toLowerCase() || '';
    
    if (contentType.includes('pdf')) {
      // PDF viewer - would use a PDF library in production
      return (
        <div className="bg-gray-100 rounded-lg p-4">
          <iframe
            src={`data:application/pdf;base64,${btoa(document.content)}`}
            className="w-full h-[600px] border-0" style={{ borderColor: 'var(--color-border)' }}
            title={document.title}
          />
        </div>
      );
    }
    
    if (contentType.includes('image')) {
      // Image viewer
      return (
        <div className="bg-gray-100 rounded-lg p-4 flex items-center justify-center">
          <img
            src={`data:${document.type};base64,${btoa(document.content)}`}
            alt={document.title}
            className="max-w-full max-h-[600px] object-contain"
          />
        </div>
      );
    }
    
    // Text viewer (default)
    return (
      <div className="rounded-lg border p-4" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
        <pre className="whitespace-pre-wrap text-sm font-mono overflow-auto max-h-[600px]" style={{ color: 'var(--color-text-primary)' }}>
          {document.content}
        </pre>
      </div>
    );
  };
  
  return (
    <div className="rounded-lg border shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Document Preview</h2>
      </div>
      <div className="p-4">
        {renderContent()}
      </div>
    </div>
  );
}
