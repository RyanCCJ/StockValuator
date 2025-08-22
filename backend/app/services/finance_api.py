import yfinance as yf
from functools import lru_cache

class TickerNotFound(Exception):
    """Custom exception for when a ticker is not found by yfinance."""
    def __init__(self, ticker):
        self.ticker = ticker
        super().__init__(f"Ticker '{ticker}' not found or invalid.")

@lru_cache(maxsize=128)
def get_ticker_data(ticker_symbol: str):
    """
    Fetches data for a given ticker using yfinance.
    Uses caching to avoid repeated API calls for the same ticker.
    Raises TickerNotFound if the ticker is invalid or not found.
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # yfinance downloads a lot of data, history() is a good way to check if it's valid
    # If history is empty, the ticker is likely invalid.
    if ticker.history(period="1d").empty:
        raise TickerNotFound(ticker_symbol)
        
    return ticker

def get_stock_price_info(ticker_symbol: str):
    """
    Gets the current price and basic info for a stock.
    """
    try:
        ticker = get_ticker_data(ticker_symbol)
        # .info is a dictionary with a lot of data
        info = ticker.info
        
        required_keys = [
            'currentPrice', 'open', 'dayHigh', 'dayLow', 'previousClose', 
            'volume', 'marketCap', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow'
        ]
        
        price_info = {key: info.get(key) for key in required_keys}
        price_info['ticker'] = ticker_symbol
        
        return price_info

    except TickerNotFound:
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching price info for {ticker_symbol}: {e}")
        return None

def get_stock_kline(ticker_symbol: str, period: str = "6mo", interval: str = "1d"):
    """
    Gets historical K-line (OHLCV) data for a stock.
    
    :param ticker_symbol: The stock ticker.
    :param period: The period of data to fetch (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
    :param interval: The data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo").
    """
    try:
        ticker = get_ticker_data(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None
            
        # Reset index to make 'Date' a column
        hist = hist.reset_index()
        # Convert timestamp to string for JSON serialization
        # The column name could be 'Date' or 'Datetime' depending on interval
        date_col = 'Date' if 'Date' in hist.columns else 'Datetime'
        hist[date_col] = hist[date_col].dt.strftime('%Y-%m-%d')
        
        # Convert dataframe to list of dictionaries
        return hist.to_dict(orient='records')
        
    except TickerNotFound:
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching k-line for {ticker_symbol}: {e}")
        return None
