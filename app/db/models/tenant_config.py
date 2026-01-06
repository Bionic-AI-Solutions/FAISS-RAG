"""
TenantConfig model for storing tenant-specific configuration.
"""

from typing import Any, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.tenant import Tenant
    from app.db.models.template import Template


class TenantConfig(BaseModel):
    """
    TenantConfig model for storing tenant-specific configuration.
    
    Stores template-based configuration, model settings, compliance settings,
    and other tenant-specific configurations.
    """
    
    __tablename__ = "tenant_configs"
    
    config_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the configuration"
    )
    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Foreign key to tenants table (one-to-one relationship)"
    )
    template_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("templates.template_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to templates table (template used for onboarding)"
    )
    model_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Model configuration (embedding_model, llm_model, etc.)"
    )
    compliance_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Compliance settings (PCI DSS, HIPAA, etc.) from template"
    )
    rate_limit_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Rate limiting configuration (requests_per_minute, burst_limit, etc.)"
    )
    data_isolation_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Data isolation configuration (enforced, level, etc.)"
    )
    audit_logging_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Audit logging configuration (enabled, retention_days, etc.)"
    )
    custom_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Custom tenant-specific configuration (extensible)"
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="config",
        lazy="selectin"
    )
    template: Mapped["Template | None"] = relationship(
        "Template",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<TenantConfig(config_id={self.config_id}, tenant_id={self.tenant_id}, template_id={self.template_id})>"

