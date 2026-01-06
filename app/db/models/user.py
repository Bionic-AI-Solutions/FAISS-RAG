"""
User model for tenant-scoped user management.
"""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantScopedModel

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant
    from app.db.models.document import Document
    from app.db.models.audit_log import AuditLog


class User(TenantScopedModel):
    """
    User model representing a user within a tenant.
    
    Each user belongs to a tenant and is isolated to that tenant's data.
    """
    
    __tablename__ = "users"
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the user"
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User email address (unique across all tenants)"
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="end_user",
        index=True,
        comment="User role (uber_admin, tenant_admin, project_admin, end_user). Legacy roles 'user' and 'viewer' map to 'end_user'"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
        lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('uber_admin', 'tenant_admin', 'project_admin', 'end_user', 'user', 'viewer')",
            name="check_user_role"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email}, role={self.role}, tenant_id={self.tenant_id})>"

