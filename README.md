# StockValuator

A comprehensive full-stack web application for value investing, designed to estimate fair stock prices and support portfolio allocation. It offers multi-dimensional equity scoring, detailed ETF insights, and personalized portfolio management features.

## Features

- **Dynamic Dashboard**: Interactive K-line chart (candlestick) for price visualization, and key daily metrics.
- **State-Driven Navigation**: A clean, tab-based UI to switch between Dashboard, Analysis, and Portfolio views.
- **Advanced Stock Analysis**: 
  - **Confidence Score**: Evaluates long-term stability based on EPS, dividends, FCF, and ROE.
  - **Dividend Score**: Assesses the quality and sustainability of a company's dividend.
  - **Value Score**: Determines if a stock is undervalued based on various metrics like P/E, yield, and DDM.
  - **Fair Value Estimation**: Provides calculated estimates for a stock's fair value based on Growth, Dividend, or Asset models.
- **ETF-Specific View**: When an ETF is selected, the analysis view adapts to show:
  - A detailed summary.
  - Key metrics like expense ratio, yield, and P/E.
  - A visual breakdown of the Top 15 holdings in a pie chart and a detailed table.
- **Portfolio Management**: 
  - Track individual stock holdings with share count and average price.
  - Real-time profit/loss and total value calculation.
  - Manage total assets to see portfolio allocation vs. cash.
  - Visualize holdings by ticker and category with interactive pie charts.
- **Data Aggregation**: 
  - Backend scrapers fetch data from multiple online financial sources.
  - Data sources are de-identified and configurable via environment variables for security and flexibility.
- **Customizable UI**:
  - Light/Dark mode support, with a manual toggle and respect for system preference.
  - A responsive layout for various screen sizes.

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Web Scraping**: Playwright (for dynamic JavaScript-heavy sites)
- **Financial Data API**: yfinance
- **Data Analysis**: Pandas, NumPy, SciPy
- **Asynchronous Operations**: asyncio, async-lru
- **Database**: PostgreSQL (managed via Docker)
- **Task Queuing**: Celery, Redis
- **Environment Management**: Docker, Docker Compose, python-dotenv

### Frontend
- **Framework**: Next.js (React)
- **State Management**: Zustand
- **UI Components**: Shadcn/UI, Radix UI
- **Styling**: Tailwind CSS
- **Charting**: 
  - `lightweight-charts` for professional Candlestick charts.
  - `recharts` for Pie charts.
- **Language**: TypeScript

## Running the Application

This project is fully containerized using Docker. The following command will build and run all the necessary services, including the backend, frontend, database, and redis.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RyanCCJ/StockValuator.git
    cd StockValuator
    ```

2.  **Configure Environment Variables:**
    - In the project's root directory, find the `.env.example` file.
    - Create a copy of this file and name it `backend/.env`.
    - The URLs for the data sources are pre-filled, but you should modify them into the proper format.
    ```bash
    # This command works on Linux/macOS
    cp .env.example backend/.env
    ```

3.  **Build and Run the Application:**
    - This command will build the Docker images for all services and start them in detached mode.
    ```bash
    docker-compose up --build -d
    ```
    - The first time you run the application, you need to install the Playwright browsers inside the backend container:
    ```bash
    docker-compose exec backend playwright install
    ```

4.  **Access the Application:**
    - **Frontend Application**: Accessible at `http://localhost:3000`
    - **Backend API**: Accessible at `http://localhost:8000`
    - **API Documentation**: Interactive API documentation (via Swagger UI) is available at `http://localhost:8000/docs`.

To stop all services:
```bash
docker-compose down
```

## Project Structure

```
/StockValuator
├── .env.example        # Example environment file to guide setup
├── .gitignore          # Files and directories ignored by Git
├── docker-compose.yml  # Defines and configures all backend services
├── backend/
│   ├── app/            # Main application folder
│   │   ├── services/   # Contains all business logic
│   │   │   ├── finance_api.py    # Handles yfinance API calls
│   │   │   ├── scraper_service.py  # Generic web scrapers
│   │   │   └── analysis_service.py # Core scoring and valuation logic
│   │   ├── main.py     # FastAPI application entrypoint and API routes
│   │   └── ...
|   ├── Dockerfile      # Instructions to build the backend Docker image
│   └── .env            # (Private) Your local environment variables
└── frontend/
    ├── app/            # Next.js App Router pages and layouts
    ├── components/     # All React components
    │   ├── ui/         # Shadcn/UI components
    │   ├── Analysis.tsx
    │   ├── Dashboard.tsx
    │   ├── Portfolio.tsx
    │   └── ...
    ├── store/          # Zustand store for global state management
    │   └── tickerStore.ts
    └── package.json    # Frontend dependencies
```
