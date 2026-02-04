"""Market Cycle Service for calculating market phase and risk."""

import asyncio
from datetime import date
from typing import Any

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.yfinance_async import run_in_yf_executor
from src.models.market_cycle import MarketCycleSnapshot
from src.services.scrapers.shiller_pe import ShillerPEScraper
from src.services.scrapers.breadth import BreadthScraper


def _sync_fetch_trend_data() -> dict[str, float | None]:
    """Synchronous helper to fetch S&P 500 price and 200-day MA."""
    try:
        ticker = yf.Ticker("^GSPC")
        hist = ticker.history(period="1y")

        if hist.empty:
            return {"sp500_price": None, "sp500_ma200": None}

        current_price = float(hist["Close"].iloc[-1])
        ma200 = float(hist["Close"].rolling(window=200).mean().iloc[-1])

        return {"sp500_price": current_price, "sp500_ma200": ma200}
    except Exception:
        return {"sp500_price": None, "sp500_ma200": None}


def _sync_fetch_yield_data() -> dict[str, float | None]:
    """Synchronous helper to fetch Treasury yields and calculate spread."""
    try:
        tnx = yf.Ticker("^TNX")  # 10-Year Treasury
        irx = yf.Ticker("^IRX")  # 3-Month Treasury

        tnx_hist = tnx.history(period="5d")
        irx_hist = irx.history(period="5d")

        if tnx_hist.empty or irx_hist.empty:
            return {"treasury_10y": None, "treasury_3m": None, "yield_spread": None}

        treasury_10y = float(tnx_hist["Close"].iloc[-1])
        treasury_3m = float(irx_hist["Close"].iloc[-1])
        yield_spread = treasury_10y - treasury_3m

        return {
            "treasury_10y": treasury_10y,
            "treasury_3m": treasury_3m,
            "yield_spread": yield_spread,
        }
    except Exception:
        return {"treasury_10y": None, "treasury_3m": None, "yield_spread": None}


def _sync_fetch_vix() -> float | None:
    """Synchronous helper to fetch VIX index."""
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="5d")

        if hist.empty:
            return None

        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


def _sync_fetch_market_pulse() -> dict[str, float | None]:
    """Synchronous helper to fetch market pulse data for major indices."""
    indices = {
        "^DJI": ("djia", "djia"),
        "^IXIC": ("nasdaq", "nasdaq"),
        "^GSPC": ("sp500", "sp500"),
        "^RUT": ("russell", "russell"),
    }

    result: dict[str, float | None] = {}

    for symbol, (price_key, change_key) in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist.empty:
                if price_key != "sp500":
                    result[f"{price_key}_price"] = None
                result[f"{change_key}_change_percent"] = None
                continue

            current_price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
            change_percent = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0

            if price_key != "sp500":  # sp500_price already captured in trend data
                result[f"{price_key}_price"] = current_price
            result[f"{change_key}_change_percent"] = change_percent
        except Exception:
            if price_key != "sp500":
                result[f"{price_key}_price"] = None
            result[f"{change_key}_change_percent"] = None

    return result


class MarketCycleService:
    """
    Service for market cycle analysis.

    Aggregates 5 key indicators to compute market phase and composite score:
    1. Trend: S&P 500 vs 200-day MA
    2. Valuation: Shiller PE Ratio
    3. Recession: Yield Curve Spread (10Y - 3M)
    4. Fear: VIX Index
    5. Breadth: NASDAQ Advance-Decline Line

    Score Interpretation:
    - Bull Market (50-100): Higher = more dangerous/overheated
    - Bear Market (0-50): Lower = better buying opportunity
    """

    def __init__(self):
        self.shiller_scraper = ShillerPEScraper()
        self.breadth_scraper = BreadthScraper()

    async def refresh_data(self, db: AsyncSession) -> MarketCycleSnapshot:
        """
        Fetch all indicators and create a new daily snapshot.

        Args:
            db: Database session.

        Returns:
            The newly created MarketCycleSnapshot.
        """
        today = date.today()

        # Fetch all indicators concurrently
        (
            trend_data,
            shiller_pe,
            yield_data,
            vix,
            breadth_data,
            market_pulse,
        ) = await asyncio.gather(
            self._fetch_trend_data(),
            self._fetch_shiller_pe(),
            self._fetch_yield_data(),
            self._fetch_vix(),
            self._fetch_breadth_data(),
            self._fetch_market_pulse(),
        )

        # Calculate phase and score
        phase_info = self.calculate_phase_and_score(
            sp500_price=trend_data.get("sp500_price"),
            sp500_ma200=trend_data.get("sp500_ma200"),
            shiller_pe=shiller_pe,
            yield_spread=yield_data.get("yield_spread"),
            vix=vix,
            breadth_ma5=breadth_data.get("breadth_ma5"),
            breadth_ma20=breadth_data.get("breadth_ma20"),
        )

        # Upsert snapshot (insert or update on conflict)
        snapshot_data = {
            "snapshot_date": today,
            # Trend
            "sp500_price": trend_data.get("sp500_price"),
            "sp500_ma200": trend_data.get("sp500_ma200"),
            # Valuation
            "shiller_pe": shiller_pe,
            # Yield
            "treasury_10y": yield_data.get("treasury_10y"),
            "treasury_3m": yield_data.get("treasury_3m"),
            "yield_spread": yield_data.get("yield_spread"),
            # Fear
            "vix": vix,
            # Breadth
            "breadth_ma5": breadth_data.get("breadth_ma5"),
            "breadth_ma20": breadth_data.get("breadth_ma20"),
            # Computed
            "total_score": phase_info["total_score"],
            "phase": phase_info["phase"],
            "phase_number": phase_info["phase_number"],
            "risk_level": phase_info["risk_level"],
            # Market Pulse
            "djia_price": market_pulse.get("djia_price"),
            "djia_change_percent": market_pulse.get("djia_change_percent"),
            "nasdaq_price": market_pulse.get("nasdaq_price"),
            "nasdaq_change_percent": market_pulse.get("nasdaq_change_percent"),
            "sp500_change_percent": market_pulse.get("sp500_change_percent"),
            "russell_price": market_pulse.get("russell_price"),
            "russell_change_percent": market_pulse.get("russell_change_percent"),
        }

        stmt = insert(MarketCycleSnapshot).values(**snapshot_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["snapshot_date"],
            set_=snapshot_data,
        )
        await db.execute(stmt)
        await db.commit()

        # Fetch the snapshot to return
        result = await db.execute(
            select(MarketCycleSnapshot).where(
                MarketCycleSnapshot.snapshot_date == today
            )
        )
        snapshot = result.scalar_one()

        return snapshot

    def calculate_phase_and_score(
        self,
        sp500_price: float | None,
        sp500_ma200: float | None,
        shiller_pe: float | None,
        yield_spread: float | None,
        vix: float | None,
        breadth_ma5: float | None,
        breadth_ma20: float | None,
    ) -> dict[str, Any]:
        """
        Calculate market cycle score and determine phase.

        Score Logic:
        - Bull Market (price > MA200): Score 50-100, higher = more dangerous
        - Bear Market (price <= MA200): Score 0-50, lower = better buying opportunity

        Bull Market Factors (add to base 50):
        - PE: (PE - 25) * 1.5, max 15 (overheating)
        - Yield: 15 if inverted (recession warning)
        - VIX: (13 - VIX) * 2, max 10 (complacency)
        - Breadth: 10 if MA5 < MA20 (structural divergence)

        Bear Market Factors (subtract from base 50):
        - PE: (25 - PE) * 1.5, max 15 (value emerging)
        - VIX: (VIX - 25) * 1.25, max 25 (extreme fear = opportunity)
        - Breadth: 10 if MA5 > MA20 (stabilizing)

        Returns:
            Dict with phase, phase_number, risk_level, and total_score.
        """
        base_score = 50
        risk_score = 0.0

        # Determine primary trend
        is_bull = True
        if sp500_price is not None and sp500_ma200 is not None:
            is_bull = sp500_price > sp500_ma200

        # Use safe defaults for None values
        pe = shiller_pe if shiller_pe is not None else 25.0
        vix_val = vix if vix is not None else 20.0
        yield_val = yield_spread if yield_spread is not None else 0.5
        ma5 = breadth_ma5 if breadth_ma5 is not None else 0.0
        ma20 = breadth_ma20 if breadth_ma20 is not None else 0.0

        if is_bull:
            # === Bull Market Mode (higher score = more dangerous, max +50) ===

            # 1. PE Score (Max 15): Each point above 25 adds 1.5, max at PE=35
            pe_contribution = min(max(0, (pe - 25) * 1.5), 15)

            # 2. Yield Score (Max 15): Inverted yield curve = recession warning
            yield_contribution = 15.0 if yield_val < 0 else 0.0

            # 3. VIX Score (Max 10): Each point below 13 adds 2, max at VIX=8
            vix_contribution = min(max(0, (13 - vix_val) * 2), 10)

            # 4. Breadth Score (Max 10): MA5 < MA20 = structural divergence
            breadth_contribution = 10.0 if ma5 < ma20 else 0.0

            risk_score = pe_contribution + yield_contribution + vix_contribution + breadth_contribution

            # Bull market score range: 50-100
            final_score = base_score + risk_score

            # Determine phase based on risk score
            if risk_score >= 30:
                phase = "Distribution"
                phase_number = 3
                risk_level = "High"
            elif risk_score >= 15:
                phase = "Distribution"
                phase_number = 3
                risk_level = "Medium"
            else:
                phase = "Mark-Up"
                phase_number = 2
                risk_level = "Low" if risk_score < 5 else "Medium"

        else:
            # === Bear Market Mode (lower score = better buying opportunity, max -50) ===

            # 1. PE Score (Max -15): Each point below 25 subtracts 1.5, max at PE=15
            pe_contribution = min(max(0, (25 - pe) * 1.5), 15)

            # 2. VIX Score (Max -25): Each point above 25 subtracts 1.25, max at VIX=45
            # This is the most important bottom signal
            vix_contribution = min(max(0, (vix_val - 25) * 1.25), 25)

            # 3. Breadth Score (Max -10): MA5 > MA20 = stabilizing
            breadth_contribution = 10.0 if ma5 > ma20 else 0.0

            risk_score = pe_contribution + vix_contribution + breadth_contribution

            # Bear market score range: 0-50 (lower = better buying opportunity)
            final_score = base_score - risk_score

            # Determine phase based on risk score (opportunity score)
            if risk_score >= 30:
                phase = "Accumulation"
                phase_number = 1
                risk_level = "Low"
            elif risk_score >= 15:
                phase = "Accumulation"
                phase_number = 1
                risk_level = "Medium"
            else:
                phase = "Mark-Down"
                phase_number = 4
                risk_level = "High"

        total_score = round(max(0, min(100, final_score)), 1)

        return {
            "phase": phase,
            "phase_number": phase_number,
            "risk_level": risk_level,
            "total_score": int(total_score),
        }

    async def get_current_cycle(self, db: AsyncSession) -> MarketCycleSnapshot:
        """
        Get today's market cycle snapshot, refreshing if needed.

        Args:
            db: Database session.

        Returns:
            Today's MarketCycleSnapshot.
        """
        today = date.today()

        # Check for existing snapshot
        stmt = select(MarketCycleSnapshot).where(
            MarketCycleSnapshot.snapshot_date == today
        )
        result = await db.execute(stmt)
        snapshot = result.scalar_one_or_none()

        if snapshot:
            return snapshot

        # No snapshot for today, trigger refresh
        return await self.refresh_data(db)

    async def _fetch_trend_data(self) -> dict[str, float | None]:
        """Fetch S&P 500 price and 200-day MA (non-blocking)."""
        return await run_in_yf_executor(_sync_fetch_trend_data)

    async def _fetch_shiller_pe(self) -> float | None:
        """Fetch Shiller PE ratio via scraper."""
        try:
            return await self.shiller_scraper.get_shiller_pe()
        except Exception:
            return None

    async def _fetch_yield_data(self) -> dict[str, float | None]:
        """Fetch Treasury yields and calculate spread (non-blocking)."""
        return await run_in_yf_executor(_sync_fetch_yield_data)

    async def _fetch_vix(self) -> float | None:
        """Fetch VIX index (non-blocking)."""
        return await run_in_yf_executor(_sync_fetch_vix)

    async def _fetch_breadth_data(self) -> dict[str, float | None]:
        """Fetch NASDAQ Advance-Decline MA values via scraper."""
        try:
            data = await self.breadth_scraper.get_breadth_data()
            return {
                "breadth_ma5": data.get("ma5"),
                "breadth_ma20": data.get("ma20"),
            }
        except Exception:
            return {"breadth_ma5": None, "breadth_ma20": None}

    async def _fetch_market_pulse(self) -> dict[str, float | None]:
        """Fetch market pulse data for major indices (non-blocking)."""
        return await run_in_yf_executor(_sync_fetch_market_pulse)
