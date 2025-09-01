from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from . import models
from .database import engine, get_db
from .services import finance_api, scraper_service, analysis_service
from .tasks import update_finviz_data

# Create the database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StockValuator API",
    description="API for stock valuation and portfolio tracking.",
    version="0.1.0",
)

# Set up CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """
    Root endpoint to check API status.
    """
    return {"status": "ok", "message": "Welcome to the StockValuator API!"}


@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    """
    An endpoint to test the database connection.
    It tries to add and retrieve a test user.
    """
    try:
        test_email = "test@example.com"
        db_user = db.query(models.User).filter(models.User.email == test_email).first()
        if not db_user:
            db_user = models.User(email=test_email, hashed_password="notarealpassword")
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return {"status": "ok", "message": "Database connection successful. Test user created.", "email": db_user.email}
        return {"status": "ok", "message": "Database connection successful. Test user already exists.", "email": db_user.email}
    except Exception as e:
        return {"status": "error", "message": f"Database connection failed: {e}"}

# --- Stock Data Endpoints ---

@app.get("/api/v1/stock/{ticker}/price")
def get_price(ticker: str):
    """
    Get current price information for a given stock ticker.
    """
    try:
        price_data = finance_api.get_stock_price_info(ticker)
        return price_data
    except finance_api.TickerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/api/v1/stock/{ticker}/kline")
def get_kline(ticker: str, period: Optional[str] = "6mo", interval: Optional[str] = "1d"):
    """
    Get historical K-line data for a given stock ticker.
    """
    try:
        kline_data = finance_api.get_stock_kline(ticker, period=period, interval=interval)
        if kline_data is None:
            raise HTTPException(status_code=404, detail=f"Could not retrieve k-line data for ticker '{ticker}'. It might be delisted or have no historical data for the given period.")
        return kline_data
    except finance_api.TickerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# --- Scraper and Analysis Endpoint ---

@app.get("/api/v1/stock/{ticker}/analysis")
async def get_stock_analysis(ticker: str):
    """
    Get a full fundamental analysis for a stock or ETF.
    """
    try:
        quote_type = finance_api.get_quote_type(ticker)

        if quote_type == 'ETF':
            # For ETFs, get details from yfinance and holdings from the scraper
            details = finance_api.get_etf_details_from_yfinance(ticker)
            
            holdings = await scraper_service.get_etf_holdings_data(ticker)

            etf_data = {
                "details": details,
                "top_holdings": holdings
            }
            return {"quoteType": "ETF", "data": etf_data}

        elif quote_type == 'EQUITY':
            # For stocks, all data sources are async, so gather them all
            stock_results = await asyncio.gather(
                scraper_service.get_key_metrics_data(ticker),
                scraper_service.get_financial_statements_data(ticker),
                return_exceptions=True
            )
            
            key_metrics_data, financial_statements_df = None, None
            for result in stock_results:
                if isinstance(result, dict):
                    key_metrics_data = result
                elif isinstance(result, Exception):
                    raise HTTPException(status_code=500, detail=f"An error occurred during scraping: {result}")
                else: # It's the DataFrame
                    financial_statements_df = result

            if key_metrics_data is None or financial_statements_df is None:
                raise HTTPException(status_code=500, detail="Failed to retrieve all necessary data for stock analysis.")

            manual_inputs = {'economic_moat': 2, 'environment_risk': -1}
            sp500_yield = 1.19
            user_assumptions = {'dividend_required_return': 0.04, 'asset_pb_threshold': 0.8}
            
            confidence_results = analysis_service.calculate_confidence_score(financial_statements_df, key_metrics_data, manual_inputs)
            dividend_results = analysis_service.calculate_dividend_score(financial_statements_df, key_metrics_data)
            value_results = analysis_service.calculate_value_score(financial_statements_df, key_metrics_data, sp500_yield)
            fair_value_estimates = analysis_service.estimate_fair_value(financial_statements_df, key_metrics_data, confidence_results, dividend_results, user_assumptions)

            stock_data = {
                "ticker": ticker,
                "key_metrics": key_metrics_data,
                "financial_statements": financial_statements_df.to_dict(orient='records'),
                "analysis_scores": {
                    "confidence": confidence_results,
                    "dividend": dividend_results,
                    "value": value_results
                },
                "fair_value": fair_value_estimates
            }
            return {"quoteType": "EQUITY", "data": stock_data}
        else:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' has an unsupported quote type: {quote_type}")

    except finance_api.TickerNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except scraper_service.ScraperError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred in the analysis endpoint: {e}")


# --- Background Task Endpoint ---

@app.post("/api/v1/stock/{ticker}/update-metrics-background")
def trigger_metrics_update(ticker: str):
    """
    Triggers a background task to scrape key metrics data.
    Returns immediately with a task ID.
    """
    # Note: The task itself would need to be updated to a generic name if it's being used.
    task = update_finviz_data.delay(ticker)
    return {"message": "Metrics update task has been queued.", "task_id": task.id}