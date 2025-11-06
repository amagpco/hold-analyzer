"""
Data fetching service for stock/ETF price data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from app.services.technical_analysis import calculate_technical_indicators


def fetch_historical_data(symbol: str, months: int = 24) -> Optional[pd.DataFrame]:
    """
    Fetch historical price data with technical indicators.
    
    Args:
        symbol: Stock/ETF symbol
        months: Number of months of historical data
        
    Returns:
        DataFrame with OHLCV data and technical indicators, or None if error
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 32)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            return None
        
        # Standardize column names
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df.index.name = 'timestamp'
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        return df
    except Exception as e:
        raise ValueError(f"Error fetching data for {symbol}: {str(e)}")

