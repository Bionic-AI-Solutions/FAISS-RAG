"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useAuth } from "./AuthContext";
import { useRole } from "./RoleContext";

interface TenantContextType {
  currentTenantId: string | null;
  currentTenantName: string | null;
  switchTenant: (tenantId: string, tenantName: string) => void;
  exitTenantContext: () => void;
  isInTenantContext: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const { isUberAdmin } = useRole();
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(null);
  const [currentTenantName, setCurrentTenantName] = useState<string | null>(null);
  
  // Initialize tenant context from user or session storage
  useEffect(() => {
    if (user?.tenant_id && !isUberAdmin) {
      // Tenant Admin always has their tenant_id
      setCurrentTenantId(user.tenant_id);
      // Tenant name would come from API if needed
      setCurrentTenantName(null);
    } else if (isUberAdmin) {
      // Uber Admin can switch contexts - check session storage
      const storedTenantId = sessionStorage.getItem("current_tenant_id");
      const storedTenantName = sessionStorage.getItem("current_tenant_name");
      if (storedTenantId && storedTenantName) {
        setCurrentTenantId(storedTenantId);
        setCurrentTenantName(storedTenantName);
      }
    }
  }, [user, isUberAdmin]);
  
  const switchTenant = (tenantId: string, tenantName: string) => {
    if (!isUberAdmin) {
      console.warn("Only Uber Admin can switch tenant context");
      return;
    }
    setCurrentTenantId(tenantId);
    setCurrentTenantName(tenantName);
    sessionStorage.setItem("current_tenant_id", tenantId);
    sessionStorage.setItem("current_tenant_name", tenantName);
  };
  
  const exitTenantContext = () => {
    if (!isUberAdmin) {
      console.warn("Only Uber Admin can exit tenant context");
      return;
    }
    setCurrentTenantId(null);
    setCurrentTenantName(null);
    sessionStorage.removeItem("current_tenant_id");
    sessionStorage.removeItem("current_tenant_name");
  };
  
  const isInTenantContext = isUberAdmin && currentTenantId !== null;
  
  return (
    <TenantContext.Provider
      value={{
        currentTenantId,
        currentTenantName,
        switchTenant,
        exitTenantContext,
        isInTenantContext,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error("useTenant must be used within a TenantProvider");
  }
  return context;
}
