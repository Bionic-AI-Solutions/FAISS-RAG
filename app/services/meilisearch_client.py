"""
Meilisearch client setup with tenant-scoped index support.
"""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

import structlog
from meilisearch import Client
from meilisearch.errors import MeilisearchError

from app.config.meilisearch import meilisearch_settings

logger = structlog.get_logger(__name__)


# Global Meilisearch client instance
_meilisearch_client: Optional[Client] = None


def create_meilisearch_client() -> Client:
    """
    Create Meilisearch client instance.
    
    Returns:
        Client: Configured Meilisearch client
    """
    global _meilisearch_client
    
    if _meilisearch_client is None:
        _meilisearch_client = Client(
            meilisearch_settings.url,
            api_key=meilisearch_settings.api_key,
            timeout=meilisearch_settings.timeout / 1000,  # Convert ms to seconds
        )
    
    return _meilisearch_client


async def get_tenant_index_name(tenant_id: str) -> str:
    """
    Get the Meilisearch index name for a tenant.
    
    Args:
        tenant_id: Tenant ID (UUID string)
        
    Returns:
        str: Index name (tenant-scoped: tenant-{tenant_id})
    """
    return f"tenant-{tenant_id}"


async def create_tenant_index(tenant_id: str) -> None:
    """
    Create a tenant-scoped Meilisearch index.
    
    Args:
        tenant_id: Tenant ID (UUID string)
        
    Raises:
        MeilisearchError: If index creation fails
    """
    client = create_meilisearch_client()
    index_name = await get_tenant_index_name(tenant_id)
    
    try:
        # Try to get existing index
        try:
            index = client.get_index(index_name)
            # Index already exists, just update settings
            logger.info(f"Meilisearch index {index_name} already exists, updating settings")
        except MeilisearchError:
            # Index doesn't exist, create it
            index = client.create_index(index_name)
            logger.info(f"Created Meilisearch index {index_name}")
        
        # Configure index settings for tenant isolation
        # Set filterable attributes to include tenant_id for isolation
        index.update_filterable_attributes(["tenant_id"])
        
        # Set searchable attributes (can be customized per tenant later)
        index.update_searchable_attributes(["content", "title", "metadata"])
        
    except MeilisearchError as e:
        # Log error but don't fail registration if index creation fails
        logger.error(
            f"Failed to create/configure Meilisearch index {index_name}",
            error=str(e)
        )
        raise


async def add_document_to_index(
    tenant_id: str,
    document_id: str,
    title: str,
    content: str,
    metadata: Optional[dict] = None,
) -> None:
    """
    Add a document to the tenant's Meilisearch index.
    
    Args:
        tenant_id: Tenant ID (UUID string)
        document_id: Document ID (UUID string)
        title: Document title
        content: Document content (text)
        metadata: Optional document metadata dictionary
        
    Raises:
        MeilisearchError: If document addition fails
    """
    client = create_meilisearch_client()
    index_name = await get_tenant_index_name(tenant_id)
    
    try:
        # Get or create index
        try:
            index = client.get_index(index_name)
        except MeilisearchError:
            # Index doesn't exist, create it
            await create_tenant_index(tenant_id)
            index = client.get_index(index_name)
        
        # Prepare document for indexing
        document = {
            "id": document_id,
            "tenant_id": tenant_id,
            "title": title,
            "content": content,
            "metadata": metadata or {},
        }
        
        # Add document to index
        index.add_documents([document])
        
        logger.info(
            "Document added to Meilisearch index",
            tenant_id=tenant_id,
            document_id=document_id,
            index_name=index_name,
        )
        
    except MeilisearchError as e:
        logger.error(
            "Error adding document to Meilisearch index",
            tenant_id=tenant_id,
            document_id=document_id,
            error=str(e),
        )
        raise


async def remove_document_from_index(
    tenant_id: str,
    document_id: str,
) -> None:
    """
    Remove a document from the tenant's Meilisearch index.
    
    Args:
        tenant_id: Tenant ID (UUID string)
        document_id: Document ID (UUID string)
        
    Raises:
        MeilisearchError: If document removal fails
    """
    client = create_meilisearch_client()
    index_name = await get_tenant_index_name(tenant_id)
    
    try:
        # Get index
        index = client.get_index(index_name)
        
        # Delete document from index
        index.delete_document(document_id)
        
        logger.info(
            "Document removed from Meilisearch index",
            tenant_id=tenant_id,
            document_id=document_id,
            index_name=index_name,
        )
        
    except MeilisearchError as e:
        # If index doesn't exist or document not found, log warning but don't fail
        if "not found" in str(e).lower():
            logger.warning(
                "Document or index not found in Meilisearch",
                tenant_id=tenant_id,
                document_id=document_id,
                error=str(e),
            )
        else:
            logger.error(
                "Error removing document from Meilisearch index",
                tenant_id=tenant_id,
                document_id=document_id,
                error=str(e),
            )
            raise


async def search_documents(
    tenant_id: str,
    query: str,
    k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Tuple[str, float]]:
    """
    Search documents in the tenant's Meilisearch index.
    
    Args:
        tenant_id: Tenant ID (UUID string)
        query: Search query text
        k: Number of results to return (default: 10)
        filters: Optional filters (e.g., {"document_type": "text", "tags": ["tag1"]})
        
    Returns:
        List of tuples: [(document_id, relevance_score), ...]
        Results are sorted by relevance (highest first)
        Relevance scores are normalized by Meilisearch (typically 0-1 range)
        
    Raises:
        MeilisearchError: If search fails
        ValueError: If query is empty
    """
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    
    client = create_meilisearch_client()
    index_name = await get_tenant_index_name(tenant_id)
    
    try:
        # Get index
        try:
            index = client.get_index(index_name)
        except MeilisearchError:
            # Index doesn't exist, return empty results
            logger.warning(
                "Meilisearch index not found for tenant, returning empty results",
                tenant_id=tenant_id,
                index_name=index_name,
            )
            return []
        
        # Build filter string for tenant isolation and additional filters
        # tenant_id is already enforced by index isolation, but we add it as a filter for extra safety
        filter_parts = [f"tenant_id = {tenant_id}"]
        
        if filters:
            # Add document_type filter if provided
            if "document_type" in filters:
                doc_type = filters["document_type"]
                filter_parts.append(f'metadata.type = "{doc_type}"')
            
            # Add tags filter if provided
            if "tags" in filters and filters["tags"]:
                tags = filters["tags"]
                if isinstance(tags, list):
                    # Meilisearch filter syntax: tags IN ["tag1", "tag2"]
                    tag_list = ", ".join([f'"{tag}"' for tag in tags])
                    filter_parts.append(f"metadata.tags IN [{tag_list}]")
                elif isinstance(tags, str):
                    filter_parts.append(f'metadata.tags = "{tags}"')
            
            # Add date range filter if provided
            if "date_from" in filters or "date_to" in filters:
                # Note: Meilisearch doesn't support date filtering directly
                # We'll need to handle this in post-processing or use a different approach
                # For now, we'll skip date filtering at the Meilisearch level
                logger.debug(
                    "Date range filtering not supported in Meilisearch, will be handled post-search",
                    tenant_id=tenant_id,
                )
        
        filter_string = " AND ".join(filter_parts) if len(filter_parts) > 1 else filter_parts[0]
        
        # Perform search
        search_results = index.search(
            query,
            {
                "limit": k,
                "filter": filter_string,
                "attributesToRetrieve": ["id", "title", "content", "metadata"],
            }
        )
        
        # Extract document IDs and relevance scores
        results: List[Tuple[str, float]] = []
        
        for hit in search_results.get("hits", []):
            document_id = hit.get("id")
            # Meilisearch provides _rankingScore or _formatted fields
            # Use _rankingScore if available, otherwise use a default score
            relevance_score = hit.get("_rankingScore", hit.get("_score", 1.0))
            
            if document_id:
                results.append((document_id, float(relevance_score)))
        
        logger.debug(
            "Meilisearch search completed",
            tenant_id=tenant_id,
            query=query[:100],  # Log first 100 chars
            k_requested=k,
            k_returned=len(results),
            index_name=index_name,
        )
        
        return results
        
    except MeilisearchError as e:
        logger.error(
            "Error performing Meilisearch search",
            tenant_id=tenant_id,
            query=query[:100],
            index_name=index_name,
            error=str(e),
        )
        raise


async def check_meilisearch_health() -> dict[str, bool | str]:
    """
    Check Meilisearch connectivity and health.
    
    Returns:
        dict: Health check result with status and message
    """
    try:
        client = create_meilisearch_client()
        
        # Get health status
        health = client.health()
        
        if health.get("status") == "available":
            # Get search settings info
            try:
                indexes = client.get_indexes()
                return {
                    "status": True,
                    "message": f"Meilisearch is healthy (Indexes: {len(indexes.results)})",
                }
            except MeilisearchError:
                return {
                    "status": True,
                    "message": "Meilisearch is healthy (Unable to list indexes)",
                }
        return {"status": False, "message": f"Meilisearch status: {health.get('status')}"}
    except Exception as e:
        return {"status": False, "message": f"Meilisearch health check failed: {str(e)}"}






