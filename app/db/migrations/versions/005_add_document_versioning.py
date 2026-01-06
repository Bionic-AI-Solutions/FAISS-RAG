"""
Add document versioning support.

Revision ID: 005_add_document_versioning
Revises: 004_add_tenant_configs_table
Create Date: 2026-01-06

Adds document_versions table and version_number/deleted_at fields to documents table.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '005_add_document_versioning'
down_revision: Union[str, None] = '004_add_tenant_configs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add version_number and deleted_at to documents table
    op.add_column('documents', sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('documents', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_documents_version_number'), 'documents', ['version_number'], unique=False)
    
    # Create document_versions table
    op.create_table(
        'document_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.tenant_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('version_id'),
        sa.UniqueConstraint('document_id', 'version_number', name='uq_document_version')
    )
    op.create_index(op.f('ix_document_versions_document_id'), 'document_versions', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_versions_tenant_id'), 'document_versions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_versions_content_hash'), 'document_versions', ['content_hash'], unique=False)
    op.create_index(op.f('ix_document_versions_created_by'), 'document_versions', ['created_by'], unique=False)
    
    # Enable RLS on document_versions table
    op.execute("ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY document_versions_isolation_policy ON document_versions
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    # Create RLS policy for Uber Admin bypass
    op.execute("""
        CREATE POLICY document_versions_uber_admin_bypass ON document_versions
        FOR ALL
        USING (current_setting('app.current_role', true) = 'uber_admin')
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS document_versions_uber_admin_bypass ON document_versions")
    op.execute("DROP POLICY IF EXISTS document_versions_isolation_policy ON document_versions")
    
    # Drop document_versions table
    op.drop_index(op.f('ix_document_versions_created_by'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_content_hash'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_tenant_id'), table_name='document_versions')
    op.drop_index(op.f('ix_document_versions_document_id'), table_name='document_versions')
    op.drop_table('document_versions')
    
    # Remove columns from documents table
    op.drop_index(op.f('ix_documents_version_number'), table_name='documents')
    op.drop_column('documents', 'deleted_at')
    op.drop_column('documents', 'version_number')

