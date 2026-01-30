import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.schemas.value_analysis import (
    DataStatusEnum,
    FairValueRequest,
    FairValueResponse,
    ScoreBreakdownResponse,
    ValueAnalysisResponse,
    YearValueResponse,
    ConfidenceScoreResponse,
    DividendScoreResponse,
    ValueScoreResponse,
)
from src.services.financial_data_service import get_financial_data
from src.core.cache import cache_get, cache_set
from src.services.value_analysis import (
    calculate_confidence_score,
    calculate_dividend_score,
    calculate_value_score,
    calculate_fair_value,
    ValuationModel,
)
from src.services.ai_scoring import (
    generate_moat_prompt,
    generate_risk_prompt,
)
from src.services.market_data import get_stock_price, get_fundamental_data, get_sp500_yield

router = APIRouter(prefix="/analysis", tags=["analysis"])

_prefetch_tasks: dict[str, bool] = {}


def _determine_data_status(metrics) -> DataStatusEnum:
    has_history = bool(metrics.eps_history or metrics.roe_history or metrics.dividend_history)
    has_roic = "roic" in (metrics.source or "").lower()

    if has_roic and has_history:
        return DataStatusEnum.COMPLETE
    elif has_history:
        return DataStatusEnum.PARTIAL
    else:
        return DataStatusEnum.INSUFFICIENT


@router.get("/{symbol}/status")
async def get_analysis_status(symbol: str, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    cache_key = f"financial_data:{symbol}"
    cached = await cache_get(cache_key)

    return {
        "symbol": symbol,
        "cached": cached is not None,
        "fetching": _prefetch_tasks.get(symbol, False),
    }


async def _background_prefetch(symbol: str, db: AsyncSession):
    symbol = symbol.upper()
    _prefetch_tasks[symbol] = True
    try:
        await get_financial_data(symbol, db)
    finally:
        _prefetch_tasks[symbol] = False


@router.post("/{symbol}/prefetch")
async def prefetch_analysis(
    symbol: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    symbol = symbol.upper()
    cache_key = f"financial_data:{symbol}"
    cached = await cache_get(cache_key)

    if cached:
        return {"symbol": symbol, "status": "cached"}

    if _prefetch_tasks.get(symbol):
        return {"symbol": symbol, "status": "fetching"}

    background_tasks.add_task(_background_prefetch, symbol, db)
    return {"symbol": symbol, "status": "started"}


@router.get("/{symbol}/value", response_model=ValueAnalysisResponse)
async def get_value_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    fundamental = await get_fundamental_data(symbol, db)
    if fundamental and fundamental.get("is_etf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Value analysis is not available for ETFs",
        )

    metrics = await get_financial_data(symbol, db)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch financial data for {symbol.upper()}",
        )

    price_data = await get_stock_price(symbol)
    current_price = price_data.get("price") if price_data else None

    # Get dynamic S&P 500 yield
    sp500_yield = await get_sp500_yield(db)

    confidence = calculate_confidence_score(metrics)
    dividend = calculate_dividend_score(metrics, metrics.beta)
    
    # Extract Key Statistics for Value Score comparison
    trailing_pe = fundamental.get("trailing_pe") if fundamental else None
    # Note: yfinance returns dividend_yield as percentage (e.g., 0.4 = 40%)
    # Historical data uses decimal form (e.g., 0.004 = 0.4%), so divide by 100
    dividend_yield_raw = fundamental.get("dividend_yield") if fundamental else None
    dividend_yield_stat = dividend_yield_raw / 100 if dividend_yield_raw else None
    
    value = calculate_value_score(
        metrics,
        current_price,
        sp500_yield=sp500_yield,
        trailing_pe=trailing_pe,
        dividend_yield=dividend_yield_stat,
    )

    data_status = _determine_data_status(metrics)

    return ValueAnalysisResponse(
        symbol=symbol.upper(),
        data_status=data_status,
        data_source=metrics.source,
        confidence=ConfidenceScoreResponse(
            total=confidence.total,
            max_possible=confidence.max_possible,
            breakdown=[
                ScoreBreakdownResponse(
                    name=b.name,
                    score=b.score,
                    max_score=b.max_score,
                    reason=b.reason,
                )
                for b in confidence.breakdown
            ],
            moat_score=confidence.moat_score,
            risk_score=confidence.risk_score,
        ),
        dividend=DividendScoreResponse(
            total=dividend.total,
            max_possible=dividend.max_possible,
            breakdown=[
                ScoreBreakdownResponse(
                    name=b.name,
                    score=b.score,
                    max_score=b.max_score,
                    reason=b.reason,
                )
                for b in dividend.breakdown
            ],
        ),
        value=ValueScoreResponse(
            total=value.total,
            max_possible=value.max_possible,
            breakdown=[
                ScoreBreakdownResponse(
                    name=b.name,
                    score=b.score,
                    max_score=b.max_score,
                    reason=b.reason,
                )
                for b in value.breakdown
            ],
        ),
        pe_history=[
            YearValueResponse(year=item["year"], value=item["value"])
            for item in (metrics.pe_history or [])
        ] or None,
        dividend_yield_history=[
            YearValueResponse(year=item["year"], value=item["value"])
            for item in (metrics.dividend_yield_history or [])
        ] or None,
    )


@router.post("/{symbol}/fair-value", response_model=FairValueResponse)
async def get_fair_value(
    symbol: str,
    request: FairValueRequest,
    db: AsyncSession = Depends(get_db),
):
    metrics = await get_financial_data(symbol, db)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch financial data for {symbol.upper()}",
        )

    price_data = await get_stock_price(symbol)
    current_price = price_data.get("price") if price_data else None

    model = ValuationModel(request.model.value)
    result = calculate_fair_value(
        metrics,
        model,
        current_price,
        request.expected_return,
        request.pb_threshold,
    )

    return FairValueResponse(
        model=request.model,
        fair_value=result.fair_value,
        current_price=result.current_price,
        is_undervalued=result.is_undervalued,
        explanation=result.explanation,
    )





@router.get("/{symbol}/ai-prompt/{score_type}")
async def get_ai_prompt(
    symbol: str,
    score_type: str,
    db: AsyncSession = Depends(get_db),
):
    if score_type not in ("moat", "risk"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="score_type must be 'moat' or 'risk'",
        )

    fundamental = await get_fundamental_data(symbol, db)
    company_name = fundamental.get("long_name", symbol) if fundamental else symbol
    sector = fundamental.get("sector") if fundamental else None
    industry = fundamental.get("industry") if fundamental else None

    if score_type == "moat":
        prompt = generate_moat_prompt(symbol, company_name, sector, industry)
    else:
        prompt = generate_risk_prompt(symbol, company_name, sector, industry)

    return {"symbol": symbol.upper(), "score_type": score_type, "prompt": prompt}
