![Alt text](https://i.postimg.cc/jSK4hCnK/tech-analysis.webp)

# Smart DCA Calculator API

A FastAPI-based Dollar Cost Averaging (DCA) calculator with intelligent boom range detection for stocks, ETFs, and gold.

## Features

- **Smart DCA Strategy**: Only buys when price is in a "boom range" (significant dips)
- **Budget Accumulation**: Budget accumulates when no buy opportunity is found
- **Technical Analysis**: Uses Moving Averages, RSI, and price drop indicators
- **Multiple Assets**: Supports stocks, ETFs, and gold
- **RESTful API**: Clean, documented API endpoints

## Project Structure

```
hold-analyzor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py             # Pydantic request/response models
│   └── services/
│       ├── __init__.py
│       ├── data_fetcher.py   # Data fetching service
│       ├── dca_calculator.py # DCA calculation logic
│       └── technical_analysis.py # Technical indicators
├── requirements.txt
└── README.md
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running:
- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## Response Structure

Each result includes:

### Trade Details
- **trades**: List of all executed trades with:
  - `trade_date`: Date of the trade
  - `entry_price`: Price at which shares were bought
  - `amount_invested`: Amount invested in this trade
  - `shares_bought`: Number of shares purchased
  - `signal_strength`: Technical signal strength (0-100+)
  - `signal_reason`: Why the buy signal was triggered
  - `trade_type`: "boom_range" or "fallback"
  - `current_value`: Current value of shares from this trade
  - `profit_loss`: Profit/loss from this specific trade

### Monthly Summary
- **monthly_summary**: Month-by-month breakdown showing:
  - `month`: Month (YYYY-MM)
  - `traded`: Whether a trade occurred
  - `trade`: Trade details if traded, null if not
  - `accumulated_budget`: Budget accumulated up to that month
  - `monthly_budget`: Budget added that month

## API Endpoints

### 1. Root Endpoint
```
GET /
```
Returns API information and available endpoints.

### 2. Health Check
```
GET /health
```
Returns API health status.

### 3. Analyze Multiple Symbols
```
POST /api/analyze
```
Analyze multiple stocks/ETFs using Smart DCA strategy.

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "monthly_amount": 100,
  "months": 24
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "symbol": "AAPL",
      "total_invested": 2400.0,
      "total_shares": 15.5,
      "current_value": 2800.0,
      "current_price": 180.65,
      "profit_loss": 400.0,
      "return_percent": 16.67,
      "months_bought": 18,
      "months_waited": 6,
      "buy_rate": 0.75,
      "unused_budget": 0.0,
      "trades": [
        {
          "trade_date": "2023-01-15",
          "month": "2023-01",
          "entry_price": 150.25,
          "amount_invested": 200.0,
          "shares_bought": 1.3319,
          "total_shares_after": 1.3319,
          "signal_strength": 45.5,
          "signal_reason": "-6.2% below MA20 | RSI oversold (35.2)",
          "trade_type": "boom_range",
          "accumulated_budget_used": 200.0,
          "current_price": 180.65,
          "current_value": 240.65,
          "profit_loss": 40.65,
          "profit_loss_percent": 20.33
        }
      ],
      "monthly_summary": [
        {
          "month": "2023-01",
          "traded": true,
          "trade": {
            "trade_date": "2023-01-15",
            "month": "2023-01",
            "entry_price": 150.25,
            "amount_invested": 200.0,
            "shares_bought": 1.3319,
            "total_shares_after": 1.3319,
            "signal_strength": 45.5,
            "signal_reason": "-6.2% below MA20 | RSI oversold (35.2)",
            "trade_type": "boom_range",
            "accumulated_budget_used": 200.0,
            "current_price": 180.65,
            "current_value": 240.65,
            "profit_loss": 40.65,
            "profit_loss_percent": 20.33
          },
          "accumulated_budget": 0.0,
          "monthly_budget": 100.0
        },
        {
          "month": "2023-02",
          "traded": false,
          "trade": null,
          "accumulated_budget": 100.0,
          "monthly_budget": 100.0
        }
      ]
    }
  ],
  "summary": {
    "best_performer": {
      "symbol": "AAPL",
      "return_percent": 16.67
    },
    "worst_performer": {
      "symbol": "MSFT",
      "return_percent": 8.5
    },
    "total_symbols": 3
  },
  "message": "Successfully analyzed 3 symbol(s)"
}
```

### 4. Analyze Single Symbol
```
POST /api/analyze/single
```
Analyze a single stock/ETF.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "monthly_amount": 100,
  "months": 24
}
```

### 5. Analyze Gold
```
POST /api/analyze/gold
```
Analyze gold investment using gold ETFs (GLD, IAU, SGOL).

**Request Body:**
```json
{
  "gold_symbol": "GLD",
  "monthly_amount": 100,
  "months": 24
}
```

## Example Usage

### Using cURL

```bash
# Analyze multiple stocks
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "monthly_amount": 100,
    "months": 24
  }'

# Analyze gold
curl -X POST "http://localhost:8000/api/analyze/gold" \
  -H "Content-Type: application/json" \
  -d '{
    "gold_symbol": "GLD",
    "monthly_amount": 100,
    "months": 24
  }'
```

### Using Python

```python
import requests

# Analyze multiple symbols
response = requests.post(
    "http://localhost:8000/api/analyze",
    json={
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "monthly_amount": 100,
        "months": 24
    }
)
print(response.json())

# Analyze gold
response = requests.post(
    "http://localhost:8000/api/analyze/gold",
    json={
        "gold_symbol": "GLD",
        "monthly_amount": 100,
        "months": 24
    }
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Analyze multiple symbols
fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    symbols: ['AAPL', 'MSFT', 'GOOGL'],
    monthly_amount: 100,
    months: 24
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Smart DCA Strategy

The calculator uses intelligent buy signals based on:

1. **Moving Averages**: Price below MA20 or MA50
2. **RSI (Relative Strength Index)**: Oversold conditions
3. **Price Drops**: Significant 7-day or 30-day drops
4. **Budget Accumulation**: If no buy signal, budget accumulates for next month

Only buys when signal strength ≥ 40, ensuring quality entry points.

## Gold ETF Options

- **GLD**: SPDR Gold Shares (most liquid, ~$200/share)
- **IAU**: iShares Gold Trust (lower cost, ~$40/share)
- **SGOL**: abrdn Physical Gold Shares ETF (~$20/share)

## Error Handling

The API includes comprehensive error handling:
- Invalid symbols return 404
- Calculation errors return 500
- Validation errors return 422
- All errors include descriptive messages

## Development

### Code Structure

- **Models** (`app/models.py`): Pydantic models for request/response validation
- **Services**: Reusable business logic
  - `data_fetcher.py`: Fetches historical data from yfinance
  - `technical_analysis.py`: Calculates technical indicators
  - `dca_calculator.py`: Performs DCA calculations
- **Main** (`app/main.py`): FastAPI routes and endpoints

### Adding New Features

1. Add new service functions in `app/services/`
2. Create request/response models in `app/models.py`
3. Add endpoints in `app/main.py`
4. Update API documentation

## License

MIT

