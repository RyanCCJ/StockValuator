"""News and Research schemas for API responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """Represents a news article from yfinance."""

    title: str = Field(..., description="The headline of the news article")
    publisher: str = Field(..., description="The publisher/source of the news")
    link: str = Field(..., description="URL to the full article")
    published_at: datetime | None = Field(
        None, description="When the article was published"
    )
    news_type: str | None = Field(
        None, description="Type of news (e.g., 'STORY', 'VIDEO')"
    )
    thumbnail: str | None = Field(None, description="URL to thumbnail image")


class ResearchItem(BaseModel):
    """Represents a research report from yfinance."""

    title: str = Field(..., description="The headline of the research report")
    publisher: str = Field(..., description="The publisher/source of the report")
    link: str = Field(..., description="URL to the full report")
    published_at: datetime | None = Field(
        None, description="When the report was published"
    )


class NewsAndResearchResponse(BaseModel):
    """Response containing news and research for a stock."""

    symbol: str = Field(..., description="The stock symbol")
    news: list[NewsItem] = Field(
        default_factory=list, description="List of news articles"
    )
    research: list[ResearchItem] = Field(
        default_factory=list, description="List of research reports"
    )
