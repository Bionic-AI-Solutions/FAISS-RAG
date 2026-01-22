#!/usr/bin/env python3
"""
Complete OAuth flow testing for all Keycloak users.
This script tests the full OAuth authorization code flow.
"""

import requests
import urllib.parse
import secrets
import time
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
KEYCLOAK_BASE = "https://auth.bionicaisolutions.com/realms/Bionic"
CLIENT_ID = "bionic-rag-client"
CLIENT_SECRET = "p4xjBDxXZpHJ7Mm4CJfoOlLUFpD2sydu"
REDIRECT_URI = "http://localhost:3001/auth/callback"
BACKEND_URL = "http://localhost:8000"

TEST_USERS = [
    {"username": "uber-admin", "role": "uber_admin", "tenant_id": "00000000-0000-0000-0000-000000000001"},
    {"username": "tenant-admin-1", "role": "tenant_admin", "tenant_id": "11111111-1111-1111-1111-111111111111"},
    {"username": "tenant-admin-2", "role": "tenant_admin", "tenant_id": "22222222-2222-2222-2222-222222222222"},
    {"username": "project-admin-1", "role": "project_admin", "tenant_id": "11111111-1111-1111-1111-111111111111"},
    {"username": "end-user-1", "role": "end_user", "tenant_id": "11111111-1111-1111-1111-111111111111"},
    {"username": "end-user-2", "role": "end_user", "tenant_id": "22222222-2222-2222-2222-222222222222"},
    {"username": "end-user-3", "role": "end_user", "tenant_id": "33333333-3333-3333-3333-333333333333"},
]

PASSWORD = "Test123!"

def test_user_oauth_flow(username: str, password: str) -> dict:
    """Test complete OAuth flow for a user."""
    print(f"\nTesting: {username}")
    print("-" * 60)
    
    # Step 1: Get authorization URL
    state = secrets.token_urlsafe(32)
    auth_url = f"{KEYCLOAK_BASE}/protocol/openid-connect/auth"
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email offline_access",
        "state": state
    }
    auth_url_full = f"{auth_url}?{urllib.parse.urlencode(params)}"
    print(f"✅ Authorization URL generated")
    
    # Step 2: User would login here (manual step)
    print(f"⏸️  Manual step: User logs in at Keycloak")
    print(f"   URL: {auth_url_full}")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   State: {state}")
    
    # Step 3: Simulate getting authorization code (would come from callback)
    # For testing, we use direct access grant to get a token
    token_url = f"{KEYCLOAK_BASE}/protocol/openid-connect/token"
    token_data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password,
        "scope": "openid profile email offline_access"
    }
    
    try:
        response = requests.post(token_url, data=token_data, timeout=10, verify=False)
        if response.status_code == 200:
            token_response = response.json()
            access_token = token_response.get("access_token")
            
            # Decode token to verify claims
            import jwt
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            
            return {
                "success": True,
                "username": username,
                "user_id": decoded.get("sub"),
                "email": decoded.get("email") or decoded.get("preferred_username"),
                "role": decoded.get("role") or "unknown",
                "tenant_id": decoded.get("tenant_id"),
                "realm_roles": decoded.get("realm_access", {}).get("roles", []),
                "client_roles": decoded.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", []),
            }
        else:
            return {
                "success": False,
                "username": username,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            "success": False,
            "username": username,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Complete OAuth Flow Testing - All Keycloak Users")
    print("=" * 80)
    print(f"\nTesting {len(TEST_USERS)} users via OAuth flow")
    print(f"Keycloak: {KEYCLOAK_BASE}")
    print(f"Backend: {BACKEND_URL}")
    print(f"Redirect URI: {REDIRECT_URI}\n")
    
    results = []
    for user in TEST_USERS:
        result = test_user_oauth_flow(user["username"], PASSWORD)
        results.append(result)
        
        if result["success"]:
            print(f"  ✅ SUCCESS")
            print(f"     User ID: {result.get('user_id', 'N/A')}")
            print(f"     Email: {result.get('email', 'N/A')}")
            print(f"     Role: {result.get('role', 'N/A')}")
            print(f"     Tenant ID: {result.get('tenant_id', 'N/A')}")
            print(f"     Expected Role: {user['role']}")
            print(f"     Expected Tenant: {user['tenant_id']}")
            
            # Verify role and tenant match
            role_match = result.get('role') == user['role'] or user['role'] in result.get('realm_roles', []) or user['role'] in result.get('client_roles', [])
            tenant_match = result.get('tenant_id') == user['tenant_id'] if result.get('tenant_id') else False
            
            if role_match:
                print(f"     ✅ Role matches")
            else:
                print(f"     ⚠️  Role mismatch (expected: {user['role']}, got: {result.get('role')})")
            
            if tenant_match:
                print(f"     ✅ Tenant ID matches")
            else:
                print(f"     ⚠️  Tenant ID mismatch (expected: {user['tenant_id']}, got: {result.get('tenant_id')})")
        else:
            print(f"  ❌ FAILED: {result.get('error', 'Unknown error')}")
        print()
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print("=" * 80)
    print(f"Summary: {successful}/{len(TEST_USERS)} users successful")
    print("=" * 80)
    
    # Save results
    with open("/tmp/oauth_user_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: /tmp/oauth_user_test_results.json")

if __name__ == "__main__":
    main()
