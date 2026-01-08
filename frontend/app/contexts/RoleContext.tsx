"use client";

import React, { createContext, useContext } from "react";
import { useAuth } from "./AuthContext";
import { UserRole, getRolePermissions, RolePermissions } from "@/app/lib/rbac";

interface RoleContextType {
  role: UserRole | null;
  permissions: RolePermissions;
  isUberAdmin: boolean;
  isTenantAdmin: boolean;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  
  const role = (user?.role as UserRole) || null;
  const permissions = role ? getRolePermissions(role) : {
    canViewPlatformDashboard: false,
    canManageTenants: false,
    canViewTenantDashboard: false,
    canManageDocuments: false,
    canManageConfiguration: false,
    canViewAnalytics: false,
    canManageUsers: false,
    canSwitchTenantContext: false,
  };
  
  const isUberAdmin = role === "uber_admin";
  const isTenantAdmin = role === "tenant_admin";
  
  return (
    <RoleContext.Provider
      value={{
        role,
        permissions,
        isUberAdmin,
        isTenantAdmin,
      }}
    >
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = useContext(RoleContext);
  if (context === undefined) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
