from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine, get_db
from .services import finance_api, scraper_service
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
    "http://192.168.0.116:3000",
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

@app.get("/stock/{ticker}/price")
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


@app.get("/stock/{ticker}/kline")
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

# --- Scraper Endpoint ---

@app.get("/stock/{ticker}/finviz")
async def get_finviz(ticker: str):
    """
    Get fundamental data from Finviz for a given stock ticker.
    This is an async endpoint because it uses a web scraper.
    """
    try:
        finviz_data = await scraper_service.get_finviz_data(ticker)
        return finviz_data
    except scraper_service.ScraperError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

# --- Background Task Endpoint ---

@app.post("/stock/{ticker}/update-finviz-background")
def trigger_finviz_update(ticker: str):
    """
    Triggers a background task to scrape data from Finviz.
    Returns immediately with a task ID.
    """
    task = update_finviz_data.delay(ticker)
    return {"message": "Finviz update task has been queued.", "task_id": task.id}
