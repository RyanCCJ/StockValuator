"""Generic CSV importer service using YAML-based broker configurations."""

import csv
import io
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import UUID

import yaml
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.cash import CashTransaction
from src.models.trade import Trade
from src.schemas.cash import CashTransactionCreate
from src.schemas.trade import TradeCreate
from src.services.cash_service import create_cash_transaction
from src.services.trade_service import create_trade

logger = logging.getLogger(__name__)


@dataclass
class ImportResult:
    """Result of an import operation."""

    trades_created: int = 0
    cash_transactions_created: int = 0
    duplicates_skipped: int = 0
    rows_skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


@dataclass
class BrokerConfig:
    """Configuration for a broker's CSV format."""

    name: str
    description: str
    columns: dict[str, str]  # field -> column_name mapping
    date_formats: list[str]
    date_strip_suffix: str | None = None


@dataclass
class ParsedRow:
    """A parsed CSV row."""

    row_num: int
    date: datetime
    symbol: str | None
    action: str
    price: Decimal | None
    quantity: Decimal | None
    fees: Decimal | None
    amount: Decimal | None
    notes: str | None

    @property
    def is_trade(self) -> bool:
        """Check if this row should be a trade (has both price and quantity)."""
        return self.price is not None and self.quantity is not None

    @property
    def is_cash(self) -> bool:
        """Check if this row should be a cash transaction (has amount but not both price/quantity)."""
        return self.amount is not None and not self.is_trade

    @property
    def is_incomplete(self) -> bool:
        """Check if row has partial price/quantity (should be skipped with warning)."""
        has_price = self.price is not None
        has_quantity = self.quantity is not None
        return has_price != has_quantity  # XOR - one but not both


class ImporterService:
    """Service for importing brokerage transaction files."""

    def __init__(self):
        self._brokers: list[BrokerConfig] = []
        self._load_broker_configs()

    def _load_broker_configs(self) -> None:
        """Load broker configurations from YAML file."""
        yaml_path = Path(__file__).parent / "brokers.yaml"
        if not yaml_path.exists():
            logger.warning(f"Broker config file not found: {yaml_path}")
            return

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        for broker_data in data.get("brokers", []):
            config = BrokerConfig(
                name=broker_data["name"],
                description=broker_data.get("description", ""),
                columns=broker_data["columns"],
                date_formats=broker_data.get("date_formats", ["%Y-%m-%d"]),
                date_strip_suffix=broker_data.get("date_strip_suffix"),
            )
            self._brokers.append(config)

        logger.info(f"Loaded {len(self._brokers)} broker configurations")

    def get_available_brokers(self) -> list[dict]:
        """Get list of available broker configurations."""
        return [{"name": b.name, "description": b.description} for b in self._brokers]

    async def import_file(
        self,
        db: AsyncSession,
        user_id: UUID,
        content: bytes,
        filename: str,
        broker_name: str | None = None,
    ) -> ImportResult:
        """Import transactions from a brokerage CSV or Excel file.

        Args:
            db: Database session.
            user_id: ID of the user importing the file.
            content: Raw file content bytes.
            filename: Original filename.
            broker_name: Optional broker name. If not provided, will auto-detect.

        Returns:
            ImportResult with counts and any warnings/errors.
        """
        result = ImportResult()

        # Parse file based on extension
        try:
            rows, headers = self._parse_file(content, filename)
        except Exception as e:
            result.errors.append({"error": f"Failed to parse file: {e}"})
            return result

        if not headers:
            result.errors.append({"error": "No headers found in file"})
            return result

        # Find matching broker config
        broker = self._find_broker(headers, broker_name)
        if broker is None:
            result.errors.append({
                "error": "Could not identify broker format. Please ensure file has correct headers."
            })
            return result

        logger.info(f"Using broker config: {broker.name}")

        # Parse all rows
        parsed_rows: list[ParsedRow] = []
        for row_num, row in enumerate(rows, start=2):
            try:
                parsed = self._parse_row(row, row_num, broker, result.warnings)
                if parsed:
                    parsed_rows.append(parsed)
            except Exception as e:
                result.warnings.append(f"Row {row_num}: Error parsing - {e}")

        # Count occurrences for duplicate detection
        trade_file_counts: Counter[tuple] = Counter()
        cash_file_counts: Counter[tuple] = Counter()

        for row in parsed_rows:
            if row.is_trade:
                key = self._get_trade_key(row)
                trade_file_counts[key] += 1
            elif row.is_cash:
                key = self._get_cash_key(row)
                cash_file_counts[key] += 1

        # Pre-fetch existing counts from DB
        trade_db_counts = await self._get_trade_db_counts(db, user_id, trade_file_counts.keys())
        cash_db_counts = await self._get_cash_db_counts(db, user_id, cash_file_counts.keys())

        # Track created counts
        trade_created: Counter[tuple] = Counter()
        cash_created: Counter[tuple] = Counter()

        # Process each row
        for row in parsed_rows:
            try:
                if row.is_incomplete:
                    # Show full row content for clarity
                    result.warnings.append(
                        f"Row {row.row_num} skipped (incomplete): "
                        f"date={row.date.strftime('%Y-%m-%d')}, symbol={row.symbol}, action='{row.action}', "
                        f"price={row.price}, quantity={row.quantity}, amount={row.amount}"
                    )
                    result.rows_skipped += 1
                    continue

                if row.is_trade:
                    key = self._get_trade_key(row)
                    need_to_create = (
                        trade_file_counts[key]
                        - trade_db_counts.get(key, 0)
                        - trade_created[key]
                    )

                    if need_to_create <= 0:
                        result.duplicates_skipped += 1
                        continue

                    await self._create_trade(db, user_id, row)
                    trade_created[key] += 1
                    result.trades_created += 1

                elif row.is_cash:
                    key = self._get_cash_key(row)
                    need_to_create = (
                        cash_file_counts[key]
                        - cash_db_counts.get(key, 0)
                        - cash_created[key]
                    )

                    if need_to_create <= 0:
                        result.duplicates_skipped += 1
                        continue

                    await self._create_cash(db, user_id, row)
                    cash_created[key] += 1
                    result.cash_transactions_created += 1

                else:
                    # No price, quantity, or amount - show full row content
                    result.warnings.append(
                        f"Row {row.row_num} skipped (no data): "
                        f"date={row.date.strftime('%Y-%m-%d')}, symbol={row.symbol}, action='{row.action}', "
                        f"price={row.price}, quantity={row.quantity}, amount={row.amount}"
                    )
                    result.rows_skipped += 1

            except Exception as e:
                result.errors.append({
                    "row": row.row_num,
                    "symbol": row.symbol,
                    "action": row.action,
                    "error": str(e),
                })

        return result

    def _parse_file(
        self, content: bytes, filename: str
    ) -> tuple[list[dict[str, str]], list[str]]:
        """Parse file content based on file extension.

        Returns:
            Tuple of (rows as list of dicts, headers as list of strings)
        """
        filename_lower = filename.lower()

        if filename_lower.endswith((".xlsx", ".xls")):
            return self._parse_excel(content)
        else:
            # Default to CSV
            return self._parse_csv(content)

    def _parse_csv(self, content: bytes) -> tuple[list[dict[str, str]], list[str]]:
        """Parse CSV content."""
        text = content.decode("utf-8-sig")  # Handle BOM
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        rows = list(reader)
        return rows, headers

    def _parse_excel(self, content: bytes) -> tuple[list[dict[str, str]], list[str]]:
        """Parse Excel content."""
        import openpyxl

        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.active

        if sheet is None:
            return [], []

        rows_iter = sheet.iter_rows(values_only=True)

        # First row is headers
        header_row = next(rows_iter, None)
        if header_row is None:
            return [], []

        headers = [str(h) if h is not None else "" for h in header_row]

        # Parse data rows
        rows = []
        for row in rows_iter:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    # Convert value to string, handling None and numbers
                    if value is None:
                        row_dict[headers[i]] = ""
                    else:
                        row_dict[headers[i]] = str(value)
            rows.append(row_dict)

        workbook.close()
        return rows, headers

    def _find_broker(
        self, headers: list[str], broker_name: str | None = None
    ) -> BrokerConfig | None:
        """Find matching broker configuration."""
        normalized_headers = {h.lower().strip() for h in headers}

        # If broker name specified, find it
        if broker_name:
            for broker in self._brokers:
                if broker.name.lower() == broker_name.lower():
                    return broker
            return None

        # Auto-detect by matching headers
        for broker in self._brokers:
            if broker.name == "default":
                continue  # Skip default for auto-detection

            required_columns = {v.lower() for v in broker.columns.values() if v}
            if required_columns.issubset(normalized_headers):
                return broker

        # Fall back to default
        for broker in self._brokers:
            if broker.name == "default":
                return broker

        return self._brokers[0] if self._brokers else None

    def _parse_row(
        self,
        row: dict[str, str],
        row_num: int,
        broker: BrokerConfig,
        warnings: list[str],
    ) -> ParsedRow | None:
        """Parse a single CSV row."""
        # Normalize row keys
        row = {k.lower().strip(): v.strip() if v else "" for k, v in row.items()}

        def get_col(field: str) -> str:
            """Get column value by field name."""
            col_name = broker.columns.get(field, "").lower().strip()
            return row.get(col_name, "")

        # Parse action (required)
        action = get_col("action")
        if not action:
            return None

        # Parse date (required)
        date_str = get_col("date")
        if not date_str:
            warnings.append(f"Row {row_num}: Missing date - skipped")
            return None

        date = self._parse_date(date_str, broker)
        if date is None:
            warnings.append(f"Row {row_num}: Invalid date '{date_str}' - skipped")
            return None

        # Parse optional fields
        symbol = get_col("symbol").upper() or None
        price = self._parse_decimal(get_col("price"))
        quantity = self._parse_decimal(get_col("quantity"))
        fees = self._parse_decimal(get_col("fees"))
        amount = self._parse_decimal(get_col("amount"))
        notes = get_col("notes") or None

        return ParsedRow(
            row_num=row_num,
            date=date,
            symbol=symbol,
            action=action,
            price=price,
            quantity=quantity,
            fees=fees,
            amount=amount,
            notes=notes,
        )

    def _parse_date(self, date_str: str, broker: BrokerConfig) -> datetime | None:
        """Parse date string using broker's date formats."""
        date_str = date_str.strip()

        # Strip suffix if configured (e.g., " as of ")
        if broker.date_strip_suffix and broker.date_strip_suffix in date_str:
            date_str = date_str.split(broker.date_strip_suffix)[0].strip()

        for fmt in broker.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_decimal(self, value: str) -> Decimal | None:
        """Parse a decimal value from string."""
        if not value or not value.strip():
            return None

        value = value.strip()

        # Handle negative amounts
        is_negative = value.startswith("-") or value.startswith("(")
        value = value.replace("-", "").replace("(", "").replace(")", "")

        # Remove currency symbols and commas
        value = re.sub(r"[,$€£¥]", "", value).strip()

        if not value:
            return None

        try:
            result = Decimal(value)
            return -result if is_negative else result
        except InvalidOperation:
            return None

    def _get_trade_key(self, row: ParsedRow) -> tuple:
        """Get a key for trade duplicate detection."""
        # Use absolute values for quantity and price to handle brokers that use negative values
        quantity = abs(row.quantity) if row.quantity else None
        price = abs(row.price) if row.price else None
        return (row.date, row.symbol, row.action, quantity, price)

    def _get_cash_key(self, row: ParsedRow) -> tuple:
        """Get a key for cash duplicate detection."""
        return (row.date, row.action, row.amount, row.symbol)

    async def _get_trade_db_counts(
        self, db: AsyncSession, user_id: UUID, keys: list[tuple]
    ) -> dict[tuple, int]:
        """Get counts of existing trades matching the given keys."""
        counts = {}
        for key in keys:
            date, symbol, action, quantity, price = key
            if symbol is None:
                counts[key] = 0
                continue
            
            query = select(func.count(Trade.id)).where(
                and_(
                    Trade.user_id == user_id,
                    Trade.date == date,
                    Trade.symbol == symbol,
                    Trade.action == action,
                    Trade.quantity == quantity,
                    Trade.price == price,
                )
            )
            result = await db.execute(query)
            counts[key] = result.scalar_one()

        return counts

    async def _get_cash_db_counts(
        self, db: AsyncSession, user_id: UUID, keys: list[tuple]
    ) -> dict[tuple, int]:
        """Get counts of existing cash transactions matching the given keys."""
        counts = {}
        for key in keys:
            date, action, amount, symbol = key
            if amount is None:
                counts[key] = 0
                continue

            conditions = [
                CashTransaction.user_id == user_id,
                CashTransaction.date == date,
                CashTransaction.action == action,
                CashTransaction.amount == amount,
            ]

            if symbol:
                conditions.append(CashTransaction.notes.contains(symbol))

            query = select(func.count(CashTransaction.id)).where(and_(*conditions))
            result = await db.execute(query)
            counts[key] = result.scalar_one()

        return counts

    async def _create_trade(
        self, db: AsyncSession, user_id: UUID, row: ParsedRow
    ) -> Trade:
        """Create a trade from a parsed row."""
        # Use absolute value for quantity (some brokers use negative for sells)
        quantity = abs(row.quantity) if row.quantity else Decimal("0")
        # Use absolute value for price (should always be positive)
        price = abs(row.price) if row.price else Decimal("0")

        # Keep original amount with sign for display purposes
        # If no amount provided, infer from quantity sign
        amount = row.amount
        if amount is None and row.quantity is not None:
            # Use quantity sign to determine amount sign
            sign = -1 if row.quantity < 0 else 1
            amount = sign * (price * quantity)

        trade_data = TradeCreate(
            symbol=row.symbol or "UNKNOWN",
            date=row.date,
            action=row.action,
            price=price,
            quantity=quantity,
            amount=amount,
            fees=abs(row.fees) if row.fees else Decimal("0"),
            currency="USD",
            notes=row.notes,
        )
        return await create_trade(db, user_id, trade_data)

    async def _create_cash(
        self, db: AsyncSession, user_id: UUID, row: ParsedRow
    ) -> CashTransaction:
        """Create a cash transaction from a parsed row."""
        # Build notes with symbol if present
        notes_parts = []
        if row.symbol:
            notes_parts.append(row.symbol)
        if row.notes:
            notes_parts.append(row.notes)
        notes = " | ".join(notes_parts) if notes_parts else None

        cash_data = CashTransactionCreate(
            date=row.date,
            action=row.action,
            amount=row.amount or Decimal("0"),
            currency="USD",
            notes=notes,
        )
        return await create_cash_transaction(db, user_id, cash_data)
