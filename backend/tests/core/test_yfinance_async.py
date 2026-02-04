"""Unit tests for yfinance async wrapper."""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

from src.core.yfinance_async import (
    get_yf_executor,
    run_in_yf_executor,
    shutdown_yf_executor,
)


class TestYfinanceExecutor:
    """Test suite for yfinance ThreadPoolExecutor."""

    @pytest.fixture(autouse=True)
    def reset_executor(self):
        """Reset the global executor before each test."""
        import src.core.yfinance_async as yf_module
        yf_module._yf_executor = None
        yield
        # Clean up after test
        if yf_module._yf_executor is not None:
            yf_module._yf_executor.shutdown(wait=False)
            yf_module._yf_executor = None

    def test_get_yf_executor_creates_executor_on_first_call(self):
        """Test that get_yf_executor creates executor on first call."""
        executor = get_yf_executor()

        assert executor is not None
        assert executor._max_workers == 10  # Default from settings

    def test_get_yf_executor_returns_same_executor(self):
        """Test that get_yf_executor returns the same executor instance."""
        executor1 = get_yf_executor()
        executor2 = get_yf_executor()

        assert executor1 is executor2

    def test_shutdown_yf_executor_clears_executor(self):
        """Test that shutdown_yf_executor properly cleans up."""
        import src.core.yfinance_async as yf_module

        # Create an executor
        executor = get_yf_executor()
        assert yf_module._yf_executor is not None

        # Shutdown
        shutdown_yf_executor()

        assert yf_module._yf_executor is None

    def test_shutdown_yf_executor_handles_none(self):
        """Test that shutdown_yf_executor handles None gracefully."""
        import src.core.yfinance_async as yf_module
        yf_module._yf_executor = None

        # Should not raise
        shutdown_yf_executor()

        assert yf_module._yf_executor is None


class TestRunInYfExecutor:
    """Test suite for run_in_yf_executor helper."""

    @pytest.fixture(autouse=True)
    def reset_executor(self):
        """Reset the global executor before each test."""
        import src.core.yfinance_async as yf_module
        yf_module._yf_executor = None
        yield
        if yf_module._yf_executor is not None:
            yf_module._yf_executor.shutdown(wait=False)
            yf_module._yf_executor = None

    @pytest.mark.asyncio
    async def test_run_in_yf_executor_executes_sync_function(self):
        """Test that run_in_yf_executor executes a sync function."""
        def sync_func(x, y):
            return x + y

        result = await run_in_yf_executor(sync_func, 2, 3)

        assert result == 5

    @pytest.mark.asyncio
    async def test_run_in_yf_executor_with_kwargs(self):
        """Test that run_in_yf_executor handles kwargs."""
        def sync_func(a, b=10):
            return a * b

        result = await run_in_yf_executor(sync_func, 5, b=20)

        assert result == 100

    @pytest.mark.asyncio
    async def test_run_in_yf_executor_does_not_block_event_loop(self):
        """Test that run_in_yf_executor doesn't block the event loop."""
        import time

        def slow_sync_func():
            time.sleep(0.1)
            return "done"

        # Run multiple slow functions concurrently
        start = time.time()
        results = await asyncio.gather(
            run_in_yf_executor(slow_sync_func),
            run_in_yf_executor(slow_sync_func),
            run_in_yf_executor(slow_sync_func),
        )
        elapsed = time.time() - start

        assert all(r == "done" for r in results)
        # Should complete in less than 0.4s (if they ran concurrently)
        # Serial execution would take 0.3s minimum
        assert elapsed < 0.4

    @pytest.mark.asyncio
    async def test_run_in_yf_executor_propagates_exceptions(self):
        """Test that run_in_yf_executor propagates exceptions from sync function."""
        def error_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await run_in_yf_executor(error_func)

    @pytest.mark.asyncio
    async def test_run_in_yf_executor_with_no_args(self):
        """Test that run_in_yf_executor works with no arguments."""
        def no_arg_func():
            return 42

        result = await run_in_yf_executor(no_arg_func)

        assert result == 42
