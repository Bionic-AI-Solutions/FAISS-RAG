"""create custom variables

Revision ID: 006_create_custom_variables
Revises: 005_add_document_versioning
Create Date: 2026-01-07 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '006_create_custom_variables'
down_revision: Union[str, None] = '005_add_document_versioning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create custom PostgreSQL configuration variables for RLS enforcement.
    
    These variables are used by RLS policies to enforce tenant isolation
    and role-based access control.
    """
    # Note: PostgreSQL doesn't require explicit creation of custom variables
    # They can be set dynamically with SET/SET LOCAL
    # However, we can set them at the database level for documentation
    
    # Set default values (NULL) for the custom variables
    # This doesn't create them, but documents their existence
    # The variables will be set per-session in app/db/connection.py
    
    # For PostgreSQL 9.2+, custom variables work automatically
    # We just need to ensure they're documented and used consistently
    pass


def downgrade() -> None:
    """No action needed - variables are session-scoped."""
    pass


