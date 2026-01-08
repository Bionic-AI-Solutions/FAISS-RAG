"use client";

import React from 'react';

interface HealthStatusProps {
  status: string;
  components: Record<string, { status: boolean; message: string }>;
}

export default function HealthStatus({ status, components }: HealthStatusProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'degraded':
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'unhealthy':
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return '✅';
      case 'degraded':
      case 'warning':
        return '⚠️';
      case 'unhealthy':
      case 'error':
        return '❌';
      default:
        return '❓';
    }
  };
  
  return (
    <div className="rounded-lg border p-4 shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>Health Status</h2>
        <div className={`px-4 py-1 rounded-md border font-medium ${getStatusColor(status)}`}>
          <span className="mr-1">{getStatusIcon(status)}</span>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        {Object.entries(components).map(([component, { status: compStatus, message }]) => (
          <div
            key={component}
            className={`p-2 rounded-md border ${
              compStatus
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-center gap-1 mb-1">
              <span>{compStatus ? '✅' : '❌'}</span>
              <span className="font-medium text-sm capitalize">{component}</span>
            </div>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
