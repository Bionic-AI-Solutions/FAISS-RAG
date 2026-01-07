"""
Context-aware search service for personalizing search results.

Personalizes search results based on:
- User memory (from Mem0)
- Session context (from Redis)
- User preferences (from session context)

Personalization is optional and configurable per tenant.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import structlog

from app.db.connection import get_db_session
from app.db.repositories.tenant_config_repository import TenantConfigRepository
from app.services.mem0_client import Mem0Client
from app.services.session_context import get_session_context_service
from app.utils.errors import ValidationError

logger = structlog.get_logger(__name__)

# Singleton instances
mem0_client = Mem0Client()
session_context_service = get_session_context_service()

# Personalization boost factors
MEMORY_BOOST_FACTOR = 0.15  # Boost documents matching user memory
SESSION_CONTEXT_BOOST_FACTOR = 0.10  # Boost documents matching session context
PREFERENCE_BOOST_FACTOR = 0.10  # Boost documents matching user preferences


class ContextAwareSearchService:
    """
    Service for personalizing search results based on user context.
    
    Personalization factors:
    1. User memory: Documents matching user's historical preferences/interests
    2. Session context: Documents related to recent interactions or interrupted queries
    3. User preferences: Documents matching user's configured preferences
    
    Performance target: <200ms p95 (personalization overhead)
    """
    
    def __init__(self):
        """Initialize context-aware search service."""
        self.mem0_client = mem0_client
        self.session_context_service = session_context_service
    
    async def _is_personalization_enabled(
        self,
        tenant_id: UUID,
    ) -> bool:
        """
        Check if personalization is enabled for the tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            bool: True if personalization is enabled, False otherwise
        """
        try:
            async for session in get_db_session():
                config_repo = TenantConfigRepository(session)
                tenant_config = await config_repo.get_by_tenant_id(tenant_id)
                
                if not tenant_config:
                    # No config found, default to disabled
                    return False
                
                # Check custom_configuration for personalization setting
                custom_config = tenant_config.custom_configuration or {}
                personalization_enabled = custom_config.get("personalization_enabled", False)
                
                return bool(personalization_enabled)
        except Exception as e:
            logger.warning(
                "Failed to check personalization setting, defaulting to disabled",
                tenant_id=str(tenant_id),
                error=str(e)
            )
            return False
    
    async def _get_user_memory_context(
        self,
        user_id: UUID,
        query_text: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user memory context relevant to the search query.
        
        Args:
            user_id: User UUID
            query_text: Search query text
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memory entries relevant to the query
        """
        try:
            # Ensure Mem0 client is initialized
            await self.mem0_client.initialize()
            
            # Search user memories for relevant context
            memory_result = await self.mem0_client.search_memory(
                query=query_text,
                user_id=str(user_id),
                limit=limit,
            )
            
            if memory_result.get("success"):
                memories = memory_result.get("results", [])
                logger.debug(
                    "Retrieved user memory context",
                    user_id=str(user_id),
                    query_length=len(query_text),
                    memory_count=len(memories)
                )
                return memories
            else:
                logger.debug(
                    "No user memory context found",
                    user_id=str(user_id),
                    query_length=len(query_text)
                )
                return []
        except Exception as e:
            logger.warning(
                "Failed to retrieve user memory context",
                user_id=str(user_id),
                error=str(e)
            )
            return []
    
    async def _get_session_context(
        self,
        session_id: Optional[str],
        user_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve session context for personalization.
        
        Args:
            session_id: Session ID (optional)
            user_id: User UUID
            
        Returns:
            Session context dictionary or None if not found
        """
        if not session_id:
            return None
        
        try:
            session_context = await self.session_context_service.get_session_context(
                session_id=session_id,
                user_id=user_id,
            )
            
            if session_context:
                logger.debug(
                    "Retrieved session context",
                    session_id=session_id,
                    user_id=str(user_id)
                )
            else:
                logger.debug(
                    "No session context found",
                    session_id=session_id,
                    user_id=str(user_id)
                )
            
            return session_context
        except Exception as e:
            logger.warning(
                "Failed to retrieve session context",
                session_id=session_id,
                user_id=str(user_id),
                error=str(e)
            )
            return None
    
    def _extract_keywords_from_memory(
        self,
        memories: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Extract keywords from user memories for matching.
        
        Args:
            memories: List of memory entries
            
        Returns:
            List of keywords extracted from memories
        """
        keywords = []
        
        for memory in memories:
            # Extract keywords from memory value/content
            memory_value = memory.get("memory_value") or memory.get("memory") or memory.get("value") or memory.get("content", "")
            memory_key = memory.get("memory_key") or memory.get("key", "")
            
            # Simple keyword extraction (split by spaces, filter short words)
            if memory_value:
                words = memory_value.lower().split()
                keywords.extend([w for w in words if len(w) > 3])  # Filter short words
            
            if memory_key:
                keywords.append(memory_key.lower())
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _extract_keywords_from_session_context(
        self,
        session_context: Dict[str, Any],
    ) -> List[str]:
        """
        Extract keywords from session context for matching.
        
        Args:
            session_context: Session context dictionary
            
        Returns:
            List of keywords extracted from session context
        """
        keywords = []
        
        # Extract from interrupted queries
        interrupted_queries = session_context.get("interrupted_queries", [])
        for query in interrupted_queries:
            if isinstance(query, str):
                words = query.lower().split()
                keywords.extend([w for w in words if len(w) > 3])
        
        # Extract from recent interactions
        recent_interactions = session_context.get("recent_interactions", [])
        for interaction in recent_interactions:
            if isinstance(interaction, dict):
                interaction_text = interaction.get("query") or interaction.get("text") or ""
                if interaction_text:
                    words = interaction_text.lower().split()
                    keywords.extend([w for w in words if len(w) > 3])
        
        # Extract from conversation state
        conversation_state = session_context.get("conversation_state", {})
        if isinstance(conversation_state, dict):
            for key, value in conversation_state.items():
                if isinstance(value, str):
                    words = value.lower().split()
                    keywords.extend([w for w in words if len(w) > 3])
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _extract_preferences_from_session_context(
        self,
        session_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract user preferences from session context.
        
        Args:
            session_context: Session context dictionary
            
        Returns:
            Dictionary of user preferences
        """
        user_preferences = session_context.get("user_preferences", {})
        
        if not isinstance(user_preferences, dict):
            return {}
        
        return user_preferences
    
    def _calculate_personalization_score(
        self,
        document: Dict[str, Any],
        memory_keywords: List[str],
        session_keywords: List[str],
        user_preferences: Dict[str, Any],
    ) -> float:
        """
        Calculate personalization boost score for a document.
        
        Args:
            document: Document result dictionary (with title, snippet, metadata)
            memory_keywords: Keywords extracted from user memory
            session_keywords: Keywords extracted from session context
            user_preferences: User preferences dictionary
            
        Returns:
            Personalization boost score (0.0 to 1.0)
        """
        boost_score = 0.0
        
        # Extract document text for matching
        document_text = (
            (document.get("title") or "") + " " +
            (document.get("snippet") or "") + " " +
            str(document.get("metadata", {}))
        ).lower()
        
        # Memory-based boost
        if memory_keywords:
            memory_matches = sum(1 for keyword in memory_keywords if keyword in document_text)
            if memory_matches > 0:
                memory_match_ratio = memory_matches / len(memory_keywords)
                boost_score += memory_match_ratio * MEMORY_BOOST_FACTOR
        
        # Session context-based boost
        if session_keywords:
            session_matches = sum(1 for keyword in session_keywords if keyword in document_text)
            if session_matches > 0:
                session_match_ratio = session_matches / len(session_keywords)
                boost_score += session_match_ratio * SESSION_CONTEXT_BOOST_FACTOR
        
        # User preferences-based boost
        if user_preferences:
            # Check if document matches user preferences (e.g., preferred document types, tags)
            preferred_types = user_preferences.get("preferred_document_types", [])
            preferred_tags = user_preferences.get("preferred_tags", [])
            
            document_type = document.get("metadata", {}).get("type") or document.get("source", "")
            document_tags = document.get("metadata", {}).get("tags", [])
            
            if preferred_types and document_type in preferred_types:
                boost_score += PREFERENCE_BOOST_FACTOR
            
            if preferred_tags and any(tag in document_tags for tag in preferred_tags):
                boost_score += PREFERENCE_BOOST_FACTOR
        
        return min(boost_score, 1.0)  # Cap at 1.0
    
    async def personalize_search_results(
        self,
        search_results: List[Tuple[UUID, float]],
        tenant_id: UUID,
        user_id: UUID,
        query_text: str,
        session_id: Optional[str] = None,
        document_metadata: Optional[Dict[UUID, Dict[str, Any]]] = None,
    ) -> List[Tuple[UUID, float]]:
        """
        Personalize search results based on user context.
        
        Args:
            search_results: List of (document_id, relevance_score) tuples
            tenant_id: Tenant ID
            user_id: User UUID
            query_text: Search query text
            session_id: Session ID (optional)
            document_metadata: Dictionary mapping document_id to metadata (optional)
            
        Returns:
            List of (document_id, personalized_score) tuples, sorted by score descending
        """
        start_time = time.time()
        
        # Check if personalization is enabled
        is_enabled = await self._is_personalization_enabled(tenant_id)
        
        if not is_enabled:
            logger.debug(
                "Personalization disabled for tenant, returning original results",
                tenant_id=str(tenant_id)
            )
            return search_results
        
        # Retrieve user context (concurrently for performance)
        memories = []
        session_context = None
        
        try:
            memory_task = self._get_user_memory_context(user_id, query_text)
            session_task = self._get_session_context(session_id, user_id) if session_id else None
            
            # Await both tasks, handling errors gracefully
            try:
                memories = await memory_task
            except Exception as e:
                logger.warning(
                    "Failed to retrieve user memory context",
                    tenant_id=str(tenant_id),
                    user_id=str(user_id),
                    error=str(e)
                )
                memories = []
            
            if session_task:
                try:
                    session_context = await session_task
                except Exception as e:
                    logger.warning(
                        "Failed to retrieve session context",
                        tenant_id=str(tenant_id),
                        user_id=str(user_id),
                        session_id=session_id,
                        error=str(e)
                    )
                    session_context = None
        except Exception as e:
            # If context retrieval fails completely, log and continue without personalization
            logger.warning(
                "Failed to retrieve user context for personalization, using original results",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                error=str(e)
            )
            return search_results
        
        # Extract keywords and preferences
        memory_keywords = self._extract_keywords_from_memory(memories) if memories else []
        session_keywords = self._extract_keywords_from_session_context(session_context) if session_context else []
        user_preferences = self._extract_preferences_from_session_context(session_context) if session_context else {}
        
        # If no context available, return original results
        if not memory_keywords and not session_keywords and not user_preferences:
            logger.debug(
                "No user context available for personalization",
                tenant_id=str(tenant_id),
                user_id=str(user_id)
            )
            return search_results
        
        # Personalize each result
        personalized_results: List[Tuple[UUID, float]] = []
        
        for doc_id, original_score in search_results:
            # Get document metadata if available
            document = document_metadata.get(doc_id, {}) if document_metadata else {}
            
            # Calculate personalization boost
            personalization_boost = self._calculate_personalization_score(
                document=document,
                memory_keywords=memory_keywords,
                session_keywords=session_keywords,
                user_preferences=user_preferences,
            )
            
            # Apply boost to original score
            personalized_score = original_score + personalization_boost
            
            personalized_results.append((doc_id, personalized_score))
        
        # Sort by personalized score descending
        personalized_results.sort(key=lambda x: x[1], reverse=True)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Log performance warning if personalization exceeds threshold
        if elapsed_ms > 50:  # Personalization should add <50ms overhead
            logger.warning(
                "Personalization exceeded performance threshold",
                tenant_id=str(tenant_id),
                user_id=str(user_id),
                elapsed_ms=elapsed_ms,
                threshold_ms=50
            )
        
        logger.info(
            "Search results personalized",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            original_count=len(search_results),
            personalized_count=len(personalized_results),
            elapsed_ms=elapsed_ms,
            memory_keywords_count=len(memory_keywords),
            session_keywords_count=len(session_keywords),
            has_preferences=bool(user_preferences)
        )
        
        return personalized_results


# Global context-aware search service instance
context_aware_search_service = ContextAwareSearchService()

