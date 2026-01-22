#!/usr/bin/env python3
"""
Update Keycloak client redirect URIs to use port 3001.
"""

import json
import requests
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_admin_token(base_url: str, username: str, password: str) -> str:
    """Get admin access token."""
    token_url = f"{base_url}/realms/master/protocol/openid-connect/token"
    data = {
        'client_id': 'admin-cli',
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    response = requests.post(token_url, data=data, verify=False)
    response.raise_for_status()
    return response.json()['access_token']


def update_client_redirect_uris(base_url: str, token: str, realm: str, client_id: str, redirect_uris: list, web_origins: list):
    """Update client redirect URIs."""
    # Get client UUID
    url = f"{base_url}/admin/realms/{realm}/clients"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'clientId': client_id}
    
    response = requests.get(url, headers=headers, params=params, verify=False)
    response.raise_for_status()
    
    clients = response.json()
    if not clients:
        raise ValueError(f"Client {client_id} not found")
    
    client_uuid = clients[0]['id']
    
    # Get current client config
    client_url = f"{base_url}/admin/realms/{realm}/clients/{client_uuid}"
    response = requests.get(client_url, headers=headers, verify=False)
    response.raise_for_status()
    client_data = response.json()
    
    # Update redirect URIs and web origins
    client_data['redirectUris'] = redirect_uris
    client_data['webOrigins'] = web_origins
    
    # Update client
    response = requests.put(client_url, headers=headers, json=client_data, verify=False)
    response.raise_for_status()
    
    print(f"✅ Updated client {client_id} redirect URIs:")
    for uri in redirect_uris:
        print(f"   - {uri}")
    print(f"✅ Updated web origins:")
    for origin in web_origins:
        print(f"   - {origin}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python update_keycloak_redirect_uri.py <keycloak_url> <admin_username> <admin_password>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    realm = "Bionic"
    client_id = "bionic-rag-client"
    
    # Redirect URIs to configure
    redirect_uris = [
        "http://localhost:3001/auth/callback",
        "http://localhost:3000/auth/callback",  # Keep old one for compatibility
        "https://your-domain.com/auth/callback",
        "bionic-rag://callback"
    ]
    
    # Web origins
    web_origins = [
        "http://localhost:3001",
        "http://localhost:3000",  # Keep old one for compatibility
        "https://your-domain.com"
    ]
    
    try:
        print("Getting admin token...")
        token = get_admin_token(base_url, username, password)
        
        print(f"Updating client {client_id} in realm {realm}...")
        update_client_redirect_uris(
            base_url, token, realm, client_id, 
            redirect_uris, web_origins
        )
        
        print("\n✅ Keycloak client configuration updated successfully!")
        print("\nYou can now test the OAuth login flow.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
