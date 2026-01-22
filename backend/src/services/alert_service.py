"""Alert service for managing price alerts."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alerts import AlertStatus, PriceAlert
from src.services.market_data import get_stock_price


async def create_alert(
    db: AsyncSession,
    user_id: UUID,
    symbol: str,
    target_price: float,
) -> PriceAlert:
    """
    Create a new price alert.
    
    Args:
        db: Database session
        user_id: User's UUID
        symbol: Stock ticker symbol
        target_price: Target price for alert
        
    Returns:
        Created PriceAlert object
    """
    # Get current price to store as initial price
    price_data = await get_stock_price(symbol)
    initial_price = price_data["price"] if price_data else target_price
    
    alert = PriceAlert(
        user_id=user_id,
        symbol=symbol.upper(),
        target_price=Decimal(str(target_price)),
        initial_price=Decimal(str(initial_price)),
        status=AlertStatus.ACTIVE,
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return alert


async def get_user_alerts(
    db: AsyncSession,
    user_id: UUID,
    status: AlertStatus | None = None,
) -> list[PriceAlert]:
    """
    Get all alerts for a user.
    
    Args:
        db: Database session
        user_id: User's UUID
        status: Optional filter by status
        
    Returns:
        List of PriceAlert objects
    """
    query = select(PriceAlert).where(PriceAlert.user_id == user_id)
    
    if status:
        query = query.where(PriceAlert.status == status)
    
    query = query.order_by(PriceAlert.created_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_alert_by_id(
    db: AsyncSession,
    alert_id: UUID,
    user_id: UUID,
) -> PriceAlert | None:
    """
    Get a specific alert by ID for a user.
    
    Args:
        db: Database session
        alert_id: Alert UUID
        user_id: User's UUID
        
    Returns:
        PriceAlert object or None
    """
    result = await db.execute(
        select(PriceAlert).where(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_alert(
    db: AsyncSession,
    alert_id: UUID,
    user_id: UUID,
) -> bool:
    """
    Delete an alert.
    
    Args:
        db: Database session
        alert_id: Alert UUID
        user_id: User's UUID
        
    Returns:
        True if deleted, False if not found
    """
    alert = await get_alert_by_id(db, alert_id, user_id)
    
    if not alert:
        return False
    
    await db.delete(alert)
    await db.commit()
    return True


async def update_alert_status(
    db: AsyncSession,
    alert: PriceAlert,
    status: AlertStatus,
) -> PriceAlert:
    """
    Update an alert's status.
    
    Args:
        db: Database session
        alert: PriceAlert object
        status: New status
        
    Returns:
        Updated PriceAlert object
    """
    alert.status = status
    if status == AlertStatus.TRIGGERED:
        alert.triggered_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(alert)
    return alert


async def check_price_alerts(db: AsyncSession) -> list[dict]:
    """
    Check all active alerts and trigger those that meet conditions.
    
    Args:
        db: Database session
        
    Returns:
        List of triggered alerts with details
    """
    # Get all active alerts
    result = await db.execute(
        select(PriceAlert).where(PriceAlert.status == AlertStatus.ACTIVE)
    )
    active_alerts = list(result.scalars().all())
    
    triggered = []
    
    for alert in active_alerts:
        # Get current price
        price_data = await get_stock_price(alert.symbol)
        
        if not price_data:
            continue
        
        current_price = Decimal(str(price_data["price"]))
        
        # Update last checked time
        alert.last_checked_at = datetime.now(timezone.utc)
        
        # Check if alert should trigger
        should_trigger = False
        
        # If target > initial, trigger when current >= target (crossing above)
        if alert.target_price > alert.initial_price:
            should_trigger = current_price >= alert.target_price
        # If target < initial, trigger when current <= target (crossing below)
        else:
            should_trigger = current_price <= alert.target_price
        
        if should_trigger:
            alert.status = AlertStatus.TRIGGERED
            alert.triggered_at = datetime.now(timezone.utc)
            
            triggered.append({
                "alert_id": str(alert.id),
                "user_id": str(alert.user_id),
                "symbol": alert.symbol,
                "target_price": float(alert.target_price),
                "current_price": float(current_price),
            })
    
    await db.commit()
    
    return triggered
