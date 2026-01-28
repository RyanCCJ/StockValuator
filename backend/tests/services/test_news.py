"""Unit tests for news and research fetching functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.market_data import get_company_news_and_research


class TestGetCompanyNewsAndResearch:
    """Tests for the get_company_news_and_research function."""

    @pytest.mark.asyncio
    async def test_returns_cached_data_when_available(self):
        """Should return cached data without calling yfinance."""
        cached_data = {
            "symbol": "AAPL",
            "news": [{"title": "Cached News", "publisher": "Test", "link": "http://test.com"}],
            "research": [],
        }

        with patch("src.services.market_data.cache_get") as mock_cache_get:
            mock_cache_get.return_value = '{"symbol": "AAPL", "news": [], "research": []}'

            result = await get_company_news_and_research("AAPL")

            assert result is not None
            assert result["symbol"] == "AAPL"
            mock_cache_get.assert_called_once_with("news:AAPL")

    @pytest.mark.asyncio
    async def test_fetches_from_yfinance_on_cache_miss(self):
        """Should fetch from yfinance when cache is empty."""
        mock_search = MagicMock()
        mock_search.news = [
            {
                "title": "Apple announces new iPhone",
                "publisher": "Reuters",
                "link": "https://reuters.com/apple",
                "providerPublishTime": 1706400000,
                "type": "STORY",
            }
        ]
        mock_search.research = [
            {
                "reportHeadline": "Apple Q4 Analysis",
                "provider": "Morgan Stanley",
                "reportDate": 1706300000000,  # milliseconds
                "id": "MS_AAPL_AnalystReport_123",
            }
        ]

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock) as mock_cache_set,
            patch("src.services.market_data.yf.Search", return_value=mock_search),
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("AAPL")

            assert result is not None
            assert result["symbol"] == "AAPL"
            assert len(result["news"]) == 1
            assert result["news"][0]["title"] == "Apple announces new iPhone"
            assert result["news"][0]["publisher"] == "Reuters"
            assert len(result["research"]) == 1
            assert result["research"][0]["title"] == "Apple Q4 Analysis"

            # Verify cache was set with 1 hour TTL
            mock_cache_set.assert_called_once()
            call_args = mock_cache_set.call_args
            assert call_args[1]["ttl"] == 3600

    @pytest.mark.asyncio
    async def test_uses_include_research_true(self):
        """Should call yfinance.Search with include_research=True."""
        mock_search = MagicMock()
        mock_search.news = []
        mock_search.research = []

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock),
            patch("src.services.market_data.yf.Search", return_value=mock_search) as mock_yf_search,
        ):
            mock_cache_get.return_value = None

            await get_company_news_and_research("MSFT")

            # Verify Search was called with include_research=True
            mock_yf_search.assert_called_once_with("MSFT", include_research=True)

    @pytest.mark.asyncio
    async def test_handles_empty_news_and_research(self):
        """Should handle case when no news or research is available."""
        mock_search = MagicMock()
        mock_search.news = []
        mock_search.research = []

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock),
            patch("src.services.market_data.yf.Search", return_value=mock_search),
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("UNKNOWN")

            assert result is not None
            assert result["symbol"] == "UNKNOWN"
            assert result["news"] == []
            assert result["research"] == []

    @pytest.mark.asyncio
    async def test_handles_yfinance_exception(self):
        """Should return None when yfinance raises an exception."""
        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.yf.Search", side_effect=Exception("API Error")),
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("ERROR")

            assert result is None

    @pytest.mark.asyncio
    async def test_symbol_is_uppercased(self):
        """Should uppercase the symbol before processing."""
        mock_search = MagicMock()
        mock_search.news = []
        mock_search.research = []

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock),
            patch("src.services.market_data.yf.Search", return_value=mock_search) as mock_yf_search,
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("aapl")

            assert result["symbol"] == "AAPL"
            mock_cache_get.assert_called_with("news:AAPL")
            mock_yf_search.assert_called_with("AAPL", include_research=True)

    @pytest.mark.asyncio
    async def test_handles_missing_news_attribute(self):
        """Should handle case when Search object has no news attribute."""
        mock_search = MagicMock(spec=[])  # Empty spec = no attributes

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock),
            patch("src.services.market_data.yf.Search", return_value=mock_search),
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("TEST")

            assert result is not None
            assert result["news"] == []
            assert result["research"] == []

    @pytest.mark.asyncio
    async def test_extracts_thumbnail_correctly(self):
        """Should extract thumbnail URL from nested structure."""
        mock_search = MagicMock()
        mock_search.news = [
            {
                "title": "News with thumbnail",
                "publisher": "Test",
                "link": "http://test.com",
                "thumbnail": {
                    "resolutions": [
                        {"url": "http://thumbnail.com/small.jpg"},
                        {"url": "http://thumbnail.com/large.jpg"},
                    ]
                },
            }
        ]
        mock_search.research = []

        with (
            patch("src.services.market_data.cache_get", new_callable=AsyncMock) as mock_cache_get,
            patch("src.services.market_data.cache_set", new_callable=AsyncMock),
            patch("src.services.market_data.yf.Search", return_value=mock_search),
        ):
            mock_cache_get.return_value = None

            result = await get_company_news_and_research("AAPL")

            assert result["news"][0]["thumbnail"] == "http://thumbnail.com/small.jpg"
