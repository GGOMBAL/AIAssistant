# Report Layer Modules Documentation

## Overview

The Report Layer consists of three main modules that work together to provide comprehensive trading analysis and reporting capabilities.

## Module Structure

```
project/reporting/
├── pl_analyzer.py          # Profit/Loss Analysis
├── balance_analyzer.py     # Balance Evolution Analysis
└── gap_analyzer.py         # Backtest vs Live Comparison (Future)
```

---

## 1. P/L Analyzer Module

### Purpose
Analyzes trading performance by calculating profit/loss metrics, win rates, and risk-reward ratios from trading history.

### Location
`project/reporting/pl_analyzer.py`

### Main Class: `PLAnalyzer`

#### Key Methods

##### `analyze_trades(order_history: pd.DataFrame) -> Dict[str, Any]`
Main analysis method that generates comprehensive P/L report.

**Parameters:**
- `order_history`: DataFrame with trading history

**Returns:**
- Dictionary containing:
  - `summary`: Overall trading statistics
  - `performance_metrics`: Detailed performance metrics
  - `trade_distribution`: P/L and holding period distributions
  - `time_analysis`: Performance by time periods
  - `ticker_performance`: Performance by ticker
  - `risk_metrics`: Risk-related metrics
  - `streak_analysis`: Winning/losing streak analysis

**Example Usage:**
```python
from project.reporting.pl_analyzer import PLAnalyzer

analyzer = PLAnalyzer()
report = analyzer.analyze_trades(order_history_df)

# Access specific metrics
win_rate = report['summary']['win_rate']
sharpe_ratio = report['performance_metrics']['sharpe_ratio']
max_drawdown = report['risk_metrics']['max_drawdown']
```

##### `_calculate_closed_positions(order_history: pd.DataFrame) -> pd.DataFrame`
Matches buy and sell orders using FIFO to calculate closed position P/L.

**Internal Method - Key Logic:**
- Uses FIFO (First In, First Out) matching
- Calculates gross and net P/L per position
- Tracks holding periods
- Handles partial fills

##### `generate_text_report() -> str`
Generates formatted text report from analysis results.

**Returns:**
- Formatted string report with tables and statistics

#### Key Metrics Calculated

1. **Summary Statistics**
   - Total trades, winning/losing trades
   - Win rate percentage
   - Total and average P/L
   - Best/worst trades

2. **Performance Metrics**
   - Risk-reward ratio
   - Profit factor
   - Expectancy
   - Sharpe ratio
   - Skewness and kurtosis

3. **Risk Metrics**
   - Maximum drawdown
   - Value at Risk (VaR)
   - Conditional VaR
   - Recovery factor

4. **Distribution Analysis**
   - P/L distribution by bins
   - Holding period distribution
   - Performance by ticker
   - Monthly/daily performance

---

## 2. Balance Analyzer Module

### Purpose
Tracks and analyzes account balance evolution over time, including cash utilization, portfolio value, and health indicators.

### Location
`project/reporting/balance_analyzer.py`

### Main Class: `BalanceAnalyzer`

#### Key Methods

##### `analyze_balance_history(order_history: pd.DataFrame, market_prices: Optional[pd.DataFrame]) -> Dict[str, Any]`
Analyzes account balance evolution from trading history.

**Parameters:**
- `order_history`: DataFrame with trading history
- `market_prices`: Optional current market prices for portfolio valuation

**Returns:**
- Dictionary containing:
  - `summary`: Balance summary statistics
  - `growth_metrics`: Growth and performance metrics
  - `volatility_metrics`: Volatility and risk metrics
  - `drawdown_analysis`: Drawdown periods and recovery
  - `cash_utilization`: Cash usage patterns
  - `period_analysis`: Performance by time periods
  - `milestone_analysis`: Achievement milestones
  - `health_indicators`: Account health score and recommendations
  - `forecast`: Statistical projections

**Example Usage:**
```python
from project.reporting.balance_analyzer import BalanceAnalyzer

analyzer = BalanceAnalyzer(initial_balance=100000)
report = analyzer.analyze_balance_history(order_history_df, market_prices_df)

# Access health indicators
health_score = report['health_indicators']['health_score']
risk_level = report['health_indicators']['risk_level']
recommendations = report['health_indicators']['recommended_actions']
```

##### `_calculate_daily_balance(order_history: pd.DataFrame, market_prices: Optional[pd.DataFrame]) -> pd.DataFrame`
Calculates daily account balance including cash and portfolio positions.

**Internal Method - Key Logic:**
- Tracks cash balance changes from trades
- Maintains position inventory
- Calculates portfolio value using market prices
- Computes daily returns and cumulative metrics

##### `_calculate_health_score(...) -> float`
Calculates overall account health score (0-100).

**Scoring Components:**
- Cash cushion (25 points)
- Trend strength (25 points)
- Drawdown severity (25 points)
- Base score (25 points)

##### `generate_text_report() -> str`
Generates formatted text report from balance analysis.

#### Key Features

1. **Balance Tracking**
   - Daily balance calculation
   - Cash vs invested percentage
   - Portfolio value evolution
   - Position count tracking

2. **Growth Analysis**
   - CAGR (Compound Annual Growth Rate)
   - Annualized returns
   - Monthly/quarterly performance
   - YTD returns

3. **Volatility Analysis**
   - Daily and annual volatility
   - Sortino ratio
   - Downside deviation
   - Rolling volatility metrics

4. **Drawdown Analysis**
   - Maximum drawdown detection
   - Drawdown periods identification
   - Recovery time calculation
   - Current drawdown status

5. **Health Indicators**
   - Health score (0-100)
   - Risk level assessment
   - Trend analysis
   - Automated recommendations

6. **Forecasting**
   - Statistical projections (30, 90, 180, 365 days)
   - Confidence intervals
   - Monte Carlo simulation (simplified)

---

## 3. GAP Analyzer Module (Future Implementation)

### Purpose
Analyzes discrepancies between backtesting results and live trading performance.

### Location
`project/reporting/gap_analyzer.py`

### Status
**STUB IMPLEMENTATION** - Placeholder for future development

### Main Class: `GAPAnalyzer`

#### Planned Features

##### `analyze_gaps(backtest_orders: pd.DataFrame, live_orders: pd.DataFrame) -> Dict[str, Any]`
Will analyze differences between backtest and live trading.

**Planned Analysis:**
- Slippage analysis
- Execution timing comparison
- Commission impact
- Market impact measurement
- Signal fidelity tracking
- Performance attribution

##### `analyze_slippage(...)`
Will calculate price differences between expected and actual execution.

##### `analyze_market_impact(...)`
Will measure the impact of trades on market prices.

##### `calculate_implementation_shortfall(...)`
Will calculate total execution costs including implicit costs.

**Example Future Usage:**
```python
from project.reporting.gap_analyzer import GAPAnalyzer

analyzer = GAPAnalyzer()
gap_report = analyzer.analyze_gaps(backtest_df, live_df)

# Will provide insights on:
# - Why live performance differs from backtest
# - Areas for strategy improvement
# - Execution quality metrics
```

---

## Module Integration

### How Modules Work Together

```python
# Report Agent integrates all modules
from project.reporting.pl_analyzer import PLAnalyzer
from project.reporting.balance_analyzer import BalanceAnalyzer
from project.reporting.gap_analyzer import GAPAnalyzer

class ReportAgent:
    def __init__(self):
        self.pl_analyzer = PLAnalyzer()
        self.balance_analyzer = BalanceAnalyzer()
        self.gap_analyzer = GAPAnalyzer()

    def generate_comprehensive_report(self, order_history, market_prices=None):
        # Combines analysis from all modules
        pl_analysis = self.pl_analyzer.analyze_trades(order_history)
        balance_analysis = self.balance_analyzer.analyze_balance_history(
            order_history, market_prices
        )

        # Generate insights based on combined analysis
        return {
            'pl_analysis': pl_analysis,
            'balance_analysis': balance_analysis,
            'insights': self._generate_insights(...),
            'recommendations': self._generate_recommendations(...)
        }
```

---

## Common Utilities

### Shared Functions

#### Date/Time Handling
- ISO format conversion
- Period aggregation (daily, monthly, quarterly)
- Trading day calculations

#### Statistical Calculations
- Sharpe ratio calculation
- Drawdown computation
- Value at Risk (VaR)
- Moving averages

#### Data Validation
- DataFrame structure validation
- Required columns checking
- Data type verification

---

## Performance Optimization

### Caching Strategy
- Reports cached for 60 minutes
- Intermediate calculations cached
- DataFrame operations optimized

### Large Dataset Handling
- Batch processing for >10,000 trades
- Chunked analysis for memory efficiency
- Parallel processing capability (future)

---

## Error Handling

### Common Error Patterns

1. **Empty Data Handling**
```python
if order_history.empty:
    return self._empty_report()
```

2. **Missing Columns**
```python
missing_columns = [col for col in required_columns
                  if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")
```

3. **Division by Zero**
```python
profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
```

---

## Testing Guidelines

### Unit Tests
Each module should have corresponding tests:
- `test_pl_analyzer.py`
- `test_balance_analyzer.py`
- `test_gap_analyzer.py`

### Test Coverage Areas
1. Normal operation with valid data
2. Edge cases (empty data, single trade)
3. Error conditions
4. Performance with large datasets

### Sample Test Data
```python
# Minimal test dataset
test_orders = pd.DataFrame({
    'ticker': ['AAPL', 'AAPL'],
    'order_type': ['BUY', 'SELL'],
    'order_date': pd.date_range('2024-01-01', periods=2),
    'execution_price': [150.0, 155.0],
    'quantity': [100, 100],
    'commission': [1.0, 1.0]
})
```

---

## Future Enhancements

### Planned Improvements

1. **Enhanced Analytics**
   - Machine learning insights
   - Pattern recognition
   - Anomaly detection

2. **Real-time Processing**
   - Streaming analysis
   - Live dashboard updates
   - Alert generation

3. **Multi-Strategy Support**
   - Strategy comparison
   - Portfolio attribution
   - Cross-strategy correlations

4. **Advanced Visualizations**
   - Interactive charts
   - HTML report generation
   - PDF export capability

---

## Maintenance Notes

### Update Frequency
- Bug fixes: As needed
- Feature updates: Monthly
- Documentation: With each change

### Backward Compatibility
- Maintain interface stability
- Deprecate features gracefully
- Version all breaking changes

### Dependencies
- Keep dependencies minimal
- Use standard libraries when possible
- Document all external requirements

---

## Contact and Support

**Module Owner**: Report Agent Team
**Primary Contact**: Via Orchestrator Agent
**Documentation**: This file and REPORT_LAYER_INTERFACE.md
**Source Code**: `project/reporting/`