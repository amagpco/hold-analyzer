"""
DCA (Dollar Cost Averaging) calculator with boom range detection
"""

import pandas as pd
from typing import Dict, Optional, List
from app.services.technical_analysis import detect_boom_range


PROFILE_CONFIG: Dict[str, Dict[str, float]] = {
    "aggressive": {
        "min_signal_strength": 30.0,
        "fallback_threshold": 0.97,  # 3% below average
        "tiered_base": 0.50,
        "tiered_bonus": 0.45,
        "tiered_floor": 0.35,
        "fallback_fraction": 0.60,
    },
    "balanced": {
        "min_signal_strength": 40.0,
        "fallback_threshold": 0.95,  # 5% below average
        "tiered_base": 0.45,
        "tiered_bonus": 0.45,
        "tiered_floor": 0.30,
        "fallback_fraction": 0.50,
    },
    "conservative": {
        "min_signal_strength": 55.0,
        "fallback_threshold": 0.93,  # 7% below average
        "tiered_base": 0.35,
        "tiered_bonus": 0.40,
        "tiered_floor": 0.25,
        "fallback_fraction": 0.40,
    },
}

DEFAULT_PROFILE = "balanced"


def calculate_smart_dca(
    df: pd.DataFrame,
    symbol: str,
    monthly_amount: float,
    months: int = 24,
    strategy: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Calculate Smart DCA with boom range detection and budget accumulation.
    
    Args:
        df: DataFrame with historical price data and technical indicators
        symbol: Stock/ETF symbol
        monthly_amount: Monthly investment budget
        months: Number of months to simulate
        
    Returns:
        Dictionary with DCA calculation results, or None if error
    """
    if df is None or df.empty:
        return None
    
    strategy = strategy or {}
    strategy_profile = strategy.get("strategy_profile", DEFAULT_PROFILE)
    profile_cfg = PROFILE_CONFIG.get(strategy_profile, PROFILE_CONFIG[DEFAULT_PROFILE])
    allocation_mode = strategy.get("allocation_mode", "full")
    allocation_mode = allocation_mode if allocation_mode in {"full", "tiered"} else "full"
    min_signal_strength = strategy.get("min_signal_strength")
    if min_signal_strength is None:
        min_signal_strength = profile_cfg["min_signal_strength"]
    min_trade_amount = strategy.get("min_trade_amount") or 0.0
    fallback_threshold = strategy.get("fallback_threshold") or profile_cfg["fallback_threshold"]

    df = df.sort_index()
    start_date = df.index[0]
    end_date = df.index[-1]
    
    # Calculate monthly intervals safely using pandas
    start_month = pd.Timestamp(start_date).normalize().replace(day=1)
    end_month = pd.Timestamp(end_date).normalize().replace(day=1)
    monthly_dates = pd.date_range(start=start_month, end=end_month, freq='MS').to_list()[:months]
    
    total_shares = 0.0
    total_invested = 0.0
    accumulated_budget = 0.0
    months_waited = 0
    months_bought = 0
    trades = []
    monthly_summaries = []
    
    current_price = df.iloc[-1]['close']
    
    for purchase_date in monthly_dates:
        # Find available dates in this month
        month_start = pd.Timestamp(purchase_date)
        month_end = month_start + pd.offsets.MonthBegin(1)
        month_str = month_start.strftime('%Y-%m')
        
        month_data = df[(df.index >= month_start) & (df.index < month_end)].copy()
        
        # Add monthly budget
        accumulated_budget += monthly_amount
        
        if month_data.empty:
            # No data for this month
            monthly_summaries.append({
                'month': month_str,
                'traded': False,
                'trade': None,
                'accumulated_budget': accumulated_budget,
                'monthly_budget': monthly_amount
            })
            continue
        
        # Find best buy day with boom signal
        best_buy_day = None
        best_buy_price = None
        best_signal_strength = 0
        best_signal_reason = None
        trade_type = None
        
        for idx, row in month_data.iterrows():
            is_boom, reason, strength = detect_boom_range(row)
            
            if is_boom and strength > best_signal_strength:
                best_buy_day = idx
                best_buy_price = row['close']
                best_signal_strength = strength
                best_signal_reason = reason
                trade_type = 'boom_range'
        
        # Discard weak boom signals if below the required minimum
        if trade_type == 'boom_range' and best_signal_strength < min_signal_strength:
            best_buy_day = None
            best_buy_price = None
            best_signal_reason = None
            trade_type = None

        # Fallback: check for moderate dip
        if best_buy_day is None:
            month_avg = month_data['close'].mean()
            month_min_idx = month_data['close'].idxmin()
            month_min_price = month_data.loc[month_min_idx, 'close']
            
            if month_min_price < month_avg * fallback_threshold:
                best_buy_day = month_min_idx
                best_buy_price = month_min_price
                best_signal_reason = f"Monthly dip ({((month_min_price - month_avg) / month_avg * 100):.1f}% below avg)"
                trade_type = 'fallback'
        
        # Execute buy if opportunity found
        if best_buy_day is not None:
            allocation_fraction = 1.0
            effective_signal = best_signal_strength if trade_type == 'boom_range' else 0

            if allocation_mode == 'tiered':
                if trade_type == 'boom_range':
                    normalized_strength = 0.0
                    if min_signal_strength < 100:
                        normalized_strength = max(
                            0.0,
                            min(1.0, (effective_signal - min_signal_strength) / (100 - min_signal_strength))
                        )
                    allocation_fraction = profile_cfg['tiered_base'] + profile_cfg['tiered_bonus'] * normalized_strength
                    allocation_fraction = max(profile_cfg['tiered_floor'], min(allocation_fraction, 1.0))
                else:
                    allocation_fraction = profile_cfg['fallback_fraction']

            amount_invested = accumulated_budget * allocation_fraction

            if amount_invested < min_trade_amount:
                monthly_summaries.append({
                    'month': month_str,
                    'traded': False,
                    'trade': None,
                    'accumulated_budget': round(accumulated_budget, 2),
                    'monthly_budget': monthly_amount
                })
                months_waited += 1
                continue

            amount_invested = round(amount_invested, 2)
            shares_bought = amount_invested / best_buy_price
            total_shares += shares_bought
            total_invested += amount_invested
            
            # Calculate current value and P/L for this trade
            trade_current_value = shares_bought * current_price
            trade_profit_loss = trade_current_value - amount_invested
            trade_profit_loss_percent = (trade_profit_loss / amount_invested * 100) if amount_invested > 0 else 0
            
            # Create trade record
            trade = {
                'trade_date': pd.Timestamp(best_buy_day).strftime('%Y-%m-%d'),
                'month': month_str,
                'entry_price': round(best_buy_price, 4),
                'amount_invested': round(amount_invested, 2),
                'shares_bought': round(shares_bought, 6),
                'total_shares_after': round(total_shares, 6),
                'signal_strength': round(best_signal_strength, 2) if best_signal_strength > 0 else None,
                'signal_reason': best_signal_reason,
                'trade_type': trade_type,
                'accumulated_budget_used': round(amount_invested, 2),
                'current_price': round(current_price, 4),
                'current_value': round(trade_current_value, 2),
                'profit_loss': round(trade_profit_loss, 2),
                'profit_loss_percent': round(trade_profit_loss_percent, 2),
                'allocation_fraction': round(allocation_fraction, 3) if allocation_mode == 'tiered' else 1.0,
                'signal_threshold': round(min_signal_strength, 2)
            }
            trades.append(trade)
            
            accumulated_budget = max(round(accumulated_budget - amount_invested, 2), 0.0)
            monthly_summaries.append({
                'month': month_str,
                'traded': True,
                'trade': trade,
                'accumulated_budget': accumulated_budget,
                'monthly_budget': monthly_amount,
                'allocation_fraction': trade['allocation_fraction']
            })
            
            months_bought += 1
        else:
            # No trade this month
            monthly_summaries.append({
                'month': month_str,
                'traded': False,
                'trade': None,
                'accumulated_budget': accumulated_budget,
                'monthly_budget': monthly_amount
            })
            months_waited += 1
    
    current_price = df.iloc[-1]['close']
    current_value = total_shares * current_price
    profit_loss = current_value - total_invested
    profit_loss_percent = (profit_loss / total_invested) * 100 if total_invested > 0 else 0
    
    return {
        'symbol': symbol,
        'total_invested': round(total_invested, 2),
        'total_shares': round(total_shares, 6),
        'current_value': round(current_value, 2),
        'current_price': round(current_price, 4),
        'profit_loss': round(profit_loss, 2),
        'return_percent': round(profit_loss_percent, 2),
        'months_bought': months_bought,
        'months_waited': months_waited,
        'buy_rate': round(months_bought / len(monthly_dates), 4) if monthly_dates else 0,
        'unused_budget': round(accumulated_budget, 2),
        'trades': trades,
        'monthly_summary': monthly_summaries,
        'strategy_profile': strategy_profile,
        'allocation_mode': allocation_mode,
        'min_signal_strength': round(min_signal_strength, 2),
        'min_trade_amount': round(min_trade_amount, 2) if min_trade_amount else 0,
        'fallback_threshold': round(fallback_threshold, 2)
    }

