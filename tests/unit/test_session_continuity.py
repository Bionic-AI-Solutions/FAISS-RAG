"""
Unit tests for SessionContinuityService.

Tests cover:
- Session interruption detection and storage
- Session resumption with context restoration
- Interrupted query preservation
- Performance requirements (<500ms for resumption)
- Tenant isolation
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.mcp.middleware.tenant import _tenant_id_context, _user_id_context
from app.services.session_continuity import SessionContinuityService
from app.services.session_context import SessionContextService
from app.utils.errors import TenantIsolationError, ValidationError, ResourceNotFoundError


class TestSessionContinuityService:
    """Tests for SessionContinuityService."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset context variables before each test."""
        _tenant_id_context.set(None)
        _user_id_context.set(None)

    @pytest.fixture
    def tenant_id(self):
        """Create a test tenant ID."""
        return uuid4()

    @pytest.fixture
    def user_id(self):
        """Create a test user ID."""
        return uuid4()

    @pytest.fixture
    def session_id(self):
        """Create a test session ID."""
        return "test-session-123"

    @pytest.fixture
    def mock_session_context_service(self):
        """Create a mock SessionContextService."""
        service = AsyncMock(spec=SessionContextService)
        return service

    @pytest.fixture
    def session_continuity_service(self, mock_session_context_service):
        """Create a SessionContinuityService instance with mocked dependencies."""
        return SessionContinuityService(session_context_service=mock_session_context_service)

    @pytest.mark.asyncio
    async def test_interrupt_session_success(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test successful session interruption."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        # Mock existing context (None for new session)
        mock_session_context_service.get_session_context = AsyncMock(return_value=None)
        mock_session_context_service.store_session_context = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": 86400,
            "response_time_ms": 10.5
        })

        result = await session_continuity_service.interrupt_session(
            session_id=session_id,
            current_query="What is the weather?",
            conversation_state={"topic": "weather"},
        )

        assert result["session_id"] == session_id
        assert result["user_id"] == str(user_id)
        assert result["tenant_id"] == str(tenant_id)
        assert result["interrupted_query"] == "What is the weather?"
        assert len(result["interrupted_queries"]) == 1
        assert "response_time_ms" in result

        # Verify store_session_context was called with interruption flag
        mock_session_context_service.store_session_context.assert_called_once()
        call_kwargs = mock_session_context_service.store_session_context.call_args[1]
        assert call_kwargs["conversation_state"]["interrupted"] is True
        assert "interrupted_at" in call_kwargs["conversation_state"]

    @pytest.mark.asyncio
    async def test_interrupt_session_merges_existing_context(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test that interruption merges with existing session context."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        # Mock existing context with previous interrupted queries
        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "conversation_state": {"topic": "previous_topic"},
            "interrupted_queries": ["Previous query?"],
            "recent_interactions": [{"query": "Hello", "response": "Hi"}],
            "user_preferences": {"language": "en"},
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)
        mock_session_context_service.store_session_context = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": 86400,
            "response_time_ms": 10.5
        })

        result = await session_continuity_service.interrupt_session(
            session_id=session_id,
            current_query="New query?",
            conversation_state={"new_field": "new_value"},
        )

        # Verify interrupted queries were merged (deduplicated)
        assert len(result["interrupted_queries"]) == 2  # Previous + New
        assert "Previous query?" in result["interrupted_queries"]
        assert "New query?" in result["interrupted_queries"]

        # Verify conversation state was merged
        call_kwargs = mock_session_context_service.store_session_context.call_args[1]
        assert call_kwargs["conversation_state"]["topic"] == "previous_topic"
        assert call_kwargs["conversation_state"]["new_field"] == "new_value"

    @pytest.mark.asyncio
    async def test_interrupt_session_tenant_isolation_error(
        self, session_continuity_service, user_id, session_id, mock_session_context_service
    ):
        """Test that interruption fails when tenant_id is not available."""
        _tenant_id_context.set(None)
        _user_id_context.set(str(user_id))

        with pytest.raises(TenantIsolationError) as exc_info:
            await session_continuity_service.interrupt_session(
                session_id=session_id,
                current_query="Test query",
            )

        assert "Tenant ID not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_interrupt_session_validation_error(
        self, session_continuity_service, tenant_id, user_id, mock_session_context_service
    ):
        """Test that interruption fails with invalid session_id."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        with pytest.raises(ValidationError) as exc_info:
            await session_continuity_service.interrupt_session(
                session_id="",  # Empty session_id
                current_query="Test query",
            )

        assert "Session ID is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resume_session_success(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test successful session resumption."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        # Mock existing session context
        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "conversation_state": {"topic": "weather", "interrupted": True},
            "interrupted_queries": ["What is the weather?"],
            "recent_interactions": [{"query": "Hello", "response": "Hi"}],
            "user_preferences": {"language": "en"},
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)
        mock_session_context_service.update_session_context = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": 86400,
            "response_time_ms": 10.5
        })

        result = await session_continuity_service.resume_session(
            session_id=session_id,
        )

        assert result["session_id"] == session_id
        assert result["user_id"] == str(user_id)
        assert result["tenant_id"] == str(tenant_id)
        assert result["can_resume"] is True
        assert len(result["interrupted_queries"]) == 1
        assert result["interrupted_queries"][0] == "What is the weather?"
        assert "restored_context" in result
        assert "response_time_ms" in result

        # Verify context was restored
        assert result["restored_context"]["conversation_state"]["topic"] == "weather"
        assert result["restored_context"]["recent_interactions"] == [{"query": "Hello", "response": "Hi"}]
        assert result["restored_context"]["user_preferences"] == {"language": "en"}

        # Verify update_session_context was called with resumed flag
        mock_session_context_service.update_session_context.assert_called_once()
        call_kwargs = mock_session_context_service.update_session_context.call_args[1]
        assert call_kwargs["conversation_state"]["resumed"] is True
        assert "resumed_at" in call_kwargs["conversation_state"]

    @pytest.mark.asyncio
    async def test_resume_session_not_found(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test resumption fails when session context not found."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        mock_session_context_service.get_session_context = AsyncMock(return_value=None)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await session_continuity_service.resume_session(
                session_id=session_id,
            )

        assert "Session context not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resume_session_tenant_isolation_error(
        self, session_continuity_service, user_id, session_id, mock_session_context_service
    ):
        """Test that resumption fails when tenant_id is not available."""
        _tenant_id_context.set(None)
        _user_id_context.set(str(user_id))

        with pytest.raises(TenantIsolationError) as exc_info:
            await session_continuity_service.resume_session(
                session_id=session_id,
            )

        assert "Tenant ID not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resume_session_performance(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test that resumption completes within <500ms (cold start acceptable)."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "conversation_state": {},
            "interrupted_queries": [],
            "recent_interactions": [],
            "user_preferences": {},
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)
        mock_session_context_service.update_session_context = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": 86400,
            "response_time_ms": 10.5
        })

        result = await session_continuity_service.resume_session(
            session_id=session_id,
        )

        # Performance requirement: <500ms (cold start acceptable)
        assert result["response_time_ms"] < 500

    @pytest.mark.asyncio
    async def test_get_interrupted_queries_success(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test successful retrieval of interrupted queries."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "interrupted_queries": ["Query 1", "Query 2", "Query 3"],
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)

        result = await session_continuity_service.get_interrupted_queries(
            session_id=session_id,
        )

        assert result == ["Query 1", "Query 2", "Query 3"]

    @pytest.mark.asyncio
    async def test_get_interrupted_queries_not_found(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test retrieval fails when session context not found."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        mock_session_context_service.get_session_context = AsyncMock(return_value=None)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await session_continuity_service.get_interrupted_queries(
                session_id=session_id,
            )

        assert "Session context not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_interrupted_queries_empty_list(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test retrieval returns empty list when no interrupted queries."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "interrupted_queries": [],
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)

        result = await session_continuity_service.get_interrupted_queries(
            session_id=session_id,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_interrupt_session_preserves_all_context_fields(
        self, session_continuity_service, tenant_id, user_id, session_id, mock_session_context_service
    ):
        """Test that interruption preserves all context fields."""
        _tenant_id_context.set(tenant_id)
        _user_id_context.set(str(user_id))

        existing_context = {
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "conversation_state": {"field1": "value1"},
            "interrupted_queries": ["Old query"],
            "recent_interactions": [{"old": "interaction"}],
            "user_preferences": {"pref1": "value1"},
        }

        mock_session_context_service.get_session_context = AsyncMock(return_value=existing_context)
        mock_session_context_service.store_session_context = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "stored_at": datetime.utcnow().isoformat(),
            "ttl": 86400,
            "response_time_ms": 10.5
        })

        await session_continuity_service.interrupt_session(
            session_id=session_id,
            current_query="New query",
            conversation_state={"field2": "value2"},
            recent_interactions=[{"new": "interaction"}],
            user_preferences={"pref2": "value2"},
        )

        # Verify all fields were preserved and merged
        call_kwargs = mock_session_context_service.store_session_context.call_args[1]
        assert call_kwargs["conversation_state"]["field1"] == "value1"
        assert call_kwargs["conversation_state"]["field2"] == "value2"
        assert len(call_kwargs["interrupted_queries"]) == 2  # Old + New
        assert len(call_kwargs["recent_interactions"]) == 2  # Old + New
        assert call_kwargs["user_preferences"]["pref1"] == "value1"
        assert call_kwargs["user_preferences"]["pref2"] == "value2"








