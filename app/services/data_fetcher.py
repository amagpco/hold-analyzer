"""
Data fetching service for stock/ETF and cryptocurrency price data
Supports both traditional stocks (via yfinance) and crypto (via CCXT/KuCoin)
"""

import yfinance as yf
import pandas as pd
import ccxt
from datetime import datetime, timedelta
from typing import Optional
from app.services.technical_analysis import calculate_technical_indicators

# Initialize KuCoin exchange (no API keys needed for public data)
_kucoin_exchange = None


def get_kucoin_exchange():
    """Get or create KuCoin exchange instance."""
    global _kucoin_exchange
    if _kucoin_exchange is None:
        _kucoin_exchange = ccxt.kucoin({
            'enableRateLimit': True,
            'timeout': 30000,
        })
    return _kucoin_exchange


def normalize_crypto_symbol(symbol: str) -> str:
    """
    Normalize crypto symbol for CCXT (e.g., BTC -> BTC/USDT, BTC-USD -> BTC/USDT).
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'BTC-USD', 'BTC/USDT')
        
    Returns:
        Normalized symbol in CCXT format (e.g., 'BTC/USDT')
    """
    symbol = symbol.upper().strip()
    
    # Remove common separators and convert to CCXT format
    if '/' in symbol:
        # Already in CCXT format, but check if it has USDT/USD
        parts = symbol.split('/')
        if len(parts) == 2:
            base = parts[0]
            quote = parts[1]
            # Normalize quote to USDT if USD
            if quote == 'USD':
                quote = 'USDT'
            return f"{base}/{quote}"
    
    # Handle dash format (BTC-USD -> BTC/USDT)
    if '-' in symbol:
        parts = symbol.split('-')
        if len(parts) == 2:
            base = parts[0]
            quote = parts[1]
            if quote.upper() == 'USD':
                quote = 'USDT'
            return f"{base}/{quote}"
    
    # Assume it's a base currency, default to USDT pair
    return f"{symbol}/USDT"


def fetch_crypto_data(symbol: str, months: int = 24) -> Optional[pd.DataFrame]:
    """
    Fetch cryptocurrency historical data from KuCoin via CCXT.
    
    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'BTC/USDT', 'ETH-USD')
        months: Number of months of historical data
        
    Returns:
        DataFrame with OHLCV data and technical indicators, or None if error
    """
    try:
        exchange = get_kucoin_exchange()
        normalized_symbol = normalize_crypto_symbol(symbol)
        
        # Load markets to get available trading pairs
        exchange.load_markets()
        
        # Check if symbol exists on exchange
        if normalized_symbol not in exchange.markets:
            # Try alternative quotes (USDC, BTC, etc.)
            base = normalized_symbol.split('/')[0]
            for quote in ['USDT', 'USDC', 'BTC', 'ETH']:
                alt_symbol = f"{base}/{quote}"
                if alt_symbol in exchange.markets:
                    normalized_symbol = alt_symbol
                    break
            else:
                return None
        
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 32)
        since = int(start_date.timestamp() * 1000)  # CCXT uses milliseconds
        
        # Fetch OHLCV data (1 day candles)
        timeframe = '1d'
        ohlcv_data = []
        
        # CCXT may limit the number of candles per request, so we may need to paginate
        current_since = since
        limit = 1000  # Max candles per request
        
        while current_since < int(end_date.timestamp() * 1000):
            candles = exchange.fetch_ohlcv(
                normalized_symbol,
                timeframe=timeframe,
                since=current_since,
                limit=limit
            )
            
            if not candles:
                break
            
            ohlcv_data.extend(candles)
            
            # Move to next batch
            if len(candles) < limit:
                break
            current_since = candles[-1][0] + 1  # Next timestamp after last candle
        
        if not ohlcv_data:
            return None
        
        # Convert to DataFrame
        # CCXT returns: [timestamp, open, high, low, close, volume]
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df.index.name = 'timestamp'
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Filter to date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        
        if df.empty:
            return None
        
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        return df
        
    except Exception as e:
        # If crypto fetch fails, return None (will try stock fetch)
        return None


def fetch_stock_data(symbol: str, months: int = 24) -> Optional[pd.DataFrame]:
    """
    Fetch stock/ETF historical data from yfinance.
    
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
        
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate technical indicators
        df = calculate_technical_indicators(df)
        
        return df
    except Exception as e:
        return None


def fetch_historical_data(symbol: str, months: int = 24) -> Optional[pd.DataFrame]:
    """
    Fetch historical price data with technical indicators.
    Supports both stocks (via yfinance) and cryptocurrencies (via CCXT/KuCoin).
    Tries crypto first, then falls back to stocks.
    
    Args:
        symbol: Stock/ETF symbol or cryptocurrency symbol (e.g., 'AAPL', 'BTC', 'BTC/USDT', 'ETH-USD')
        months: Number of months of historical data
        
    Returns:
        DataFrame with OHLCV data and technical indicators, or None if error
    """
    # Try crypto first (KuCoin via CCXT)
    df = fetch_crypto_data(symbol, months)
    if df is not None and not df.empty:
        return df
    
    # Fall back to stock data (yfinance)
    df = fetch_stock_data(symbol, months)
    if df is not None and not df.empty:
        return df
    
    # Both failed
    raise ValueError(f"Error fetching data for {symbol}: No data available from crypto or stock sources")

