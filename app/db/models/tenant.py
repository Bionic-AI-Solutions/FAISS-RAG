"""
Tenant model for multi-tenant isolation.
"""

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.document import Document
    from app.db.models.audit_log import AuditLog
    from app.db.models.tenant_api_key import TenantApiKey
    from app.db.models.tenant_config import TenantConfig


class Tenant(BaseModel):
    """
    Tenant model representing a multi-tenant organization.
    
    Each tenant is isolated from others and has its own users, documents, and data.
    """
    
    __tablename__ = "tenants"
    
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the tenant"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Tenant organization name"
    )
    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="Tenant domain name (e.g., example.com)"
    )
    subscription_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="basic",
        comment="Subscription tier (basic, premium, enterprise)"
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    api_keys: Mapped[list["TenantApiKey"]] = relationship(
        "TenantApiKey",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    config: Mapped["TenantConfig | None"] = relationship(
        "TenantConfig",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "subscription_tier IN ('basic', 'premium', 'enterprise')",
            name="check_subscription_tier"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Tenant(tenant_id={self.tenant_id}, name={self.name}, domain={self.domain})>"





