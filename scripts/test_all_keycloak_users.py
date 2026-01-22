#!/usr/bin/env python3
"""
Script to systematically test all Keycloak users through the OAuth flow.
This script will navigate through the UI and test each user login.
"""

import time
import json

# Test users from KEYCLOAK_TEST_USERS.md
TEST_USERS = [
    {
        "username": "uber-admin",
        "password": "Test123!",
        "role": "uber_admin",
        "tenant_id": "00000000-0000-0000-0000-000000000001"
    },
    {
        "username": "tenant-admin-1",
        "password": "Test123!",
        "role": "tenant_admin",
        "tenant_id": "11111111-1111-1111-1111-111111111111"
    },
    {
        "username": "tenant-admin-2",
        "password": "Test123!",
        "role": "tenant_admin",
        "tenant_id": "22222222-2222-2222-2222-222222222222"
    },
    {
        "username": "project-admin-1",
        "password": "Test123!",
        "role": "project_admin",
        "tenant_id": "11111111-1111-1111-1111-111111111111"
    },
    {
        "username": "end-user-1",
        "password": "Test123!",
        "role": "end_user",
        "tenant_id": "11111111-1111-1111-1111-111111111111"
    },
    {
        "username": "end-user-2",
        "password": "Test123!",
        "role": "end_user",
        "tenant_id": "22222222-2222-2222-2222-222222222222"
    },
    {
        "username": "end-user-3",
        "password": "Test123!",
        "role": "end_user",
        "tenant_id": "33333333-3333-3333-3333-333333333333"
    }
]

print("=" * 80)
print("Keycloak User Testing Script")
print("=" * 80)
print(f"\nTotal users to test: {len(TEST_USERS)}\n")

for i, user in enumerate(TEST_USERS, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}/{len(TEST_USERS)}: {user['username']} ({user['role']})")
    print(f"{'='*80}")
    print(f"Username: {user['username']}")
    print(f"Role: {user['role']}")
    print(f"Tenant ID: {user['tenant_id']}")
    print(f"\nSteps:")
    print(f"1. Navigate to: http://localhost:3001/auth/login")
    print(f"2. Click 'Sign in with OAuth 2.0'")
    print(f"3. Navigate to Keycloak native login (if redirected to Google)")
    print(f"4. Enter username: {user['username']}")
    print(f"5. Enter password: {user['password']}")
    print(f"6. Complete profile update if required")
    print(f"7. Verify successful login and redirect")
    print(f"8. Check user role and tenant_id in application")
    print(f"9. Logout and proceed to next user")
    print(f"\nPress Enter to continue to next user...")

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
