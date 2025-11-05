# Automated Strategy Workflow - User Guide

**Version**: 1.0
**Last Updated**: 2025-11-05
**Status**: Production Ready

## Overview

The Automated Strategy Workflow allows you to generate, backtest, and analyze trading strategies by simply describing them in natural language. **No manual code writing or YAML editing required.**

### What You Can Do

1. **Describe your strategy in plain English**
2. **System automatically generates YAML strategy file**
3. **Backtest runs automatically** (no code changes needed)
4. **Comprehensive report generated** with insights and recommendations

### Workflow Diagram

```
Natural Language Description
           ↓
  [Strategy Generator]
     (LLM/Rule-based)
           ↓
    YAML Strategy File
     (Auto-generated)
           ↓
  [Strategy Validator]
    (JSON Schema)
           ↓
[Indicator Calculator]
 (Auto-calculation)
           ↓
   [Backtest Engine]
    (Execution)
           ↓
  [Report Generator]
  (Analysis & Insights)
           ↓
    Final Report
```

---

## Quick Start

### 1. Prepare Your Data

```python
import pandas as pd
from project.database.mongodb_operations import MongoDBOperations

# Load data from MongoDB
db = MongoDBOperations(db_address="MONGODB_LOCAL")

data = {}
for symbol in ['AAPL', 'MSFT', 'GOOGL']:
    df = db.execute_query(db_name="NasDataBase_D", collection_name=symbol)
    data[symbol] = df
```

### 2. Describe Your Strategy

```python
strategy_description = """
Buy when RSI is below 30 (oversold) and price is above 20-day SMA.
Sell at 10% profit target or use 3% initial stop with 5% risk unit stepped trailing.
Confirm entry with volume above 20-day average.
Use mean reversion approach.
"""
```

### 3. Run Automated Workflow

```python
from project.workflow.automated_strategy_workflow import AutomatedStrategyWorkflow

# Initialize workflow
workflow = AutomatedStrategyWorkflow()

# Run complete workflow
result = workflow.run_complete_workflow(
    strategy_description=strategy_description,
    data=data,
    strategy_name="My_RSI_Strategy",  # Optional - auto-generated if not provided
    author="Your Name",
    use_llm=False,  # Set to True to use LLM (if available)
    store_backtest=True,  # Store results in MongoDB
    save_report=True  # Save report to file
)

# Check results
if result['success']:
    print(f"Strategy saved to: {result['yaml_path']}")
    print(f"Total return: {result['backtest_result'].performance_metrics['total_return']:.2%}")
    print(f"\nFull Report:\n{result['report']}")
else:
    print(f"Workflow failed: {result['errors']}")
```

### 4. View Results

The workflow automatically:
- Generates YAML at: `config/strategies/{strategy_name}.yaml`
- Saves report at: `reports/report_{strategy_name}_{timestamp}.txt`
- Stores backtest in MongoDB (if `store_backtest=True`)
- Displays comprehensive report in console

---

## Strategy Description Format

### Natural Language Guidelines

The system can understand various description patterns. Here are examples:

#### Example 1: RSI Mean Reversion

```python
description = """
Buy when RSI is below 30 (oversold) and price is above 20-day SMA.
Volume should be above 20-day average for confirmation.
Exit at 10% profit or use 3% stepped trailing stop.
"""
```

**Extracted Strategy**:
- **Category**: Mean Reversion
- **Indicators**: RSI_14, SMA_20, Volume_SMA_20
- **Entry**: RSI < 30 AND Price > SMA_20 AND Volume > Volume_SMA_20
- **Exit**: 10% profit target, 3% stepped trailing stop

#### Example 2: MACD Trend Following

```python
description = """
Enter long when MACD crosses above signal line.
Confirm with volume above average.
Exit at 15% profit or when MACD crosses below signal line.
"""
```

**Extracted Strategy**:
- **Category**: Trend Following
- **Indicators**: MACD_12_26_9, Volume_SMA_20
- **Entry**: MACD crosses above Signal
- **Exit**: 15% profit or MACD crosses below Signal

#### Example 3: Moving Average Crossover

```python
description = """
Buy when price crosses above 20-day SMA.
Sell when price crosses below 20-day SMA or at 12% profit.
"""
```

**Extracted Strategy**:
- **Category**: Trend Following
- **Indicators**: SMA_20
- **Entry**: Price crosses above SMA_20
- **Exit**: 12% profit or Price crosses below SMA_20

### Supported Keywords

**Indicators**:
- `RSI`, `RSI-14`, `14-period RSI`
- `SMA`, `20-day SMA`, `SMA 20`
- `EMA`, `exponential moving average`
- `MACD`
- `ATR`, `average true range`
- `Volume`

**Conditions**:
- `above`, `below`, `>`, `<`, `crosses above`, `crosses below`
- `oversold`, `overbought`
- `confirm`, `confirmation`

**Strategy Types**:
- `mean reversion`, `reversal`
- `trend`, `trend following`, `momentum`
- `breakout`

**Exit Criteria**:
- `profit target`, `take profit`, `X% profit`
- `stop loss`, `trailing stop`, `stepped trailing`
- `exit when`, `sell when`

---

## Complete API Reference

### AutomatedStrategyWorkflow

```python
class AutomatedStrategyWorkflow:
    def __init__(
        self,
        strategy_output_dir: Optional[str] = None,  # Where to save YAML files
        report_output_dir: Optional[str] = None     # Where to save reports
    )
```

### run_complete_workflow()

```python
def run_complete_workflow(
    self,
    strategy_description: str,        # Natural language description
    data: Dict[str, pd.DataFrame],    # Market data {symbol: DataFrame}
    strategy_name: Optional[str] = None,  # Name (auto-generated if None)
    author: str = "Auto-Generated",   # Strategy author
    use_llm: bool = False,            # Use LLM for parsing
    store_backtest: bool = False,     # Store in MongoDB
    save_report: bool = True          # Save report to file
) -> Dict[str, Any]
```

**Returns**:
```python
{
    'success': True,
    'steps_completed': ['generation', 'validation', 'backtest', 'report'],
    'errors': [],
    'yaml_path': 'config/strategies/My_Strategy.yaml',
    'backtest_result': BacktestResult(...),
    'report': '... formatted report text ...',
    'execution_time': 0.24
}
```

### run_from_existing_yaml()

```python
def run_from_existing_yaml(
    self,
    yaml_path: str,                   # Path to existing YAML
    data: Dict[str, pd.DataFrame],    # Market data
    store_backtest: bool = False,     # Store in MongoDB
    save_report: bool = True          # Save report to file
) -> Dict[str, Any]
```

Use this if you already have a YAML strategy file and want to re-run backtest.

---

## Report Structure

The generated report includes:

### 1. Executive Summary
- Execution time
- Total trades
- Initial capital
- Final value
- Total return

### 2. Performance Metrics
- **Returns**: Total, Annualized, Benchmark, Alpha
- **Risk-Adjusted**: Sharpe Ratio, Sortino Ratio, Calmar Ratio
- **Risk**: Max Drawdown, Volatility, VaR
- **Efficiency**: Win Rate, Profit Factor, Win/Loss Ratio

### 3. Trade Analysis
- Trade count (total, winning, losing)
- Average win/loss
- Largest win/loss
- Holding periods

### 4. Risk Analysis
- Drawdown analysis
- Exposure metrics
- Capital efficiency

### 5. Individual Trade Details
- Sample trades with entry/exit dates and prices
- Profit/loss for each trade
- Days held

### 6. Key Insights
- Automated recommendations
- Performance assessment
- Risk warnings
- Suggestions for improvement

### Example Report

```
================================================================================
STRATEGY BACKTEST REPORT
================================================================================

Strategy: RSI_Mean_Reversion_Auto
Generated: 2025-11-05 11:24:44

================================================================================
EXECUTIVE SUMMARY
================================================================================

Execution Time: 0.23s
Total Trades: 15
Initial Capital: $100,000,000.00
Final Value: $110,500,000.00
Total Return: 10.50%

================================================================================
PERFORMANCE METRICS
================================================================================

Returns:
  Total Return:           10.50%
  Annualized Return:      42.00%
  Benchmark Return:        8.00%
  Alpha:                   2.50%

Risk-Adjusted Metrics:
  Sharpe Ratio:            1.85
  Sortino Ratio:           2.10
  Calmar Ratio:            3.50

Risk Metrics:
  Max Drawdown:           -5.20%
  Volatility (Annual):    22.70%
  VaR (95%):             -2.30%

Efficiency:
  Win Rate:               66.67%
  Profit Factor:           2.15
  Average Win/Loss:        1.85

...

================================================================================
KEY INSIGHTS
================================================================================

[POSITIVE] Strong performance with >15% total return
[POSITIVE] Excellent risk-adjusted returns (Sharpe > 2)
[POSITIVE] High win rate (66.7%)
[POSITIVE] Small drawdown (5.2%) - low risk
```

---

## Advanced Usage

### Batch Processing Multiple Strategies

```python
workflow = AutomatedStrategyWorkflow()

strategies_to_test = [
    {
        'name': 'RSI_Mean_Reversion',
        'description': 'Buy when RSI < 30 and price > SMA_20. Sell at 10% profit.'
    },
    {
        'name': 'MACD_Trend',
        'description': 'Buy when MACD crosses above signal. Sell at 15% profit.'
    },
    {
        'name': 'SMA_Crossover',
        'description': 'Buy when price > SMA_20. Sell when price < SMA_20 or 12% profit.'
    }
]

results = []
for strat in strategies_to_test:
    result = workflow.run_complete_workflow(
        strategy_description=strat['description'],
        data=data,
        strategy_name=strat['name'],
        save_report=True
    )
    results.append({
        'name': strat['name'],
        'success': result['success'],
        'return': result['backtest_result'].performance_metrics.get('total_return', 0) if result['success'] else 0,
        'sharpe': result['backtest_result'].performance_metrics.get('sharpe_ratio', 0) if result['success'] else 0
    })

# Compare strategies
for r in sorted(results, key=lambda x: x['sharpe'], reverse=True):
    print(f"{r['name']:<30} Return: {r['return']:>8.2%}  Sharpe: {r['sharpe']:>6.2f}")
```

### Re-running Existing Strategy

```python
# You already have a YAML file from previous generation
yaml_path = "config/strategies/RSI_Mean_Reversion_Auto.yaml"

# Load new data (e.g., updated time period)
data_new = load_latest_market_data()

# Re-run backtest
result = workflow.run_from_existing_yaml(
    yaml_path=yaml_path,
    data=data_new,
    save_report=True
)
```

### Custom Output Directories

```python
workflow = AutomatedStrategyWorkflow(
    strategy_output_dir="C:/MyStrategies",
    report_output_dir="C:/MyReports"
)
```

---

## Understanding Generated YAML

The system automatically creates a complete YAML strategy file. Here's what it looks like:

```yaml
strategy:
  name: "RSI_Mean_Reversion_Auto"
  version: "1.0"
  author: "Auto-Generated"
  created: "2025-11-05"
  description: |
    Buy when RSI is below 30 (oversold) and price is above 20-day SMA.
    Sell at 10% profit target or use 3% initial stop with 5% risk unit stepped trailing.
  category: "mean_reversion"
  market_type: "stocks"
  timeframe: "daily"

indicators:
  - name: "RSI"
    parameters:
      period: 14
    output_column: "RSI_14"
    description: "RSI indicator with period 14"

  - name: "SMA"
    parameters:
      period: 20
    output_column: "SMA_20"
    description: "Simple Moving Average with period 20"

  - name: "Volume_SMA"
    parameters:
      period: 20
    output_column: "Volume_SMA_20"

entry:
  conditions:
    - group: "entry_signals"
      operator: "AND"
      rules:
        - indicator: "RSI_14"
          operator: "<"
          value: 30
          description: "RSI below 30"

        - indicator: "close"
          operator: ">"
          reference: "SMA_20"
          description: "Price above SMA_20"

        - indicator: "volume"
          operator: ">"
          reference: "Volume_SMA_20"
          description: "Volume above average"

  logic: "entry_signals"

exit:
  profit_target:
    enabled: true
    type: "percentage"
    value: 0.1

  stop_loss:
    enabled: true
    type: "stepped_trailing"
    initial_stop: 0.03
    risk_unit: 0.05

risk_management:
  initial_capital: 100000000.0
  max_portfolio_risk: 0.2
  max_position_size: 0.1
  position_sizing:
    method: "risk_parity"
    base_risk: 0.05
```

You can manually edit this YAML file if needed, then re-run with `run_from_existing_yaml()`.

---

## Data Requirements

### Input Data Format

```python
data = {
    'SYMBOL': pd.DataFrame({
        'open': [...],
        'high': [...],
        'low': [...],
        'close': [...],
        'volume': [...]
    }, index=pd.DatetimeIndex([...]))
}
```

**Requirements**:
- Dictionary of DataFrames (one per symbol)
- Each DataFrame must have DatetimeIndex
- Required columns: `open`, `high`, `low`, `close`, `volume`
- No NaN values in OHLCV columns

### Loading from MongoDB

```python
from project.database.mongodb_operations import MongoDBOperations

db = MongoDBOperations(db_address="MONGODB_LOCAL")

# Load single symbol
df = db.execute_query(db_name="NasDataBase_D", collection_name="AAPL")

# Load multiple symbols
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
data = {symbol: db.execute_query("NasDataBase_D", symbol) for symbol in symbols}
```

---

## Troubleshooting

### Issue: "No trades executed"

**Cause**: Strategy conditions are never met with the provided data.

**Solutions**:
1. Adjust thresholds in description (e.g., "RSI < 35" instead of "RSI < 30")
2. Use longer time periods (more data = more opportunities)
3. Test with more symbols
4. Check if data is valid (no NaN, correct date range)

### Issue: "Strategy validation failed"

**Cause**: Generated YAML doesn't match schema requirements.

**Solutions**:
1. Check the error message for specific issues
2. Make description more explicit (mention specific periods: "14-period RSI")
3. Use simpler descriptions with clear keywords
4. Manually edit the generated YAML file if needed

### Issue: "Indicator not found"

**Cause**: Auto-calculation didn't recognize the indicator.

**Solutions**:
1. Ensure indicators are properly spelled in description
2. Use standard names: "RSI", "SMA", "EMA", "MACD", "ATR"
3. Include periods: "20-day SMA" or "RSI 14"

### Issue: "LLM not available"

**Cause**: LLM integration not configured (optional feature).

**Solutions**:
1. Use `use_llm=False` (default) - rule-based parsing works well
2. Or configure LLM API credentials if you want LLM-based parsing

---

## Best Practices

### Strategy Description

1. **Be Specific**: Include exact numbers and periods
   - Good: "Buy when RSI-14 is below 30"
   - Bad: "Buy when RSI is oversold"

2. **One Strategy at a Time**: Don't mix multiple strategies
   - Good: Focus on RSI mean reversion OR MACD trend
   - Bad: "Use RSI for stocks and MACD for ETFs..."

3. **Clear Exit Rules**: Specify profit targets and stop losses
   - Good: "Exit at 10% profit or 3% stop loss"
   - Bad: "Exit when appropriate"

4. **Include Confirmations**: Add volume or other filters
   - Good: "Confirm with volume above 20-day average"
   - Bad: Just entry conditions without confirmation

### Testing

1. **Start Simple**: Test with 2-3 symbols first
2. **Use Sufficient Data**: At least 1 year (252 trading days)
3. **Out-of-Sample Testing**: Test on different time periods
4. **Compare Multiple Strategies**: Generate and test variations

### Performance Evaluation

Focus on these metrics:
- **Sharpe Ratio > 1.0**: Good risk-adjusted returns
- **Max Drawdown < 20%**: Acceptable risk level
- **Win Rate > 50%**: More wins than losses
- **Profit Factor > 1.5**: Winners bigger than losers

---

## Integration with Existing System

The Automated Workflow integrates seamlessly with existing components:

### Phase 1-4 Integration

```
Phase 1: Strategy Infrastructure (LoadedStrategy, Validator)
           ↓
Phase 2: Strategy Execution (YAMLStrategyExecutor)
           ↓
Phase 3: Indicator Auto-Calculation (IndicatorCalculator)
           ↓
Phase 4: Advanced Features (Combiner, Optimizer)
           ↓
    Automated Workflow (End-to-End Automation)
```

### Using with Strategy Combiner

```python
from project.strategy.strategy_combiner import StrategyCombiner, CombinationMethod

# Generate multiple strategies
workflow = AutomatedStrategyWorkflow()

strategies_descriptions = [
    "Buy when RSI < 30 and price > SMA_20. Exit at 10% profit.",
    "Buy when MACD crosses above signal. Exit at 15% profit.",
    "Buy when price > SMA_50. Exit at 12% profit."
]

yaml_paths = []
for i, desc in enumerate(strategies_descriptions):
    result = workflow.run_complete_workflow(
        strategy_description=desc,
        data=data,
        strategy_name=f"Strategy_{i+1}",
        save_report=False
    )
    if result['success']:
        yaml_paths.append(result['yaml_path'])

# Combine generated strategies
combiner = StrategyCombiner()
strategies, _ = combiner.load_strategies(yaml_paths)

combined_result = combiner.combine_strategies(
    strategies=strategies,
    data=data,
    method=CombinationMethod.AND,  # All must agree
    calculate_indicators=True
)
```

---

## Example Scripts

### Script 1: Quick Test

```python
"""Quick strategy test script"""

from project.workflow.automated_strategy_workflow import AutomatedStrategyWorkflow
from project.database.mongodb_operations import MongoDBOperations

# Load data
db = MongoDBOperations(db_address="MONGODB_LOCAL")
data = {
    'AAPL': db.execute_query("NasDataBase_D", "AAPL"),
    'MSFT': db.execute_query("NasDataBase_D", "MSFT")
}

# Define strategy
description = """
Buy when RSI is below 30 and price is above 20-day SMA.
Exit at 10% profit or 3% stop loss.
"""

# Run workflow
workflow = AutomatedStrategyWorkflow()
result = workflow.run_complete_workflow(
    strategy_description=description,
    data=data,
    strategy_name="Quick_Test",
    save_report=True
)

print(f"Success: {result['success']}")
if result['success']:
    perf = result['backtest_result'].performance_metrics
    print(f"Return: {perf['total_return']:.2%}")
    print(f"Sharpe: {perf['sharpe_ratio']:.2f}")
```

### Script 2: Strategy Comparison

```python
"""Compare multiple strategy variations"""

from project.workflow.automated_strategy_workflow import AutomatedStrategyWorkflow

workflow = AutomatedStrategyWorkflow()

# Test different RSI thresholds
thresholds = [25, 30, 35]
results = []

for threshold in thresholds:
    description = f"""
    Buy when RSI is below {threshold} and price is above 20-day SMA.
    Exit at 10% profit or 3% stop loss.
    """

    result = workflow.run_complete_workflow(
        strategy_description=description,
        data=data,
        strategy_name=f"RSI_{threshold}",
        save_report=False
    )

    if result['success']:
        perf = result['backtest_result'].performance_metrics
        results.append({
            'threshold': threshold,
            'return': perf['total_return'],
            'sharpe': perf['sharpe_ratio'],
            'max_dd': perf['max_drawdown']
        })

# Print comparison
print("Strategy Comparison:")
print(f"{'Threshold':<12} {'Return':<10} {'Sharpe':<10} {'Max DD':<10}")
for r in results:
    print(f"{r['threshold']:<12} {r['return']:<10.2%} {r['sharpe']:<10.2f} {r['max_dd']:<10.2%}")
```

---

## Support

### Documentation
- **Interface Spec**: `docs/interfaces/STRATEGY_YAML_INTERFACE.md`
- **Main README**: `docs/YAML_STRATEGY_README.md`
- **Code Quality**: `docs/rules/CODE_QUALITY.md`

### Components
- **StrategyGenerator**: `project/strategy/strategy_generator.py`
- **AutomatedWorkflow**: `project/workflow/automated_strategy_workflow.py`
- **ReportGenerator**: `project/reporting/strategy_report_generator.py`

### Testing
- **Automated Workflow Test**: `Test/test_automated_workflow.py`
- **E2E Test**: `Test/test_complete_e2e_workflow.py`

---

## Conclusion

The Automated Strategy Workflow provides a complete, code-free solution for:

✅ **Natural Language → Strategy**: Describe in plain English
✅ **Auto-Generation**: YAML created automatically
✅ **Auto-Validation**: Schema checking
✅ **Auto-Indicators**: Missing indicators calculated
✅ **Auto-Backtest**: Complete backtest execution
✅ **Auto-Report**: Comprehensive analysis and insights

**No manual YAML editing. No code changes. Just describe and run.**

---

**System Version**: 1.0
**Status**: Production Ready
**Last Tested**: 2025-11-05
**Test Status**: All core features operational
