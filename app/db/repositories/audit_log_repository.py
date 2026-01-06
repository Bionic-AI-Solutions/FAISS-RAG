"""
Repository for AuditLog model operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog operations with tenant isolation."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
    
    async def get_by_action(
        self,
        action: str,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs by action with optional tenant filtering.
        
        Args:
            action: Action name
            tenant_id: Optional tenant ID for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AuditLog instances
        """
        query = select(AuditLog).where(AuditLog.action == action)
        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
        
        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        tenant_id: Optional[UUID] = None,
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            tenant_id: Optional tenant ID for filtering
            
        Returns:
            List of AuditLog instances
        """
        query = select(AuditLog).where(
            and_(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
        )
        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
        
        query = query.order_by(AuditLog.timestamp.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs within a time range.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            tenant_id: Optional tenant ID for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AuditLog instances
        """
        query = select(AuditLog).where(
            and_(
                AuditLog.timestamp >= start_time,
                AuditLog.timestamp <= end_time
            )
        )
        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
        
        query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())





