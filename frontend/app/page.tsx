"use client";

import { useAuth } from "./contexts/AuthContext";
import { useRole } from "./contexts/RoleContext";
import AppShell from "@/components/AppShell";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const { isUberAdmin, isTenantAdmin } = useRole();
  const router = useRouter();
  
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      if (isUberAdmin) {
        router.push("/platform/dashboard");
      } else if (isTenantAdmin) {
        router.push("/tenant/dashboard");
      }
    }
  }, [isAuthenticated, isLoading, isUberAdmin, isTenantAdmin, router]);
  
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
        <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>Loading...</p>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return null; // AuthProvider will redirect to login
  }
  
  return (
    <AppShell>
      <div className="max-w-5xl">
        <h1 className="text-3xl font-bold mb-4" style={{ color: 'var(--color-primary)' }}>
          RAG Platform Admin UI
        </h1>
        <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
          Welcome to the Admin Interface
        </p>
      </div>
    </AppShell>
  );
}
