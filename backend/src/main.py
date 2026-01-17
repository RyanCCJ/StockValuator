"""StockValuator API - Main Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.api.routes import auth, trades, watchlist, market, portfolio, cash, export, import_, user

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Could initialize database connections, etc.
    yield
    # Shutdown: Clean up resources


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
