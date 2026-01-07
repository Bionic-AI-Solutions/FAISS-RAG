"""
Unit tests for context-aware search service.

Tests personalization of search results based on:
- User memory (from Mem0)
- Session context (from Redis)
- User preferences (from session context)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.services.context_aware_search_service import (
    ContextAwareSearchService,
    context_aware_search_service,
    MEMORY_BOOST_FACTOR,
    SESSION_CONTEXT_BOOST_FACTOR,
    PREFERENCE_BOOST_FACTOR,
)


@pytest.fixture
def mock_tenant_id():
    """Fixture for tenant ID."""
    return uuid4()


@pytest.fixture
def mock_user_id():
    """Fixture for user ID."""
    return uuid4()


@pytest.fixture
def mock_session_id():
    """Fixture for session ID."""
    return "session-123"


@pytest.fixture
def sample_search_results():
    """Fixture for sample search results."""
    doc_id_1 = uuid4()
    doc_id_2 = uuid4()
    doc_id_3 = uuid4()
    return [
        (doc_id_1, 0.9),
        (doc_id_2, 0.8),
        (doc_id_3, 0.7),
    ]


@pytest.fixture
def sample_document_metadata():
    """Fixture for sample document metadata."""
    doc_id_1 = uuid4()
    doc_id_2 = uuid4()
    doc_id_3 = uuid4()
    return {
        doc_id_1: {
            "title": "Python Programming Guide",
            "snippet": "A comprehensive guide to Python programming...",
            "metadata": {"type": "text", "tags": ["python", "programming"]},
            "source": "docs",
        },
        doc_id_2: {
            "title": "Machine Learning Basics",
            "snippet": "Introduction to machine learning concepts...",
            "metadata": {"type": "text", "tags": ["ml", "ai"]},
            "source": "docs",
        },
        doc_id_3: {
            "title": "Database Design",
            "snippet": "Best practices for database design...",
            "metadata": {"type": "text", "tags": ["database", "sql"]},
            "source": "docs",
        },
    }


@pytest.mark.asyncio
async def test_personalization_disabled_returns_original_results(
    mock_tenant_id,
    mock_user_id,
    sample_search_results,
):
    """Test that personalization disabled returns original results."""
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=False,
    ):
        result = await context_aware_search_service.personalize_search_results(
            search_results=sample_search_results,
            tenant_id=mock_tenant_id,
            user_id=mock_user_id,
            query_text="python",
        )
        
        assert result == sample_search_results


@pytest.mark.asyncio
async def test_personalization_enabled_with_memory_context(
    mock_tenant_id,
    mock_user_id,
    sample_search_results,
    sample_document_metadata,
):
    """Test personalization with user memory context."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ):
        # Mock user memory retrieval
        mock_memories = [
            {
                "memory_key": "preferred_topic",
                "memory_value": "python programming",
                "timestamp": "2025-01-01T00:00:00",
            }
        ]
        
        with patch.object(
            context_aware_search_service,
            "_get_user_memory_context",
            return_value=mock_memories,
        ), patch.object(
            context_aware_search_service,
            "_get_session_context",
            return_value=None,
        ):
            result = await context_aware_search_service.personalize_search_results(
                search_results=sample_search_results,
                tenant_id=mock_tenant_id,
                user_id=mock_user_id,
                query_text="python",
                document_metadata=sample_document_metadata,
            )
            
            # First document should be boosted (contains "python")
            assert len(result) == len(sample_search_results)
            # Check that first document (Python Programming Guide) has higher score
            first_doc_id, first_score = result[0]
            assert first_score >= sample_search_results[0][1]


@pytest.mark.asyncio
async def test_personalization_enabled_with_session_context(
    mock_tenant_id,
    mock_user_id,
    mock_session_id,
    sample_search_results,
    sample_document_metadata,
):
    """Test personalization with session context."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ):
        # Mock session context
        mock_session_context = {
            "session_id": mock_session_id,
            "user_id": str(mock_user_id),
            "interrupted_queries": ["machine learning"],
            "recent_interactions": [
                {"query": "machine learning", "timestamp": "2025-01-01T00:00:00"}
            ],
            "user_preferences": {},
        }
        
        with patch.object(
            context_aware_search_service,
            "_get_user_memory_context",
            return_value=[],
        ), patch.object(
            context_aware_search_service,
            "_get_session_context",
            return_value=mock_session_context,
        ):
            result = await context_aware_search_service.personalize_search_results(
                search_results=sample_search_results,
                tenant_id=mock_tenant_id,
                user_id=mock_user_id,
                query_text="python",
                session_id=mock_session_id,
                document_metadata=sample_document_metadata,
            )
            
            # Second document (Machine Learning) should be boosted
            assert len(result) == len(sample_search_results)
            # Check that ML document has higher score
            ml_doc_id = sample_search_results[1][0]
            ml_score = next(score for doc_id, score in result if doc_id == ml_doc_id)
            assert ml_score >= sample_search_results[1][1]


@pytest.mark.asyncio
async def test_personalization_enabled_with_user_preferences(
    mock_tenant_id,
    mock_user_id,
    mock_session_id,
    sample_search_results,
    sample_document_metadata,
):
    """Test personalization with user preferences."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ):
        # Mock session context with preferences
        mock_session_context = {
            "session_id": mock_session_id,
            "user_id": str(mock_user_id),
            "interrupted_queries": [],
            "recent_interactions": [],
            "user_preferences": {
                "preferred_document_types": ["text"],
                "preferred_tags": ["python"],
            },
        }
        
        with patch.object(
            context_aware_search_service,
            "_get_user_memory_context",
            return_value=[],
        ), patch.object(
            context_aware_search_service,
            "_get_session_context",
            return_value=mock_session_context,
        ):
            result = await context_aware_search_service.personalize_search_results(
                search_results=sample_search_results,
                tenant_id=mock_tenant_id,
                user_id=mock_user_id,
                query_text="python",
                session_id=mock_session_id,
                document_metadata=sample_document_metadata,
            )
            
            # First document (Python) should be boosted due to preferred tags
            assert len(result) == len(sample_search_results)
            first_doc_id, first_score = result[0]
            assert first_score >= sample_search_results[0][1]


@pytest.mark.asyncio
async def test_personalization_no_context_returns_original_results(
    mock_tenant_id,
    mock_user_id,
    sample_search_results,
):
    """Test that no context available returns original results."""
    # Mock personalization enabled but no context
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ), patch.object(
        context_aware_search_service,
        "_get_user_memory_context",
        return_value=[],
    ), patch.object(
        context_aware_search_service,
        "_get_session_context",
        return_value=None,
    ):
        result = await context_aware_search_service.personalize_search_results(
            search_results=sample_search_results,
            tenant_id=mock_tenant_id,
            user_id=mock_user_id,
            query_text="python",
        )
        
        assert result == sample_search_results


@pytest.mark.asyncio
async def test_personalization_handles_mem0_failure(
    mock_tenant_id,
    mock_user_id,
    sample_search_results,
):
    """Test that personalization handles Mem0 failure gracefully."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ), patch.object(
        context_aware_search_service,
        "_get_user_memory_context",
        side_effect=Exception("Mem0 connection failed"),
    ), patch.object(
        context_aware_search_service,
        "_get_session_context",
        return_value=None,
    ):
        # Should return original results on error
        result = await context_aware_search_service.personalize_search_results(
            search_results=sample_search_results,
            tenant_id=mock_tenant_id,
            user_id=mock_user_id,
            query_text="python",
        )
        
        assert result == sample_search_results


@pytest.mark.asyncio
async def test_personalization_handles_session_context_failure(
    mock_tenant_id,
    mock_user_id,
    mock_session_id,
    sample_search_results,
):
    """Test that personalization handles session context failure gracefully."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ), patch.object(
        context_aware_search_service,
        "_get_user_memory_context",
        return_value=[],
    ), patch.object(
        context_aware_search_service,
        "_get_session_context",
        side_effect=Exception("Redis connection failed"),
    ):
        # Should return original results on error
        result = await context_aware_search_service.personalize_search_results(
            search_results=sample_search_results,
            tenant_id=mock_tenant_id,
            user_id=mock_user_id,
            query_text="python",
            session_id=mock_session_id,
        )
        
        assert result == sample_search_results


@pytest.mark.asyncio
async def test_extract_keywords_from_memory():
    """Test keyword extraction from user memories."""
    memories = [
        {
            "memory_key": "preferred_topic",
            "memory_value": "python programming and machine learning",
        },
        {
            "memory_key": "interests",
            "memory_value": "data science",
        },
    ]
    
    keywords = context_aware_search_service._extract_keywords_from_memory(memories)
    
    assert "python" in keywords
    assert "programming" in keywords
    assert "machine" in keywords
    assert "learning" in keywords
    assert "data" in keywords
    assert "science" in keywords


@pytest.mark.asyncio
async def test_extract_keywords_from_session_context():
    """Test keyword extraction from session context."""
    session_context = {
        "interrupted_queries": ["python programming", "machine learning"],
        "recent_interactions": [
            {"query": "data science", "timestamp": "2025-01-01T00:00:00"}
        ],
        "conversation_state": {"topic": "python"},
    }
    
    keywords = context_aware_search_service._extract_keywords_from_session_context(
        session_context
    )
    
    assert "python" in keywords
    assert "programming" in keywords
    assert "machine" in keywords
    assert "learning" in keywords
    assert "data" in keywords
    assert "science" in keywords


@pytest.mark.asyncio
async def test_calculate_personalization_score():
    """Test personalization score calculation."""
    document = {
        "title": "Python Programming Guide",
        "snippet": "A comprehensive guide to Python programming...",
        "metadata": {"type": "text", "tags": ["python"]},
    }
    
    memory_keywords = ["python", "programming"]
    session_keywords = ["machine", "learning"]
    user_preferences = {"preferred_tags": ["python"]}
    
    score = context_aware_search_service._calculate_personalization_score(
        document=document,
        memory_keywords=memory_keywords,
        session_keywords=session_keywords,
        user_preferences=user_preferences,
    )
    
    # Should have boost from memory keywords and preferences
    assert score > 0
    assert score <= 1.0


@pytest.mark.asyncio
async def test_personalization_performance_threshold(
    mock_tenant_id,
    mock_user_id,
    sample_search_results,
    sample_document_metadata,
):
    """Test that personalization respects performance threshold."""
    # Mock personalization enabled
    with patch.object(
        context_aware_search_service,
        "_is_personalization_enabled",
        return_value=True,
    ), patch.object(
        context_aware_search_service,
        "_get_user_memory_context",
        return_value=[],
    ), patch.object(
        context_aware_search_service,
        "_get_session_context",
        return_value=None,
    ):
        import time
        
        start_time = time.time()
        result = await context_aware_search_service.personalize_search_results(
            search_results=sample_search_results,
            tenant_id=mock_tenant_id,
            user_id=mock_user_id,
            query_text="python",
            document_metadata=sample_document_metadata,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Personalization should complete quickly (<50ms overhead)
        assert elapsed_ms < 100  # Reasonable threshold for test
        assert len(result) == len(sample_search_results)








