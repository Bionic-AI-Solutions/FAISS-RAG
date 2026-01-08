"use client";

import React, { useState } from "react";
import { useAuth } from "@/app/contexts/AuthContext";
import { useRole } from "@/app/contexts/RoleContext";
import { useTenant } from "@/app/contexts/TenantContext";

export default function Header() {
  const { user, logout } = useAuth();
  const { role, isUberAdmin } = useRole();
  const { currentTenantName, isInTenantContext, exitTenantContext } = useTenant();
  const [showTenantSwitcher, setShowTenantSwitcher] = useState(false);
  
  return (
    <header className="border-b sticky top-0 z-10" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            RAG Platform Admin
          </h1>
          {role && (
            <span
              className="px-3 py-1 rounded text-sm font-medium"
              style={{
                backgroundColor: isUberAdmin ? 'rgba(156, 39, 176, 0.1)' : 'rgba(33, 150, 243, 0.1)',
                color: isUberAdmin ? 'var(--color-uber-admin)' : 'var(--color-tenant-admin)',
              }}
            >
              {isUberAdmin ? "Uber Admin" : "Tenant Admin"}
            </span>
          )}
          {isInTenantContext && currentTenantName && (
            <div className="flex items-center gap-2 px-3 py-1 rounded" style={{ backgroundColor: 'rgba(255, 193, 7, 0.1)' }}>
              <span className="text-sm" style={{ color: 'var(--color-context-switch)' }}>
                🔧 Viewing: {currentTenantName}
              </span>
              <button
                onClick={exitTenantContext}
                className="text-xs underline"
                style={{ color: 'var(--color-context-switch)' }}
              >
                Exit
              </button>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {user.email}
            </span>
          )}
          <button
            onClick={logout}
            className="px-4 py-2 rounded text-sm font-medium border"
            style={{
              borderColor: 'var(--color-border)',
              color: 'var(--color-text-primary)',
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
