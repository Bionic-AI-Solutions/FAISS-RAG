#!/usr/bin/env python3
"""
Disable VERIFY_PROFILE required action for test users in Keycloak.
This allows users to login without being forced to update their profile.
"""

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

def get_user_id(base_url: str, token: str, realm: str, username: str) -> str:
    """Get user ID by username."""
    url = f"{base_url}/admin/realms/{realm}/users"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'username': username}
    response = requests.get(url, headers=headers, params=params, verify=False)
    response.raise_for_status()
    users = response.json()
    if not users:
        raise ValueError(f"User {username} not found")
    return users[0]['id']

def remove_required_action(base_url: str, token: str, realm: str, user_id: str, action: str):
    """Remove a required action from a user."""
    # Get current user
    url = f"{base_url}/admin/realms/{realm}/users/{user_id}"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers, verify=False)
    response.raise_for_status()
    user = response.json()
    
    # Remove required action
    required_actions = user.get('requiredActions', [])
    if action in required_actions:
        required_actions.remove(action)
        update_data = {"requiredActions": required_actions}
        response = requests.put(url, headers=headers, json=update_data, verify=False)
        response.raise_for_status()
        print(f"  ✅ Removed {action} required action")
    else:
        print(f"  ℹ️  {action} not in required actions (already removed)")

def main():
    if len(sys.argv) != 4:
        print("Usage: python disable_profile_update_required_action.py <keycloak_url> <admin_username> <admin_password>")
        sys.exit(1)
    
    base_url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    realm = "Bionic"
    
    test_users = [
        "uber-admin", "tenant-admin-1", "tenant-admin-2", 
        "project-admin-1", "end-user-1", "end-user-2", "end-user-3"
    ]
    
    print("Getting admin token...")
    token = get_admin_token(base_url, username, password)
    
    print(f"\nRemoving VERIFY_PROFILE required action for {len(test_users)} users...")
    for user in test_users:
        try:
            user_id = get_user_id(base_url, token, realm, user)
            print(f"\nProcessing: {user}")
            remove_required_action(base_url, token, realm, user_id, "VERIFY_PROFILE")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n✅ Complete!")

if __name__ == "__main__":
    main()
