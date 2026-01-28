from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.services.scrapers.base import FinancialMetrics


class ValuationModel(str, Enum):
    GROWTH = "growth"
    DIVIDEND = "dividend"
    ASSET = "asset"


@dataclass
class ScoreBreakdown:
    name: str
    score: float
    max_score: float
    reason: str


@dataclass
class ConfidenceScore:
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdown] = field(default_factory=list)
    moat_score: float | None = None
    risk_score: float | None = None


@dataclass
class DividendScore:
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdown] = field(default_factory=list)


@dataclass
class ValueScore:
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdown] = field(default_factory=list)


@dataclass
class FairValueEstimate:
    model: ValuationModel
    fair_value: float | None
    current_price: float | None
    is_undervalued: bool
    explanation: str


@dataclass
class ValueAnalysisResult:
    symbol: str
    confidence: ConfidenceScore
    dividend: DividendScore
    value: ValueScore
    fair_value: FairValueEstimate | None


def calculate_confidence_score(metrics: FinancialMetrics) -> ConfidenceScore:
    breakdown: list[ScoreBreakdown] = []
    total = 0.0

    eps_score = _score_rising_trend(metrics.eps_history, "EPS", 10, 2)
    breakdown.append(eps_score)
    total += eps_score.score

    dividend_score = _score_consistent_positive(metrics.dividend_history, "Dividends", 10, 2)
    breakdown.append(dividend_score)
    total += dividend_score.score

    fcf_score = _score_mostly_positive(metrics.fcf_history, "FCF", 10, 2)
    breakdown.append(fcf_score)
    total += fcf_score.score

    roe_score = _score_above_threshold(metrics.roe_history, "ROE", 0.15, 10, 2)
    breakdown.append(roe_score)
    total += roe_score.score

    ic_score = _score_interest_coverage(metrics.interest_coverage)
    breakdown.append(ic_score)
    total += ic_score.score

    nm_score = _score_net_margin(metrics.net_margin_history)
    breakdown.append(nm_score)
    total += nm_score.score

    return ConfidenceScore(total=total, max_possible=6.0, breakdown=breakdown)


def calculate_dividend_score(metrics: FinancialMetrics, beta: float | None = None) -> DividendScore:
    breakdown: list[ScoreBreakdown] = []
    total = 0.0

    years_score = _score_dividend_years(metrics.dividend_growth_years)
    breakdown.append(years_score)
    total += years_score.score

    growth_5y = _calculate_cagr(metrics.dividend_history, 5)
    growth_10y = _calculate_cagr(metrics.dividend_history, 10)

    g5_score = _score_growth_rate(growth_5y, "5Y Dividend Growth")
    breakdown.append(g5_score)
    total += g5_score.score

    accel_score = _score_growth_acceleration(growth_5y, growth_10y)
    breakdown.append(accel_score)
    total += accel_score.score

    fcf_payout = _calculate_payout_ratio(metrics.dividend_history, metrics.fcf_per_share_history)
    fcf_payout_score = _score_payout_ratio(fcf_payout, "FCF Payout", 0.40, 0.75)
    breakdown.append(fcf_payout_score)
    total += fcf_payout_score.score

    eps_payout = _calculate_payout_ratio(metrics.dividend_history, metrics.eps_history)
    eps_payout_score = _score_payout_ratio(eps_payout, "EPS Payout", 0.50, 0.75)
    breakdown.append(eps_payout_score)
    total += eps_payout_score.score

    eps_positive_score = _score_eps_stability(metrics.eps_history)
    breakdown.append(eps_positive_score)
    total += eps_positive_score.score

    buyback_score = _score_buyback(metrics.shares_outstanding_history)
    breakdown.append(buyback_score)
    total += buyback_score.score

    roe_avg_score = _score_average_roe(metrics.roe_history)
    breakdown.append(roe_avg_score)
    total += roe_avg_score.score

    debt_score = _score_debt_ratio(metrics.net_debt_to_capital_history)
    breakdown.append(debt_score)
    total += debt_score.score

    beta_score = _score_beta(beta or metrics.beta)
    breakdown.append(beta_score)
    total += beta_score.score

    return DividendScore(total=total, max_possible=13.0, breakdown=breakdown)


def calculate_value_score(
    metrics: FinancialMetrics,
    current_price: float | None = None,
    sp500_yield: float = 0.015,
    trailing_pe: float | None = None,
    dividend_yield: float | None = None,
) -> ValueScore:
    """Calculate value score for a stock.
    
    Args:
        metrics: Financial metrics from scraped data
        current_price: Current stock price
        sp500_yield: S&P 500 dividend yield for comparison
        trailing_pe: Current trailing P/E from Key Statistics (for PE vs History)
        dividend_yield: Current dividend yield from Key Statistics (for Yield vs History)
    """
    breakdown: list[ScoreBreakdown] = []
    total = 0.0

    pe_score = _score_pe_relative_to_history(metrics.pe_history, current_pe=trailing_pe)
    breakdown.append(pe_score)
    total += pe_score.score

    yield_score = _score_yield_relative_to_history(metrics.dividend_yield_history, current_yield=dividend_yield)
    breakdown.append(yield_score)
    total += yield_score.score

    div_yield = _get_current_yield(metrics.dividend_history, current_price)

    high_yield_score = _score_high_yield(div_yield)
    breakdown.append(high_yield_score)
    total += high_yield_score.score

    sp_relative_score = _score_yield_vs_sp500(div_yield, sp500_yield)
    breakdown.append(sp_relative_score)
    total += sp_relative_score.score

    growth_5y = _calculate_cagr(metrics.dividend_history, 5)
    chowder_score = _score_chowder_rule(div_yield, growth_5y)
    breakdown.append(chowder_score)
    total += chowder_score.score

    fcf_yield_score = _score_fcf_yield(metrics.fcf_per_share_history, current_price)
    breakdown.append(fcf_yield_score)
    total += fcf_yield_score.score

    low_pe_score = _score_low_pe(metrics.pe_ratio)
    breakdown.append(low_pe_score)
    total += low_pe_score.score

    pe_roe_score = _score_pe_with_high_roe(metrics.pe_ratio, metrics.roe_history)
    breakdown.append(pe_roe_score)
    total += pe_roe_score.score

    return ValueScore(total=total, max_possible=9.0, breakdown=breakdown)


def calculate_fair_value(
    metrics: FinancialMetrics,
    model: ValuationModel,
    current_price: float | None = None,
    expected_return: float = 0.04,
    pb_threshold: float = 0.8,
) -> FairValueEstimate:
    if model == ValuationModel.GROWTH:
        return _calculate_growth_fair_value(metrics, current_price)
    elif model == ValuationModel.DIVIDEND:
        return _calculate_dividend_fair_value(metrics, current_price, expected_return)
    else:
        return _calculate_asset_fair_value(metrics, current_price, pb_threshold)


def _get_latest_value(history: list[dict[str, Any]] | None) -> float | None:
    if not history:
        return None
    sorted_history = sorted(history, key=lambda x: x.get("year", 0), reverse=True)
    return sorted_history[0].get("value") if sorted_history else None


def _score_rising_trend(
    history: list[dict[str, Any]] | None,
    name: str,
    years: int,
    tolerance: int,
) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="Insufficient data")

    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-years:]
    if len(sorted_data) < 3:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="Insufficient data")

    declining_years = 0
    for i in range(1, len(sorted_data)):
        if sorted_data[i]["value"] < sorted_data[i - 1]["value"]:
            declining_years += 1

    if declining_years <= tolerance:
        return ScoreBreakdown(
            name=name, score=1, max_score=1, reason=f"Rising trend over {len(sorted_data)}y"
        )
    return ScoreBreakdown(
        name=name, score=0, max_score=1, reason=f"Declining {declining_years} years"
    )


def _score_consistent_positive(
    history: list[dict[str, Any]] | None,
    name: str,
    years: int,
    tolerance: int,
) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="Insufficient data")

    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-years:]
    missing_years = sum(1 for d in sorted_data if d.get("value", 0) <= 0)

    if missing_years <= tolerance:
        return ScoreBreakdown(
            name=name, score=1, max_score=1, reason=f"Consistent over {len(sorted_data)}y"
        )
    return ScoreBreakdown(name=name, score=0, max_score=1, reason=f"Missing {missing_years} years")


def _score_mostly_positive(
    history: list[dict[str, Any]] | None,
    name: str,
    years: int,
    tolerance: int,
) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="Insufficient data")

    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-years:]
    negative_years = sum(1 for d in sorted_data if d.get("value", 0) < 0)

    if negative_years <= tolerance:
        return ScoreBreakdown(
            name=name, score=1, max_score=1, reason=f"Mostly positive over {len(sorted_data)}y"
        )
    return ScoreBreakdown(
        name=name, score=0, max_score=1, reason=f"Negative {negative_years} years"
    )


def _score_above_threshold(
    history: list[dict[str, Any]] | None,
    name: str,
    threshold: float,
    years: int,
    tolerance: int,
) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="Insufficient data")

    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-years:]
    below_threshold = sum(1 for d in sorted_data if d.get("value", 0) < threshold)

    if below_threshold <= tolerance:
        return ScoreBreakdown(
            name=name, score=1, max_score=1, reason=f"Above {threshold:.0%} for {len(sorted_data)}y"
        )
    return ScoreBreakdown(
        name=name, score=0, max_score=1, reason=f"Below threshold {below_threshold} years"
    )


def _score_interest_coverage(ic: float | None) -> ScoreBreakdown:
    if ic is None:
        return ScoreBreakdown(name="Interest Coverage", score=0, max_score=1, reason="No data")
    if ic < 0:
        return ScoreBreakdown(name="Interest Coverage", score=1, max_score=1, reason="No debt")
    if ic >= 10:
        return ScoreBreakdown(
            name="Interest Coverage", score=1, max_score=1, reason=f"IC={ic:.1f}x (excellent)"
        )
    if ic >= 4:
        return ScoreBreakdown(
            name="Interest Coverage", score=0.5, max_score=1, reason=f"IC={ic:.1f}x (adequate)"
        )
    return ScoreBreakdown(
        name="Interest Coverage", score=0, max_score=1, reason=f"IC={ic:.1f}x (low)"
    )


def _score_net_margin(history: list[dict[str, Any]] | None) -> ScoreBreakdown:
    latest = _get_latest_value(history)
    if latest is None:
        return ScoreBreakdown(name="Net Margin", score=0, max_score=1, reason="No data")
    if latest >= 0.20:
        return ScoreBreakdown(
            name="Net Margin", score=1, max_score=1, reason=f"Margin={latest:.1%} (excellent)"
        )
    if latest >= 0.10:
        return ScoreBreakdown(
            name="Net Margin", score=0.5, max_score=1, reason=f"Margin={latest:.1%} (good)"
        )
    return ScoreBreakdown(
        name="Net Margin", score=0, max_score=1, reason=f"Margin={latest:.1%} (low)"
    )


def _score_dividend_years(years: int | None) -> ScoreBreakdown:
    if years is None:
        return ScoreBreakdown(name="Dividend Growth", score=0, max_score=4, reason="Unknown")
    if years >= 50:
        return ScoreBreakdown(
            name="Dividend Growth", score=4, max_score=4, reason=f"{years}y (King)"
        )
    if years >= 25:
        return ScoreBreakdown(
            name="Dividend Growth", score=3, max_score=4, reason=f"{years}y (Aristocrat)"
        )
    if years >= 10:
        return ScoreBreakdown(
            name="Dividend Growth", score=2, max_score=4, reason=f"{years}y (Achiever)"
        )
    if years >= 5:
        return ScoreBreakdown(
            name="Dividend Growth", score=1, max_score=4, reason=f"{years}y (Contender)"
        )
    return ScoreBreakdown(name="Dividend Growth", score=0, max_score=4, reason=f"{years}y (short)")


def _calculate_cagr(history: list[dict[str, Any]] | None, years: int) -> float | None:
    if not history or len(history) < 2:
        return None
    sorted_data = sorted(history, key=lambda x: x.get("year", 0))
    if len(sorted_data) < years:
        years = len(sorted_data)
    start_val = sorted_data[-years]["value"]
    end_val = sorted_data[-1]["value"]
    if start_val <= 0 or end_val <= 0:
        return None
    return (end_val / start_val) ** (1 / years) - 1


def _score_growth_rate(rate: float | None, name: str) -> ScoreBreakdown:
    if rate is None:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="No data")
    if rate >= 0.10:
        return ScoreBreakdown(name=name, score=1, max_score=1, reason=f"{rate:.1%} (excellent)")
    if rate >= 0.06:
        return ScoreBreakdown(name=name, score=0.5, max_score=1, reason=f"{rate:.1%} (good)")
    return ScoreBreakdown(name=name, score=0, max_score=1, reason=f"{rate:.1%} (low)")


def _score_growth_acceleration(g5: float | None, g10: float | None) -> ScoreBreakdown:
    if g5 is None or g10 is None or g10 <= 0:
        return ScoreBreakdown(
            name="Growth Acceleration", score=0, max_score=1, reason="Insufficient data"
        )
    ratio = g5 / g10
    if ratio >= 1:
        return ScoreBreakdown(
            name="Growth Acceleration",
            score=1,
            max_score=1,
            reason=f"5Y/10Y={ratio:.2f} (accelerating)",
        )
    return ScoreBreakdown(
        name="Growth Acceleration",
        score=0,
        max_score=1,
        reason=f"5Y/10Y={ratio:.2f} (decelerating)",
    )


def _calculate_payout_ratio(
    dividend_history: list[dict[str, Any]] | None,
    denominator_history: list[dict[str, Any]] | None,
) -> float | None:
    div = _get_latest_value(dividend_history)
    denom = _get_latest_value(denominator_history)
    if div is None or denom is None or denom == 0:
        return None
    return abs(div) / abs(denom)


def _score_payout_ratio(ratio: float | None, name: str, low: float, high: float) -> ScoreBreakdown:
    if ratio is None:
        return ScoreBreakdown(name=name, score=0, max_score=1, reason="No data")
    if ratio < low:
        return ScoreBreakdown(name=name, score=1, max_score=1, reason=f"{ratio:.0%} (safe)")
    if ratio < high:
        return ScoreBreakdown(name=name, score=0.5, max_score=1, reason=f"{ratio:.0%} (moderate)")
    return ScoreBreakdown(name=name, score=0, max_score=1, reason=f"{ratio:.0%} (high)")


def _score_eps_stability(history: list[dict[str, Any]] | None) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(
            name="EPS Stability", score=0, max_score=1, reason="Insufficient data"
        )
    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-10:]
    positive = sum(1 for d in sorted_data if d.get("value", 0) > 0)
    is_rising = _score_rising_trend(history, "", 10, 2).score > 0
    if is_rising:
        return ScoreBreakdown(name="EPS Stability", score=1, max_score=1, reason="Rising trend")
    if positive >= len(sorted_data) - 2:
        return ScoreBreakdown(
            name="EPS Stability", score=0.5, max_score=1, reason="Mostly positive"
        )
    return ScoreBreakdown(name="EPS Stability", score=0, max_score=1, reason="Unstable")


def _score_buyback(shares_history: list[dict[str, Any]] | None) -> ScoreBreakdown:
    if not shares_history or len(shares_history) < 5:
        return ScoreBreakdown(name="Buyback", score=0, max_score=1, reason="Insufficient data")
    sorted_data = sorted(shares_history, key=lambda x: x.get("year", 0))[-5:]
    declining = 0
    for i in range(1, len(sorted_data)):
        if sorted_data[i]["value"] < sorted_data[i - 1]["value"]:
            declining += 1
    if declining >= len(sorted_data) - 2:
        return ScoreBreakdown(name="Buyback", score=1, max_score=1, reason="Active buyback program")
    return ScoreBreakdown(name="Buyback", score=0, max_score=1, reason="No buyback detected")


def _score_average_roe(history: list[dict[str, Any]] | None) -> ScoreBreakdown:
    if not history or len(history) < 3:
        return ScoreBreakdown(name="Avg ROE", score=0, max_score=1, reason="Insufficient data")
    sorted_data = sorted(history, key=lambda x: x.get("year", 0))[-10:]
    avg = sum(d.get("value", 0) for d in sorted_data) / len(sorted_data)
    if avg >= 0.15:
        return ScoreBreakdown(name="Avg ROE", score=1, max_score=1, reason=f"Avg={avg:.1%}")
    return ScoreBreakdown(name="Avg ROE", score=0, max_score=1, reason=f"Avg={avg:.1%} (low)")


def _score_beta(beta: float | None) -> ScoreBreakdown:
    if beta is None:
        return ScoreBreakdown(name="Beta", score=0, max_score=1, reason="No data")
    if beta <= 1.2:
        return ScoreBreakdown(name="Beta", score=1, max_score=1, reason=f"Beta={beta:.2f} (stable)")
    return ScoreBreakdown(name="Beta", score=0, max_score=1, reason=f"Beta={beta:.2f} (volatile)")


def _get_current_yield(
    dividend_history: list[dict[str, Any]] | None, price: float | None
) -> float | None:
    div = _get_latest_value(dividend_history)
    if div is None or price is None or price <= 0:
        return None
    return abs(div) / price


def _calculate_stats(history: list[dict[str, Any]] | None) -> tuple[float, float, float] | None:
    """Calculate mean, std, and latest value from history."""
    if not history or len(history) < 2:
        return None
    values = [item["value"] for item in history if item.get("value") is not None and item["value"] > 0]
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    # Get latest value (assuming sorted by year)
    sorted_history = sorted(history, key=lambda x: x.get("year", 0))
    latest = sorted_history[-1].get("value")
    if latest is None or latest <= 0:
        return None
    return mean, std, latest


def _calculate_history_stats(history: list[dict[str, Any]] | None) -> tuple[float, float] | None:
    """Calculate mean and std from history (without extracting latest)."""
    if not history or len(history) < 2:
        return None
    values = [item["value"] for item in history if item.get("value") is not None and item["value"] > 0]
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance ** 0.5
    return mean, std


def _score_yield_relative_to_history(
    dividend_yield_history: list[dict[str, Any]] | None,
    current_yield: float | None = None,
) -> ScoreBreakdown:
    """Score if current dividend yield is at or above upper band (mean + std).
    Higher yield relative to history is better.
    
    Args:
        dividend_yield_history: Historical yield data for calculating mean/std
        current_yield: Current dividend yield from Key Statistics (preferred)
    """
    # Calculate mean/std from history
    stats = _calculate_history_stats(dividend_yield_history)
    if stats is None:
        return ScoreBreakdown(
            name="Yield vs History", score=0, max_score=1, reason="Insufficient yield history"
        )
    
    mean, std = stats
    upper_band = mean + std
    
    # Use provided current_yield, or fall back to latest from history
    if current_yield is not None:
        latest = current_yield
    else:
        # Fallback to extracting from history
        full_stats = _calculate_stats(dividend_yield_history)
        if full_stats is None:
            return ScoreBreakdown(
                name="Yield vs History", score=0, max_score=1, reason="No current yield"
            )
        _, _, latest = full_stats
    
    # Score if yield is at or above upper band (historically high yield)
    if latest >= upper_band:
        return ScoreBreakdown(
            name="Yield vs History",
            score=1,
            max_score=1,
            reason=f"{latest:.2%} ≥ {upper_band:.2%} (high)",
        )
    return ScoreBreakdown(
        name="Yield vs History",
        score=0,
        max_score=1,
        reason=f"{latest:.2%} < {upper_band:.2%}",
    )


def _score_pe_relative_to_history(
    pe_history: list[dict[str, Any]] | None,
    current_pe: float | None = None,
) -> ScoreBreakdown:
    """Score if current PE is at or below lower band (mean - std).
    Lower PE relative to history is better.
    
    Args:
        pe_history: Historical PE data for calculating mean/std
        current_pe: Current trailing PE from Key Statistics (preferred)
    """
    # Calculate mean/std from history
    stats = _calculate_history_stats(pe_history)
    if stats is None:
        return ScoreBreakdown(
            name="PE vs History", score=0, max_score=1, reason="Insufficient PE history"
        )
    
    mean, std = stats
    lower_band = max(0, mean - std)
    
    # Use provided current_pe, or fall back to latest from history
    if current_pe is not None:
        latest = current_pe
    else:
        # Fallback to extracting from history
        full_stats = _calculate_stats(pe_history)
        if full_stats is None:
            return ScoreBreakdown(
                name="PE vs History", score=0, max_score=1, reason="No current PE"
            )
        _, _, latest = full_stats
    
    # Score if PE is at or below lower band (historically low PE)
    if latest <= lower_band:
        return ScoreBreakdown(
            name="PE vs History",
            score=1,
            max_score=1,
            reason=f"{latest:.1f} ≤ {lower_band:.1f} (low)",
        )
    return ScoreBreakdown(
        name="PE vs History",
        score=0,
        max_score=1,
        reason=f"{latest:.1f} > {lower_band:.1f}",
    )


def _score_high_yield(div_yield: float | None) -> ScoreBreakdown:
    if div_yield is None:
        return ScoreBreakdown(name="High Yield", score=0, max_score=1, reason="No yield data")
    if div_yield >= 0.04:
        return ScoreBreakdown(
            name="High Yield", score=1, max_score=1, reason=f"Yield={div_yield:.1%}"
        )
    return ScoreBreakdown(name="High Yield", score=0, max_score=1, reason=f"Yield={div_yield:.1%}")


def _score_yield_vs_sp500(div_yield: float | None, sp500_yield: float) -> ScoreBreakdown:
    if div_yield is None:
        return ScoreBreakdown(name="Yield vs S&P500", score=0, max_score=1, reason="No yield data")
    if div_yield >= sp500_yield * 1.5:
        return ScoreBreakdown(
            name="Yield vs S&P500",
            score=1,
            max_score=1,
            reason=f"{div_yield:.1%} >= 1.5x S&P ({sp500_yield:.2%})",
        )
    return ScoreBreakdown(
        name="Yield vs S&P500",
        score=0,
        max_score=1,
        reason=f"{div_yield:.1%} < 1.5x S&P ({sp500_yield:.2%})",
    )


def _score_chowder_rule(div_yield: float | None, growth_5y: float | None) -> ScoreBreakdown:
    if div_yield is None or growth_5y is None:
        return ScoreBreakdown(name="Chowder Rule", score=0, max_score=1, reason="Insufficient data")
    chowder = div_yield + growth_5y
    if chowder >= 0.15:
        return ScoreBreakdown(
            name="Chowder Rule", score=1, max_score=1, reason=f"{chowder:.1%} >= 15%"
        )
    return ScoreBreakdown(name="Chowder Rule", score=0, max_score=1, reason=f"{chowder:.1%} < 15%")


def _score_fcf_yield(
    fcf_history: list[dict[str, Any]] | None, price: float | None
) -> ScoreBreakdown:
    fcf = _get_latest_value(fcf_history)
    if fcf is None or price is None or price <= 0:
        return ScoreBreakdown(name="FCF Yield", score=0, max_score=2, reason="No data")
    fcf_yield = fcf / price
    if fcf_yield >= 0.10:
        return ScoreBreakdown(
            name="FCF Yield", score=2, max_score=2, reason=f"FCF Yield={fcf_yield:.1%}"
        )
    if fcf_yield >= 0.05:
        return ScoreBreakdown(
            name="FCF Yield", score=1, max_score=2, reason=f"FCF Yield={fcf_yield:.1%}"
        )
    return ScoreBreakdown(
        name="FCF Yield", score=0, max_score=2, reason=f"FCF Yield={fcf_yield:.1%}"
    )


def _score_low_pe(pe: float | None) -> ScoreBreakdown:
    if pe is None:
        return ScoreBreakdown(name="Low PE", score=0, max_score=1, reason="No PE data")
    if pe < 15:
        return ScoreBreakdown(name="Low PE", score=1, max_score=1, reason=f"PE={pe:.1f}")
    return ScoreBreakdown(name="Low PE", score=0, max_score=1, reason=f"PE={pe:.1f}")


def _score_pe_with_high_roe(
    pe: float | None, roe_history: list[dict[str, Any]] | None
) -> ScoreBreakdown:
    if pe is None or not roe_history:
        return ScoreBreakdown(name="PE+ROE Combo", score=0, max_score=1, reason="Insufficient data")
    sorted_data = sorted(roe_history, key=lambda x: x.get("year", 0))[-10:]
    avg_roe = sum(d.get("value", 0) for d in sorted_data) / len(sorted_data)
    if pe < 15 and avg_roe >= 0.20:
        return ScoreBreakdown(
            name="PE+ROE Combo", score=1, max_score=1, reason=f"PE={pe:.1f}, ROE={avg_roe:.1%}"
        )
    return ScoreBreakdown(
        name="PE+ROE Combo", score=0, max_score=1, reason=f"PE={pe:.1f}, ROE={avg_roe:.1%}"
    )


def _calculate_growth_fair_value(
    metrics: FinancialMetrics,
    current_price: float | None,
) -> FairValueEstimate:
    # Use Finviz forward-looking data: EPS next Y * EPS next 5Y growth
    eps_next = metrics.eps_next_year
    growth_5y = metrics.eps_growth_next_5y

    if eps_next is None or growth_5y is None or growth_5y <= 0:
        # Fallback to historical data if Finviz data unavailable
        eps = _get_latest_value(metrics.eps_history)
        growth = _calculate_cagr(metrics.eps_history, 5)
        
        if eps is None or growth is None or growth <= 0:
            return FairValueEstimate(
                model=ValuationModel.GROWTH,
                fair_value=None,
                current_price=current_price,
                is_undervalued=False,
                explanation="Cannot calculate: EPS or growth data unavailable",
            )
        
        growth_pct = growth * 100
        fair_value = eps * growth_pct
        is_undervalued = current_price is not None and current_price <= fair_value
        return FairValueEstimate(
            model=ValuationModel.GROWTH,
            fair_value=round(fair_value, 2),
            current_price=current_price,
            is_undervalued=is_undervalued,
            explanation=f"EPS ({eps:.2f}) × Growth Rate ({growth:.1%}) = ${fair_value:.2f} (historical)",
        )

    # Finviz formula: EPS next Y × EPS next 5Y growth (as multiplier)
    growth_pct = growth_5y * 100
    fair_value = eps_next * growth_pct

    is_undervalued = current_price is not None and current_price <= fair_value

    return FairValueEstimate(
        model=ValuationModel.GROWTH,
        fair_value=round(fair_value, 2),
        current_price=current_price,
        is_undervalued=is_undervalued,
        explanation=f"EPS next Y (${eps_next:.2f}) × Growth 5Y ({growth_5y:.1%}) = ${fair_value:.2f}",
    )


def _calculate_dividend_fair_value(
    metrics: FinancialMetrics,
    current_price: float | None,
    expected_return: float,
) -> FairValueEstimate:
    # Use Finviz dividend_est, fallback to historical if unavailable
    div = metrics.dividend_est
    source = "Finviz"
    
    if div is None or div <= 0:
        div = _get_latest_value(metrics.dividend_history)
        source = "historical"

    if div is None or div <= 0:
        return FairValueEstimate(
            model=ValuationModel.DIVIDEND,
            fair_value=None,
            current_price=current_price,
            is_undervalued=False,
            explanation="Cannot calculate: No dividend data",
        )

    # DDM: Fair Value = Dividend / Expected Return
    fair_value = abs(div) / expected_return

    is_undervalued = current_price is not None and current_price <= fair_value

    return FairValueEstimate(
        model=ValuationModel.DIVIDEND,
        fair_value=round(fair_value, 2),
        current_price=current_price,
        is_undervalued=is_undervalued,
        explanation=f"Dividend Est (${abs(div):.2f}) / Required Return ({expected_return:.1%}) = ${fair_value:.2f}",
    )


def _calculate_asset_fair_value(
    metrics: FinancialMetrics,
    current_price: float | None,
    pb_threshold: float,
) -> FairValueEstimate:
    # Use Finviz book_value_per_share, fallback to historical if unavailable
    bvps = metrics.book_value_per_share
    source = "Finviz"
    
    if bvps is None or bvps <= 0:
        bvps = _get_latest_value(metrics.book_value_history)
        source = "historical"

    if bvps is None or bvps <= 0:
        return FairValueEstimate(
            model=ValuationModel.ASSET,
            fair_value=None,
            current_price=current_price,
            is_undervalued=False,
            explanation="Cannot calculate: No book value data",
        )

    # Fair Value = BVPS * P/B threshold
    fair_value = bvps * pb_threshold

    is_undervalued = current_price is not None and current_price <= fair_value

    return FairValueEstimate(
        model=ValuationModel.ASSET,
        fair_value=round(fair_value, 2),
        current_price=current_price,
        is_undervalued=is_undervalued,
        explanation=f"Book/sh (${bvps:.2f}) × P/B Threshold ({pb_threshold}) = ${fair_value:.2f}",
    )


def _score_debt_ratio(history: list[dict[str, Any]] | None) -> ScoreBreakdown:
    latest = _get_latest_value(history)
    if latest is None:
        return ScoreBreakdown(name="Debt Ratio", score=0, max_score=1, reason="No data")
    if latest < 0.20:
        return ScoreBreakdown(
            name="Debt Ratio", score=1, max_score=1, reason=f"Debt/Cap={latest:.1%} (safe)"
        )
    if latest > 0.50:
        return ScoreBreakdown(
            name="Debt Ratio", score=-1, max_score=1, reason=f"Debt/Cap={latest:.1%} (high risk)"
        )
    return ScoreBreakdown(
        name="Debt Ratio", score=0, max_score=1, reason=f"Debt/Cap={latest:.1%} (moderate)"
    )
