"use client";

import React from "react";
import { usePathname } from "next/navigation";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Breadcrumbs from "./Breadcrumbs";

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * AppShell Component
 *
 * Base layout component providing consistent page structure.
 * This is the foundation for all Admin UI pages.
 *
 * Design Reference: admin-ui-wireframes.md (Base Layout section)
 */
export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  // Check if we're on an auth page (login, callback, etc.)
  const isAuthPage = pathname?.startsWith('/auth');

  if (isAuthPage) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--color-background)' }}>
        {children}
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--color-background)' }}>
      <Header />

      <div className="flex">
        <Sidebar />

        {/* Main content area */}
        <main className="flex-1 p-6">
          <Breadcrumbs />

          {children}
        </main>
      </div>
    </div>
  );
}
