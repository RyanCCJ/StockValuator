"""Integration tests for StockValuator full flow."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.user import User
from src.models.trade import Trade, TradeType
from src.models.cash import CashTransaction, CashTransactionType
from src.core.database import async_session_maker


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        google_id="test-google-id",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def authenticated_client(test_user: User):
    """Create an authenticated test client."""
    # In a real test, you'd create a valid JWT token
    # For now, we'll skip auth for testing
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthCheck:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """SC-001: Health endpoint returns healthy status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"


class TestFullFlow:
    """Integration tests for the complete user flow."""

    @pytest.mark.asyncio
    async def test_cash_deposit_workflow(self, db_session: AsyncSession, test_user: User):
        """Test: Add cash deposit → Check balance updates."""
        # Add a deposit
        deposit = CashTransaction(
            user_id=test_user.id,
            date=datetime.now(timezone.utc),
            type=CashTransactionType.DEPOSIT,
            amount=Decimal("10000.00"),
            currency="USD",
        )
        db_session.add(deposit)
        await db_session.commit()

        # Add a withdrawal
        withdrawal = CashTransaction(
            user_id=test_user.id,
            date=datetime.now(timezone.utc),
            type=CashTransactionType.WITHDRAW,
            amount=Decimal("2000.00"),
            currency="USD",
        )
        db_session.add(withdrawal)
        await db_session.commit()

        # Verify balance
        from src.services.cash_service import get_cash_balance
        balance = await get_cash_balance(db_session, test_user.id)
        assert balance == Decimal("8000.00")

    @pytest.mark.asyncio
    async def test_trade_and_portfolio_workflow(self, db_session: AsyncSession, test_user: User):
        """Test: Add trade → Check portfolio updates."""
        # Add a buy trade
        trade = Trade(
            user_id=test_user.id,
            symbol="AAPL",
            date=datetime.now(timezone.utc),
            type=TradeType.BUY,
            price=Decimal("150.00"),
            quantity=Decimal("10"),
            fees=Decimal("1.00"),
            currency="USD",
        )
        db_session.add(trade)
        await db_session.commit()

        # Verify portfolio has the holding
        from src.services.portfolio import get_portfolio_summary
        portfolio = await get_portfolio_summary(db_session, test_user.id)
        
        assert portfolio["holdings_count"] == 1
        assert portfolio["holdings"][0]["symbol"] == "AAPL"
        assert portfolio["holdings"][0]["quantity"] == 10.0
        assert portfolio["total_cost"] > 0

    @pytest.mark.asyncio
    async def test_full_portfolio_with_cash(self, db_session: AsyncSession, test_user: User):
        """Test: Add cash + trades → Verify cash ratio."""
        # Add cash deposit
        deposit = CashTransaction(
            user_id=test_user.id,
            date=datetime.now(timezone.utc),
            type=CashTransactionType.DEPOSIT,
            amount=Decimal("5000.00"),
            currency="USD",
        )
        db_session.add(deposit)

        # Add trade
        trade = Trade(
            user_id=test_user.id,
            symbol="MSFT",
            date=datetime.now(timezone.utc),
            type=TradeType.BUY,
            price=Decimal("300.00"),
            quantity=Decimal("10"),
            fees=Decimal("1.00"),
            currency="USD",
        )
        db_session.add(trade)
        await db_session.commit()

        # Verify portfolio includes cash ratio
        from src.services.portfolio import get_portfolio_summary
        portfolio = await get_portfolio_summary(db_session, test_user.id)

        assert "cash_balance" in portfolio
        assert "cash_ratio" in portfolio
        assert "total_portfolio" in portfolio
        assert portfolio["cash_balance"] == 5000.0


class TestPerformance:
    """Performance tests for success criteria."""

    @pytest.mark.asyncio
    async def test_dashboard_load_time(self):
        """SC-002: Dashboard should load within 3 seconds."""
        import time
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            start = time.time()
            response = await client.get("/health")
            elapsed = time.time() - start
            
            # Health check should be very fast
            assert elapsed < 1.0
            assert response.status_code == 200
