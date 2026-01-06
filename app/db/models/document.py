"""
Document model for storing document metadata.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import String, ForeignKey, JSON, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantScopedModel

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant
    from app.db.models.user import User
    from app.db.models.document_version import DocumentVersion


class Document(TenantScopedModel):
    """
    Document model representing a document within a tenant.
    
    Documents are tenant-scoped and user-scoped for proper isolation.
    """
    
    __tablename__ = "documents"
    
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the document"
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to users table (document owner)"
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Document title"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash of document content for deduplication"
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Additional document metadata (JSON)"
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Current version number (starts at 1)"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        "deleted_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp (NULL if not deleted)"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="documents",
        lazy="selectin"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
        lazy="selectin"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        lazy="selectin",
        order_by="DocumentVersion.version_number"
    )
    
    def __repr__(self) -> str:
        return f"<Document(document_id={self.document_id}, title={self.title}, tenant_id={self.tenant_id}, user_id={self.user_id}, version={self.version_number})>"

