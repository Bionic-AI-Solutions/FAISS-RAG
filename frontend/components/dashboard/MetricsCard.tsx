"use client";

import React from 'react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export default function MetricsCard({ title, value, subtitle, icon, trend }: MetricsCardProps) {
  return (
    <div className="rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>{title}</h3>
          <div className="flex items-baseline gap-1">
            {icon && <span className="text-lg">{icon}</span>}
            <span className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </span>
          </div>
        </div>
        {trend && (
          <div className={`text-xs font-medium ${
            trend.isPositive ? 'text-green-600' : 'text-red-600'
          }`}>
            {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
          </div>
        )}
      </div>
      {subtitle && (
        <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{subtitle}</p>
      )}
    </div>
  );
}
