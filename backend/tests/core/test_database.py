"""Unit tests for database connection pool."""

import pytest
from unittest.mock import patch, MagicMock

from src.core.database import engine, async_session_maker, get_db, dispose_engine


class TestDatabasePool:
    """Test suite for database connection pool."""

    def test_engine_exists(self):
        """Test that engine is created."""
        assert engine is not None

    def test_async_session_maker_configured(self):
        """Test that async_session_maker is properly configured."""
        assert async_session_maker is not None

    def test_get_db_is_async_generator(self):
        """Test that get_db is an async generator function."""
        import inspect
        assert inspect.isasyncgenfunction(get_db)

    @pytest.mark.asyncio
    async def test_dispose_engine_is_coroutine(self):
        """Test that dispose_engine is a coroutine function."""
        import inspect
        assert inspect.iscoroutinefunction(dispose_engine)
