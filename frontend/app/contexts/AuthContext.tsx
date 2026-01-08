"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, AuthState, getToken, removeToken, extractUserFromToken, isTokenExpired, getOAuthUrl } from "@/app/lib/auth";

interface AuthContextType extends AuthState {
  login: () => void;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });
  
  const router = useRouter();
  const pathname = usePathname();
  
  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, []);
  
  // Redirect to login if not authenticated and trying to access protected route
  useEffect(() => {
    if (!authState.isLoading && !authState.isAuthenticated && pathname !== "/auth/login" && pathname !== "/auth/callback") {
      router.push("/auth/login");
    }
  }, [authState.isAuthenticated, authState.isLoading, pathname, router]);
  
  const checkAuth = useCallback(() => {
    const token = getToken();
    if (!token) {
      setAuthState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return;
    }
    
    // Check if token is expired
    if (isTokenExpired(token)) {
      removeToken();
      setAuthState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return;
    }
    
    // Extract user from token
    const user = extractUserFromToken(token);
    if (user) {
      setAuthState({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });
    } else {
      removeToken();
      setAuthState({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  }, []);
  
  const login = useCallback(() => {
    // Redirect to OAuth provider
    window.location.href = getOAuthUrl();
  }, []);
  
  const logout = useCallback(() => {
    removeToken();
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
    router.push("/auth/login");
  }, [router]);
  
  const refreshToken = useCallback(async () => {
    // TODO: Implement token refresh via API
    // For now, just re-check auth
    checkAuth();
  }, [checkAuth]);
  
  return (
    <AuthContext.Provider
      value={{
        ...authState,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
