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
    Gets the current price and basic info for a stock or ETF.
    It standardizes the output keys regardless of the quote type.
    """
    try:
        ticker = get_ticker_data(ticker_symbol)
        info = ticker.info
        quote_type = info.get('quoteType')

        price_info = {
            'ticker': ticker_symbol,
            'quoteType': quote_type,
        }

        if quote_type == 'ETF':
            price_info.update({
                'currentPrice': info.get('navPrice') or info.get('regularMarketPrice'),
                'open': info.get('open'),
                'dayHigh': info.get('dayHigh'),
                'dayLow': info.get('dayLow'),
                'previousClose': info.get('previousClose'),
                'volume': info.get('volume'),
                'marketCap': info.get('totalAssets'), # Use totalAssets for ETFs
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
            })
        else: # Default to EQUITY keys
            price_info.update({
                'currentPrice': info.get('currentPrice'),
                'open': info.get('open'),
                'dayHigh': info.get('dayHigh'),
                'dayLow': info.get('dayLow'),
                'previousClose': info.get('previousClose'),
                'volume': info.get('volume'),
                'marketCap': info.get('marketCap'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
            })
        
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

def get_quote_type(ticker_symbol: str) -> str | None:
    """Gets the quote type (e.g., 'EQUITY', 'ETF') for a ticker."""
    try:
        ticker = get_ticker_data(ticker_symbol)
        return ticker.info.get('quoteType')
    except TickerNotFound:
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching quote type for {ticker_symbol}: {e}")
        return None

def get_etf_details_from_yfinance(ticker_symbol: str) -> dict | None:
    """Gets a dictionary of detailed information for an ETF from yfinance."""
    try:
        ticker = get_ticker_data(ticker_symbol)
        info = ticker.info

        # Format data and handle missing values gracefully
        expense_ratio = info.get('netExpenseRatio')
        if expense_ratio is not None:
            expense_ratio = f"{expense_ratio}%"
        
        trailing_PE = info.get('trailingPE')
        if trailing_PE is not None:
            trailing_PE = f"{trailing_PE:.2f}"
        
        dividend_yield = info.get('dividendYield')
        if dividend_yield is not None:
            dividend_yield = f"{dividend_yield}%"

        five_year_return = info.get('fiveYearAverageReturn')
        if five_year_return is not None:
            five_year_return = f"{five_year_return * 100:.2f}%"
        
        beta = info.get('beta3Year')
        if beta is not None:
            beta = str(beta)

        return {
            "longBusinessSummary": info.get('longBusinessSummary'),
            "fundFamily": info.get('fundFamily'),
            "expenseRatio": expense_ratio,
            "trailingPE": trailing_PE,
            "dividendYield": dividend_yield,
            "fiveYearAverageReturn": five_year_return,
            "beta": beta,
        }
    except TickerNotFound:
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching ETF details for {ticker_symbol}: {e}")
        return None
