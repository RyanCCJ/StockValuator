"""Shiller PE Ratio scraper using browser pool."""

import re

from src.core.browser_pool import BrowserContextManager
from src.services.scrapers.base import BaseScraper, ScraperError


class ShillerPEScraper(BaseScraper):
    """Scraper for Shiller PE Ratio from multpl.com."""

    SOURCE_NAME = "shiller_pe"
    CACHE_TTL = 86400  # 24 hours
    BASE_URL = "https://www.multpl.com/shiller-pe"

    def _extract_pe_value(self, text: str) -> float | None:
        """
        Extract the PE value from text that may contain extra content.

        Args:
            text: Raw text from the page, e.g., "Current\nShiller PE Ratio:\n40.46\n..."

        Returns:
            The extracted PE value as a float, or None if not found.
        """
        if not text:
            return None

        # Find all numbers in the text (including decimals)
        # The PE ratio is typically the first large number (> 10)
        numbers = re.findall(r'\d+\.?\d*', text)

        for num_str in numbers:
            try:
                value = float(num_str)
                # Shiller PE is typically between 5 and 50
                if 5.0 <= value <= 60.0:
                    return value
            except ValueError:
                continue

        return None

    async def _fetch_and_parse(self, symbol: str = "") -> float:
        """
        Fetch and parse the current Shiller PE ratio.

        Args:
            symbol: Ignored for this scraper (market-wide indicator).

        Returns:
            The current Shiller PE ratio as a float.

        Raises:
            ScraperError: If scraping fails.
        """
        return await self._do_fetch()

    async def _do_fetch(self) -> float:
        """Execute the scraping logic using browser pool."""
        async with BrowserContextManager() as (browser, context):
            page = await context.new_page()

            try:
                await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)

                # The current PE value is displayed in a big-value element
                pe_value = await page.evaluate("""
                    () => {
                        // Try the main value display first
                        const bigValue = document.querySelector('#current');
                        if (bigValue) {
                            const text = bigValue.textContent.trim();
                            return text;
                        }
                        // Fallback: look for the value in the first table row
                        const table = document.querySelector('table');
                        if (table) {
                            const firstRow = table.querySelector('tr:nth-child(2)');
                            if (firstRow) {
                                const valueCell = firstRow.querySelector('td:nth-child(2)');
                                if (valueCell) {
                                    return valueCell.textContent.trim();
                                }
                            }
                        }
                        return null;
                    }
                """)

                if not pe_value:
                    raise ScraperError("Could not find Shiller PE value on multpl.com")

                # Extract just the numeric value from the response
                # The response may contain text like "Current\nShiller PE Ratio:\n40.46\n..."
                parsed_value = self._extract_pe_value(pe_value)
                if parsed_value is None:
                    raise ScraperError(f"Could not parse Shiller PE value: {pe_value}")

                return parsed_value

            finally:
                await page.close()

    async def get_shiller_pe(self, force_refresh: bool = False) -> float:
        """
        Get the current Shiller PE ratio with caching.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            The current Shiller PE ratio.
        """
        from src.core.cache import cache_get, cache_set

        cache_key = f"scraper:{self.SOURCE_NAME}:current"

        if not force_refresh:
            cached = await cache_get(cache_key)
            if cached is not None:
                return float(cached)

        pe_value = await self._fetch_and_parse()
        await cache_set(cache_key, pe_value, ttl=self.CACHE_TTL)
        return pe_value
