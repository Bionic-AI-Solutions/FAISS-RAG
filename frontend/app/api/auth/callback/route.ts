import { NextRequest, NextResponse } from "next/server";

/**
 * OAuth callback API route.
 * 
 * Exchanges Keycloak authorization code for access token via backend.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { code, state } = body;
    
    if (!code) {
      return NextResponse.json(
        { error: "Authorization code required" },
        { status: 400 }
      );
    }
    
    // Exchange code for token via backend API
    // Backend handles Keycloak token exchange
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    try {
      const response = await fetch(`${backendUrl}/api/auth/callback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code, state }),
        // Increase timeout for Keycloak token exchange
        signal: AbortSignal.timeout(30000), // 30 seconds
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Token exchange failed" }));
        return NextResponse.json(
          { error: error.detail || error.message || "Token exchange failed" },
          { status: response.status }
        );
      }
      
      const data = await response.json();
      
      // Return Keycloak access token
      return NextResponse.json({ 
        token: data.access_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
      });
    } catch (fetchError: any) {
      // Handle network errors or timeouts
      if (fetchError.name === "TimeoutError") {
        return NextResponse.json(
          { error: "Token exchange timed out. Please try again." },
          { status: 504 }
        );
      }
      throw fetchError;
    }
  } catch (error: any) {
    console.error("OAuth callback error:", error);
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 }
    );
  }
}
