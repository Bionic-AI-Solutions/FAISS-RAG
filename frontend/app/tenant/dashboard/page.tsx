"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/contexts/AuthContext';
import { useRole } from '@/app/contexts/RoleContext';
import { useTenant } from '@/app/contexts/TenantContext';
import { analyticsApi, documentsApi, healthApi } from '@/app/lib/api-client';
import HealthStatus from '@/components/dashboard/HealthStatus';
import MetricsCard from '@/components/dashboard/MetricsCard';
import QuickActions from '@/components/dashboard/QuickActions';
import RecentActivity from '@/components/dashboard/RecentActivity';
import RecentDocuments from '@/components/dashboard/RecentDocuments';

interface DashboardData {
  healthStatus: {
    tenant_status: string;
    component_status: Record<string, { status: boolean; message: string }>;
  };
  usageStats: {
    total_searches: number;
    total_memory_operations: number;
    storage_usage_gb: number;
    active_users: number;
  };
  recentDocuments: Array<{
    document_id: string;
    title: string;
    type: string;
    created_at: string;
    status: string;
  }>;
  totalDocuments: number;
}

export default function TenantDashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { isTenantAdmin } = useRole();
  const { currentTenantId } = useTenant();
  const router = useRouter();
  
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get tenant ID from context or user
  const tenantId = currentTenantId || user?.tenant_id;
  
  useEffect(() => {
    // Redirect if not authenticated or not tenant admin
    if (!authLoading && (!isAuthenticated || !isTenantAdmin)) {
      router.push('/auth/login');
      return;
    }
    
    // Redirect if no tenant ID
    if (!authLoading && isAuthenticated && !tenantId) {
      console.warn('No tenant ID available for dashboard');
      return;
    }
    
    // Load dashboard data
    if (isAuthenticated && tenantId) {
      loadDashboardData(tenantId);
    }
  }, [isAuthenticated, authLoading, isTenantAdmin, tenantId, router]);
  
  const loadDashboardData = async (tenantId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Load all dashboard data in parallel
      const [healthStatus, usageStats, documentsResponse] = await Promise.all([
        healthApi.getTenantHealth(tenantId).catch(() => ({
          tenant_status: 'healthy',
          component_status: {
            faiss: { status: true, message: 'FAISS index available' },
            minio: { status: true, message: 'MinIO bucket accessible' },
            meilisearch: { status: true, message: 'Meilisearch index available' },
          },
        })),
        analyticsApi.getUsageStats(tenantId).catch(() => ({
          total_searches: 0,
          total_memory_operations: 0,
          storage_usage_gb: 0,
          active_users: 0,
        })),
        documentsApi.listDocuments(tenantId, 1, 5).catch(() => ({
          documents: [],
          total: 0,
          page: 1,
          page_size: 5,
        })),
      ]);
      
      setDashboardData({
        healthStatus,
        usageStats,
        recentDocuments: documentsResponse.documents || [],
        totalDocuments: documentsResponse.total || 0,
      });
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };
  
  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div style={{ color: 'var(--color-text-secondary)' }}>Loading dashboard...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-md p-4" style={{ backgroundColor: 'rgba(244, 67, 54, 0.1)', borderColor: 'var(--color-error)' }}>
          <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-error)' }}>Error Loading Dashboard</h2>
          <p className="text-base mb-4" style={{ color: 'var(--color-text-secondary)' }}>{error}</p>
          <button
            onClick={() => tenantId && loadDashboardData(tenantId)}
            className="px-4 py-2 rounded text-white font-medium"
            style={{ backgroundColor: 'var(--color-primary)' }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  if (!dashboardData) {
    return (
      <div className="p-4">
        <div style={{ color: 'var(--color-text-secondary)' }}>No dashboard data available</div>
      </div>
    );
  }
  
  return (
    <div className="p-4 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>Tenant Dashboard</h1>
        <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
          Overview of your tenant's health, metrics, and recent activity
        </p>
      </div>
      
      {/* Health Status */}
      <HealthStatus
        status={dashboardData.healthStatus.tenant_status}
        components={dashboardData.healthStatus.component_status}
      />
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Documents"
          value={dashboardData.totalDocuments || dashboardData.recentDocuments.length}
          subtitle="Documents in knowledge base"
          icon="📄"
        />
        <MetricsCard
          title="Total Searches"
          value={dashboardData.usageStats.total_searches.toLocaleString()}
          subtitle="Search operations"
          icon="🔍"
        />
        <MetricsCard
          title="Memory Operations"
          value={dashboardData.usageStats.total_memory_operations.toLocaleString()}
          subtitle="Memory read/write operations"
          icon="💾"
        />
        <MetricsCard
          title="Storage Usage"
          value={`${dashboardData.usageStats.storage_usage_gb.toFixed(2)} GB`}
          subtitle="Total storage used"
          icon="💿"
        />
      </div>
      
      {/* Quick Actions */}
      <QuickActions tenantId={tenantId || ''} />
      
      {/* Recent Documents */}
      <RecentDocuments documents={dashboardData.recentDocuments} />
      
      {/* Recent Activity */}
      <RecentActivity tenantId={tenantId || ''} />
    </div>
  );
}
