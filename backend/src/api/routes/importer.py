"""API routes for unified transaction importer."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.api.deps import CurrentUser, DbSession
from src.schemas.importer import BrokerInfo, ImportResultResponse
from src.services.importer.service import ImporterService


router = APIRouter(prefix="/importer", tags=["importer"])


@router.get("/brokers", response_model=list[BrokerInfo])
async def list_brokers() -> list[BrokerInfo]:
    """Get list of supported brokers for CSV import."""
    service = ImporterService()
    brokers = service.get_available_brokers()
    return [BrokerInfo(**b) for b in brokers]


@router.post("/upload", response_model=ImportResultResponse)
async def upload_transactions(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
    broker: str | None = Form(None),
) -> ImportResultResponse:
    """Upload and import brokerage transaction file.

    Args:
        file: CSV file to import
        broker: Optional broker name. If not provided, will auto-detect.

    The importer will:
    - Parse the CSV file to extract trades and cash transactions
    - Detect and skip duplicate transactions
    - Create Trade records for rows with price AND quantity
    - Create CashTransaction records for rows with only amount
    - Skip rows with incomplete data (price XOR quantity)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file extension
    filename = file.filename.lower()
    if not filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a CSV file."
        )

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Process import
    service = ImporterService()
    result = await service.import_file(
        db, current_user.id, content, file.filename, broker_name=broker
    )

    # Commit if there were no critical errors
    if result.trades_created > 0 or result.cash_transactions_created > 0:
        await db.commit()

    return ImportResultResponse(
        trades_created=result.trades_created,
        cash_transactions_created=result.cash_transactions_created,
        duplicates_skipped=result.duplicates_skipped,
        rows_skipped=result.rows_skipped,
        warnings=result.warnings,
        errors=result.errors,
    )
