"use client";

import React, { useEffect, useState } from 'react';
import { analyticsApi } from '@/app/lib/api-client';

interface RecentActivityProps {
  tenantId: string;
}

interface ActivityItem {
  id: string;
  type: 'search' | 'upload' | 'memory' | 'config';
  description: string;
  timestamp: string;
}

export default function RecentActivity({ tenantId }: RecentActivityProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Load recent activity
    // For now, we'll use usage stats to generate activity items
    // In a full implementation, this would call an audit log endpoint
    const loadActivity = async () => {
      try {
        const stats = await analyticsApi.getUsageStats(tenantId);
        
        // Generate mock activity items from stats
        const mockActivities: ActivityItem[] = [];
        
        if (stats.total_searches > 0) {
          mockActivities.push({
            id: '1',
            type: 'search',
            description: `${stats.total_searches} search operations performed`,
            timestamp: new Date().toISOString(),
          });
        }
        
        if (stats.total_memory_operations > 0) {
          mockActivities.push({
            id: '2',
            type: 'memory',
            description: `${stats.total_memory_operations} memory operations performed`,
            timestamp: new Date().toISOString(),
          });
        }
        
        setActivities(mockActivities.slice(0, 5));
      } catch (error) {
        console.error('Failed to load activity:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (tenantId) {
      loadActivity();
    }
  }, [tenantId]);
  
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'search':
        return '🔍';
      case 'upload':
        return '📤';
      case 'memory':
        return '💾';
      case 'config':
        return '⚙️';
      default:
        return '📋';
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return timestamp;
    }
  };
  
  return (
    <div className="rounded-lg border p-4 shadow-sm" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Recent Activity</h2>
      
      {loading ? (
        <div className="text-center py-4" style={{ color: 'var(--color-text-secondary)' }}>Loading activity...</div>
      ) : activities.length === 0 ? (
        <div className="text-center py-4" style={{ color: 'var(--color-text-secondary)' }}>
          <p>No recent activity</p>
        </div>
      ) : (
        <div className="space-y-2">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-2 p-2 rounded-md hover:bg-gray-50"
            >
              <span className="text-lg">{getActivityIcon(activity.type)}</span>
              <div className="flex-1">
                <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{activity.description}</p>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                  {formatTimestamp(activity.timestamp)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
