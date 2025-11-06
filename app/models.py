"""
Pydantic models for request and response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class DCARequest(BaseModel):
    """Request model for DCA calculation."""
    symbols: List[str] = Field(..., description="List of stock/ETF symbols to analyze")
    monthly_amount: float = Field(100.0, ge=0, description="Monthly investment amount")
    months: int = Field(24, ge=1, le=120, description="Number of months to analyze (1-120)")
    strategy_profile: Literal['aggressive', 'balanced', 'conservative'] = Field(
        'balanced', description="Strategy profile to adjust signal thresholds"
    )
    allocation_mode: Literal['full', 'tiered'] = Field(
        'full', description="Budget deployment mode for qualifying trades"
    )
    min_signal_strength: Optional[float] = Field(
        None, ge=0, le=100,
        description="Minimum boom-range signal strength required to trigger a trade"
    )
    min_trade_amount: Optional[float] = Field(
        None, ge=0,
        description="Do not execute trades below this invested amount"
    )


class Trade(BaseModel):
    """Model for individual trade/transaction."""
    trade_date: str = Field(..., description="Date of the trade")
    month: str = Field(..., description="Month of the trade (YYYY-MM)")
    entry_price: float = Field(..., description="Price at which shares were bought")
    amount_invested: float = Field(..., description="Amount invested in this trade")
    shares_bought: float = Field(..., description="Number of shares bought")
    total_shares_after: float = Field(..., description="Total shares accumulated after this trade")
    signal_strength: Optional[float] = Field(None, description="Signal strength that triggered the buy")
    signal_reason: Optional[str] = Field(None, description="Reason for the buy signal")
    trade_type: str = Field(..., description="Type of trade: 'boom_range' or 'fallback'")
    accumulated_budget_used: float = Field(..., description="Total accumulated budget used for this trade")
    current_price: Optional[float] = Field(None, description="Current price of the asset")
    current_value: Optional[float] = Field(None, description="Current value of shares from this trade")
    profit_loss: Optional[float] = Field(None, description="Profit/loss from this trade")
    profit_loss_percent: Optional[float] = Field(None, description="Profit/loss percentage from this trade")
    allocation_fraction: Optional[float] = Field(
        None, description="Portion of available budget deployed in this trade"
    )
    signal_threshold: Optional[float] = Field(
        None, description="Minimum signal strength required for this trade"
    )


class MonthlySummary(BaseModel):
    """Model for monthly summary (trades or no trades)."""
    month: str = Field(..., description="Month (YYYY-MM)")
    traded: bool = Field(..., description="Whether a trade occurred this month")
    trade: Optional[Trade] = None
    accumulated_budget: float = Field(..., description="Budget accumulated up to this month")
    monthly_budget: float = Field(..., description="Budget added this month")
    allocation_fraction: Optional[float] = Field(
        None, description="Allocation fraction used when a trade executed"
    )


class DCAResult(BaseModel):
    """Result model for a single symbol DCA calculation."""
    symbol: str
    total_invested: float
    total_shares: float
    current_value: float
    current_price: float
    profit_loss: float
    return_percent: float
    months_bought: int
    months_waited: int
    buy_rate: float
    unused_budget: float
    trades: List[Trade] = Field(default_factory=list, description="List of all trades executed")
    monthly_summary: List[MonthlySummary] = Field(default_factory=list, description="Summary for each month")
    strategy_profile: Optional[str] = Field(
        None, description="Strategy profile applied during analysis"
    )
    allocation_mode: Optional[str] = Field(
        None, description="Budget deployment mode used"
    )
    min_signal_strength: Optional[float] = Field(
        None, description="Effective minimum signal strength used for boom trades"
    )
    min_trade_amount: Optional[float] = Field(
        None, description="Minimum trade amount constraint applied"
    )
    fallback_threshold: Optional[float] = Field(
        None, description="Fallback dip threshold used (relative to monthly average)"
    )


class DCAResponse(BaseModel):
    """Response model for DCA analysis."""
    success: bool
    results: List[DCAResult]
    summary: Optional[dict] = None
    message: Optional[str] = None


class SingleSymbolRequest(BaseModel):
    """Request model for single symbol analysis."""
    symbol: str = Field(..., description="Stock/ETF symbol to analyze")
    monthly_amount: float = Field(100.0, ge=0, description="Monthly investment amount")
    months: int = Field(24, ge=1, le=120, description="Number of months to analyze")
    strategy_profile: Literal['aggressive', 'balanced', 'conservative'] = Field(
        'balanced', description="Strategy profile to adjust signal thresholds"
    )
    allocation_mode: Literal['full', 'tiered'] = Field(
        'full', description="Budget deployment mode for qualifying trades"
    )
    min_signal_strength: Optional[float] = Field(
        None, ge=0, le=100,
        description="Minimum boom-range signal strength required to trigger a trade"
    )
    min_trade_amount: Optional[float] = Field(
        None, ge=0,
        description="Do not execute trades below this invested amount"
    )


class GoldAnalysisRequest(BaseModel):
    """Request model for gold analysis."""
    gold_symbol: str = Field("GLD", description="Gold ETF symbol (GLD, IAU, SGOL)")
    monthly_amount: float = Field(100.0, ge=0)
    months: int = Field(24, ge=1, le=120)
    strategy_profile: Literal['aggressive', 'balanced', 'conservative'] = Field(
        'balanced', description="Strategy profile to adjust signal thresholds"
    )
    allocation_mode: Literal['full', 'tiered'] = Field(
        'full', description="Budget deployment mode for qualifying trades"
    )
    min_signal_strength: Optional[float] = Field(
        None, ge=0, le=100,
        description="Minimum boom-range signal strength required to trigger a trade"
    )
    min_trade_amount: Optional[float] = Field(
        None, ge=0,
        description="Do not execute trades below this invested amount"
    )

