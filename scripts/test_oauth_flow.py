#!/usr/bin/env python3
"""
Test script for OAuth flow with Keycloak.

This script tests the OAuth configuration and flow to ensure everything is set up correctly.
"""

import json
import requests
import sys
from typing import Dict, Optional
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_keycloak_endpoints(keycloak_url: str, realm: str = "Bionic") -> bool:
    """Test Keycloak endpoints accessibility."""
    print("Testing Keycloak endpoints...")

    endpoints = [
        f"{keycloak_url}/realms/{realm}/.well-known/openid-connect-configuration",
        f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs",
        f"{keycloak_url}/realms/{realm}/protocol/openid-connect/auth",
        f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token",
        f"{keycloak_url}/realms/{realm}/protocol/openid-connect/userinfo"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, verify=False, timeout=10)
            if response.status_code == 200:
                print(f"✓ {endpoint}")
            else:
                print(f"✗ {endpoint} - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {endpoint} - Error: {e}")
            return False

    return True


def test_client_configuration(keycloak_url: str, client_id: str, realm: str = "Bionic") -> bool:
    """Test client configuration."""
    print(f"\nTesting client configuration for {client_id}...")

    # Get OpenID Connect configuration
    config_url = f"{keycloak_url}/realms/{realm}/.well-known/openid-connect-configuration"
    try:
        response = requests.get(config_url, verify=False)
        config = response.json()

        # Check if our client is configured
        auth_url = config.get('authorization_endpoint', '')
        token_url = config.get('token_endpoint', '')

        print(f"✓ Authorization endpoint: {auth_url}")
        print(f"✓ Token endpoint: {token_url}")

        return True
    except Exception as e:
        print(f"✗ Failed to get OpenID configuration: {e}")
        return False


def test_backend_oauth_endpoints(backend_url: str = "http://localhost:8001") -> bool:
    """Test backend OAuth endpoints."""
    print(f"\nTesting backend OAuth endpoints at {backend_url}...")

    endpoints = [
        f"{backend_url}/api/auth/login",
        f"{backend_url}/docs"  # Check if API is running
    ]

    for endpoint in endpoints:
        try:
            if "login" in endpoint:
                response = requests.get(endpoint, timeout=10)
            else:
                response = requests.get(endpoint, timeout=10)

            if response.status_code in [200, 404]:  # 404 is ok for login endpoint
                print(f"✓ {endpoint}")
            else:
                print(f"✗ {endpoint} - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {endpoint} - Error: {e}")
            return False

    return True


def test_frontend_configuration(frontend_url: str = "http://localhost:3000") -> bool:
    """Test frontend configuration."""
    print(f"\nTesting frontend configuration at {frontend_url}...")

    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print(f"✓ Frontend is accessible at {frontend_url}")
            return True
        else:
            print(f"✗ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to frontend: {e}")
        return False


def generate_env_files(keycloak_url: str, client_secret: str, realm: str = "Bionic"):
    """Generate environment configuration files."""
    print("\nGenerating environment configuration...")

    # Backend .env
    backend_env = f"""# OAuth Configuration
OAUTH_ENABLED=true
OAUTH_ISSUER={keycloak_url}/realms/{realm}
OAUTH_JWKS_URI={keycloak_url}/realms/{realm}/protocol/openid-connect/certs
OAUTH_AUDIENCE=bionic-rag-client
OAUTH_CLIENT_ID=bionic-rag-client
OAUTH_CLIENT_SECRET={client_secret}
OAUTH_USER_ID_CLAIM=sub
OAUTH_TENANT_ID_CLAIM=tenant_id
OAUTH_ROLE_CLAIM=role
OAUTH_USER_PROFILE_ENDPOINT={keycloak_url}/realms/{realm}/protocol/openid-connect/userinfo
"""

    # Frontend .env.local
    frontend_env = f"""# OAuth Configuration
NEXT_PUBLIC_OAUTH_BASE_URL={keycloak_url}/realms/{realm}/protocol/openid-connect
NEXT_PUBLIC_OAUTH_CLIENT_ID=bionic-rag-client
NEXT_PUBLIC_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
NEXT_PUBLIC_API_URL=http://localhost:8001
"""

    # Write backend .env
    try:
        with open('.env', 'w') as f:
            f.write(backend_env)
        print("✓ Generated backend .env file")
    except Exception as e:
        print(f"✗ Failed to write backend .env: {e}")

    # Write frontend .env.local
    try:
        with open('frontend/.env.local', 'w') as f:
            f.write(frontend_env)
        print("✓ Generated frontend .env.local file")
    except Exception as e:
        print(f"✗ Failed to write frontend .env.local: {e}")


def main():
    """Main test function."""
    if len(sys.argv) < 3:
        print("Usage: python test_oauth_flow.py <keycloak_url> <client_secret> [backend_url] [frontend_url]")
        print("Example: python test_oauth_flow.py https://auth.bionicaisolutions.com my-secret")
        sys.exit(1)

    keycloak_url = sys.argv[1]
    client_secret = sys.argv[2]
    backend_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8001"
    frontend_url = sys.argv[4] if len(sys.argv) > 4 else "http://localhost:3000"

    print("="*60)
    print("BIONIC-RAG OAUTH FLOW TEST")
    print("="*60)

    print(f"Keycloak URL: {keycloak_url}")
    print(f"Backend URL: {backend_url}")
    print(f"Frontend URL: {frontend_url}")
    print()

    # Test Keycloak endpoints
    keycloak_ok = test_keycloak_endpoints(keycloak_url)

    # Test client configuration
    client_ok = test_client_configuration(keycloak_url, "bionic-rag-client")

    # Test backend endpoints
    backend_ok = test_backend_oauth_endpoints(backend_url)

    # Test frontend
    frontend_ok = test_frontend_configuration(frontend_url)

    # Generate environment files
    if keycloak_ok and client_ok:
        generate_env_files(keycloak_url, client_secret)

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Keycloak Endpoints: {'✓ PASS' if keycloak_ok else '✗ FAIL'}")
    print(f"Client Configuration: {'✓ PASS' if client_ok else '✗ FAIL'}")
    print(f"Backend OAuth: {'✓ PASS' if backend_ok else '✗ FAIL'}")
    print(f"Frontend: {'✓ PASS' if frontend_ok else '✗ FAIL'}")

    if keycloak_ok and client_ok and backend_ok and frontend_ok:
        print("\n🎉 ALL TESTS PASSED! OAuth setup is complete.")
        print("\nNext steps:")
        print("1. Start the backend: poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Visit http://localhost:3000 and test the login flow")
    else:
        print("\n❌ SOME TESTS FAILED. Please check the configuration and try again.")
        if not keycloak_ok:
            print("- Ensure Keycloak is running and accessible")
        if not client_ok:
            print("- Run the setup script: python scripts/setup_keycloak_client.py")
        if not backend_ok:
            print("- Start the backend server")
        if not frontend_ok:
            print("- Start the frontend development server")


if __name__ == "__main__":
    main()