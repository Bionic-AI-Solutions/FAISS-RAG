"""enable rls

Revision ID: 002_enable_rls
Revises: 001_initial_schema
Create Date: 2025-01-15 12:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_enable_rls'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable Row Level Security on tenant-scoped tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenant_api_keys ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy for users table: users can only access their tenant's data
    op.execute("""
        CREATE POLICY tenant_isolation_users ON users
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    # Create RLS policy for documents table: users can only access their tenant's documents
    op.execute("""
        CREATE POLICY tenant_isolation_documents ON documents
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    # Create RLS policy for audit_logs table: users can only access their tenant's audit logs
    op.execute("""
        CREATE POLICY tenant_isolation_audit_logs ON audit_logs
        FOR ALL
        USING (
            tenant_id IS NULL OR 
            tenant_id = current_setting('app.current_tenant_id', true)::uuid
        )
    """)
    
    # Create RLS policy for tenant_api_keys table: users can only access their tenant's API keys
    op.execute("""
        CREATE POLICY tenant_isolation_tenant_api_keys ON tenant_api_keys
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    # Create policy for Uber Admin role to bypass RLS
    op.execute("""
        CREATE POLICY uber_admin_bypass_users ON users
        FOR ALL
        TO postgres
        USING (true)
        WITH CHECK (true)
    """)
    
    op.execute("""
        CREATE POLICY uber_admin_bypass_documents ON documents
        FOR ALL
        TO postgres
        USING (true)
        WITH CHECK (true)
    """)
    
    op.execute("""
        CREATE POLICY uber_admin_bypass_audit_logs ON audit_logs
        FOR ALL
        TO postgres
        USING (true)
        WITH CHECK (true)
    """)
    
    op.execute("""
        CREATE POLICY uber_admin_bypass_tenant_api_keys ON tenant_api_keys
        FOR ALL
        TO postgres
        USING (true)
        WITH CHECK (true)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS uber_admin_bypass_tenant_api_keys ON tenant_api_keys")
    op.execute("DROP POLICY IF EXISTS uber_admin_bypass_audit_logs ON audit_logs")
    op.execute("DROP POLICY IF EXISTS uber_admin_bypass_documents ON documents")
    op.execute("DROP POLICY IF EXISTS uber_admin_bypass_users ON users")
    
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tenant_api_keys ON tenant_api_keys")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_audit_logs ON audit_logs")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_documents ON documents")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    
    # Disable RLS
    op.execute("ALTER TABLE tenant_api_keys DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")












