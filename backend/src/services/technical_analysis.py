"""Technical indicator calculations using pandas."""

import pandas as pd
import numpy as np
from typing import Any


def calculate_sma(
    prices: pd.Series, periods: list[int] = [5, 20, 60]
) -> dict[str, list[float | None]]:
    """
    Calculate Simple Moving Averages for given periods.
    
    Args:
        prices: Series of closing prices
        periods: List of periods to calculate SMA for
        
    Returns:
        Dictionary with SMA values for each period
    """
    result = {}
    for period in periods:
        sma = prices.rolling(window=period).mean()
        result[f"ma{period}"] = [None if pd.isna(x) else round(x, 2) for x in sma]
    return result


def calculate_rsi(prices: pd.Series, period: int = 14) -> list[float | None]:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: Series of closing prices
        period: RSI period (default 14)
        
    Returns:
        List of RSI values (0-100)
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return [None if pd.isna(x) else round(x, 2) for x in rsi]


def calculate_macd(
    prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> dict[str, list[float | None]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: Series of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
        
    Returns:
        Dictionary with MACD line, signal line, and histogram
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        "line": [None if pd.isna(x) else round(x, 4) for x in macd_line],
        "signal": [None if pd.isna(x) else round(x, 4) for x in signal_line],
        "histogram": [None if pd.isna(x) else round(x, 4) for x in histogram],
    }


def calculate_bollinger_bands(
    prices: pd.Series, period: int = 20, std_dev: int = 2
) -> dict[str, list[float | None]]:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: Series of closing prices
        period: Moving average period (default 20)
        std_dev: Number of standard deviations (default 2)
        
    Returns:
        Dictionary with upper, middle, and lower bands
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        "upper": [None if pd.isna(x) else round(x, 2) for x in upper],
        "middle": [None if pd.isna(x) else round(x, 2) for x in middle],
        "lower": [None if pd.isna(x) else round(x, 2) for x in lower],
    }


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 9,
    d_period: int = 3,
) -> dict[str, list[float | None]]:
    """
    Calculate Stochastic Oscillator (KDJ indicator).
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of closing prices
        k_period: %K period (default 9)
        d_period: %D period (default 3)
        
    Returns:
        Dictionary with K, D, and J values
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    # Calculate %K
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    # Calculate %D (3-period SMA of %K)
    d = k.rolling(window=d_period).mean()
    
    # Calculate %J (3*K - 2*D)
    j = 3 * k - 2 * d
    
    return {
        "k": [None if pd.isna(x) else round(x, 2) for x in k],
        "d": [None if pd.isna(x) else round(x, 2) for x in d],
        "j": [None if pd.isna(x) else round(x, 2) for x in j],
    }


def calculate_all_indicators(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate all technical indicators for a DataFrame with OHLCV data.
    
    Args:
        df: DataFrame with columns: Open, High, Low, Close, Volume
        
    Returns:
        Dictionary containing all indicator values
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    
    return {
        "sma": calculate_sma(close),
        "rsi": calculate_rsi(close),
        "macd": calculate_macd(close),
        "bollinger": calculate_bollinger_bands(close),
        "stochastic": calculate_stochastic(high, low, close),
        "volume": [int(v) for v in volume],
    }
