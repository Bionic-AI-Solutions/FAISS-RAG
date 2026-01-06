"""
TenantApiKey model for managing tenant API keys.
"""

from typing import TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantScopedModel

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant


class TenantApiKey(TenantScopedModel):
    """
    TenantApiKey model for managing API keys for tenant authentication.
    
    API keys are hashed before storage and can have expiration dates.
    """
    
    __tablename__ = "tenant_api_keys"
    
    key_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the API key"
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Hashed API key (SHA-256 or bcrypt hash, never store plaintext)"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name for the API key"
    )
    permissions: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string of permissions granted to this API key"
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Expiration timestamp for the API key (NULL = never expires)"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="api_keys",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<TenantApiKey(key_id={self.key_id}, name={self.name}, tenant_id={self.tenant_id}, expires_at={self.expires_at})>"





