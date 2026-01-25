from datetime import datetime, timezone
from typing import Any

from playwright.async_api import async_playwright

from src.services.scrapers.base import BaseScraper, FinancialMetrics, ScraperError


class RoicScraper(BaseScraper):
    SOURCE_NAME = "roic"
    CACHE_TTL = 86400 * 7
    BASE_URL = "https://roic.ai/quote/{symbol}/ratios?period=annual"

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
                await page.wait_for_timeout(2000)

                table_data = await page.evaluate("""
                    () => {
                        const scripts = document.querySelectorAll('script');
                        for (const script of scripts) {
                            const content = script.textContent || '';
                            if (content.includes('tableData')) {
                                const match = content.replace(/\\\\"/g, '"').match(/"tableData":(\\[.*?\\])/);
                                if (match) {
                                    try {
                                        return JSON.parse(match[1]);
                                    } catch (e) {}
                                }
                            }
                        }
                        return null;
                    }
                """)

                if not table_data:
                    raise ScraperError(
                        f"Could not find tableData for {symbol}. "
                        "This may be a non-US company or data is unavailable."
                    )

                return self._parse_table_data(symbol, table_data)

            finally:
                await context.close()
                await browser.close()

    def _parse_table_data(self, symbol: str, data: list[dict[str, Any]]) -> FinancialMetrics:
        sorted_data = sorted(data, key=lambda x: x.get("fiscal_year", 0))
        last_10_years = sorted_data[-10:] if len(sorted_data) > 10 else sorted_data

        latest_year = sorted_data[-1] if sorted_data else {}
        raw_ic = latest_year.get("oper_inc_to_int_exp") or latest_year.get(
            "ebitda_to_interest_expn"
        )
        if raw_ic == "- -":
            interest_coverage = -1.0
        else:
            interest_coverage = self._safe_float(raw_ic)

        return FinancialMetrics(
            symbol=symbol.upper(),
            source=self.SOURCE_NAME,
            fetched_at=datetime.now(timezone.utc),
            eps_history=self._extract_yearly_metric(last_10_years, "eps"),
            revenue_history=self._extract_yearly_metric(last_10_years, "revenue_per_sh"),
            dividend_history=self._extract_yearly_metric(last_10_years, "div_per_shr"),
            fcf_history=self._extract_yearly_metric(last_10_years, "free_cash_flow_per_sh"),
            fcf_per_share_history=self._extract_yearly_metric(
                last_10_years, "free_cash_flow_per_sh"
            ),
            shares_outstanding_history=self._extract_yearly_metric(last_10_years, "bs_sh_out"),
            book_value_history=self._extract_yearly_metric(last_10_years, "book_val_per_sh"),
            roe_history=self._extract_yearly_metric(last_10_years, "return_com_eqy", divisor=100),
            net_margin_history=self._extract_yearly_metric(
                last_10_years, "net_income_to_common_margin", divisor=100
            ),
            interest_coverage=interest_coverage,
            raw_data={"table_data": last_10_years},
        )

    def _extract_yearly_metric(
        self, data: list[dict[str, Any]], key: str, divisor: float = 1.0
    ) -> list[dict[str, Any]] | None:
        result = []
        for row in data:
            year = row.get("fiscal_year")
            value = row.get(key)
            if year is not None and value is not None:
                parsed_value = self._safe_float(value)
                if parsed_value is not None:
                    result.append({"year": int(year), "value": parsed_value / divisor})

        return result if result else None
