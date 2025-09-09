# Strategy Agent API Documentation

## Overview
The Strategy Agent provides APIs for signal generation, position sizing, and strategy management within the AIAgentProject trading system.

## Base URL
`internal://strategy-agent/api/v1`

## Authentication
- **Type**: Internal Agent Token
- **Header**: `X-Agent-Token: <agent_token>`
- **Scope**: Inter-agent communication only

## Endpoints

### 1. Signal Generation

#### Generate Trading Signal
```http
POST /signals/generate
Content-Type: application/json

{
  "symbol": "AAPL",
  "timeframe": "1D",
  "indicators": {
    "rsi": 65.4,
    "macd": 2.1,
    "sma_20": 150.25
  },
  "market_conditions": "BULLISH"
}
```

**Response:**
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
  "reasoning": "Strong momentum + RSI oversold reversal"
}
```

#### Get Signal History
```http
GET /signals/history?symbol={symbol}&days={days}
```

**Parameters:**
- `symbol` (optional): Stock symbol to filter
- `days` (optional): Number of days to look back (default: 7)

### 2. Position Management

#### Calculate Position Size
```http
POST /positions/calculate
Content-Type: application/json

{
  "signal_id": "SIG_20240101_001",
  "account_balance": 100000,
  "risk_percentage": 0.02,
  "entry_price": 151.25,
  "stop_loss": 148.00
}
```

**Response:**
```json
{
  "position_size": 100,
  "position_value": 15125.00,
  "risk_amount": 325.00,
  "portfolio_weight": 0.05
}
```

### 3. Strategy Management

#### Get Active Strategies
```http
GET /strategies/active
```

**Response:**
```json
{
  "strategies": [
    {
      "id": "momentum_v2",
      "name": "Momentum Strategy V2",
      "status": "ACTIVE",
      "performance": {
        "total_return": 0.12,
        "sharpe_ratio": 1.8,
        "max_drawdown": 0.06
      }
    }
  ]
}
```

#### Update Strategy Parameters
```http
PUT /strategies/{strategy_id}/parameters
Content-Type: application/json

{
  "signal_threshold": 0.8,
  "risk_tolerance": 0.015,
  "rebalance_frequency": "weekly"
}
```

### 4. Performance Analytics

#### Get Strategy Performance
```http
GET /performance?strategy_id={id}&period={period}
```

**Parameters:**
- `strategy_id`: Strategy identifier
- `period`: Time period (1d, 7d, 30d, 90d, 1y)

**Response:**
```json
{
  "strategy_id": "momentum_v2",
  "period": "30d",
  "metrics": {
    "total_return": 0.08,
    "sharpe_ratio": 1.5,
    "win_rate": 0.68,
    "max_drawdown": 0.04,
    "profit_factor": 1.8
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "INVALID_SIGNAL_DATA",
    "message": "Missing required indicator data",
    "timestamp": "2024-01-01T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

### Error Codes
- `400` - Bad Request: Invalid parameters
- `401` - Unauthorized: Invalid agent token
- `404` - Not Found: Resource not found
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Error: Processing failure

## Rate Limits
- Signal Generation: 100 requests/minute
- Position Calculation: 200 requests/minute  
- Strategy Management: 50 requests/minute
- Performance Queries: 1000 requests/minute

## Webhooks

### Signal Generated
**Event**: `signal.generated`
**Payload**:
```json
{
  "event": "signal.generated",
  "timestamp": "2024-01-01T10:15:00Z",
  "data": {
    "signal_id": "SIG_20240101_001",
    "symbol": "AAPL",
    "action": "BUY",
    "strength": 0.8
  }
}
```

### Strategy Status Change
**Event**: `strategy.status_changed`
**Payload**:
```json
{
  "event": "strategy.status_changed",
  "timestamp": "2024-01-01T10:00:00Z",
  "data": {
    "strategy_id": "momentum_v2",
    "old_status": "ACTIVE",
    "new_status": "PAUSED",
    "reason": "Risk threshold exceeded"
  }
}
```

## SDK Examples

### Python
```python
from aiagent_sdk import StrategyAgent

client = StrategyAgent(token="agent_token_123")

# Generate signal
signal = client.generate_signal(
    symbol="AAPL",
    indicators={"rsi": 65.4, "macd": 2.1}
)

# Calculate position
position = client.calculate_position(
    signal_id=signal.id,
    account_balance=100000,
    risk_percentage=0.02
)
```

### JavaScript
```javascript
const { StrategyAgent } = require('aiagent-sdk');

const client = new StrategyAgent({token: 'agent_token_123'});

// Generate signal
const signal = await client.generateSignal({
  symbol: 'AAPL',
  indicators: {rsi: 65.4, macd: 2.1}
});

// Get performance
const performance = await client.getPerformance({
  strategyId: 'momentum_v2',
  period: '30d'
});
```