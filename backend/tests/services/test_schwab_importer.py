"""Unit tests for SchwabImporterStrategy."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.services.importer.base import ParsedTransactionType
from src.services.importer.schwab import SchwabImporterStrategy, SCHWAB_HEADERS


class TestSchwabImporterStrategy:
    """Tests for the SchwabImporterStrategy class."""

    @pytest.fixture
    def strategy(self):
        """Create a SchwabImporterStrategy instance."""
        return SchwabImporterStrategy()

    def _make_csv(self, rows: list[dict]) -> bytes:
        """Create a Schwab-format CSV from row dictionaries."""
        import csv
        import io

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

    # ======= can_parse tests =======

    def test_can_parse_valid_schwab_headers(self, strategy):
        """Should recognize valid Schwab CSV headers."""
        headers = ["Date", "Action", "Symbol", "Description", "Quantity", "Price", "Fees & Comm", "Amount"]
        assert strategy.can_parse(headers) is True

    def test_can_parse_case_insensitive(self, strategy):
        """Should match headers case-insensitively."""
        headers = ["DATE", "ACTION", "SYMBOL", "DESCRIPTION", "QUANTITY", "PRICE", "FEES & COMM", "AMOUNT"]
        assert strategy.can_parse(headers) is True

    def test_can_parse_with_extra_headers(self, strategy):
        """Should accept files with additional columns."""
        headers = ["Date", "Action", "Symbol", "Description", "Quantity", "Price", "Fees & Comm", "Amount", "Extra"]
        assert strategy.can_parse(headers) is True

    def test_can_parse_missing_headers(self, strategy):
        """Should reject files missing required headers."""
        headers = ["Date", "Action", "Symbol"]  # Missing other required headers
        assert strategy.can_parse(headers) is False

    def test_broker_name(self, strategy):
        """Should return correct broker name."""
        assert strategy.broker_name == "Charles Schwab"

    # ======= Buy transaction tests =======

    def test_parse_buy_transaction(self, strategy):
        """Should parse a Buy transaction correctly."""
        csv_content = self._make_csv([{
            "Date": "01/15/2026",
            "Action": "Buy",
            "Symbol": "AAPL",
            "Description": "APPLE INC",
            "Quantity": "10",
            "Price": "$150.50",
            "Fees & Comm": "$0.00",
            "Amount": "-$1505.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.TRADE
        assert txn.trade_type == "buy"
        assert txn.symbol == "AAPL"
        assert txn.quantity == Decimal("10")
        assert txn.price == Decimal("150.50")
        assert txn.fees == Decimal("0")
        assert txn.date == datetime(2026, 1, 15)

    def test_parse_buy_with_fees(self, strategy):
        """Should parse a Buy transaction with fees."""
        csv_content = self._make_csv([{
            "Date": "01/15/2026",
            "Action": "Buy",
            "Symbol": "MSFT",
            "Description": "MICROSOFT CORP",
            "Quantity": "5",
            "Price": "$400.00",
            "Fees & Comm": "$4.95",
            "Amount": "-$2004.95",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.fees == Decimal("4.95")

    # ======= Sell transaction tests =======

    def test_parse_sell_transaction(self, strategy):
        """Should parse a Sell transaction correctly."""
        csv_content = self._make_csv([{
            "Date": "02/01/2026",
            "Action": "Sell",
            "Symbol": "GOOGL",
            "Description": "ALPHABET INC CL A",
            "Quantity": "3",
            "Price": "$175.25",
            "Fees & Comm": "$0.00",
            "Amount": "$525.75",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.TRADE
        assert txn.trade_type == "sell"
        assert txn.symbol == "GOOGL"
        assert txn.quantity == Decimal("3")
        assert txn.price == Decimal("175.25")

    # ======= Reinvest tests =======

    def test_parse_reinvest_shares(self, strategy):
        """Should parse Reinvest Shares (DRIP purchase) correctly."""
        csv_content = self._make_csv([{
            "Date": "01/20/2026",
            "Action": "Reinvest Shares",
            "Symbol": "VTI",
            "Description": "VANGUARD TOTAL STOCK MARKET ETF",
            "Quantity": "0.123",
            "Price": "$250.00",
            "Fees & Comm": "",
            "Amount": "-$30.75",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.TRADE
        assert txn.trade_type == "buy"
        assert txn.symbol == "VTI"
        assert txn.quantity == Decimal("0.123")
        assert txn.price == Decimal("250.00")
        assert "DRIP" in (txn.notes or "")

    def test_parse_reinvest_shares_calculates_price(self, strategy):
        """Should calculate price from amount/quantity if price not provided."""
        csv_content = self._make_csv([{
            "Date": "01/20/2026",
            "Action": "Reinvest Shares",
            "Symbol": "VTI",
            "Description": "VANGUARD TOTAL STOCK MARKET ETF",
            "Quantity": "0.5",
            "Price": "",  # No price provided
            "Fees & Comm": "",
            "Amount": "-$125.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.price == Decimal("250")  # 125.00 / 0.5

    # ======= Dividend tests =======

    def test_parse_qualified_dividend(self, strategy):
        """Should parse Qualified Dividend correctly."""
        csv_content = self._make_csv([{
            "Date": "03/15/2026",
            "Action": "Qualified Dividend",
            "Symbol": "MSFT",
            "Description": "MICROSOFT CORP",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$75.50",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "dividend"
        assert txn.symbol == "MSFT"
        assert txn.amount == Decimal("75.50")

    def test_parse_cash_dividend(self, strategy):
        """Should parse Cash Dividend correctly."""
        csv_content = self._make_csv([{
            "Date": "03/15/2026",
            "Action": "Cash Dividend",
            "Symbol": "JNJ",
            "Description": "JOHNSON & JOHNSON",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$45.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "dividend"
        assert txn.amount == Decimal("45")

    def test_parse_reinvest_dividend(self, strategy):
        """Should parse Reinvest Dividend as dividend income."""
        csv_content = self._make_csv([{
            "Date": "01/20/2026",
            "Action": "Qual Div Reinvest",
            "Symbol": "VTI",
            "Description": "VANGUARD TOTAL STOCK MARKET ETF",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$30.75",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "dividend"
        assert txn.amount == Decimal("30.75")

    def test_parse_cash_in_lieu(self, strategy):
        """Should parse Cash In Lieu as dividend."""
        csv_content = self._make_csv([{
            "Date": "04/01/2026",
            "Action": "Cash In Lieu",
            "Symbol": "AAPL",
            "Description": "APPLE INC CASH IN LIEU",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$5.23",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "dividend"
        assert "Cash in lieu" in (txn.notes or "")

    # ======= Tax tests =======

    def test_parse_nra_tax_adj(self, strategy):
        """Should parse NRA Tax Adj correctly."""
        csv_content = self._make_csv([{
            "Date": "03/15/2026",
            "Action": "NRA Tax Adj",
            "Symbol": "TSM",
            "Description": "TAIWAN SEMICONDUCTOR",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "-$7.50",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "tax"
        assert txn.symbol == "TSM"
        assert txn.amount == Decimal("7.50")  # Stored as positive

    def test_parse_foreign_tax_paid(self, strategy):
        """Should parse Foreign Tax Paid correctly."""
        csv_content = self._make_csv([{
            "Date": "02/28/2026",
            "Action": "Foreign Tax Paid",
            "Symbol": "VXUS",
            "Description": "VANGUARD INTL STOCK ETF",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "-$12.30",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "tax"
        assert txn.amount == Decimal("12.30")

    # ======= Fee tests =======

    def test_parse_adr_mgmt_fee(self, strategy):
        """Should parse ADR Mgmt Fee correctly."""
        csv_content = self._make_csv([{
            "Date": "06/15/2026",
            "Action": "ADR Mgmt Fee",
            "Symbol": "TSM",
            "Description": "TAIWAN SEMICONDUCTOR ADR FEE",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "-$2.50",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "fee"
        assert txn.amount == Decimal("2.50")

    # ======= Interest tests =======

    def test_parse_credit_interest(self, strategy):
        """Should parse Credit Interest correctly."""
        csv_content = self._make_csv([{
            "Date": "01/31/2026",
            "Action": "Credit Interest",
            "Symbol": "",
            "Description": "SCHWAB BANK INTEREST",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$15.23",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "interest"
        assert txn.amount == Decimal("15.23")
        assert txn.symbol is None

    # ======= Deposit/Withdrawal tests =======

    def test_parse_wire_received(self, strategy):
        """Should parse Wire Received as deposit."""
        csv_content = self._make_csv([{
            "Date": "01/05/2026",
            "Action": "Wire Received",
            "Symbol": "",
            "Description": "WIRE TRANSFER",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$10000.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "deposit"
        assert txn.amount == Decimal("10000")

    def test_parse_ach_received(self, strategy):
        """Should parse ACH Received as deposit."""
        csv_content = self._make_csv([{
            "Date": "01/10/2026",
            "Action": "ACH Received",
            "Symbol": "",
            "Description": "ACH TRANSFER",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$5000.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.cash_type == "deposit"

    def test_parse_ach_sent(self, strategy):
        """Should parse ACH Sent as withdrawal."""
        csv_content = self._make_csv([{
            "Date": "02/15/2026",
            "Action": "ACH Sent",
            "Symbol": "",
            "Description": "ACH WITHDRAWAL",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "-$3000.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 1
        txn = transactions[0]
        assert txn.type == ParsedTransactionType.CASH
        assert txn.cash_type == "withdraw"
        assert txn.amount == Decimal("3000")

    # ======= Skip actions tests =======

    def test_skip_stock_split(self, strategy):
        """Should skip stock split with warning."""
        csv_content = self._make_csv([{
            "Date": "03/01/2026",
            "Action": "Stock Split",
            "Symbol": "NVDA",
            "Description": "NVIDIA CORP 4:1 SPLIT",
            "Quantity": "30",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 0
        assert len(warnings) == 1
        assert "Stock Split" in warnings[0]
        assert "manual adjustment" in warnings[0]

    def test_skip_spinoff(self, strategy):
        """Should skip spin-off with warning."""
        csv_content = self._make_csv([{
            "Date": "04/01/2026",
            "Action": "Spin-off",
            "Symbol": "PARA",
            "Description": "PARAMOUNT GLOBAL",
            "Quantity": "10",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 0
        assert len(warnings) == 1

    def test_skip_reverse_stock_split(self, strategy):
        """Should skip reverse stock split with warning."""
        csv_content = self._make_csv([{
            "Date": "05/01/2026",
            "Action": "Reverse Stock Split",
            "Symbol": "XYZ",
            "Description": "XYZ CORP 1:10 REVERSE SPLIT",
            "Quantity": "-9",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 0
        assert len(warnings) == 1

    # ======= Unknown action tests =======

    def test_unknown_action_skipped_with_warning(self, strategy):
        """Should skip unknown actions with warning."""
        csv_content = self._make_csv([{
            "Date": "01/01/2026",
            "Action": "Some Unknown Action",
            "Symbol": "ABC",
            "Description": "UNKNOWN",
            "Quantity": "",
            "Price": "",
            "Fees & Comm": "",
            "Amount": "$100.00",
        }])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 0
        assert len(warnings) == 1
        assert "Unknown action" in warnings[0]

    # ======= Date parsing tests =======

    def test_parse_date_mm_dd_yyyy(self, strategy):
        """Should parse MM/DD/YYYY format."""
        csv_content = self._make_csv([{
            "Date": "12/31/2025",
            "Action": "Qualified Dividend",
            "Symbol": "AAPL",
            "Description": "APPLE INC",
            "Amount": "$10.00",
        }])

        transactions, _ = strategy.parse(csv_content)
        assert transactions[0].date == datetime(2025, 12, 31)

    def test_parse_date_with_as_of(self, strategy):
        """Should handle 'as of' dates correctly."""
        csv_content = self._make_csv([{
            "Date": "02/02/2026 as of 01/31/2026",
            "Action": "Qualified Dividend",
            "Symbol": "VTI",
            "Description": "VANGUARD ETF",
            "Amount": "$50.00",
        }])

        transactions, _ = strategy.parse(csv_content)
        # Should use the first date (settlement date)
        assert transactions[0].date == datetime(2026, 2, 2)

    # ======= Amount parsing tests =======

    def test_parse_amount_with_commas(self, strategy):
        """Should parse amounts with comma thousands separator."""
        csv_content = self._make_csv([{
            "Date": "01/01/2026",
            "Action": "Wire Received",
            "Symbol": "",
            "Description": "WIRE",
            "Amount": "$1,234,567.89",
        }])

        transactions, _ = strategy.parse(csv_content)
        assert transactions[0].amount == Decimal("1234567.89")

    def test_parse_negative_amount(self, strategy):
        """Should parse negative amounts correctly."""
        csv_content = self._make_csv([{
            "Date": "01/01/2026",
            "Action": "NRA Tax Adj",
            "Symbol": "TSM",
            "Description": "TAX",
            "Amount": "-$15.00",
        }])

        transactions, _ = strategy.parse(csv_content)
        assert transactions[0].amount == Decimal("15")  # Stored as positive

    # ======= Multiple transactions tests =======

    def test_parse_multiple_transactions(self, strategy):
        """Should parse multiple transactions correctly."""
        csv_content = self._make_csv([
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
                "Action": "Qualified Dividend",
                "Symbol": "MSFT",
                "Description": "MICROSOFT",
                "Amount": "$25.00",
            },
            {
                "Date": "01/17/2026",
                "Action": "Sell",
                "Symbol": "GOOGL",
                "Description": "ALPHABET",
                "Quantity": "5",
                "Price": "$180.00",
                "Amount": "$900.00",
            },
        ])

        transactions, warnings = strategy.parse(csv_content)

        assert len(transactions) == 3
        assert transactions[0].trade_type == "buy"
        assert transactions[1].cash_type == "dividend"
        assert transactions[2].trade_type == "sell"

    # ======= Empty/zero amount handling =======

    def test_skip_zero_amount_dividend(self, strategy):
        """Should skip dividends with zero amount."""
        csv_content = self._make_csv([{
            "Date": "01/01/2026",
            "Action": "Qualified Dividend",
            "Symbol": "XYZ",
            "Description": "XYZ CORP",
            "Amount": "$0.00",
        }])

        transactions, _ = strategy.parse(csv_content)
        assert len(transactions) == 0

    def test_skip_empty_amount_dividend(self, strategy):
        """Should skip dividends with empty amount."""
        csv_content = self._make_csv([{
            "Date": "01/01/2026",
            "Action": "Qualified Dividend",
            "Symbol": "XYZ",
            "Description": "XYZ CORP",
            "Amount": "",
        }])

        transactions, _ = strategy.parse(csv_content)
        assert len(transactions) == 0

    # ======= BOM handling =======

    def test_parse_with_bom(self, strategy):
        """Should handle UTF-8 BOM correctly."""
        csv_content = b"\xef\xbb\xbfDate,Action,Symbol,Description,Quantity,Price,Fees & Comm,Amount\n"
        csv_content += b"01/15/2026,Buy,AAPL,APPLE INC,10,$150.00,$0.00,-$1500.00\n"

        transactions, _ = strategy.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].symbol == "AAPL"

    # ======= Empty action row =======

    def test_skip_empty_action_row(self, strategy):
        """Should skip rows with empty action."""
        csv_content = self._make_csv([
            {
                "Date": "01/15/2026",
                "Action": "",  # Empty action
                "Symbol": "AAPL",
                "Description": "APPLE INC",
            },
            {
                "Date": "01/16/2026",
                "Action": "Buy",
                "Symbol": "MSFT",
                "Description": "MICROSOFT",
                "Quantity": "5",
                "Price": "$400.00",
                "Amount": "-$2000.00",
            },
        ])

        transactions, _ = strategy.parse(csv_content)
        assert len(transactions) == 1
        assert transactions[0].symbol == "MSFT"
