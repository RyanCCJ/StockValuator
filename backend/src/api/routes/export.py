"""Export API routes for trades and cash transactions."""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from src.api.deps import CurrentUser, DbSession
from src.services.trade_service import get_trades_by_user
from src.services.cash_service import get_cash_transactions_by_user

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/trades")
async def export_trades(
    current_user: CurrentUser,
    db: DbSession,
    format: str = Query("csv", regex="^(csv|xlsx)$"),
):
    """Export all trades for the current user as CSV or XLSX."""
    trades, _ = await get_trades_by_user(db, current_user.id, skip=0, limit=10000)
    
    headers = ["date", "symbol", "type", "price", "quantity", "fees", "currency", "notes"]
    rows = []
    for t in trades:
        rows.append([
            t.date.strftime("%Y-%m-%d %H:%M:%S"),
            t.symbol,
            t.type.value,
            str(t.price),
            str(t.quantity),
            str(t.fees),
            t.currency,
            t.notes or "",
        ])
    
    if format == "csv":
        return _create_csv_response(headers, rows, "trades.csv")
    else:
        return _create_xlsx_response(headers, rows, "trades.xlsx")


@router.get("/cash")
async def export_cash(
    current_user: CurrentUser,
    db: DbSession,
    format: str = Query("csv", regex="^(csv|xlsx)$"),
):
    """Export all cash transactions for the current user as CSV or XLSX."""
    transactions, _ = await get_cash_transactions_by_user(db, current_user.id, skip=0, limit=10000)
    
    headers = ["date", "type", "amount", "currency", "notes"]
    rows = []
    for t in transactions:
        rows.append([
            t.date.strftime("%Y-%m-%d %H:%M:%S"),
            t.type.value,
            str(t.amount),
            t.currency,
            t.notes or "",
        ])
    
    if format == "csv":
        return _create_csv_response(headers, rows, "cash_transactions.csv")
    else:
        return _create_xlsx_response(headers, rows, "cash_transactions.xlsx")


def _create_csv_response(headers: list[str], rows: list[list], filename: str):
    """Create a CSV streaming response."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _create_xlsx_response(headers: list[str], rows: list[list], filename: str):
    """Create an XLSX streaming response."""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
