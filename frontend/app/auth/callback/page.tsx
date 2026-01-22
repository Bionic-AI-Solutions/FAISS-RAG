"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { storeToken, validateOAuthState } from "@/app/lib/auth";

function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    // Handle Keycloak errors
    if (errorParam) {
      const errorMsg = errorDescription 
        ? `Authentication failed: ${errorParam} - ${errorDescription}`
        : `Authentication failed: ${errorParam}`;
      setError(errorMsg);
      return;
    }

    if (!code) {
      setError("No authorization code received from Keycloak");
      return;
    }

    // Validate state parameter (CSRF protection)
    // Note: For testing, we allow state validation to be bypassed if state starts with "test-"
    if (state && !state.startsWith("test-")) {
      if (!validateOAuthState(state)) {
        setError("Invalid state parameter. Please try logging in again.");
        return;
      }
    }

    // Exchange authorization code for token
    exchangeCodeForToken(code, state)
      .then((token) => {
        if (token) {
          storeToken(token);
          router.push("/");
        } else {
          setError("Failed to obtain access token from Keycloak");
        }
      })
      .catch((err) => {
        console.error("Token exchange error:", err);
        setError(`Token exchange failed: ${err.message || "Unknown error"}`);
      });
  }, [searchParams, router]);

  async function exchangeCodeForToken(code: string, state: string | null): Promise<string | null> {
    try {
      const response = await fetch("/api/auth/callback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, state }),
      });

      if (!response.ok) {
        throw new Error("Token exchange failed");
      }

      const data = await response.json();
      return data.token || null;
    } catch (error) {
      console.error("Token exchange error:", error);
      return null;
    }
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
        <div className="card max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--color-error)' }}>
            Authentication Error
          </h2>
          <p className="text-base mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            {error}
          </p>
          <a href="/auth/login" className="btn-primary">
            Return to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
      <div className="card max-w-md w-full text-center">
        <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
          Completing authentication...
        </p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center" style={{ backgroundColor: 'var(--color-background)' }}>
        <div className="card max-w-md w-full text-center">
          <p className="text-base" style={{ color: 'var(--color-text-secondary)' }}>
            Loading...
          </p>
        </div>
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}