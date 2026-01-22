#!/usr/bin/env python3
"""
Keycloak Client Setup Script for Bionic-RAG

This script automates the setup of a Keycloak client for the Bionic-RAG application.
It creates the necessary client configuration and provides the required environment variables.
"""

import json
import requests
import sys
from typing import Dict, Optional
import urllib3

# Disable SSL warnings for self-signed certificates (remove in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class KeycloakClientSetup:
    """Keycloak client setup utility."""

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

        print(f"Authenticating to: {token_url}")
        print(f"Username: {self.admin_username}")

        response = requests.post(token_url, data=data, verify=False)

        print(f"Auth response status: {response.status_code}")
        print(f"Auth response body: {response.text[:200]}...")

        response.raise_for_status()

        try:
            token_data = response.json()
            self.token = token_data['access_token']
            return self.token
        except (ValueError, KeyError) as e:
            print(f"Failed to parse token response: {e}")
            print(f"Response text: {response.text}")
            raise

    def create_client(self, client_config: Dict) -> Dict:
        """Create a new client in Keycloak."""
        if not self.token:
            self.get_admin_token()

        url = f"{self.base_url}/admin/realms/{self.realm}/clients"

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        print(f"Making request to: {url}")
        print(f"Client config: {json.dumps(client_config, indent=2)}")

        response = requests.post(url, headers=headers, json=client_config, verify=False)

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response body: {response.text[:500]}...")

        response.raise_for_status()

        if response.text.strip():
            return response.json()
        else:
            # Some endpoints return 201 with empty body for creation
            return {"message": "Client created successfully (empty response)"}

    def get_client_secret(self, client_id: str) -> str:
        """Get client secret for confidential client."""
        if not self.token:
            self.get_admin_token()

        # First get client UUID
        url = f"{self.base_url}/admin/realms/{self.realm}/clients"
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {'clientId': client_id}

        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()

        clients = response.json()
        if not clients:
            raise ValueError(f"Client {client_id} not found")

        client_uuid = clients[0]['id']

        # Get client secret
        secret_url = f"{self.base_url}/admin/realms/{self.realm}/clients/{client_uuid}/client-secret"
        response = requests.get(secret_url, headers=headers, verify=False)
        response.raise_for_status()

        return response.json()['value']

    def create_realm_roles(self) -> None:
        """Create necessary realm roles."""
        if not self.token:
            self.get_admin_token()

        roles = [
            {
                'name': 'uber_admin',
                'description': 'Super administrator with full access'
            },
            {
                'name': 'tenant_admin',
                'description': 'Tenant administrator'
            },
            {
                'name': 'project_admin',
                'description': 'Project-level administrator'
            },
            {
                'name': 'end_user',
                'description': 'Regular application user'
            }
        ]

        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        for role in roles:
            url = f"{self.base_url}/admin/realms/{self.realm}/roles"
            response = requests.post(url, headers=headers, json=role, verify=False)
            if response.status_code == 409:
                print(f"Role '{role['name']}' already exists, skipping...")
            else:
                response.raise_for_status()
                print(f"Created role: {role['name']}")

    def create_protocol_mapper(self, client_id: str, mapper_config: Dict) -> None:
        """Create protocol mapper for client."""
        if not self.token:
            self.get_admin_token()

        # Get client UUID
        url = f"{self.base_url}/admin/realms/{self.realm}/clients"
        headers = {'Authorization': f'Bearer {self.token}'}
        params = {'clientId': client_id}

        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()

        clients = response.json()
        if not clients:
            raise ValueError(f"Client {client_id} not found")

        client_uuid = clients[0]['id']

        # Create protocol mapper
        mapper_url = f"{self.base_url}/admin/realms/{self.realm}/clients/{client_uuid}/protocol-mappers/models"
        response = requests.post(mapper_url, headers=headers, json=mapper_config, verify=False)
        response.raise_for_status()

        print(f"Created protocol mapper: {mapper_config['name']}")


def main():
    """Main setup function."""
    if len(sys.argv) != 4:
        print("Usage: python setup_keycloak_client.py <keycloak_url> <admin_username> <admin_password>")
        print("Example: python setup_keycloak_client.py https://auth.bionicaisolutions.com admin Th1515T0p53cr3t")
        sys.exit(1)

    keycloak_url = sys.argv[1]
    admin_username = sys.argv[2]
    admin_password = sys.argv[3]

    # Initialize setup
    setup = KeycloakClientSetup(keycloak_url, admin_username, admin_password, "Bionic")

    try:
        # Create realm roles
        print("Creating realm roles...")
        setup.create_realm_roles()

        # Client configuration
        client_config = {
            "clientId": "bionic-rag-client",
            "name": "Bionic-RAG Application",
            "description": "OAuth client for Bionic-RAG multi-tenant application",
            "enabled": True,
            "clientAuthenticatorType": "client-secret",
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "implicitFlowEnabled": False,
            "standardFlowEnabled": True,
            "publicClient": False,
            "protocol": "openid-connect",
            "attributes": {
                "saml.assertion.signature": "false",
                "saml.multivalued.roles": "false",
                "saml.force.post.binding": "false",
                "saml.encrypt": "false",
                "saml.server.signature": "false",
                "saml.server.signature.keyinfo.ext": "false",
                "exclude.session.state.from.auth.response": "false",
                "saml_force_name_id_format": "false",
                "saml.client.signature": "false",
                "tls.client.certificate.bound.access.tokens": "false",
                "saml.authnstatement": "false",
                "display.on.consent.screen": "false",
                "saml.onetimeuse.condition": "false"
            },
            "redirectUris": [
                "http://localhost:3000/auth/callback",
                "https://your-domain.com/auth/callback",
                "bionic-rag://callback"
            ],
            "webOrigins": [
                "http://localhost:3000",
                "https://your-domain.com"
            ]
        }

        # Create client
        print("Creating client...")
        try:
            client = setup.create_client(client_config)
            print(f"Created client: {client.get('clientId', 'unknown')}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print("Client already exists, checking if it has the correct configuration...")
                # Client already exists, try to get it
                try:
                    existing_client = setup.get_client_secret("bionic-rag-client")
                    print("Client exists and is accessible")
                    client_secret = existing_client
                except Exception as ex:
                    print(f"Error accessing existing client: {ex}")
                    raise e
            else:
                print(f"HTTP Error creating client: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                raise

        # Get client secret
        print("Getting client secret...")
        client_secret = setup.get_client_secret("bionic-rag-client")

        # Create protocol mappers
        print("Creating protocol mappers...")

        # Tenant ID mapper
        tenant_mapper = {
            "name": "tenant_id",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usersessionmodel-note-mapper",
            "consentRequired": False,
            "config": {
                "user.session.note": "tenant_id",
                "userinfo.token.claim": "true",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "tenant_id",
                "jsonType.label": "String"
            }
        }
        setup.create_protocol_mapper("bionic-rag-client", tenant_mapper)

        # Role mapper
        role_mapper = {
            "name": "realm_roles",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-realm-role-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "role",
                "userinfo.token.claim": "true",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "claim.name": "role",
                "jsonType.label": "String"
            }
        }
        setup.create_protocol_mapper("bionic-rag-client", role_mapper)

        # Generate environment configuration
        print("\n" + "="*60)
        print("KEYCLOAK CLIENT SETUP COMPLETE")
        print("="*60)

        print("\nBackend Environment Variables (.env):")
        print("# OAuth Configuration")
        print("OAUTH_ENABLED=true")
        print(f"OAUTH_ISSUER={keycloak_url}/realms/Bionic")
        print(f"OAUTH_JWKS_URI={keycloak_url}/realms/Bionic/protocol/openid-connect/certs")
        print("OAUTH_AUDIENCE=bionic-rag-client")
        print("OAUTH_CLIENT_ID=bionic-rag-client")
        print(f"OAUTH_CLIENT_SECRET={client_secret}")
        print("OAUTH_USER_ID_CLAIM=sub")
        print("OAUTH_TENANT_ID_CLAIM=tenant_id")
        print("OAUTH_ROLE_CLAIM=role")
        print(f"OAUTH_USER_PROFILE_ENDPOINT={keycloak_url}/realms/Bionic/protocol/openid-connect/userinfo")

        print("\nFrontend Environment Variables (.env.local):")
        print("# OAuth Configuration")
        print(f"NEXT_PUBLIC_OAUTH_BASE_URL={keycloak_url}/realms/Bionic/protocol/openid-connect")
        print("NEXT_PUBLIC_OAUTH_CLIENT_ID=bionic-rag-client")
        print("NEXT_PUBLIC_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback")
        print("NEXT_PUBLIC_API_URL=http://localhost:8001")

        print("\nNext Steps:")
        print("1. Create test users in Keycloak and assign roles")
        print("2. Add tenant_id as a custom user attribute for each user")
        print("3. Configure the environment variables above")
        print("4. Test the OAuth flow")

    except Exception as e:
        print(f"Error setting up Keycloak client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()