"""NASDAQ Advance-Decline scraper from eoddata.com using browser pool."""

from src.core.browser_pool import BrowserContextManager
from src.services.scrapers.base import BaseScraper


class BreadthScraper(BaseScraper):
    """Scraper for NASDAQ Advance-Decline data from eoddata.com."""

    SOURCE_NAME = "breadth"
    CACHE_TTL = 86400  # 24 hours
    BASE_URL = "https://www.eoddata.com/stockquote/INDEX/ADDN.htm"

    async def _fetch_and_parse(self, symbol: str = "") -> dict[str, float | None]:
        """
        Fetch and parse MA5 and MA20 values.

        Returns:
            Dict with 'ma5' and 'ma20' values.
        """
        return await self._do_fetch()

    async def _do_fetch(self) -> dict[str, float | None]:
        """Execute the scraping logic using browser pool."""
        async with BrowserContextManager() as (browser, context):
            page = await context.new_page()

            try:
                await page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)

                # Extract MA values from the technical indicators section
                ma_values = await page.evaluate("""
                    () => {
                        const result = { ma5: null, ma20: null };

                        // Look for text containing MA5 and MA20
                        const allText = document.body.innerText;

                        // Find MA5 value
                        const ma5Match = allText.match(/MA5:\\s*([\\-\\d\\.]+)/);
                        if (ma5Match) {
                            result.ma5 = ma5Match[1];
                        }

                        // Find MA20 value
                        const ma20Match = allText.match(/MA20:\\s*([\\-\\d\\.]+)/);
                        if (ma20Match) {
                            result.ma20 = ma20Match[1];
                        }

                        return result;
                    }
                """)

                ma5 = self._safe_float(ma_values.get("ma5")) if ma_values else None
                ma20 = self._safe_float(ma_values.get("ma20")) if ma_values else None

                return {"ma5": ma5, "ma20": ma20}

            finally:
                await page.close()

    async def get_breadth_data(self, force_refresh: bool = False) -> dict[str, float | None]:
        """
        Get the current breadth MA values with caching.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            Dict with 'ma5' and 'ma20' values.
        """
        from src.core.cache import cache_get, cache_set

        cache_key = f"scraper:{self.SOURCE_NAME}:current"

        if not force_refresh:
            cached = await cache_get(cache_key)
            if cached is not None:
                return cached

        data = await self._fetch_and_parse()
        await cache_set(cache_key, data, ttl=self.CACHE_TTL)
        return data
