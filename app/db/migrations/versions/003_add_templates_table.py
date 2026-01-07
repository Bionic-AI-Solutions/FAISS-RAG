"""add templates table

Revision ID: 003_add_templates_table
Revises: 002_enable_rls
Create Date: 2026-01-06 07:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_add_templates_table'
down_revision: Union[str, None] = '002_enable_rls'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create templates table
    op.create_table(
        'templates',
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column('domain_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('compliance_checklist', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('default_configuration', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('customization_options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("domain_type IN ('fintech', 'healthcare', 'retail', 'customer_service', 'custom')", name='check_domain_type'),
        sa.PrimaryKeyConstraint('template_id')
    )
    op.create_index(op.f('ix_templates_template_name'), 'templates', ['template_name'], unique=True)
    op.create_index(op.f('ix_templates_domain_type'), 'templates', ['domain_type'], unique=False)
    
    # Seed initial Fintech template (idempotent)
    op.execute("""
        INSERT INTO templates (
            template_id,
            template_name,
            domain_type,
            description,
            compliance_checklist,
            default_configuration,
            customization_options
        )
        VALUES (
            '550e8400-e29b-41d4-a716-446655440001'::uuid,
            'Fintech Template',
            'fintech',
            'Template for financial technology companies requiring PCI DSS compliance, secure data handling, and financial transaction support.',
            '{
                "pci_dss": {
                    "required": true,
                    "level": "Level 1",
                    "requirements": [
                        "Encrypt cardholder data at rest",
                        "Encrypt cardholder data in transit",
                        "Maintain secure network",
                        "Implement strong access control",
                        "Regularly monitor and test networks",
                        "Maintain information security policy"
                    ]
                },
                "data_retention": {
                    "financial_transactions": "7 years",
                    "audit_logs": "7 years",
                    "user_data": "As per GDPR"
                },
                "encryption": {
                    "at_rest": "AES-256",
                    "in_transit": "TLS 1.3"
                }
            }'::jsonb,
            '{
                "embedding_model": "text-embedding-3-large",
                "llm_model": "gpt-4-turbo-preview",
                "rate_limit": {
                    "requests_per_minute": 1000,
                    "burst_limit": 100
                },
                "data_isolation": {
                    "enforced": true,
                    "level": "tenant_and_user"
                },
                "audit_logging": {
                    "enabled": true,
                    "retention_days": 2555
                }
            }'::jsonb,
            '{
                "models": {
                    "embedding": ["text-embedding-3-large", "text-embedding-3-small"],
                    "llm": ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
                },
                "compliance": {
                    "pci_dss": {
                        "customizable": false,
                        "required": true
                    },
                    "data_retention": {
                        "customizable": true,
                        "min_retention_days": 2555
                    }
                },
                "features": {
                    "multi_modal": false,
                    "cross_modal_search": false,
                    "advanced_analytics": true
                }
            }'::jsonb
        )
        ON CONFLICT (template_name) DO NOTHING
    """)


def downgrade() -> None:
    # Drop templates table
    op.drop_index(op.f('ix_templates_domain_type'), table_name='templates')
    op.drop_index(op.f('ix_templates_template_name'), table_name='templates')
    op.drop_table('templates')








