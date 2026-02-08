"""Schemas for transaction import API."""

from pydantic import BaseModel


class BrokerInfo(BaseModel):
    """Information about a supported broker."""

    name: str
    description: str


class ImportResultResponse(BaseModel):
    """Response schema for import operation results."""

    trades_created: int
    cash_transactions_created: int
    duplicates_skipped: int
    rows_skipped: int
    warnings: list[str]
    errors: list[dict]

    @property
    def total_imported(self) -> int:
        """Total number of records imported."""
        return self.trades_created + self.cash_transactions_created


class ImportSummaryResponse(BaseModel):
    """Simplified summary for quick status check."""

    success: bool
    message: str
    trades_created: int
    cash_transactions_created: int
    duplicates_skipped: int
    warning_count: int
    error_count: int
