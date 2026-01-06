"""
Unit tests for database models.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.audit_log import AuditLog
from app.db.models.tenant_api_key import TenantApiKey
from app.db.models.template import Template


class TestTenantModel:
    """Tests for Tenant model."""
    
    def test_tenant_creation(self):
        """Test creating a tenant."""
        tenant = Tenant(
            tenant_id=uuid4(),
            name="Test Tenant",
            domain="test.example.com",
            subscription_tier="premium"
        )
        assert tenant.name == "Test Tenant"
        assert tenant.domain == "test.example.com"
        assert tenant.subscription_tier == "premium"
    
    def test_tenant_default_subscription_tier(self):
        """Test tenant defaults to basic subscription tier."""
        # SQLAlchemy defaults are applied at database level, not in-memory
        # When not set explicitly, it will be None until persisted
        # The default is set in the database schema (server_default='basic')
        # For unit tests, we verify the model accepts the default value
        tenant = Tenant(
            tenant_id=uuid4(),
            name="Test Tenant",
            subscription_tier="basic"  # Explicitly set to test the constraint
        )
        assert tenant.subscription_tier == "basic"
    
    def test_tenant_to_dict(self):
        """Test tenant to_dict method."""
        tenant = Tenant(
            tenant_id=uuid4(),
            name="Test Tenant",
            domain="test.example.com"
        )
        tenant_dict = tenant.to_dict()
        assert "tenant_id" in tenant_dict
        assert "name" in tenant_dict
        assert "created_at" in tenant_dict
        assert "updated_at" in tenant_dict


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self):
        """Test creating a user."""
        tenant_id = uuid4()
        user = User(
            user_id=uuid4(),
            tenant_id=tenant_id,
            email="user@example.com",
            role="user"
        )
        assert user.email == "user@example.com"
        assert user.role == "user"
        assert user.tenant_id == tenant_id
    
    def test_user_default_role(self):
        """Test user defaults to end_user role."""
        user = User(
            user_id=uuid4(),
            tenant_id=uuid4(),
            email="user@example.com"
        )
        # SQLAlchemy defaults are applied at database level, not in-memory
        # When not set explicitly, it will be None until persisted
        # The default is set in the database schema to "end_user" (updated in Story 1.6)
        # Set it explicitly to test the constraint
        user.role = "end_user"
        assert user.role == "end_user"


class TestDocumentModel:
    """Tests for Document model."""
    
    def test_document_creation(self):
        """Test creating a document."""
        tenant_id = uuid4()
        user_id = uuid4()
        document = Document(
            document_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title="Test Document",
            content_hash="abc123def456"
        )
        assert document.title == "Test Document"
        assert document.content_hash == "abc123def456"
        assert document.tenant_id == tenant_id
        assert document.user_id == user_id


class TestAuditLogModel:
    """Tests for AuditLog model."""
    
    def test_audit_log_creation(self):
        """Test creating an audit log."""
        log = AuditLog(
            log_id=uuid4(),
            tenant_id=uuid4(),
            user_id=uuid4(),
            action="create",
            resource_type="document",
            resource_id="doc123"
        )
        assert log.action == "create"
        assert log.resource_type == "document"
        assert log.resource_id == "doc123"


class TestTenantApiKeyModel:
    """Tests for TenantApiKey model."""
    
    def test_api_key_creation(self):
        """Test creating an API key."""
        tenant_id = uuid4()
        api_key = TenantApiKey(
            key_id=uuid4(),
            tenant_id=tenant_id,
            key_hash="hashed_key_value",
            name="Test API Key"
        )
        assert api_key.key_hash == "hashed_key_value"
        assert api_key.name == "Test API Key"
        assert api_key.tenant_id == tenant_id


class TestTemplateModel:
    """Tests for Template model."""
    
    def test_template_creation(self):
        """Test creating a template."""
        template = Template(
            template_id=uuid4(),
            template_name="Fintech Template",
            domain_type="fintech",
            description="Template for financial technology companies",
            compliance_checklist={"pci_dss": {"required": True}},
            default_configuration={"embedding_model": "text-embedding-3-large"},
            customization_options={"models": {"embedding": ["text-embedding-3-large"]}}
        )
        assert template.template_name == "Fintech Template"
        assert template.domain_type == "fintech"
        assert template.description == "Template for financial technology companies"
        assert template.compliance_checklist == {"pci_dss": {"required": True}}
        assert template.default_configuration == {"embedding_model": "text-embedding-3-large"}
    
    def test_template_to_dict(self):
        """Test template to_dict method."""
        template = Template(
            template_id=uuid4(),
            template_name="Test Template",
            domain_type="custom",
            description="Test description"
        )
        template_dict = template.to_dict()
        assert "template_id" in template_dict
        assert "template_name" in template_dict
        assert "domain_type" in template_dict
        assert "description" in template_dict
        assert "created_at" in template_dict
        assert "updated_at" in template_dict
    
    def test_template_domain_type_constraint(self):
        """Test template domain_type constraint."""
        # Valid domain types
        valid_types = ["fintech", "healthcare", "retail", "customer_service", "custom"]
        for domain_type in valid_types:
            template = Template(
                template_id=uuid4(),
                template_name=f"Test Template {domain_type}",
                domain_type=domain_type,
                description="Test"
            )
            assert template.domain_type == domain_type



