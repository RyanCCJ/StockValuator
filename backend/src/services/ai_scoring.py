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
