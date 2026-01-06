"""
Repository for Template model operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.template import Template
from app.db.repositories.base_repository import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Template, session)
    
    async def get_by_template_id(self, template_id: UUID) -> Optional[Template]:
        """
        Get template by template_id.
        
        Args:
            template_id: Template UUID
            
        Returns:
            Template instance or None if not found
        """
        return await self.get_by_id(template_id)
    
    async def get_by_name(self, template_name: str) -> Optional[Template]:
        """
        Get template by name.
        
        Args:
            template_name: Template name
            
        Returns:
            Template instance or None if not found
        """
        result = await self.session.execute(
            select(Template).where(Template.template_name == template_name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_domain_type(self, domain_type: str) -> List[Template]:
        """
        Get templates by domain type.
        
        Args:
            domain_type: Domain type (fintech, healthcare, retail, customer_service, custom)
            
        Returns:
            List of Template instances
        """
        result = await self.session.execute(
            select(Template).where(Template.domain_type == domain_type)
        )
        return list(result.scalars().all())
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Template]:
        """
        List all templates with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Template instances
        """
        return await self.get_all(skip=skip, limit=limit)

