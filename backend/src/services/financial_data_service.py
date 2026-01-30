from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache_get, cache_set
from src.models.financial_data import FinancialData
from src.services.scrapers.base import FinancialMetrics
from src.services.scrapers.finviz import FinvizScraper
from src.services.scrapers.roic import RoicScraper

logger = logging.getLogger(__name__)

REDIS_TTL_SECONDS = 86400
DB_FRESHNESS_DAYS = 7


async def get_financial_data(
    symbol: str,
    db: AsyncSession,
    force_refresh: bool = False,
) -> FinancialMetrics | None:
    symbol = symbol.upper()
    redis_key = f"financial_data:{symbol}"

    if not force_refresh:
        cached = await cache_get(redis_key)
        if cached:
            return FinancialMetrics.from_dict(cached)

    if not force_refresh:
        db_data = await _get_from_db(symbol, db)
        if db_data:
            await cache_set(redis_key, db_data.to_dict(), ttl=REDIS_TTL_SECONDS)
            return db_data

    metrics = await _fetch_from_scrapers(symbol)
    if metrics:
        await _save_to_db(metrics, db)
        await cache_set(redis_key, metrics.to_dict(), ttl=REDIS_TTL_SECONDS)

    return metrics


async def _get_from_db(symbol: str, db: AsyncSession) -> FinancialMetrics | None:
    freshness_threshold = datetime.now(timezone.utc) - timedelta(days=DB_FRESHNESS_DAYS)

    stmt = (
        select(FinancialData)
        .where(FinancialData.symbol == symbol)
        .where(FinancialData.fetched_at >= freshness_threshold)
        .order_by(FinancialData.fetched_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if not row:
        return None

    return FinancialMetrics(
        symbol=row.symbol,
        source=row.source,
        fetched_at=row.fetched_at,
        eps_history=row.eps_history,
        revenue_history=row.revenue_history,
        net_income_history=row.net_income_history,
        dividend_history=row.dividend_history,
        dividend_growth_years=row.dividend_growth_years,
        fcf_history=row.fcf_history,
        fcf_per_share_history=row.fcf_per_share_history,
        shares_outstanding_history=row.shares_outstanding_history,
        book_value_history=row.book_value_history,
        total_debt_history=row.total_debt_history,
        net_debt_to_capital_history=row.net_debt_to_capital_history,
        cash_history=row.cash_history,
        roe_history=row.roe_history,
        net_margin_history=row.net_margin_history,
        pe_history=row.pe_history,
        dividend_yield_history=row.dividend_yield_history,
        interest_coverage=row.interest_coverage,
        pe_ratio=row.pe_ratio,
        forward_pe=row.forward_pe,
        peg_ratio=row.peg_ratio,
        price_to_book=row.price_to_book,
        sector=row.sector,
        industry=row.industry,
        beta=row.beta,
        eps_next_year=row.eps_next_year,
        eps_growth_next_5y=row.eps_growth_next_5y,
        dividend_est=row.dividend_est,
        dividend_growth_5y=row.dividend_growth_5y,
        book_value_per_share=row.book_value_per_share,
        return_on_assets_history=row.return_on_assets_history,
        cash_flow_per_share_history=row.cash_flow_per_share_history,
        gross_margin_history=row.gross_margin_history,
        long_term_debt_to_total_assets_history=row.long_term_debt_to_total_assets_history,
        current_ratio_history=row.current_ratio_history,
        common_equity_to_total_assets_history=row.common_equity_to_total_assets_history,
        raw_data=row.raw_data,
    )


async def _fetch_from_scrapers(symbol: str) -> FinancialMetrics | None:
    roic_scraper = RoicScraper()
    finviz_scraper = FinvizScraper()

    roic_data: FinancialMetrics | None = None
    finviz_data: FinancialMetrics | None = None

    try:
        roic_data = await roic_scraper.get_data(symbol, force_refresh=True)
    except Exception as e:
        logger.warning(f"ROIC scraper failed for {symbol}: {e}")
    finally:
        await roic_scraper.close()

    try:
        finviz_data = await finviz_scraper.get_data(symbol, force_refresh=True)
    except Exception as e:
        logger.warning(f"Finviz scraper failed for {symbol}: {e}")
    finally:
        await finviz_scraper.close()

    if not roic_data and not finviz_data:
        return None

    return _merge_metrics(roic_data, finviz_data)


def _merge_metrics(
    roic: FinancialMetrics | None,
    finviz: FinancialMetrics | None,
) -> FinancialMetrics:
    base = roic or finviz
    if not base:
        raise ValueError("At least one data source is required")

    if roic and finviz:
        return FinancialMetrics(
            symbol=roic.symbol,
            source="roic+finviz",
            fetched_at=roic.fetched_at,
            eps_history=roic.eps_history,
            revenue_history=roic.revenue_history,
            net_income_history=roic.net_income_history,
            dividend_history=roic.dividend_history,
            dividend_growth_years=finviz.dividend_growth_years or roic.dividend_growth_years,
            fcf_history=roic.fcf_history,
            fcf_per_share_history=roic.fcf_per_share_history,
            shares_outstanding_history=roic.shares_outstanding_history,
            book_value_history=roic.book_value_history,
            total_debt_history=roic.total_debt_history,
            net_debt_to_capital_history=roic.net_debt_to_capital_history,
            cash_history=roic.cash_history,
            roe_history=roic.roe_history,
            net_margin_history=roic.net_margin_history,
            pe_history=roic.pe_history,
            dividend_yield_history=roic.dividend_yield_history,
            interest_coverage=roic.interest_coverage,
            pe_ratio=finviz.pe_ratio or roic.pe_ratio,
            forward_pe=finviz.forward_pe or roic.forward_pe,
            peg_ratio=finviz.peg_ratio or roic.peg_ratio,
            price_to_book=finviz.price_to_book or roic.price_to_book,
            sector=finviz.sector or roic.sector,
            industry=finviz.industry or roic.industry,
            beta=finviz.beta or roic.beta,
            eps_next_year=finviz.eps_next_year,
            eps_growth_next_5y=finviz.eps_growth_next_5y,
            dividend_est=finviz.dividend_est,
            dividend_growth_5y=finviz.dividend_growth_5y,
            book_value_per_share=finviz.book_value_per_share,
            return_on_assets_history=roic.return_on_assets_history,
            cash_flow_per_share_history=roic.cash_flow_per_share_history,
            gross_margin_history=roic.gross_margin_history,
            long_term_debt_to_total_assets_history=roic.long_term_debt_to_total_assets_history,
            current_ratio_history=roic.current_ratio_history,
            common_equity_to_total_assets_history=roic.common_equity_to_total_assets_history,
            raw_data={"roic": roic.raw_data, "finviz": finviz.raw_data},
        )

    return base


async def _save_to_db(metrics: FinancialMetrics, db: AsyncSession) -> None:
    record = FinancialData(
        symbol=metrics.symbol,
        source=metrics.source,
        fetched_at=metrics.fetched_at,
        eps_history=metrics.eps_history,
        revenue_history=metrics.revenue_history,
        net_income_history=metrics.net_income_history,
        dividend_history=metrics.dividend_history,
        dividend_growth_years=metrics.dividend_growth_years,
        fcf_history=metrics.fcf_history,
        fcf_per_share_history=metrics.fcf_per_share_history,
        shares_outstanding_history=metrics.shares_outstanding_history,
        book_value_history=metrics.book_value_history,
        total_debt_history=metrics.total_debt_history,
        net_debt_to_capital_history=metrics.net_debt_to_capital_history,
        cash_history=metrics.cash_history,
        roe_history=metrics.roe_history,
        net_margin_history=metrics.net_margin_history,
        pe_history=metrics.pe_history,
        dividend_yield_history=metrics.dividend_yield_history,
        interest_coverage=metrics.interest_coverage,
        pe_ratio=metrics.pe_ratio,
        forward_pe=metrics.forward_pe,
        peg_ratio=metrics.peg_ratio,
        price_to_book=metrics.price_to_book,
        sector=metrics.sector,
        industry=metrics.industry,
        beta=metrics.beta,
        eps_next_year=metrics.eps_next_year,
        eps_growth_next_5y=metrics.eps_growth_next_5y,
        dividend_est=metrics.dividend_est,
        dividend_growth_5y=metrics.dividend_growth_5y,
        book_value_per_share=metrics.book_value_per_share,
        return_on_assets_history=metrics.return_on_assets_history,
        cash_flow_per_share_history=metrics.cash_flow_per_share_history,
        gross_margin_history=metrics.gross_margin_history,
        long_term_debt_to_total_assets_history=metrics.long_term_debt_to_total_assets_history,
        current_ratio_history=metrics.current_ratio_history,
        common_equity_to_total_assets_history=metrics.common_equity_to_total_assets_history,
        raw_data=metrics.raw_data,
    )
    db.add(record)
    await db.commit()
