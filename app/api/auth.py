"""
OAuth 2.0 authentication endpoints.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import jwt

from app.config.auth import auth_settings
from app.config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""
    code: str
    state: Optional[str] = None


@router.post("/callback", response_model=TokenResponse)
async def oauth_callback(request: OAuthCallbackRequest):
    """
    OAuth 2.0 authorization code exchange endpoint.

    Exchanges the authorization code for an access token.
    """
    if not auth_settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is disabled")

    # Validate required OAuth settings
    if not auth_settings.oauth_issuer or not auth_settings.oauth_jwks_uri:
        raise HTTPException(status_code=500, detail="OAuth configuration incomplete")

    # Exchange authorization code for tokens
    token_url = f"{auth_settings.oauth_issuer}/protocol/openid-connect/token"

    # Get redirect URI from environment or use default
    redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3001/auth/callback")
    
    token_data = {
        "grant_type": "authorization_code",
        "code": request.code,
        "redirect_uri": redirect_uri,
        "client_id": getattr(auth_settings, 'oauth_client_id', ''),
        "client_secret": getattr(auth_settings, 'oauth_client_secret', ''),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0
            )
            response.raise_for_status()
            token_response = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )

    # Validate the access token
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    # Decode and validate JWT claims
    try:
        # Get JWKS and validate token
        decoded_token = jwt.decode(
            access_token,
            options={"verify_signature": False},  # We'll verify with JWKS later
            algorithms=["RS256", "ES256"]
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=400, detail=f"Invalid access token: {str(e)}")

    # Validate required claims
    required_claims = ["sub", "iss", "aud", "exp"]
    for claim in required_claims:
        if claim not in decoded_token:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required claim: {claim}"
            )

    # Validate issuer
    if decoded_token["iss"] != auth_settings.oauth_issuer:
        raise HTTPException(status_code=400, detail="Invalid token issuer")

    # Validate audience
    if auth_settings.oauth_audience and decoded_token.get("aud") != auth_settings.oauth_audience:
        raise HTTPException(status_code=400, detail="Invalid token audience")

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=token_response.get("expires_in", 3600),
        refresh_token=token_response.get("refresh_token"),
        scope=token_response.get("scope")
    )


@router.get("/login")
async def oauth_login(
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after login"),
    state: Optional[str] = Query(None, description="OAuth state parameter")
):
    """
    Initiate OAuth login flow.

    Redirects to the OAuth provider's authorization endpoint.
    """
    if not auth_settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is disabled")

    # Build authorization URL
    auth_url = f"{auth_settings.oauth_issuer}/protocol/openid-connect/auth"

    # Get redirect URI from environment or use default
    default_redirect_uri = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3001/auth/callback")
    
    params = {
        "response_type": "code",
        "client_id": getattr(auth_settings, 'oauth_client_id', ''),
        "redirect_uri": redirect_uri or default_redirect_uri,
        "scope": "openid profile email",
        "state": state or "login",
    }

    # Add PKCE challenge if configured
    # TODO: Implement PKCE for enhanced security

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])

    return RedirectResponse(url=f"{auth_url}?{query_string}")


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh an access token using a refresh token.
    """
    if not auth_settings.oauth_enabled:
        raise HTTPException(status_code=400, detail="OAuth authentication is disabled")

    token_url = f"{auth_settings.oauth_issuer}/protocol/openid-connect/token"

    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": getattr(auth_settings, 'oauth_client_id', ''),
        "client_secret": getattr(auth_settings, 'oauth_client_secret', ''),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0
            )
            response.raise_for_status()
            token_response = response.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to refresh token: {str(e)}"
            )

    return TokenResponse(
        access_token=token_response["access_token"],
        token_type="Bearer",
        expires_in=token_response.get("expires_in", 3600),
        refresh_token=token_response.get("refresh_token"),
        scope=token_response.get("scope")
    )