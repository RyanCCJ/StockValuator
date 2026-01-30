import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import cache_get, cache_set
from src.core.config import get_settings
from src.models.financial_data import AIScoreCache


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

Please return the analysis in this format:

### Moat Analysis
1. **Intangible Assets**: [0 or 1] - [Brief critical reasoning]
2. **Cost Advantage**: [0 or 1] - [Brief critical reasoning]
3. **Network Effect**: [0 or 1] - [Brief critical reasoning]
4. **Switching Costs**: [0 or 1] - [Brief critical reasoning]
5. **Niche Market**: [0 or 1] - [Brief critical reasoning]

**Total Moat Score: X/5**"""

RISK_PROMPT_TEMPLATE = """Analyze environmental risks for {company_name} ({symbol}).
BE CRITICAL. Identify potential downsides. If a risk exists, apply the penalty.

Company Info:
- Sector: {sector}
- Industry: {industry}

Score each risk category (-1 or 0 points each, max -3 total):
1. Authority/Policy Risk: Is there significant exposure to government regulation, antitrust, price controls, or trade wars? (e.g., Utilities, Healthcare, Big Tech antitrust). (0 if safe, -1 if risky).
2. Science/Tech Risk: Is the business vulnerable to rapid disruption or obsolescence? (e.g., Legacy tech, single-product biotech, fashion trends). (0 if safe, -1 if risky).
3. Key People Risk: Is the company heavily dependent on a specific leader (e.g., Elon Musk) or specialized labor that is hard to replace? (0 if safe, -1 if risky).

Please return the analysis in this format:

### Risk Analysis
1. **Authority/Policy Risk**: [0 or -1] - [Brief reasoning]
2. **Science/Tech Risk**: [0 or -1] - [Brief reasoning]
3. **Key People Risk**: [0 or -1] - [Brief reasoning]

**Total Risk Score: X/0** (Negative score indicates higher risk)"""


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
