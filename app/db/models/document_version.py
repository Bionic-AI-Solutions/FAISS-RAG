"""
DocumentVersion model for storing document version history.
"""

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantScopedModel

if TYPE_CHECKING:
    from app.db.models.document import Document
    from app.db.models.user import User


class DocumentVersion(TenantScopedModel):
    """
    DocumentVersion model representing a version of a document.
    
    Stores version history for documents, allowing tracking of changes over time.
    """
    
    __tablename__ = "document_versions"
    
    version_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the version"
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to documents table"
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Version number (1, 2, 3, ...)"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash of document content for this version"
    )
    created_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User ID who created this version"
    )
    change_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Summary of changes in this version"
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="Version-specific metadata (JSON)"
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="versions",
        lazy="selectin"
    )
    creator: Mapped["User | None"] = relationship(
        "User",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<DocumentVersion(version_id={self.version_id}, document_id={self.document_id}, version_number={self.version_number})>"








