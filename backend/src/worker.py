"""Celery worker tasks for background job processing."""

from src.core.celery_app import celery_app


@celery_app.task(name="src.worker.check_price_alerts_task")
def check_price_alerts_task():
    """
    Celery task to check all active price alerts.
    
    This task is scheduled to run periodically via Celery Beat.
    It checks all active alerts and triggers notifications when conditions are met.
    """
    import asyncio
    
    async def run_check():
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy import select
        
        from src.core.config import get_settings
        from src.services.alert_service import check_price_alerts
        from src.services.email_service import send_price_alert_email
        from src.models.user import User
        
        settings = get_settings()
        
        # Create a fresh engine for this task (avoids event loop conflicts)
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
        )
        
        session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        try:
            async with session_maker() as db:
                # Check alerts and get triggered ones
                triggered_alerts = await check_price_alerts(db)
                
                # Send emails for triggered alerts
                for alert_info in triggered_alerts:
                    # Get user email
                    result = await db.execute(
                        select(User).where(User.id == alert_info["user_id"])
                    )
                    user = result.scalar_one_or_none()
                    
                    if user:
                        print(f"Sending email to {user.email} for {alert_info['symbol']}")
                        sent = await send_price_alert_email(
                            to_email=user.email,
                            symbol=alert_info["symbol"],
                            target_price=alert_info["target_price"],
                            current_price=alert_info["current_price"],
                        )
                        print(f"Email sent result: {sent}")
                    else:
                        print(f"User {alert_info['user_id']} not found for alert")
                
                await db.commit()
                
                return {
                    "checked": True,
                    "triggered_count": len(triggered_alerts),
                    "triggered_alerts": triggered_alerts,
                }
        finally:
            await engine.dispose()
    
    # Run async code in sync context (Python 3.10+ compatible)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_check())
    finally:
        loop.close()
