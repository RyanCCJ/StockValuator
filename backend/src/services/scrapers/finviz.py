from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright

from src.services.scrapers.base import BaseScraper, FinancialMetrics, ScraperError


class FinvizScraper(BaseScraper):
    SOURCE_NAME = "finviz"
    CACHE_TTL = 86400
    BASE_URL = "https://finviz.com/quote.ashx?t={symbol}"

    async def _fetch_and_parse(self, symbol: str) -> FinancialMetrics:
        url = self.BASE_URL.format(symbol=symbol.upper())
        return await self._do_fetch(symbol, url)

    async def _do_fetch(self, symbol: str, url: str) -> FinancialMetrics:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                not_found = await page.query_selector('td.body-text b:has-text("Stock not found!")')
                if not_found:
                    raise ScraperError(f"Ticker '{symbol}' not found on Finviz.")

                data = await page.evaluate("""
                    () => {
                        const table = document.querySelector('.snapshot-table2');
                        if (!table) return null;
                        const data = {};
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cols = row.querySelectorAll('td');
                            for (let i = 0; i < cols.length; i += 2) {
                                const key = cols[i]?.textContent?.trim();
                                const value = cols[i + 1]?.textContent?.trim();
                                if (key) data[key] = value || '';
                            }
                        });
                        return data;
                    }
                """)

                if not data:
                    raise ScraperError(f"Could not find data table for '{symbol}' on Finviz.")

                return self._parse_metrics(symbol, data)

            finally:
                await context.close()
                await browser.close()

    def _parse_metrics(self, symbol: str, data: dict[str, str]) -> FinancialMetrics:
        # Parse EPS next 5Y growth (comes as percentage like "10.50%")
        eps_growth_raw = self._safe_float(data.get("EPS next 5Y"))
        eps_growth_next_5y = eps_growth_raw / 100 if eps_growth_raw else None
        
        return FinancialMetrics(
            symbol=symbol.upper(),
            source=self.SOURCE_NAME,
            fetched_at=datetime.now(timezone.utc),
            pe_ratio=self._safe_float(data.get("P/E")),
            forward_pe=self._safe_float(data.get("Forward P/E")),
            peg_ratio=self._safe_float(data.get("PEG")),
            price_to_book=self._safe_float(data.get("P/B")),
            beta=self._safe_float(data.get("Beta")),
            sector=data.get("Sector"),
            industry=data.get("Industry"),
            # New fields for Fair Value calculations
            eps_next_year=self._safe_float(data.get("EPS next Y")),
            eps_growth_next_5y=eps_growth_next_5y,
            dividend_est=self._safe_float(data.get("Dividend Est")),
            book_value_per_share=self._safe_float(data.get("Book/sh")),
            raw_data=data,
        )
