# Strategy Agent - Data Interface Specification

## Input Data Interfaces

### 1. Indicator Data
**Path**: `../../Project/indicator/`
**Format**: JSON, CSV
**Update Frequency**: Real-time, Daily, Weekly, Monthly

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "symbol": "AAPL",
  "indicators": {
    "sma_20": 150.25,
    "ema_12": 151.30,
    "rsi": 65.4,
    "macd": 2.1,
    "bollinger_upper": 155.0,
    "bollinger_lower": 145.0,
    "volume": 50000000
  }
}
```

### 2. Market Data
**Path**: `../../Project/database/market_db/`
**Format**: Structured database format
**Update Frequency**: Real-time

```json
{
  "symbol": "AAPL",
  "timestamp": "2024-01-01T09:30:00Z",
  "ohlcv": {
    "open": 150.00,
    "high": 152.50,
    "low": 149.75,
    "close": 151.25,
    "volume": 1000000
  },
  "bid_ask": {
    "bid": 151.20,
    "ask": 151.30,
    "spread": 0.10
  }
}
```

### 3. Model Predictions
**Path**: `../../shared/models/`
**Format**: JSON
**Update Frequency**: On-demand

```json
{
  "model_id": "lstm_price_predictor_v1",
  "timestamp": "2024-01-01T10:00:00Z",
  "predictions": {
    "symbol": "AAPL",
    "price_direction": "UP",
    "confidence": 0.75,
    "price_target": 155.0,
    "time_horizon": "5d"
  }
}
```

### 4. Backtest Results
**Path**: `../../Project/database/backtest_db/`
**Format**: JSON, CSV
**Update Frequency**: After backtest completion

```json
{
  "strategy_id": "momentum_v2",
  "period": "2023-01-01_2023-12-31",
  "metrics": {
    "total_return": 0.15,
    "sharpe_ratio": 1.2,
    "max_drawdown": 0.08,
    "win_rate": 0.62
  }
}
```

## Output Data Interfaces

### 1. Trading Signals
**Path**: `../../Project/strategy/signals/`
**Format**: JSON
**Update Frequency**: Real-time

```json
{
  "signal_id": "SIG_20240101_001",
  "timestamp": "2024-01-01T10:15:00Z",
  "symbol": "AAPL",
  "action": "BUY",
  "strength": 0.8,
  "confidence": 0.75,
  "entry_price": 151.25,
  "stop_loss": 148.00,
  "take_profit": 156.00,
  "reasoning": "Strong momentum + RSI oversold reversal",
  "validity_period": "4h"
}
```

### 2. Position Sizing
**Path**: `../../Project/strategy/positions/`
**Format**: JSON
**Update Frequency**: Per signal generation

```json
{
  "position_id": "POS_20240101_001",
  "signal_id": "SIG_20240101_001",
  "symbol": "AAPL",
  "position_size": 100,
  "position_value": 15125.00,
  "risk_amount": 325.00,
  "portfolio_weight": 0.05,
  "risk_reward_ratio": 1.5
}
```

### 3. Strategy Reports
**Path**: `../../shared/communication/strategy_outputs/`
**Format**: Markdown, JSON
**Update Frequency**: Daily, Weekly

```json
{
  "report_id": "RPT_20240101",
  "date": "2024-01-01",
  "summary": {
    "signals_generated": 12,
    "positions_opened": 8,
    "positions_closed": 5,
    "daily_pnl": 1250.00,
    "success_rate": 0.75
  },
  "market_analysis": "Strong bullish momentum in tech sector...",
  "next_actions": ["Monitor earnings announcements", "Adjust position sizes"]
}
```

## Data Validation Rules

### Input Validation
- All timestamps must be in ISO 8601 format
- Numeric values must be within reasonable ranges
- Required fields must not be null or empty
- Data freshness: max 5 minutes old for real-time data

### Output Validation
- Signal strength must be between 0.0 and 1.0
- Position sizes must not exceed portfolio limits
- Risk amounts must not exceed daily risk budget
- All outputs must include timestamp and agent signature

## Error Handling

### Data Quality Issues
```json
{
  "error_type": "data_quality",
  "timestamp": "2024-01-01T10:00:00Z",
  "description": "Missing OHLCV data for AAPL",
  "severity": "HIGH",
  "action_taken": "Used last known values with staleness warning"
}
```

### Processing Errors
```json
{
  "error_type": "processing_error",
  "timestamp": "2024-01-01T10:00:00Z",
  "description": "Strategy calculation failed for momentum indicator",
  "severity": "CRITICAL",
  "action_taken": "Fallback to simple moving average strategy"
}
```

## Performance Metrics

### Throughput
- Target: 1000 signals processed per minute
- Latency: < 100ms per signal generation
- Uptime: 99.9% availability

### Data Quality
- Completeness: > 99.5%
- Accuracy: > 99.9%
- Timeliness: < 5 seconds delay