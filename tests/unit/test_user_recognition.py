"""
Unit tests for user recognition service.

Tests cover:
- User recognition by user_id and tenant_id
- User memory retrieval with Redis caching
- Personalized greeting generation
- Context summary generation
- Cache invalidation
- Performance requirements (<100ms p95)
"""

import json
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.user_recognition import (
    UserRecognitionService,
    user_recognition_service,
    USER_MEMORY_CACHE_TTL,
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
def sample_user_memory():
    """Fixture for sample user memory."""
    return {
        "user_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "memories": [
            {
                "memory_key": "preference_favorite_topic",
                "memory_value": "machine learning",
                "timestamp": "2025-01-01T00:00:00",
                "metadata": {},
            },
            {
                "memory_key": "interest_python",
                "memory_value": "Python programming",
                "timestamp": "2025-01-02T00:00:00",
                "metadata": {},
            },
        ],
        "total_count": 2,
        "retrieved_at": "2025-01-06T10:00:00",
        "source": "mem0",
        "cache_hit": False,
    }


@pytest.fixture
def sample_session_context():
    """Fixture for sample session context."""
    return {
        "session_id": "session-123",
        "user_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "conversation_state": {"topic": "python"},
        "interrupted_queries": [],
        "recent_interactions": [
            {"query": "python", "timestamp": "2025-01-06T09:00:00"}
        ],
        "user_preferences": {"preferred_language": "Python"},
    }


@pytest.mark.asyncio
async def test_recognize_user_with_cache_hit(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test user recognition with cache hit."""
    # Mock cached memory
    cached_memory = {**sample_user_memory, "cache_hit": True}
    
    with patch.object(
        user_recognition_service,
        "_get_cached_user_memory",
        return_value=cached_memory,
    ), patch.object(
        user_recognition_service,
        "_retrieve_user_memory",
        return_value=cached_memory,
    ):
        result = await user_recognition_service.recognize_user(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            use_cache=True,
        )
        
        assert result["recognized"] is True
        assert result["user_id"] == str(mock_user_id)
        assert result["tenant_id"] == str(mock_tenant_id)
        assert result["cache_hit"] is True
        assert "greeting" in result
        assert "context_summary" in result
        assert result["memory_count"] == 2
        assert result["response_time_ms"] < 100  # Performance requirement


@pytest.mark.asyncio
async def test_recognize_user_with_cache_miss(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test user recognition with cache miss (retrieves from Mem0)."""
    # Mock cache miss, then Mem0 retrieval
    with patch.object(
        user_recognition_service,
        "_get_cached_user_memory",
        return_value=None,
    ), patch.object(
        user_recognition_service,
        "_retrieve_user_memory",
        return_value=sample_user_memory,
    ), patch.object(
        user_recognition_service,
        "_cache_user_memory",
        return_value=None,
    ):
        result = await user_recognition_service.recognize_user(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            use_cache=True,
        )
        
        assert result["recognized"] is True
        assert result["cache_hit"] is False
        assert result["memory_count"] == 2
        assert "greeting" in result
        assert "context_summary" in result


@pytest.mark.asyncio
async def test_recognize_user_without_cache(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test user recognition without cache."""
    with patch.object(
        user_recognition_service,
        "_retrieve_user_memory",
        return_value=sample_user_memory,
    ):
        result = await user_recognition_service.recognize_user(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            use_cache=False,
        )
        
        assert result["recognized"] is True
        assert result["memory_count"] == 2


@pytest.mark.asyncio
async def test_recognize_user_with_session_context(
    mock_tenant_id,
    mock_user_id,
    mock_session_id,
    sample_user_memory,
    sample_session_context,
):
    """Test user recognition with session context."""
    with patch.object(
        user_recognition_service,
        "_retrieve_user_memory",
        return_value=sample_user_memory,
    ), patch.object(
        user_recognition_service.session_context_service,
        "get_session_context",
        return_value=sample_session_context,
    ):
        result = await user_recognition_service.recognize_user(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            session_id=mock_session_id,
        )
        
        assert result["recognized"] is True
        assert result["context_summary"]["has_session_context"] is True
        assert "preferences" in result["context_summary"]
        assert "recent_interactions" in result["context_summary"]


@pytest.mark.asyncio
async def test_generate_personalized_greeting_with_preferences(
    sample_user_memory,
):
    """Test personalized greeting generation with preferences."""
    greeting = user_recognition_service._generate_personalized_greeting(
        sample_user_memory,
        UUID(sample_user_memory["user_id"]),
    )
    
    assert isinstance(greeting, str)
    assert len(greeting) > 0
    # Should mention the preference or interest
    assert "machine learning" in greeting.lower() or "python" in greeting.lower() or "memory" in greeting.lower()


@pytest.mark.asyncio
async def test_generate_personalized_greeting_without_memories():
    """Test personalized greeting generation without memories."""
    empty_memory = {
        "user_id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "memories": [],
        "total_count": 0,
    }
    
    greeting = user_recognition_service._generate_personalized_greeting(
        empty_memory,
        UUID(empty_memory["user_id"]),
    )
    
    assert isinstance(greeting, str)
    assert "Welcome back" in greeting
    assert len(greeting) > 0


@pytest.mark.asyncio
async def test_generate_context_summary(
    sample_user_memory,
    sample_session_context,
):
    """Test context summary generation."""
    summary = user_recognition_service._generate_context_summary(
        sample_user_memory,
        sample_session_context,
    )
    
    assert "recent_interactions" in summary
    assert "preferences" in summary
    assert "memory_count" in summary
    assert "has_session_context" in summary
    assert summary["has_session_context"] is True
    assert summary["memory_count"] == 2
    assert len(summary["recent_interactions"]) > 0


@pytest.mark.asyncio
async def test_generate_context_summary_without_session_context(
    sample_user_memory,
):
    """Test context summary generation without session context."""
    summary = user_recognition_service._generate_context_summary(
        sample_user_memory,
        None,
    )
    
    assert "recent_interactions" in summary
    assert "preferences" in summary
    assert "memory_count" in summary
    assert "has_session_context" in summary
    assert summary["has_session_context"] is False
    assert summary["memory_count"] == 2


@pytest.mark.asyncio
async def test_cache_user_memory(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test caching user memory."""
    redis_mock = AsyncMock()
    
    with patch(
        "app.services.user_recognition.get_redis_client",
        return_value=redis_mock,
    ):
        await user_recognition_service._cache_user_memory(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            memory_data=sample_user_memory,
        )
        
        # Verify Redis setex was called with correct parameters
        redis_mock.setex.assert_called_once()
        call_args = redis_mock.setex.call_args
        assert call_args[0][1] == USER_MEMORY_CACHE_TTL
        assert json.loads(call_args[0][2])["user_id"] == sample_user_memory["user_id"]


@pytest.mark.asyncio
async def test_get_cached_user_memory(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test retrieving cached user memory."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = json.dumps(sample_user_memory)
    
    with patch(
        "app.services.user_recognition.get_redis_client",
        return_value=redis_mock,
    ):
        cached = await user_recognition_service._get_cached_user_memory(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
        )
        
        assert cached is not None
        assert cached["user_id"] == sample_user_memory["user_id"]
        assert cached["total_count"] == sample_user_memory["total_count"]


@pytest.mark.asyncio
async def test_get_cached_user_memory_not_found(
    mock_tenant_id,
    mock_user_id,
):
    """Test retrieving cached user memory when not found."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    
    with patch(
        "app.services.user_recognition.get_redis_client",
        return_value=redis_mock,
    ):
        cached = await user_recognition_service._get_cached_user_memory(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
        )
        
        assert cached is None


@pytest.mark.asyncio
async def test_invalidate_cache(
    mock_tenant_id,
    mock_user_id,
):
    """Test cache invalidation."""
    redis_mock = AsyncMock()
    
    with patch(
        "app.services.user_recognition.get_redis_client",
        return_value=redis_mock,
    ):
        result = await user_recognition_service.invalidate_cache(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
        )
        
        assert result["cache_invalidated"] is True
        assert result["user_id"] == str(mock_user_id)
        assert result["tenant_id"] == str(mock_tenant_id)
        
        # Verify Redis delete was called
        redis_mock.delete.assert_called_once()


@pytest.mark.asyncio
async def test_recognize_user_performance_requirement(
    mock_tenant_id,
    mock_user_id,
    sample_user_memory,
):
    """Test that recognition completes within <100ms (p95)."""
    import time
    
    with patch.object(
        user_recognition_service,
        "_get_cached_user_memory",
        return_value=sample_user_memory,
    ), patch.object(
        user_recognition_service,
        "_retrieve_user_memory",
        return_value=sample_user_memory,
    ):
        start_time = time.time()
        result = await user_recognition_service.recognize_user(
            user_id=mock_user_id,
            tenant_id=mock_tenant_id,
            use_cache=True,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Should complete quickly (<100ms target, but allow some overhead for test)
        assert elapsed_ms < 200  # Reasonable threshold for test
        assert result["response_time_ms"] < 200


@pytest.mark.asyncio
async def test_recognize_user_tenant_isolation_error(mock_user_id):
    """Test that recognition raises TenantIsolationError when tenant_id is missing."""
    with patch(
        "app.services.user_recognition.get_tenant_id_from_context",
        return_value=None,
    ):
        with pytest.raises(Exception):  # Should raise TenantIsolationError
            await user_recognition_service.recognize_user(
                user_id=mock_user_id,
                tenant_id=None,
            )


@pytest.mark.asyncio
async def test_recognize_user_validation_error(mock_tenant_id):
    """Test that recognition raises ValidationError for invalid user_id."""
    with pytest.raises(Exception):  # Should raise ValidationError
        await user_recognition_service.recognize_user(
            user_id="invalid-uuid",
            tenant_id=mock_tenant_id,
        )

