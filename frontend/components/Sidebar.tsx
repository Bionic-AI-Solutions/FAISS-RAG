"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRole } from "@/app/contexts/RoleContext";

interface NavItem {
  label: string;
  href: string;
  icon?: string;
  permission?: keyof import("@/app/lib/rbac").RolePermissions;
}

export default function Sidebar() {
  const pathname = usePathname();
  const { permissions, isUberAdmin, isTenantAdmin } = useRole();
  
  // Uber Admin navigation items
  const uberAdminNavItems: NavItem[] = [
    { label: "Platform Dashboard", href: "/platform/dashboard", permission: "canViewPlatformDashboard" },
    { label: "Tenant Management", href: "/platform/tenants", permission: "canManageTenants" },
    { label: "Platform Analytics", href: "/platform/analytics", permission: "canViewAnalytics" },
    { label: "Platform Settings", href: "/platform/settings" },
  ];
  
  // Tenant Admin navigation items
  const tenantAdminNavItems: NavItem[] = [
    { label: "Tenant Dashboard", href: "/tenant/dashboard", permission: "canViewTenantDashboard" },
    { label: "Document Management", href: "/tenant/documents", permission: "canManageDocuments" },
    { label: "Configuration", href: "/tenant/configuration", permission: "canManageConfiguration" },
    { label: "Analytics", href: "/tenant/analytics", permission: "canViewAnalytics" },
    { label: "User Management", href: "/tenant/users", permission: "canManageUsers" },
  ];
  
  // Determine which navigation items to show
  const navItems = isUberAdmin ? uberAdminNavItems : tenantAdminNavItems;
  
  // Filter items based on permissions
  const visibleNavItems = navItems.filter((item) => {
    if (!item.permission) return true;
    return permissions[item.permission];
  });
  
  return (
    <aside className="w-64 border-r min-h-[calc(100vh-73px)]" style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
      <nav className="p-4">
        <ul className="space-y-2">
          {visibleNavItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`block px-4 py-2 rounded transition-colors ${
                    isActive
                      ? "font-medium"
                      : "hover:bg-gray-100"
                  }`}
                  style={{
                    color: isActive ? 'var(--color-primary)' : 'var(--color-text-primary)',
                    backgroundColor: isActive ? 'rgba(25, 118, 210, 0.1)' : 'transparent',
                  }}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
