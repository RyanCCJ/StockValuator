import yfinance as yf
import pandas as pd
import numpy as np
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
                'PEratio': info.get('trailingPE'),
                'dividendYield': info.get('dividendYield'),
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
                'PEratio': info.get('trailingPE'),
                'dividendYield': info.get('dividendYield'),
            })
        
        return price_info

    except TickerNotFound:
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching price info for {ticker_symbol}: {e}")
        return None

def get_stock_kline(ticker_symbol: str, period: str = "6mo", interval: str = "1d"):
    """
    Gets historical K-line (OHLCV) data for a stock, including Bollinger Bands and MAs/EMAs.
    """
    try:
        ticker = get_ticker_data(ticker_symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None

        # Calculate Bollinger Bands
        window = 20
        hist['MiddleBand'] = hist['Close'].rolling(window=window).mean()
        hist['StdDev'] = hist['Close'].rolling(window=window).std()
        hist['UpperBand'] = hist['MiddleBand'] + (hist['StdDev'] * 2)
        hist['LowerBand'] = hist['MiddleBand'] - (hist['StdDev'] * 2)

        # Calculate MAs and EMAs
        ma_periods = [7, 30, 90]
        for p in ma_periods:
            hist[f'MA{p}'] = hist['Close'].rolling(window=p).mean()
        ema_periods = [5, 10, 20]
        for p in ema_periods:
            hist[f'EMA{p}'] = hist['Close'].ewm(span=p, adjust=False).mean()

        # Calculate MACD
        ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD_line'] = ema12 - ema26
        hist['Signal_line'] = hist['MACD_line'].ewm(span=9, adjust=False).mean()
        hist['MACD_histogram'] = hist['MACD_line'] - hist['Signal_line']

        # Calculate Support and Resistance Levels
        # A simple method: find N highest highs (resistance) and N lowest lows (support)
        # More complex methods like pivot points could be added later.
        sorted_lows = hist['Low'].sort_values()
        sorted_highs = hist['High'].sort_values(ascending=False)
        
        support_levels = {
            f"s{i+1}": level for i, level in enumerate(sorted_lows.unique()[:3])
        }
        resistance_levels = {
            f"r{i+1}": level for i, level in enumerate(sorted_highs.unique()[:3])
        }

        hist = hist.reset_index()
        date_col = 'Date' if 'Date' in hist.columns else 'Datetime'
        hist[date_col] = hist[date_col].dt.strftime('%Y-%m-%d')
        
        # Replace non-JSON compliant values NaN with None
        hist = hist.astype(object).where(pd.notnull(hist), None)
        kline_data = hist.to_dict(orient='records') 

        return {
            "kline_data": kline_data,
            "levels": {**support_levels, **resistance_levels}
        }
        
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
