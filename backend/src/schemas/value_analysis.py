from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DataStatusEnum(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ValuationModelEnum(str, Enum):
    GROWTH = "growth"
    DIVIDEND = "dividend"
    ASSET = "asset"


class ScoreBreakdownResponse(BaseModel):
    name: str
    score: float
    max_score: float
    reason: str


class ConfidenceScoreResponse(BaseModel):
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdownResponse] = Field(default_factory=list)
    moat_score: float | None = None
    risk_score: float | None = None


class DividendScoreResponse(BaseModel):
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdownResponse] = Field(default_factory=list)


class ValueScoreResponse(BaseModel):
    total: float
    max_possible: float
    breakdown: list[ScoreBreakdownResponse] = Field(default_factory=list)


class FairValueResponse(BaseModel):
    model: ValuationModelEnum
    fair_value: float | None
    current_price: float | None
    is_undervalued: bool
    explanation: str


class ValueAnalysisResponse(BaseModel):
    symbol: str
    data_status: DataStatusEnum = DataStatusEnum.COMPLETE
    data_source: str | None = None
    confidence: ConfidenceScoreResponse
    dividend: DividendScoreResponse
    value: ValueScoreResponse
    fair_value: FairValueResponse | None = None


class AIScoreRequest(BaseModel):
    score_type: str = Field(..., pattern="^(moat|risk)$")
    force_refresh: bool = False


class AIScoreResponse(BaseModel):
    symbol: str
    score_type: str
    score: float | None = None
    breakdown: dict[str, Any] | None = None
    reasoning: str | None = None
    prompt: str | None = None
    error: str | None = None
    manual_entry_required: bool = False


class FairValueRequest(BaseModel):
    model: ValuationModelEnum = ValuationModelEnum.GROWTH
    expected_return: float = Field(default=0.04, ge=0.01, le=0.20)
    pb_threshold: float = Field(default=0.8, ge=0.1, le=2.0)
