"""add tenant_configs table

Revision ID: 004_add_tenant_configs_table
Revises: 003_add_templates_table
Create Date: 2026-01-06 07:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_tenant_configs_table'
down_revision: Union[str, None] = '003_add_templates_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tenant_configs',
        sa.Column('config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_configuration', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('compliance_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('data_isolation_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('audit_logging_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_configuration', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['templates.template_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('config_id')
    )
    op.create_index(op.f('ix_tenant_configs_tenant_id'), 'tenant_configs', ['tenant_id'], unique=True)
    op.create_index(op.f('ix_tenant_configs_template_id'), 'tenant_configs', ['template_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tenant_configs_template_id'), table_name='tenant_configs')
    op.drop_index(op.f('ix_tenant_configs_tenant_id'), table_name='tenant_configs')
    op.drop_table('tenant_configs')








