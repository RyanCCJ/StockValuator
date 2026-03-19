import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache_get, cache_set
from src.core.config import get_settings
from src.models.financial_data import AIScoreCache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AI_SCORE_REDIS_TTL = 86400  # 24 hours
AI_SCORE_DB_TTL_DAYS = 90

REDIS_KEY_PREFIX = "ai_score"


def _redis_key(symbol: str, score_type: str) -> str:
    return f"{REDIS_KEY_PREFIX}:{symbol.upper()}:{score_type}"


# ---------------------------------------------------------------------------
# Provider config mapping (task 1.2)
# ---------------------------------------------------------------------------
PROVIDER_CONFIG: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "",  # uses SDK default
        "default_model": "gpt-5.4-nano",
        "api_key_field": "openai_api_key",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/",
        "default_model": "claude-haiku-4-5",
        "api_key_field": "anthropic_api_key",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-3.1-flash-lite-preview",
        "api_key_field": "gemini_api_key",
    },
}


def get_provider_config() -> dict[str, str] | None:
    """Return provider config dict or None if AI is disabled."""
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()
    if not provider or provider not in PROVIDER_CONFIG:
        return None
    return PROVIDER_CONFIG[provider]


def is_ai_enabled() -> bool:
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()
    return provider in PROVIDER_CONFIG


# ---------------------------------------------------------------------------
# AI client factory (task 2.1)
# ---------------------------------------------------------------------------
def _get_ai_client():
    """Return a configured openai.AsyncOpenAI client for the active provider."""
    import openai

    settings = get_settings()
    config = get_provider_config()
    if config is None:
        raise RuntimeError("AI provider is not configured")

    api_key = getattr(settings, config["api_key_field"])
    kwargs: dict[str, Any] = {"api_key": api_key}
    if config["base_url"]:
        kwargs["base_url"] = config["base_url"]

    return openai.AsyncOpenAI(**kwargs)


def _get_model() -> str:
    settings = get_settings()
    if settings.ai_model:
        return settings.ai_model
    config = get_provider_config()
    if config is None:
        raise RuntimeError("AI provider is not configured")
    return config["default_model"]


# ---------------------------------------------------------------------------
# Prompt templates (task 2.2 – updated with JSON output instructions)
# ---------------------------------------------------------------------------
MOAT_PROMPT_TEMPLATE = """Analyze the economic moat of {company_name} ({symbol}).
BE STRICT AND CRITICAL. Do not give points easily. Only award points if there is STRONG evidence of a durable competitive advantage. Most companies should NOT get a perfect score (5/5).

Company Info:
- Sector: {sector}
- Industry: {industry}

Score each moat category (0 or 1 point each, max 5 total):
1. Intangible Assets: Does it have a PREMIUM brand allowing higher pricing (e.g., Apple, Hermes) or critical patents/licenses? (Standard brand recognition is NOT enough).
2. Cost Advantage: Does it have a STRUCTURAL cost advantage allowing it to undercut rivals profitably (e.g., Costco, scale of Amazon)? (Operational efficiency alone is 0).
3. Network Effect: Does the service become better as more people use it? (e.g., Meta, Visa, MasterCard).
4. Switching Costs: Is it painful, costly, or risky for customers to switch? (e.g., Adobe, Oracle, Medical devices).
5. Niche Market: Does it DOMINATE a specific niche with few competitors? (e.g., ASML, railroads).

You MUST respond with a JSON object in the following format (no markdown, no extra text):
{{
  "total_score": <int 0-5>,
  "categories": [
    {{"name": "Intangible Assets", "score": <0 or 1>, "reasoning": "<brief critical reasoning>"}},
    {{"name": "Cost Advantage", "score": <0 or 1>, "reasoning": "<brief critical reasoning>"}},
    {{"name": "Network Effect", "score": <0 or 1>, "reasoning": "<brief critical reasoning>"}},
    {{"name": "Switching Costs", "score": <0 or 1>, "reasoning": "<brief critical reasoning>"}},
    {{"name": "Niche Market", "score": <0 or 1>, "reasoning": "<brief critical reasoning>"}}
  ],
  "reasoning": "<overall summary reasoning>"
}}"""

RISK_PROMPT_TEMPLATE = """Analyze environmental risks for {company_name} ({symbol}).
BE CRITICAL. Identify potential downsides. If a risk exists, apply the penalty.

Company Info:
- Sector: {sector}
- Industry: {industry}

Score each risk category (-1 or 0 points each, max -3 total):
1. Authority/Policy Risk: Is there significant exposure to government regulation, antitrust, price controls, or trade wars? (e.g., Utilities, Healthcare, Big Tech antitrust). (0 if safe, -1 if risky).
2. Science/Tech Risk: Is the business vulnerable to rapid disruption or obsolescence? (e.g., Legacy tech, single-product biotech, fashion trends). (0 if safe, -1 if risky).
3. Key People Risk: Is the company heavily dependent on a specific leader (e.g., Elon Musk) or specialized labor that is hard to replace? (0 if safe, -1 if risky).

You MUST respond with a JSON object in the following format (no markdown, no extra text):
{{
  "total_score": <int -3 to 0>,
  "categories": [
    {{"name": "Authority/Policy Risk", "score": <0 or -1>, "reasoning": "<brief reasoning>"}},
    {{"name": "Science/Tech Risk", "score": <0 or -1>, "reasoning": "<brief reasoning>"}},
    {{"name": "Key People Risk", "score": <0 or -1>, "reasoning": "<brief reasoning>"}}
  ],
  "reasoning": "<overall summary reasoning>"
}}"""


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


# ---------------------------------------------------------------------------
# Pydantic response models (task 2.4)
# ---------------------------------------------------------------------------
class CategoryScore(BaseModel):
    name: str
    score: int
    reasoning: str


class MoatAIResponse(BaseModel):
    total_score: int = Field(..., ge=0, le=5)
    categories: list[CategoryScore]
    reasoning: str

    @field_validator("total_score")
    @classmethod
    def validate_moat_range(cls, v: int) -> int:
        if v < 0 or v > 5:
            raise ValueError("Moat total_score must be 0-5")
        return v


class RiskAIResponse(BaseModel):
    total_score: int = Field(..., ge=-3, le=0)
    categories: list[CategoryScore]
    reasoning: str

    @field_validator("total_score")
    @classmethod
    def validate_risk_range(cls, v: int) -> int:
        if v < -3 or v > 0:
            raise ValueError("Risk total_score must be -3 to 0")
        return v


class AIScoreResult(BaseModel):
    """Unified result returned by parse_and_validate_ai_response."""
    score: float
    breakdown: dict[str, Any]
    reasoning: str


# ---------------------------------------------------------------------------
# AI call (task 2.3)
# ---------------------------------------------------------------------------
async def call_ai_provider(prompt: str, score_type: str) -> dict:
    """Call the AI API with JSON mode and return the raw parsed JSON dict."""
    client = _get_ai_client()
    model = _get_model()

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("AI returned empty response")

    return json.loads(content)


# ---------------------------------------------------------------------------
# Parse & validate (task 2.5)
# ---------------------------------------------------------------------------
def parse_and_validate_ai_response(raw_json: dict, score_type: str) -> AIScoreResult:
    """Validate with Pydantic and extract score, breakdown, reasoning."""
    if score_type == "moat":
        parsed = MoatAIResponse(**raw_json)
    elif score_type == "risk":
        parsed = RiskAIResponse(**raw_json)
    else:
        raise ValueError(f"Invalid score_type: {score_type}")

    breakdown = {cat.name: {"score": cat.score, "reasoning": cat.reasoning} for cat in parsed.categories}

    return AIScoreResult(
        score=float(parsed.total_score),
        breakdown=breakdown,
        reasoning=parsed.reasoning,
    )


# ---------------------------------------------------------------------------
# Caching layer (tasks 3.1, 3.2, 3.3)
# ---------------------------------------------------------------------------
async def get_cached_ai_score(
    symbol: str, score_type: str, db: AsyncSession
) -> AIScoreResult | None:
    """Check Redis first, then DB AIScoreCache (90-day TTL)."""
    symbol = symbol.upper()
    key = _redis_key(symbol, score_type)

    # 1. Redis
    cached = await cache_get(key)
    if cached:
        logger.info(f"AI score cache hit (Redis): {symbol} {score_type}")
        return AIScoreResult(**cached)

    # 2. DB
    now = datetime.now(timezone.utc)
    stmt = (
        select(AIScoreCache)
        .where(
            AIScoreCache.symbol == symbol,
            AIScoreCache.score_type == score_type,
            AIScoreCache.expires_at > now,
        )
        .order_by(AIScoreCache.created_at.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row:
        logger.info(f"AI score cache hit (DB): {symbol} {score_type}")
        result = AIScoreResult(
            score=row.score_value,
            breakdown=row.breakdown or {},
            reasoning=row.breakdown.get("reasoning", "") if row.breakdown else "",
        )
        # Re-populate Redis
        await cache_set(key, result.model_dump(), ttl=AI_SCORE_REDIS_TTL)
        return result

    return None


async def save_ai_score_to_cache(
    symbol: str, score_type: str, result: AIScoreResult, db: AsyncSession
) -> None:
    """Write to both Redis (24h TTL) and DB AIScoreCache."""
    symbol = symbol.upper()
    key = _redis_key(symbol, score_type)

    # Redis
    await cache_set(key, result.model_dump(), ttl=AI_SCORE_REDIS_TTL)

    # DB
    expires_at = datetime.now(timezone.utc) + timedelta(days=AI_SCORE_DB_TTL_DAYS)
    record = AIScoreCache(
        symbol=symbol,
        score_type=score_type,
        score_value=result.score,
        breakdown={**result.breakdown, "reasoning": result.reasoning},
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()
    logger.info(f"AI score saved to cache: {symbol} {score_type}")
