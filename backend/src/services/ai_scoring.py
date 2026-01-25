import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache_get, cache_set
from src.core.config import get_settings
from src.models.financial_data import AIScoreCache


MOAT_PROMPT_TEMPLATE = """Analyze the economic moat of {company_name} ({symbol}).

Company Info:
- Sector: {sector}
- Industry: {industry}

Score each moat category (0 or 1 point each, max 5 total):
1. Intangible Assets (brand recognition like MCD/DIS, or patents like JNJ/MMM)
2. Cost Advantage (like COST, WMT - economies of scale)
3. Network Effect (value increases with users, like META, V, MA)
4. Switching Costs (high cost to switch, like ADBE)
5. Niche Market (dominant in specialized market, like UNP, CNI, LMT)

Return ONLY valid JSON:
{{"intangible_assets": 0 or 1, "cost_advantage": 0 or 1, "network_effect": 0 or 1, "switching_costs": 0 or 1, "niche_market": 0 or 1, "total": 0-5, "reasoning": "brief explanation"}}"""

RISK_PROMPT_TEMPLATE = """Analyze environmental risks for {company_name} ({symbol}).

Company Info:
- Sector: {sector}
- Industry: {industry}

Score each risk category (-1, 0 points each, max -3 total):
1. Authority/Policy Risk: Government regulation exposure (energy, healthcare, biotech, tobacco/alcohol)
2. Science/Tech Risk: Product obsolescence risk (tech, fashion, trends)
3. Key People Risk: Dependence on key individuals (like TSLA) OR hard-to-replace employees (aviation, healthcare)

Return ONLY valid JSON:
{{"authority_risk": 0 or -1, "tech_risk": 0 or -1, "key_people_risk": 0 or -1, "total": -3 to 0, "reasoning": "brief explanation"}}"""


async def get_ai_moat_score(
    symbol: str,
    company_name: str,
    sector: str | None,
    industry: str | None,
    db: AsyncSession,
    force_refresh: bool = False,
) -> dict[str, Any]:
    return await _get_or_compute_ai_score(
        symbol=symbol,
        score_type="moat",
        prompt=MOAT_PROMPT_TEMPLATE.format(
            company_name=company_name,
            symbol=symbol,
            sector=sector or "Unknown",
            industry=industry or "Unknown",
        ),
        db=db,
        force_refresh=force_refresh,
    )


async def get_ai_risk_score(
    symbol: str,
    company_name: str,
    sector: str | None,
    industry: str | None,
    db: AsyncSession,
    force_refresh: bool = False,
) -> dict[str, Any]:
    return await _get_or_compute_ai_score(
        symbol=symbol,
        score_type="risk",
        prompt=RISK_PROMPT_TEMPLATE.format(
            company_name=company_name,
            symbol=symbol,
            sector=sector or "Unknown",
            industry=industry or "Unknown",
        ),
        db=db,
        force_refresh=force_refresh,
    )


def generate_moat_prompt(
    symbol: str, company_name: str, sector: str | None, industry: str | None
) -> str:
    return MOAT_PROMPT_TEMPLATE.format(
        company_name=company_name,
        symbol=symbol,
        sector=sector or "Unknown",
        industry=industry or "Unknown",
    )


def generate_risk_prompt(
    symbol: str, company_name: str, sector: str | None, industry: str | None
) -> str:
    return RISK_PROMPT_TEMPLATE.format(
        company_name=company_name,
        symbol=symbol,
        sector=sector or "Unknown",
        industry=industry or "Unknown",
    )


async def _get_or_compute_ai_score(
    symbol: str,
    score_type: str,
    prompt: str,
    db: AsyncSession,
    force_refresh: bool = False,
) -> dict[str, Any]:
    symbol = symbol.upper()
    cache_key = f"ai_score:{score_type}:{symbol}"

    if not force_refresh:
        cached = await cache_get(cache_key)
        if cached:
            return cached

        db_cached = await _get_from_db_cache(symbol, score_type, db)
        if db_cached:
            await cache_set(cache_key, db_cached, ttl=86400)
            return db_cached

    settings = get_settings()
    if not settings.openai_api_key:
        return {
            "error": "AI scoring unavailable",
            "prompt": prompt,
            "manual_entry_required": True,
        }

    try:
        result = await _call_openai(prompt, settings.openai_api_key)
        await _save_to_db_cache(symbol, score_type, result, prompt, db)
        await cache_set(cache_key, result, ttl=86400)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "prompt": prompt,
            "manual_entry_required": True,
        }


async def _get_from_db_cache(
    symbol: str, score_type: str, db: AsyncSession
) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(AIScoreCache)
        .where(AIScoreCache.symbol == symbol)
        .where(AIScoreCache.score_type == score_type)
        .where(AIScoreCache.expires_at > now)
        .order_by(AIScoreCache.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if not row:
        return None

    return {
        "score": row.score_value,
        "breakdown": row.breakdown,
        "cached_at": row.created_at.isoformat(),
    }


async def _save_to_db_cache(
    symbol: str,
    score_type: str,
    result: dict[str, Any],
    prompt: str,
    db: AsyncSession,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    total_score = result.get("total", 0)
    breakdown = {k: v for k, v in result.items() if k not in ("total", "reasoning")}

    record = AIScoreCache(
        symbol=symbol,
        score_type=score_type,
        score_value=float(total_score),
        breakdown=breakdown,
        prompt_used=prompt[:5000],
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()


async def _call_openai(prompt: str, api_key: str) -> dict[str, Any]:
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial analyst. Respond only with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        return json.loads(content)
