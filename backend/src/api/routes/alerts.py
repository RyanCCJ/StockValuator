"""Price alert API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db
from src.models.user import User
from src.schemas.alerts import CreateAlertRequest, PriceAlertResponse, AlertListResponse
from src.services.alert_service import (
    create_alert,
    get_user_alerts,
    delete_alert,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    request: CreateAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new price alert.
    
    The alert will trigger when the stock price crosses the target price.
    Direction is automatically determined based on current price vs target.
    """
    alert = await create_alert(
        db=db,
        user_id=current_user.id,
        symbol=request.symbol,
        target_price=request.target_price,
    )
    
    return PriceAlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        target_price=float(alert.target_price),
        initial_price=float(alert.initial_price),
        status=alert.status.value,
        created_at=alert.created_at,
        triggered_at=alert.triggered_at,
    )


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all alerts for the current user."""
    alerts = await get_user_alerts(db, current_user.id)
    
    return AlertListResponse(
        alerts=[
            PriceAlertResponse(
                id=alert.id,
                symbol=alert.symbol,
                target_price=float(alert.target_price),
                initial_price=float(alert.initial_price),
                status=alert.status.value,
                created_at=alert.created_at,
                triggered_at=alert.triggered_at,
            )
            for alert in alerts
        ],
        count=len(alerts),
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a price alert."""
    deleted = await delete_alert(db, alert_id, current_user.id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    
    return None
