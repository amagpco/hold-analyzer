"""
FastAPI application for Smart DCA calculator with boom range detection
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import logging
from pathlib import Path

from app.models import (
    DCARequest,
    DCAResponse,
    DCAResult,
    Trade,
    MonthlySummary,
    SingleSymbolRequest,
    GoldAnalysisRequest
)
from app.services.data_fetcher import fetch_historical_data
from app.services.dca_calculator import calculate_smart_dca

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup templates and static files
BASE_DIR = Path(__file__).parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = BASE_DIR / "static"


def convert_result_to_dca_result(result: dict) -> DCAResult:
    """
    Convert result dictionary to DCAResult with proper model conversion.
    
    Args:
        result: Dictionary from calculate_smart_dca
        
    Returns:
        DCAResult Pydantic model
    """
    # Convert trades
    trades = [Trade(**trade) if isinstance(trade, dict) else trade for trade in result.get('trades', [])]
    result['trades'] = trades
    
    # Convert monthly_summary
    monthly_summaries = []
    for summary in result.get('monthly_summary', []):
        if isinstance(summary, dict):
            if summary.get('trade'):
                summary['trade'] = Trade(**summary['trade'])
            monthly_summaries.append(MonthlySummary(**summary))
        else:
            monthly_summaries.append(summary)
    result['monthly_summary'] = monthly_summaries
    
    return DCAResult(**result)

# Initialize FastAPI app
app = FastAPI(
    title="Smart DCA Calculator API",
    description="Dollar Cost Averaging calculator with boom range detection",
    version="1.0.0"
)

# Mount static files directory if it exists
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== HTML Routes ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main analysis page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """Analysis page (alias for index)."""
    return templates.TemplateResponse("index.html", {"request": request})


# ========== API Routes ==========

@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Smart DCA Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/analyze",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=DCAResponse)
async def analyze_multiple_symbols(request: DCARequest):
    """
    Analyze multiple symbols using Smart DCA strategy.
    
    Args:
        request: DCARequest with symbols, monthly_amount, and months
        
    Returns:
        DCAResponse with analysis results for all symbols
    """
    try:
        results = []
        errors = []
        strategy_config = {
            "strategy_profile": request.strategy_profile,
            "allocation_mode": request.allocation_mode,
            "min_signal_strength": request.min_signal_strength,
            "min_trade_amount": request.min_trade_amount,
        }
        
        for symbol in request.symbols:
            try:
                logger.info(f"Processing {symbol}...")
                
                # Fetch historical data
                df = fetch_historical_data(symbol, request.months)
                if df is None:
                    errors.append(f"No data available for {symbol}")
                    continue
                
                # Calculate DCA
                result = calculate_smart_dca(
                    df,
                    symbol,
                    request.monthly_amount,
                    request.months,
                    strategy=strategy_config
                )
                
                if result:
                    results.append(convert_result_to_dca_result(result))
                    logger.info(f"✓ Successfully processed {symbol}")
                else:
                    errors.append(f"Calculation failed for {symbol}")
                    
            except Exception as e:
                error_msg = f"Error processing {symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if not results:
            raise HTTPException(
                status_code=400,
                detail=f"No successful results. Errors: {errors}"
            )
        
        # Calculate summary
        if results:
            best = max(results, key=lambda x: x.return_percent)
            worst = min(results, key=lambda x: x.return_percent)
            summary = {
                "best_performer": {
                    "symbol": best.symbol,
                    "return_percent": best.return_percent
                },
                "worst_performer": {
                    "symbol": worst.symbol,
                    "return_percent": worst.return_percent
                },
                "total_symbols": len(results)
            }
        else:
            summary = None
        
        message = f"Successfully analyzed {len(results)} symbol(s)"
        if errors:
            message += f". {len(errors)} error(s) occurred: {', '.join(errors[:3])}"
        
        return DCAResponse(
            success=True,
            results=results,
            summary=summary,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_multiple_symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

