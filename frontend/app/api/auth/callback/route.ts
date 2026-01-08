import { NextRequest, NextResponse } from "next/server";

/**
 * OAuth callback API route.
 * 
 * Exchanges authorization code for access token.
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
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const response = await fetch(`${backendUrl}/api/v1/auth/callback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code, state }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || "Token exchange failed" },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json({ token: data.access_token });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 }
    );
  }
}
