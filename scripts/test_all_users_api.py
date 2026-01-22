#!/usr/bin/env python3
"""
Test all Keycloak users via direct API calls to verify backend token exchange.
This complements UI testing by verifying backend functionality.
"""

import requests
import json
import sys

# Test users
TEST_USERS = [
    {"username": "uber-admin", "role": "uber_admin"},
    {"username": "tenant-admin-1", "role": "tenant_admin"},
    {"username": "tenant-admin-2", "role": "tenant_admin"},
    {"username": "project-admin-1", "role": "project_admin"},
    {"username": "end-user-1", "role": "end_user"},
    {"username": "end-user-2", "role": "end_user"},
    {"username": "end-user-3", "role": "end_user"},
]

KEYCLOAK_URL = "https://auth.bionicaisolutions.com/realms/Bionic"
CLIENT_ID = "bionic-rag-client"
CLIENT_SECRET = "p4xjBDxXZpHJ7Mm4CJfoOlLUFpD2sydu"
PASSWORD = "Test123!"

def test_user_login(username: str, password: str) -> dict:
    """Test user login via Keycloak direct access grant."""
    token_url = f"{KEYCLOAK_URL}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": username,
        "password": password,
        "scope": "openid profile email"
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=10, verify=False)
        response.raise_for_status()
        token_data = response.json()
        
        # Decode token to verify claims
        import jwt
        decoded = jwt.decode(token_data["access_token"], options={"verify_signature": False})
        
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
    except Exception as e:
        return {
            "success": False,
            "username": username,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Keycloak User Testing - Backend API Verification")
    print("=" * 80)
    print(f"\nTesting {len(TEST_USERS)} users...")
    print(f"Keycloak: {KEYCLOAK_URL}")
    print(f"Client: {CLIENT_ID}\n")
    
    results = []
    for user in TEST_USERS:
        print(f"Testing: {user['username']} ({user['role']})...")
        result = test_user_login(user["username"], PASSWORD)
        results.append(result)
        
        if result["success"]:
            print(f"  ✅ Success")
            print(f"     User ID: {result.get('user_id', 'N/A')}")
            print(f"     Email: {result.get('email', 'N/A')}")
            print(f"     Role: {result.get('role', 'N/A')}")
            print(f"     Tenant ID: {result.get('tenant_id', 'N/A')}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        print()
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print("=" * 80)
    print(f"Summary: {successful}/{len(TEST_USERS)} users successful")
    print("=" * 80)
    
    # Save results
    with open("/tmp/keycloak_user_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: /tmp/keycloak_user_test_results.json")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
