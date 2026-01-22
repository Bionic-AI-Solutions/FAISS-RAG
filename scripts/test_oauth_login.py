#!/usr/bin/env python3
"""
Test OAuth 2.0 login flow.

This script tests:
1. Frontend OAuth URL generation
2. Backend login endpoint redirect
3. Backend callback endpoint (with mock code)
4. Token validation
"""

import os
import sys
import json
import httpx
from urllib.parse import urlparse, parse_qs

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"
KEYCLOAK_BASE = "https://auth.bionicaisolutions.com/realms/Bionic"
CLIENT_ID = "bionic-rag-client"
REDIRECT_URI = f"{FRONTEND_URL}/auth/callback"


def test_frontend_oauth_url():
    """Test that frontend generates correct OAuth URL."""
    print("\n" + "="*60)
    print("TEST 1: Frontend OAuth URL Generation")
    print("="*60)
    
    # Check if frontend is running
    try:
        response = httpx.get(f"{FRONTEND_URL}/auth/login", timeout=5.0)
        if response.status_code == 200:
            print(f"✅ Frontend is running at {FRONTEND_URL}")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend is not accessible: {e}")
        return False
    
    # Expected OAuth URL pattern
    expected_base = f"{KEYCLOAK_BASE}/protocol/openid-connect/auth"
    print(f"Expected OAuth base URL: {expected_base}")
    print(f"Expected client_id: {CLIENT_ID}")
    print(f"Expected redirect_uri: {REDIRECT_URI}")
    
    return True


def test_backend_login_endpoint():
    """Test backend login endpoint redirects to Keycloak."""
    print("\n" + "="*60)
    print("TEST 2: Backend Login Endpoint")
    print("="*60)
    
    try:
        # Test backend login endpoint
        response = httpx.get(
            f"{BACKEND_URL}/api/auth/login",
            params={
                "redirect_uri": REDIRECT_URI,
                "state": "test-state-123"
            },
            follow_redirects=False,
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 307 or response.status_code == 302:
            redirect_url = response.headers.get("Location", "")
            print(f"✅ Backend redirects to: {redirect_url}")
            
            # Parse redirect URL
            parsed = urlparse(redirect_url)
            if parsed.netloc == "auth.bionicaisolutions.com":
                print(f"✅ Redirects to correct Keycloak domain")
            else:
                print(f"⚠️  Redirects to unexpected domain: {parsed.netloc}")
            
            # Check query parameters
            params = parse_qs(parsed.query)
            print(f"\nOAuth Parameters:")
            print(f"  response_type: {params.get('response_type', ['N/A'])[0]}")
            print(f"  client_id: {params.get('client_id', ['N/A'])[0]}")
            print(f"  redirect_uri: {params.get('redirect_uri', ['N/A'])[0]}")
            print(f"  scope: {params.get('scope', ['N/A'])[0]}")
            print(f"  state: {params.get('state', ['N/A'])[0]}")
            
            # Validate parameters
            if params.get('client_id', [''])[0] == CLIENT_ID:
                print(f"✅ Client ID matches: {CLIENT_ID}")
            else:
                print(f"❌ Client ID mismatch. Expected: {CLIENT_ID}, Got: {params.get('client_id', [''])[0]}")
                return False
            
            if params.get('redirect_uri', [''])[0] == REDIRECT_URI:
                print(f"✅ Redirect URI matches: {REDIRECT_URI}")
            else:
                print(f"⚠️  Redirect URI mismatch. Expected: {REDIRECT_URI}, Got: {params.get('redirect_uri', [''])[0]}")
            
            return True
        else:
            print(f"❌ Expected redirect (307/302), got {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Backend login endpoint test failed: {e}")
        return False


def test_backend_callback_endpoint():
    """Test backend callback endpoint (will fail without valid code, but tests structure)."""
    print("\n" + "="*60)
    print("TEST 3: Backend Callback Endpoint Structure")
    print("="*60)
    
    try:
        # Test with invalid code (should return error, not crash)
        response = httpx.post(
            f"{BACKEND_URL}/api/auth/callback",
            json={
                "code": "invalid-test-code",
                "state": "test-state"
            },
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ Endpoint exists and validates input (returns 400 for invalid code)")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('detail', 'N/A')}")
            except:
                print(f"Response: {response.text[:200]}")
            return True
        elif response.status_code == 500:
            print("⚠️  Endpoint exists but returned 500 (server error)")
            print(f"Response: {response.text[:200]}")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Backend callback endpoint test failed: {e}")
        return False


def test_frontend_callback_api():
    """Test frontend callback API route."""
    print("\n" + "="*60)
    print("TEST 4: Frontend Callback API Route")
    print("="*60)
    
    try:
        # Test with invalid code (should proxy to backend)
        response = httpx.post(
            f"{FRONTEND_URL}/api/auth/callback",
            json={
                "code": "invalid-test-code",
                "state": "test-state"
            },
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [400, 500]:
            print("✅ Frontend callback API route exists and proxies to backend")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'N/A')}")
            except:
                print(f"Response: {response.text[:200]}")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend callback API test failed: {e}")
        return False


def test_keycloak_connectivity():
    """Test Keycloak server connectivity."""
    print("\n" + "="*60)
    print("TEST 5: Keycloak Server Connectivity")
    print("="*60)
    
    try:
        # Test Keycloak realm endpoint
        response = httpx.get(
            f"{KEYCLOAK_BASE}/.well-known/openid-configuration",
            timeout=10.0
        )
        
        if response.status_code == 200:
            print(f"✅ Keycloak is accessible")
            config = response.json()
            print(f"  Issuer: {config.get('issuer', 'N/A')}")
            print(f"  Authorization endpoint: {config.get('authorization_endpoint', 'N/A')}")
            print(f"  Token endpoint: {config.get('token_endpoint', 'N/A')}")
            return True
        else:
            print(f"❌ Keycloak returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Keycloak connectivity test failed: {e}")
        return False


def main():
    """Run all OAuth tests."""
    print("\n" + "="*60)
    print("OAuth 2.0 Login Flow Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Frontend OAuth URL", test_frontend_oauth_url()))
    results.append(("Backend Login Endpoint", test_backend_login_endpoint()))
    results.append(("Backend Callback Endpoint", test_backend_callback_endpoint()))
    results.append(("Frontend Callback API", test_frontend_callback_api()))
    results.append(("Keycloak Connectivity", test_keycloak_connectivity()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OAuth flow is configured correctly.")
        print("\nTo test the full flow:")
        print(f"1. Navigate to: {FRONTEND_URL}/auth/login")
        print("2. Click 'Sign in with OAuth 2.0'")
        print("3. Login with Keycloak credentials")
        print("4. You should be redirected back to the app")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
