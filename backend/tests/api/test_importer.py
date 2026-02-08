"""Integration tests for the importer upload API endpoint."""

import io
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.user import User


class TestImporterUploadEndpoint:
    """Integration tests for POST /importer/upload endpoint."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.email = "test@example.com"
        user.is_active = True
        return user

    def _create_schwab_csv(self, rows: list[dict]) -> bytes:
        """Create a Schwab-format CSV file content."""
        import csv

        headers = ["Date", "Action", "Symbol", "Description", "Quantity", "Price", "Fees & Comm", "Amount"]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in rows:
            values = [
                row.get("Date", ""),
                row.get("Action", ""),
                row.get("Symbol", ""),
                row.get("Description", ""),
                row.get("Quantity", ""),
                row.get("Price", ""),
                row.get("Fees & Comm", ""),
                row.get("Amount", ""),
            ]
            writer.writerow(values)
        return output.getvalue().encode("utf-8")

    @pytest.mark.asyncio
    async def test_upload_requires_authentication(self):
        """Should return 401/403 when no authentication token is provided."""
        csv_content = self._create_schwab_csv([{
            "Date": "01/15/2026",
            "Action": "Buy",
            "Symbol": "AAPL",
            "Description": "APPLE INC",
            "Quantity": "10",
            "Price": "$150.00",
            "Amount": "-$1500.00",
        }])

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/importer/upload",
                files={"file": ("transactions.csv", csv_content, "text/csv")},
            )

        # HTTPBearer returns 403 when no credentials, but could also be 401
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_upload_rejects_non_csv_file(self, mock_user):
        """Should return 400 when file is not a CSV."""
        from src.api.deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/importer/upload",
                    files={"file": ("transactions.txt", b"not a csv", "text/plain")},
                    headers={"Authorization": "Bearer test-token"},
                )

            assert response.status_code == 400
            assert "CSV" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_rejects_empty_file(self, mock_user):
        """Should return 400 when file is empty."""
        from src.api.deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(
                    "/importer/upload",
                    files={"file": ("transactions.csv", b"", "text/csv")},
                    headers={"Authorization": "Bearer test-token"},
                )

            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_processes_valid_csv(self, mock_user):
        """Should successfully process a valid Schwab CSV file."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        csv_content = self._create_schwab_csv([
            {
                "Date": "01/15/2026",
                "Action": "Buy",
                "Symbol": "AAPL",
                "Description": "APPLE INC",
                "Quantity": "10",
                "Price": "$150.00",
                "Fees & Comm": "$0.00",
                "Amount": "-$1500.00",
            },
            {
                "Date": "01/16/2026",
                "Action": "Qualified Dividend",
                "Symbol": "MSFT",
                "Description": "MICROSOFT CORP",
                "Amount": "$25.00",
            },
        ])

        # Mock the import result
        mock_result = ImportResult(
            trades_created=1,
            cash_transactions_created=1,
            duplicates_skipped=0,
            rows_skipped=0,
            warnings=[],
            errors=[],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["trades_created"] == 1
            assert data["cash_transactions_created"] == 1
            assert data["duplicates_skipped"] == 0
            assert data["warnings"] == []
            assert data["errors"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_returns_warnings_for_skipped_rows(self, mock_user):
        """Should return warnings for rows that were skipped."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        csv_content = self._create_schwab_csv([
            {
                "Date": "01/15/2026",
                "Action": "Buy",
                "Symbol": "AAPL",
                "Description": "APPLE INC",
                "Quantity": "10",
                "Price": "$150.00",
                "Amount": "-$1500.00",
            },
            {
                "Date": "01/16/2026",
                "Action": "Stock Split",
                "Symbol": "NVDA",
                "Description": "NVIDIA 4:1 SPLIT",
            },
        ])

        mock_result = ImportResult(
            trades_created=1,
            cash_transactions_created=0,
            duplicates_skipped=0,
            rows_skipped=1,
            warnings=["Row 3: Skipped 'Stock Split' - requires manual adjustment"],
            errors=[],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["trades_created"] == 1
            assert len(data["warnings"]) == 1
            assert "Stock Split" in data["warnings"][0]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_reports_duplicates(self, mock_user):
        """Should report duplicate transactions that were skipped."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        csv_content = self._create_schwab_csv([{
            "Date": "01/15/2026",
            "Action": "Buy",
            "Symbol": "AAPL",
            "Description": "APPLE INC",
            "Quantity": "10",
            "Price": "$150.00",
            "Amount": "-$1500.00",
        }])

        # Simulate that this transaction already exists
        mock_result = ImportResult(
            trades_created=0,
            cash_transactions_created=0,
            duplicates_skipped=1,
            rows_skipped=0,
            warnings=[],
            errors=[],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["duplicates_skipped"] == 1
            assert data["trades_created"] == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_handles_unsupported_format(self, mock_user):
        """Should return error for unsupported file format."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        # CSV with wrong headers (not Schwab format)
        csv_content = b"wrong,headers,here\n1,2,3"

        mock_result = ImportResult(
            trades_created=0,
            cash_transactions_created=0,
            duplicates_skipped=0,
            rows_skipped=0,
            warnings=[],
            errors=[{"error": "Unsupported file format. Could not identify broker from CSV headers."}],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert len(data["errors"]) == 1
            assert "Unsupported" in data["errors"][0]["error"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_returns_correct_response_schema(self, mock_user):
        """Should return response matching ImportResultResponse schema."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        csv_content = self._create_schwab_csv([{
            "Date": "01/15/2026",
            "Action": "Buy",
            "Symbol": "AAPL",
            "Description": "APPLE INC",
            "Quantity": "10",
            "Price": "$150.00",
            "Amount": "-$1500.00",
        }])

        mock_result = ImportResult(
            trades_created=1,
            cash_transactions_created=0,
            duplicates_skipped=0,
            rows_skipped=0,
            warnings=[],
            errors=[],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()

            # Verify all expected fields are present
            assert "trades_created" in data
            assert "cash_transactions_created" in data
            assert "duplicates_skipped" in data
            assert "rows_skipped" in data
            assert "warnings" in data
            assert "errors" in data

            # Verify types
            assert isinstance(data["trades_created"], int)
            assert isinstance(data["cash_transactions_created"], int)
            assert isinstance(data["duplicates_skipped"], int)
            assert isinstance(data["rows_skipped"], int)
            assert isinstance(data["warnings"], list)
            assert isinstance(data["errors"], list)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_upload_multiple_transaction_types(self, mock_user):
        """Should process multiple transaction types in one file."""
        from src.api.deps import get_current_user
        from src.services.importer.base import ImportResult

        csv_content = self._create_schwab_csv([
            # Buy trade
            {
                "Date": "01/15/2026",
                "Action": "Buy",
                "Symbol": "AAPL",
                "Description": "APPLE INC",
                "Quantity": "10",
                "Price": "$150.00",
                "Amount": "-$1500.00",
            },
            # Sell trade
            {
                "Date": "01/16/2026",
                "Action": "Sell",
                "Symbol": "GOOGL",
                "Description": "ALPHABET",
                "Quantity": "5",
                "Price": "$175.00",
                "Amount": "$875.00",
            },
            # Dividend
            {
                "Date": "01/17/2026",
                "Action": "Qualified Dividend",
                "Symbol": "MSFT",
                "Description": "MICROSOFT",
                "Amount": "$25.00",
            },
            # Tax
            {
                "Date": "01/17/2026",
                "Action": "NRA Tax Adj",
                "Symbol": "TSM",
                "Description": "TAIWAN SEMI",
                "Amount": "-$7.50",
            },
            # Deposit
            {
                "Date": "01/01/2026",
                "Action": "Wire Received",
                "Description": "WIRE",
                "Amount": "$10000.00",
            },
        ])

        mock_result = ImportResult(
            trades_created=2,  # Buy + Sell
            cash_transactions_created=3,  # Dividend + Tax + Deposit
            duplicates_skipped=0,
            rows_skipped=0,
            warnings=[],
            errors=[],
        )

        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch(
                "src.api.routes.importer.ImporterService.import_file",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    response = await client.post(
                        "/importer/upload",
                        files={"file": ("transactions.csv", csv_content, "text/csv")},
                        headers={"Authorization": "Bearer test-token"},
                    )

            assert response.status_code == 200
            data = response.json()
            assert data["trades_created"] == 2
            assert data["cash_transactions_created"] == 3
        finally:
            app.dependency_overrides.clear()
