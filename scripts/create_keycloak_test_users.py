#!/usr/bin/env python3
"""
Create test users in Keycloak for Bionic-RAG testing.

This script creates test users with different roles and tenant_id attributes.
"""

import json
import requests
import sys
import uuid
from typing import Dict, List, Optional
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class KeycloakUserManager:
    """Keycloak user management utility."""

    def __init__(self, base_url: str, admin_username: str, admin_password: str, realm: str = "Bionic"):
        self.base_url = base_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.realm = realm
        self.token: Optional[str] = None

    def get_admin_token(self) -> str:
        """Get admin access token."""
        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"

        data = {
            'client_id': 'admin-cli',
            'username': self.admin_username,
            'password': self.admin_password,
            'grant_type': 'password'
        }

        response = requests.post(token_url, data=data, verify=False)
        response.raise_for_status()

        self.token = response.json()['access_token']
        return self.token

    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user in Keycloak."""
        if not self.token:
            self.get_admin_token()

        url = f"{self.base_url}/admin/realms/{self.realm}/users"

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, json=user_data, verify=False)
        response.raise_for_status()

        # Get the created user details
        user_id = response.headers.get('Location', '').split('/')[-1]
        return {"id": user_id, "username": user_data["username"]}

    def set_user_password(self, user_id: str, password: str, temporary: bool = False) -> None:
        """Set user password."""
        if not self.token:
            self.get_admin_token()

        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/reset-password"

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        password_data = {
            "type": "password",
            "value": password,
            "temporary": temporary
        }

        response = requests.put(url, headers=headers, json=password_data, verify=False)
        response.raise_for_status()

    def add_user_attribute(self, user_id: str, attribute_name: str, attribute_value: str) -> None:
        """Add custom attribute to user."""
        if not self.token:
            self.get_admin_token()

        # First get current user
        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        user = response.json()

        # Update attributes
        attributes = user.get('attributes', {})
        attributes[attribute_name] = [attribute_value]

        update_data = {
            "attributes": attributes
        }

        response = requests.put(url, headers=headers, json=update_data, verify=False)
        response.raise_for_status()

    def assign_realm_role(self, user_id: str, role_name: str) -> None:
        """Assign realm role to user."""
        if not self.token:
            self.get_admin_token()

        # Get role details
        role_url = f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}"
        headers = {'Authorization': f'Bearer {self.token}'}

        response = requests.get(role_url, headers=headers, verify=False)
        response.raise_for_status()
        role = response.json()

        # Assign role to user
        assign_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
        role_data = [role]

        response = requests.post(assign_url, headers=headers, json=role_data, verify=False)
        response.raise_for_status()


def create_test_users():
    """Create test users with different roles and tenant IDs."""

    if len(sys.argv) != 4:
        print("Usage: python create_keycloak_test_users.py <keycloak_url> <admin_username> <admin_password>")
        print("Example: python create_keycloak_test_users.py https://auth.bionicaisolutions.com admin Th1515T0p53cr3t")
        sys.exit(1)

    keycloak_url = sys.argv[1]
    admin_username = sys.argv[2]
    admin_password = sys.argv[3]

    # Initialize user manager
    user_manager = KeycloakUserManager(keycloak_url, admin_username, admin_password, "Bionic")

    # Test user definitions
    test_users = [
        {
            "username": "uber-admin",
            "email": "uber-admin@bionic-rag.test",
            "firstName": "Uber",
            "lastName": "Admin",
            "enabled": True,
            "emailVerified": True,
            "role": "uber_admin",
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "password": "Test123!"
        },
        {
            "username": "tenant-admin-1",
            "email": "tenant-admin-1@bionic-rag.test",
            "firstName": "Tenant",
            "lastName": "Admin One",
            "enabled": True,
            "emailVerified": True,
            "role": "tenant_admin",
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "password": "Test123!"
        },
        {
            "username": "tenant-admin-2",
            "email": "tenant-admin-2@bionic-rag.test",
            "firstName": "Tenant",
            "lastName": "Admin Two",
            "enabled": True,
            "emailVerified": True,
            "role": "tenant_admin",
            "tenant_id": "22222222-2222-2222-2222-222222222222",
            "password": "Test123!"
        },
        {
            "username": "project-admin-1",
            "email": "project-admin-1@bionic-rag.test",
            "firstName": "Project",
            "lastName": "Admin One",
            "enabled": True,
            "emailVerified": True,
            "role": "project_admin",
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "password": "Test123!"
        },
        {
            "username": "project-admin-2",
            "email": "project-admin-2@bionic-rag.test",
            "firstName": "Project",
            "lastName": "Admin Two",
            "enabled": True,
            "emailVerified": True,
            "role": "project_admin",
            "tenant_id": "22222222-2222-2222-2222-222222222222",
            "password": "Test123!"
        },
        {
            "username": "end-user-1",
            "email": "end-user-1@bionic-rag.test",
            "firstName": "End",
            "lastName": "User One",
            "enabled": True,
            "emailVerified": True,
            "role": "end_user",
            "tenant_id": "11111111-1111-1111-1111-111111111111",
            "password": "Test123!"
        },
        {
            "username": "end-user-2",
            "email": "end-user-2@bionic-rag.test",
            "firstName": "End",
            "lastName": "User Two",
            "enabled": True,
            "emailVerified": True,
            "role": "end_user",
            "tenant_id": "22222222-2222-2222-2222-222222222222",
            "password": "Test123!"
        },
        {
            "username": "end-user-3",
            "email": "end-user-3@bionic-rag.test",
            "firstName": "End",
            "lastName": "User Three",
            "enabled": True,
            "emailVerified": True,
            "role": "end_user",
            "tenant_id": "33333333-3333-3333-3333-333333333333",
            "password": "Test123!"
        }
    ]

    created_users = []

    try:
        for user_data in test_users:
            print(f"Creating user: {user_data['username']}")

            # Prepare user creation data (exclude our custom fields)
            create_data = {
                "username": user_data["username"],
                "email": user_data["email"],
                "firstName": user_data["firstName"],
                "lastName": user_data["lastName"],
                "enabled": user_data["enabled"],
                "emailVerified": user_data["emailVerified"]
            }

            try:
                # Create user
                user = user_manager.create_user(create_data)
                user_id = user["id"]

                # Set password
                user_manager.set_user_password(user_id, user_data["password"], temporary=False)

                # Add tenant_id attribute
                user_manager.add_user_attribute(user_id, "tenant_id", user_data["tenant_id"])

                # Assign role
                user_manager.assign_realm_role(user_id, user_data["role"])

                created_users.append({
                    "username": user_data["username"],
                    "user_id": user_id,
                    "role": user_data["role"],
                    "tenant_id": user_data["tenant_id"],
                    "password": user_data["password"]
                })

                print(f"✓ Created user {user_data['username']} with role {user_data['role']}")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:
                    print(f"⚠ User {user_data['username']} already exists, skipping...")
                else:
                    print(f"✗ Failed to create user {user_data['username']}: {e}")
                    raise

        # Print summary
        print("\n" + "="*80)
        print("TEST USERS CREATION COMPLETE")
        print("="*80)

        print("\nCreated Users:")
        print("-" * 40)
        for user in created_users:
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print(f"Role: {user['role']}")
            print(f"Tenant ID: {user['tenant_id']}")
            print("-" * 40)

        print("\nTenant Distribution:")
        tenants = {}
        for user in created_users:
            tenant = user['tenant_id']
            if tenant not in tenants:
                tenants[tenant] = []
            tenants[tenant].append(user['username'])

        for tenant_id, users in tenants.items():
            print(f"Tenant {tenant_id}: {', '.join(users)}")

        print("\n" + "="*80)
        print("You can now test the OAuth flow with these users!")
        print("Visit http://localhost:3000 and login with any of the above credentials.")
        print("="*80)

    except Exception as e:
        print(f"Error creating users: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_test_users()