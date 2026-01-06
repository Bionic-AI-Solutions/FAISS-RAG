"""
AuditLog model for tracking all system operations.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import String, ForeignKey, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant
    from app.db.models.user import User


class AuditLog(BaseModel):
    """
    AuditLog model for tracking all system operations and changes.
    
    Provides audit trail for compliance and security monitoring.
    """
    
    __tablename__ = "audit_logs"
    
    log_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the audit log entry"
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to tenants table (nullable for system-level operations)"
    )
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to users table (nullable for system-level operations)"
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (e.g., 'create', 'update', 'delete', 'search')"
    )
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of resource affected (e.g., 'document', 'user', 'tenant')"
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Identifier of the affected resource"
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional details about the action (JSON)"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp when the action occurred"
    )
    
    # Override created_at to use timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created (same as timestamp)"
    )
    
    # Relationships
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant",
        back_populates="audit_logs",
        lazy="selectin"
    )
    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, action={self.action}, resource_type={self.resource_type}, tenant_id={self.tenant_id})>"

