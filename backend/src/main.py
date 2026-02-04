"""StockValuator API - Main Application Entry Point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.cache import close_redis_pool
from src.core.database import dispose_engine
from src.core.yfinance_async import shutdown_yf_executor
from src.core.browser_pool import close_browser_pool
from src.api.routes import (
    auth,
    trades,
    watchlist,
    market,
    portfolio,
    cash,
    export,
    import_,
    user,
    alerts,
    email,
    analysis,
    market_cycle,
    health,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting application...")
    yield
    # Shutdown: Clean up resources
    logger.info("Shutting down application...")
    shutdown_yf_executor()
    await close_browser_pool()
    await close_redis_pool()
    await dispose_engine()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Stock analysis and management platform API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(auth.router)
app.include_router(trades.router)
app.include_router(watchlist.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(cash.router)
app.include_router(export.router)
app.include_router(import_.router)
app.include_router(user.router)
app.include_router(alerts.router)
app.include_router(email.router)
app.include_router(analysis.router)
app.include_router(market_cycle.router)
app.include_router(health.router)
