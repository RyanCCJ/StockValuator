# System Architecture

## Overview

StockValuator is a full-stack application designed for self-directed investors. It combines real-time market data and historical financial analysis to provide a comprehensive view of stock valuation.

The system is built on a decoupled architecture:
- **Frontend**: A responsive Next.js web application.
- **Backend**: A high-performance FastAPI service handling data aggregation and API requests.
- **Task Worker**: A Celery worker managing background price monitoring and notification tasks.
- **Data Layer**: PostgreSQL for relational data and Redis for caching, locking, and task queue management.

## High-Level Diagram

```mermaid
graph TD
    Client[Web Client (Next.js)] -->|REST API| API[Backend API (FastAPI)]
    
    subgraph Backend Services
        API -->|Read/Write| DB[(PostgreSQL)]
        API -->|Cache/Lock| Redis[(Redis)]
        API -->|Scrape| BrowserPool[Browser Pool (Playwright)]
        API -->|Enqueue| Redis
        
        Redis -->|Dequeue| Worker[Celery Worker]
        Worker -->|Check Price| YFinance[Yahoo Finance API]
        Worker -->|Send Email| Mail[Mail Server / Gmail API]
        
        BrowserPool -->|HTML| ExternalSites[External Financial Sites]
    end
    
    subgraph Data Processing
        API --> Analysis[Valuation Engines]
        Analysis -->|Compute| Scores[Confidence/Value Scores]
    end
```

## Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS, Shadcn/UI
- **State Management**: Zustand (Client state), React Query (Server state)
- **Visualization**: Lightweight Charts (TradingView), Recharts

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **ORM**: SQLAlchemy (Async) + Alembic (Migrations)
- **Task Execution**: Async/Await + BackgroundTasks (Celery capability available)
- **Scraping**: Playwright (Headless Chromium)
- **Financial Data**: yfinance, pandas, numpy

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Database**: PostgreSQL 16
- **Cache**: Redis 7

## Key Design Patterns

### 1. Repository/Service Pattern
The backend is structured to separate concerns:
- **Routes (`src/api/routes`)**: Handle HTTP requests/responses and validation.
- **Services (`src/services`)**: Contain business logic (e.g., calculating fair value, fetching market data).
- **Models/Schemas**: Define database structure and Pydantic validation rules.

### 2. Async-First
All I/O operations (database queries, external API calls, scraping) are asynchronous. This ensures the API remains responsive even when handling long-running scraping tasks.

### 3. On-Demand Data with Caching
Instead of maintaining a massive database of all stock data, the system fetches data on-demand when a user requests a specific ticker.
- **Fresh Data**: If data is missing or stale, it's fetched immediately.
- **Caching**: Results are cached in Redis to serve subsequent requests instantly.
- **Persistence**: Historical data is stored in PostgreSQL for long-term trend analysis.

## Directory Structure

```
backend/
├── src/
│   ├── api/            # API endpoints
│   ├── core/           # Config, database, cache, browser pool
│   ├── models/         # SQLAlchemy DB models
│   ├── schemas/        # Pydantic data schemas
│   ├── services/       # Business logic & scrapers
│   └── worker.py       # Background worker entry point
frontend/
├── src/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # Reusable UI components
│   ├── lib/            # Utilities
│   └── services/       # API client
```
