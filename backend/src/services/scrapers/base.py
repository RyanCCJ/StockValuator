"""Base scraper interface - public API for scraper implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from src.core.cache import cache_get, cache_set


class ScraperError(Exception):
    """Raised when scraping fails due to network, parsing, or rate-limiting issues."""

    pass


@dataclass
class FinancialMetrics:
    """
    Standardized container for financial metrics scraped from external sources.

    This dataclass normalizes data from ROIC.ai, Finviz, and other sources into
    a common format for the value analysis engine.
    """

    symbol: str
    source: str
    fetched_at: datetime

    eps_history: list[dict[str, Any]] | None = None
    revenue_history: list[dict[str, Any]] | None = None
    net_income_history: list[dict[str, Any]] | None = None
    dividend_history: list[dict[str, Any]] | None = None
    dividend_growth_years: int | None = None
    fcf_history: list[dict[str, Any]] | None = None
    fcf_per_share_history: list[dict[str, Any]] | None = None
    shares_outstanding_history: list[dict[str, Any]] | None = None
    book_value_history: list[dict[str, Any]] | None = None
    total_debt_history: list[dict[str, Any]] | None = None
    net_debt_to_capital_history: list[dict[str, Any]] | None = None
    cash_history: list[dict[str, Any]] | None = None
    roe_history: list[dict[str, Any]] | None = None
    net_margin_history: list[dict[str, Any]] | None = None
    pe_history: list[dict[str, Any]] | None = None
    dividend_yield_history: list[dict[str, Any]] | None = None
    interest_coverage: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    sector: str | None = None
    industry: str | None = None
    beta: float | None = None
    # Finviz forward-looking data for Fair Value calculations
    eps_next_year: float | None = None          # Finviz "EPS next Y"
    eps_growth_next_5y: float | None = None     # Finviz "EPS next 5Y" (decimal, e.g., 0.15)
    dividend_est: float | None = None           # Finviz "Dividend Est"
    book_value_per_share: float | None = None   # Finviz "Book/sh"
    raw_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "source": self.source,
            "fetched_at": self.fetched_at.isoformat(),
            "eps_history": self.eps_history,
            "revenue_history": self.revenue_history,
            "net_income_history": self.net_income_history,
            "dividend_history": self.dividend_history,
            "dividend_growth_years": self.dividend_growth_years,
            "fcf_history": self.fcf_history,
            "fcf_per_share_history": self.fcf_per_share_history,
            "shares_outstanding_history": self.shares_outstanding_history,
            "book_value_history": self.book_value_history,
            "total_debt_history": self.total_debt_history,
            "net_debt_to_capital_history": self.net_debt_to_capital_history,
            "cash_history": self.cash_history,
            "roe_history": self.roe_history,
            "net_margin_history": self.net_margin_history,
            "pe_history": self.pe_history,
            "dividend_yield_history": self.dividend_yield_history,
            "interest_coverage": self.interest_coverage,
            "pe_ratio": self.pe_ratio,
            "forward_pe": self.forward_pe,
            "peg_ratio": self.peg_ratio,
            "price_to_book": self.price_to_book,
            "sector": self.sector,
            "industry": self.industry,
            "beta": self.beta,
            "eps_next_year": self.eps_next_year,
            "eps_growth_next_5y": self.eps_growth_next_5y,
            "dividend_est": self.dividend_est,
            "book_value_per_share": self.book_value_per_share,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialMetrics":
        data = data.copy()
        data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])
        data.pop("raw_data", None)
        return cls(**data)


class BaseScraper(ABC):
    """
    Abstract base class for financial data scrapers.

    Subclasses must implement _fetch_and_parse() to handle source-specific
    data extraction logic.
    """

    SOURCE_NAME: str = "base"
    CACHE_TTL: int = 86400 * 7

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=self._get_headers(),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _cache_key(self, symbol: str) -> str:
        return f"scraper:{self.SOURCE_NAME}:{symbol.upper()}"

    async def get_data(self, symbol: str, force_refresh: bool = False) -> FinancialMetrics:
        symbol = symbol.upper()
        cache_key = self._cache_key(symbol)

        if not force_refresh:
            cached = await cache_get(cache_key)
            if cached:
                return FinancialMetrics.from_dict(cached)

        metrics = await self._fetch_and_parse(symbol)
        await cache_set(cache_key, metrics.to_dict(), ttl=self.CACHE_TTL)
        return metrics

    @abstractmethod
    async def _fetch_and_parse(self, symbol: str) -> FinancialMetrics:
        raise NotImplementedError

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", "").replace("$", "").replace("%", "").strip()
                if value in ("", "-", "N/A", "NA"):
                    return None
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_year_value_list(
        data: dict[str, Any], years: list[int] | None = None
    ) -> list[dict[str, Any]]:
        result = []
        for year_str, value in data.items():
            try:
                year = int(year_str)
                if years is None or year in years:
                    parsed_value = BaseScraper._safe_float(value)
                    if parsed_value is not None:
                        result.append({"year": year, "value": parsed_value})
            except (ValueError, TypeError):
                continue
        return sorted(result, key=lambda x: x["year"])
