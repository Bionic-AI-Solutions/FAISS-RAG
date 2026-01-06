"""
Base repository class for database operations.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository class providing common CRUD operations.
    
    All repositories should inherit from this class.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        # Get primary key column
        pk_columns = list(self.model.__table__.primary_key.columns)
        if not pk_columns:
            raise ValueError(f"Model {self.model.__name__} has no primary key")
        
        pk_column = pk_columns[0]
        result = await self.session.execute(
            select(self.model).where(pk_column == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[UUID] = None,
    ) -> List[ModelType]:
        """
        Get all records with optional pagination and tenant filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply tenant filtering if tenant_id is provided and model has tenant_id
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Model attributes
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            id: Record ID
            **kwargs: Attributes to update
            
        Returns:
            Updated model instance or None if not found
        """
        pk_column = self.model.__table__.primary_key.columns.values()[0]
        await self.session.execute(
            update(self.model)
            .where(pk_column == id)
            .values(**kwargs)
        )
        await self.session.flush()
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
    
    async def count(self, tenant_id: Optional[UUID] = None) -> int:
        """
        Count records with optional tenant filtering.
        
        Args:
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            Number of records
        """
        from sqlalchemy import func
        
        query = select(func.count()).select_from(self.model)
        
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0

