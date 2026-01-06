"""
Base model class for SQLAlchemy models with common fields and utilities.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.orm import Mapped, mapped_column

# Base class for all models
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and utilities.
    All models should inherit from this class.
    """
    
    __abstract__ = True
    
    # Common fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TenantScopedModel(BaseModel):
    """
    Base model for tenant-scoped tables.
    All tenant-scoped models should inherit from this class.
    """
    
    __abstract__ = True
    
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table for multi-tenant isolation"
    )

