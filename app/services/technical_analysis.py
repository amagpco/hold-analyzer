"""
Technical analysis functions for boom range detection
"""

import pandas as pd
from typing import Tuple


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for boom range detection.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added technical indicators
    """
    # Moving Averages
    df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
    df['ma50'] = df['close'].rolling(window=50, min_periods=1).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Price position relative to MAs
    df['price_vs_ma20'] = (df['close'] - df['ma20']) / df['ma20'] * 100
    df['price_vs_ma50'] = (df['close'] - df['ma50']) / df['ma50'] * 100
    
    # Price drops
    df['price_drop_7d'] = (df['close'] - df['close'].shift(7)) / df['close'].shift(7) * 100
    df['price_drop_30d'] = (df['close'] - df['close'].shift(30)) / df['close'].shift(30) * 100
    
    # Monthly tracking
    df['year'] = df.index.year
    df['month'] = df.index.month
    
    return df


def detect_boom_range(row: pd.Series) -> Tuple[bool, str, float]:
    """
    Detect if price is in a boom range (significant dip).
    
    Args:
        row: Series with price data and technical indicators
        
    Returns:
        Tuple of (is_boom, reason, signal_strength)
    """
    signals = []
    signal_strength = 0
    
    # Signal 1: Price below MA20
    if pd.notna(row['price_vs_ma20']) and row['price_vs_ma20'] < -5:
        signals.append(f"{row['price_vs_ma20']:.1f}% below MA20")
        signal_strength += 25
    
    # Signal 2: Price below MA50
    if pd.notna(row['price_vs_ma50']) and row['price_vs_ma50'] < -10:
        signals.append(f"{row['price_vs_ma50']:.1f}% below MA50")
        signal_strength += 30
    
    # Signal 3: RSI oversold
    if pd.notna(row['rsi']):
        if row['rsi'] < 30:
            signals.append(f"RSI very oversold ({row['rsi']:.1f})")
            signal_strength += 30
        elif row['rsi'] < 40:
            signals.append(f"RSI oversold ({row['rsi']:.1f})")
            signal_strength += 15
    
    # Signal 4: 7-day drop
    if pd.notna(row['price_drop_7d']) and row['price_drop_7d'] < -10:
        signals.append(f"7-day drop: {row['price_drop_7d']:.1f}%")
        signal_strength += 20
    
    # Signal 5: 30-day drop
    if pd.notna(row['price_drop_30d']) and row['price_drop_30d'] < -20:
        signals.append(f"30-day drop: {row['price_drop_30d']:.1f}%")
        signal_strength += 25
    
    is_boom = signal_strength >= 40
    reason = " | ".join(signals) if signals else "No boom signals"
    
    return is_boom, reason, signal_strength

