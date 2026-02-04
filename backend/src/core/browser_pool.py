"""Browser pool for shared Playwright browser instances."""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from src.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BrowserInstance:
    """Wrapper for a browser instance with usage tracking."""

    browser: Browser
    usage_count: int = 0
    is_healthy: bool = True


@dataclass
class BrowserPool:
    """
    Pool of reusable Playwright browser instances.

    Manages a fixed number of browser instances with concurrency control,
    health tracking, and automatic replacement after extended use.
    """

    max_browsers: int = 3
    max_usage_per_browser: int = 100
    acquire_timeout: float = 60.0

    _playwright: Playwright | None = field(default=None, init=False)
    _browsers: list[BrowserInstance] = field(default_factory=list, init=False)
    _semaphore: asyncio.Semaphore = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _initialized: bool = field(default=False, init=False)

    async def _ensure_initialized(self) -> None:
        """Initialize the pool if not already done."""
        async with self._lock:
            if not self._initialized:
                settings = get_settings()
                self.max_browsers = settings.max_browsers
                self._semaphore = asyncio.Semaphore(self.max_browsers)
                self._playwright = await async_playwright().start()
                self._initialized = True
                logger.info(f"Browser pool initialized (max_browsers={self.max_browsers})")

    async def _create_browser(self) -> BrowserInstance:
        """Create a new browser instance."""
        browser = await self._playwright.chromium.launch(headless=True)
        instance = BrowserInstance(browser=browser)
        logger.debug("Created new browser instance")
        return instance

    async def acquire(self) -> tuple[Browser, BrowserContext]:
        """
        Acquire a browser and create an isolated context for scraping.

        Returns:
            Tuple of (Browser, BrowserContext) for the scraping operation.

        Raises:
            TimeoutError: If no browser becomes available within timeout.
        """
        await self._ensure_initialized()

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.acquire_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Browser pool exhausted, timed out waiting for browser")
            raise TimeoutError("Browser pool exhausted, timed out waiting for browser")

        async with self._lock:
            # Find an available healthy browser or create one
            instance = None

            # First, try to find a healthy browser that hasn't exceeded usage
            for browser_instance in self._browsers:
                if (
                    browser_instance.is_healthy
                    and browser_instance.usage_count < self.max_usage_per_browser
                ):
                    instance = browser_instance
                    break

            # If no suitable browser found, create a new one (up to max)
            if instance is None:
                if len(self._browsers) < self.max_browsers:
                    instance = await self._create_browser()
                    self._browsers.append(instance)
                else:
                    # All browsers are at max usage, replace the oldest one
                    old_instance = self._browsers.pop(0)
                    try:
                        await old_instance.browser.close()
                    except Exception as e:
                        logger.warning(f"Error closing old browser: {e}")
                    instance = await self._create_browser()
                    self._browsers.append(instance)
                    logger.info("Replaced browser instance after max usage")

            instance.usage_count += 1

        # Create an isolated context for this operation
        try:
            context = await instance.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            return instance.browser, context
        except Exception as e:
            # Browser crashed or is unhealthy
            instance.is_healthy = False
            logger.error(f"Failed to create browser context: {e}")
            self._semaphore.release()
            raise

    async def release(self, browser: Browser, context: BrowserContext) -> None:
        """
        Release a browser back to the pool after use.

        Args:
            browser: The browser that was acquired.
            context: The browser context to close.
        """
        try:
            await context.close()
        except Exception as e:
            logger.warning(f"Error closing browser context: {e}")
            # Mark browser as unhealthy if context close fails
            async with self._lock:
                for instance in self._browsers:
                    if instance.browser == browser:
                        instance.is_healthy = False
                        break

        self._semaphore.release()

    async def close_all(self) -> None:
        """Close all browsers and the Playwright instance for graceful shutdown."""
        async with self._lock:
            for instance in self._browsers:
                try:
                    await instance.browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")

            self._browsers.clear()

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._initialized = False
            logger.info("Browser pool closed")

    def get_status(self) -> dict[str, Any]:
        """Get current pool status for monitoring."""
        available = self._semaphore._value if self._semaphore else 0
        in_use = self.max_browsers - available if self._semaphore else 0

        return {
            "available": available,
            "in_use": in_use,
            "total": len(self._browsers),
            "max_browsers": self.max_browsers,
            "browsers": [
                {
                    "usage_count": b.usage_count,
                    "is_healthy": b.is_healthy,
                }
                for b in self._browsers
            ],
        }


# Global browser pool instance (lazy initialization)
_browser_pool: BrowserPool | None = None


def get_browser_pool() -> BrowserPool:
    """Get or create the global browser pool instance."""
    global _browser_pool
    if _browser_pool is None:
        _browser_pool = BrowserPool()
    return _browser_pool


async def close_browser_pool() -> None:
    """Close the global browser pool for graceful shutdown."""
    global _browser_pool
    if _browser_pool is not None:
        await _browser_pool.close_all()
        _browser_pool = None


class BrowserContextManager:
    """
    Async context manager for acquiring and releasing browsers from the pool.

    Usage:
        async with BrowserContextManager() as (browser, context):
            page = await context.new_page()
            await page.goto(url)
            # ... scrape data ...
    """

    def __init__(self, pool: BrowserPool | None = None):
        self._pool = pool or get_browser_pool()
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> tuple[Browser, BrowserContext]:
        self._browser, self._context = await self._pool.acquire()
        return self._browser, self._context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._browser and self._context:
            await self._pool.release(self._browser, self._context)
