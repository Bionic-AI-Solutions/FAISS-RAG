"""
Template model for domain templates.
"""

from typing import Any
from uuid import uuid4

from sqlalchemy import String, CheckConstraint, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class Template(BaseModel):
    """
    Template model representing a domain template for tenant onboarding.
    
    Templates define domain-specific configurations, compliance requirements,
    and default settings for tenants.
    """
    
    __tablename__ = "templates"
    
    template_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier for the template"
    )
    template_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Template name (e.g., 'Fintech Template', 'Healthcare Template')"
    )
    domain_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Domain type (fintech, healthcare, retail, customer_service, custom)"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template description and use case"
    )
    compliance_checklist: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Compliance requirements checklist (JSON)"
    )
    default_configuration: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Default configuration settings (JSON)"
    )
    customization_options: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Available customization options (JSON)"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "domain_type IN ('fintech', 'healthcare', 'retail', 'customer_service', 'custom')",
            name="check_domain_type"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Template(template_id={self.template_id}, template_name={self.template_name}, domain_type={self.domain_type})>"








