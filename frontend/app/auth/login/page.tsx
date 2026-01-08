"use client";

import { useAuth } from "@/app/contexts/AuthContext";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { devLogin } from "@/app/lib/dev-auth";

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/");
    }
  }, [isAuthenticated, router]);
  
  const handleDevLogin = (role: "uber_admin" | "tenant_admin") => {
    devLogin(role);
  };
  
  return (
    <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
      <div className="card max-w-md w-full">
        <h1 className="text-3xl font-bold mb-6 text-center" style={{ color: 'var(--color-text-primary)' }}>
          RAG Platform Admin
        </h1>
        <p className="text-base mb-8 text-center" style={{ color: 'var(--color-text-secondary)' }}>
          Sign in to access the admin interface
        </p>
        <button
          onClick={login}
          className="btn-primary w-full mb-4"
        >
          Sign in with OAuth 2.0
        </button>
        
        {process.env.NODE_ENV === "development" && (
          <div className="mt-6 pt-6 border-t" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-sm mb-4 text-center" style={{ color: 'var(--color-text-secondary)' }}>
              Development Mode
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => handleDevLogin("tenant_admin")}
                className="btn-secondary flex-1 text-sm"
              >
                Login as Tenant Admin
              </button>
              <button
                onClick={() => handleDevLogin("uber_admin")}
                className="btn-secondary flex-1 text-sm"
              >
                Login as Uber Admin
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
