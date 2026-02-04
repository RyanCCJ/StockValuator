"""Async wrapper for yfinance operations using ThreadPoolExecutor."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

from src.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global executor (lazy initialization)
_yf_executor: ThreadPoolExecutor | None = None


def get_yf_executor() -> ThreadPoolExecutor:
    """Get or create the ThreadPoolExecutor for yfinance operations (lazy initialization)."""
    global _yf_executor
    if _yf_executor is None:
        settings = get_settings()
        _yf_executor = ThreadPoolExecutor(
            max_workers=settings.yfinance_max_workers,
            thread_name_prefix="yfinance",
        )
        logger.info(
            f"yfinance ThreadPoolExecutor created (max_workers={settings.yfinance_max_workers})"
        )
    return _yf_executor


async def run_in_yf_executor(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous function in the yfinance executor thread pool.

    This prevents blocking the async event loop when calling yfinance APIs.

    Args:
        func: The synchronous function to execute
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    loop = asyncio.get_event_loop()
    executor = get_yf_executor()

    # If there are kwargs, we need to wrap the function
    if kwargs:
        def wrapped() -> T:
            return func(*args, **kwargs)
        return await loop.run_in_executor(executor, wrapped)
    else:
        return await loop.run_in_executor(executor, func, *args)


def shutdown_yf_executor() -> None:
    """Shutdown the yfinance executor for graceful application termination."""
    global _yf_executor
    if _yf_executor is not None:
        _yf_executor.shutdown(wait=True)
        _yf_executor = None
        logger.info("yfinance ThreadPoolExecutor shut down")
