"use client";

import React from 'react';
import { useRouter } from 'next/navigation';

interface QuickActionsProps {
  tenantId: string;
}

export default function QuickActions({ tenantId }: QuickActionsProps) {
  const router = useRouter();
  
  const actions = [
    {
      label: 'Upload Document',
      icon: '📤',
      description: 'Add new documents to your knowledge base',
      onClick: () => router.push('/tenant/documents/upload'),
      color: 'bg-primary hover:bg-primary-dark text-white',
    },
    {
      label: 'View Analytics',
      icon: '📊',
      description: 'View detailed analytics and reports',
      onClick: () => router.push('/tenant/analytics'),
      color: 'bg-secondary hover:bg-secondary-dark text-white',
    },
    {
      label: 'Manage Documents',
      icon: '📄',
      description: 'View and manage all documents',
      onClick: () => router.push('/tenant/documents'),
      color: 'bg-surface hover:bg-gray-50 text-text-primary border border-border',
    },
    {
      label: 'Configuration',
      icon: '⚙️',
      description: 'Configure tenant settings',
      onClick: () => router.push('/tenant/configuration'),
      color: 'bg-surface hover:bg-gray-50 text-text-primary border border-border',
    },
  ];
  
  return (
    <div className="rounded-lg border p-4 shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Quick Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {actions.map((action) => {
          const isPrimary = action.color.includes('bg-primary');
          const isSecondary = action.color.includes('bg-secondary');
          const isSurface = action.color.includes('bg-surface');
          
          let buttonStyle: React.CSSProperties = {};
          if (isPrimary) {
            buttonStyle = { backgroundColor: 'var(--color-primary)', color: 'white' };
          } else if (isSecondary) {
            buttonStyle = { backgroundColor: 'var(--color-secondary)', color: 'white' };
          } else if (isSurface) {
            buttonStyle = { 
              backgroundColor: 'var(--color-surface)', 
              color: 'var(--color-text-primary)',
              borderColor: 'var(--color-border)',
              borderWidth: '1px'
            };
          }
          
          return (
            <button
              key={action.label}
              onClick={action.onClick}
              className="p-4 rounded-md text-left transition-all hover:shadow-md border"
              style={buttonStyle}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-2xl">{action.icon}</span>
                <span className="font-semibold">{action.label}</span>
              </div>
              <p className="text-xs opacity-90">{action.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
