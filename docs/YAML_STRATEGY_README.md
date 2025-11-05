# YAML Strategy Discovery System - User Guide

**Version**: 1.0
**Last Updated**: 2025-11-05
**Status**: Production Ready

## Overview

The YAML Strategy Discovery System allows you to define, execute, and optimize trading strategies using simple YAML configuration files. No Python coding required for strategy definition.

### Key Features

- **YAML-Based Strategy Definition**: Define complete strategies in YAML
- **Automatic Indicator Calculation**: Missing indicators calculated automatically
- **Backtest Integration**: Seamless integration with backtest engine
- **Strategy Combination**: Combine multiple strategies (AND/OR/WEIGHTED/MAJORITY)
- **Parameter Optimization**: Grid search for optimal parameters
- **Zero Configuration**: Supply OHLCV data, get results

### System Architecture

```
YAML Strategy File
    |
    v
YAMLStrategyLoader (Parse & Validate)
    |
    v
IndicatorCalculator (Auto-calculate missing indicators)
    |
    v
YAMLStrategyExecutor (Generate entry/exit signals)
    |
    v
YAMLBacktestService (Run backtest)
    |
    v
Results (Trades, Performance, Statistics)
```

---

## Installation

### Prerequisites

- Python 3.8+
- MongoDB (for storing results)
- Required packages (install via pip)

### Setup

```bash
# Navigate to project directory
cd C:\WorkSpace\AIAgentProject\AIAssistant

# Install dependencies (if not already installed)
pip install pandas numpy pyyaml jsonschema pymongo

# Verify MongoDB is running
# MongoDB should be running on localhost:27017 (default)
```

---

## Quick Start

### 1. Create Your First Strategy

Create a YAML file: `config/strategies/my_strategy.yaml`

```yaml
strategy:
  name: "My_First_Strategy"
  version: "1.0"
  author: "Your Name"
  created: "2025-11-05"
  description: |
    Simple RSI mean reversion strategy
  category: "mean_reversion"
  market_type: "stocks"
  timeframe: "daily"

indicators:
  - name: "RSI"
    parameters:
      period: 14
    output_column: "RSI_14"

entry:
  conditions:
    - group: "oversold"
      operator: "AND"
      rules:
        - indicator: "RSI_14"
          operator: "<"
          value: 30
          description: "RSI oversold"

  logic: "oversold"

exit:
  profit_target:
    enabled: true
    type: "percentage"
    value: 0.10  # 10% profit target

  stop_loss:
    enabled: true
    type: "stepped_trailing"
    initial_stop: 0.03
    risk_unit: 0.05

risk_management:
  initial_capital: 100000000.0
  max_portfolio_risk: 0.20
  max_position_size: 0.10
```

### 2. Run Your Strategy

```python
from project.service.yaml_backtest_service import YAMLBacktestService
import pandas as pd

# Load your market data
data = {
    'AAPL': pd.DataFrame({...}),  # Your OHLCV data
    'MSFT': pd.DataFrame({...})
}

# Initialize service
service = YAMLBacktestService()

# Run backtest
results = service.backtest_from_file(
    yaml_path="config/strategies/my_strategy.yaml",
    data=data,
    store_results=True  # Store in MongoDB
)

# View results
if results['success']:
    print(f"Total trades: {len(results['backtest_result'].trades)}")
    print(f"Total return: {results['backtest_result'].performance_metrics['total_return']:.2%}")
    print(f"Sharpe ratio: {results['backtest_result'].performance_metrics['sharpe_ratio']:.2f}")
```

### 3. Run Test Example

```bash
# Run complete E2E test
python Test/test_complete_e2e_workflow.py
```

---

## Phase-by-Phase Usage

### Phase 1: Strategy Definition

**Purpose**: Define strategies in YAML format

**Files**:
- Strategy YAML: `config/strategies/{strategy_name}.yaml`
- Schema: `config/schemas/strategy_schema.json`

**Example**:
```python
from project.strategy.yaml_strategy_loader import YAMLStrategyLoader

loader = YAMLStrategyLoader()
success, strategy, errors = loader.load_from_file("config/strategies/my_strategy.yaml")

if success:
    print(f"Loaded: {strategy.name} v{strategy.version}")
    print(f"Required indicators: {strategy.get_indicator_names()}")
else:
    print(f"Errors: {errors}")
```

**Key Classes**:
- `YAMLStrategyLoader`: Parse YAML files
- `LoadedStrategy`: Strategy data structure
- `StrategyValidator`: JSON schema validation

---

### Phase 2: Strategy Execution

**Purpose**: Execute strategies and generate trading signals

**Example**:
```python
from project.strategy.yaml_strategy_executor import YAMLStrategyExecutor

executor = YAMLStrategyExecutor()

# Execute strategy on market data
results = executor.execute_strategy(
    strategy=strategy,
    data=data,
    calculate_indicators=True  # Auto-calculate missing indicators
)

# Access signals
for symbol in results['symbols']:
    signal_data = results['signals'][symbol]

    if 'error' not in signal_data:
        entry_signals = signal_data['entry']  # Boolean Series
        exit_signals = signal_data['exit']['signal_exit']  # Boolean Series

        print(f"{symbol}: {entry_signals.sum()} entry signals")
```

**Key Features**:
- Entry/exit signal generation
- Filter evaluation
- Multi-symbol parallel execution
- Automatic indicator calculation

---

### Phase 3: Indicator Auto-Calculation

**Purpose**: Automatically calculate missing technical indicators

**Example**:
```python
from project.indicator.indicator_calculator import IndicatorCalculator

calculator = IndicatorCalculator()

# Data with only OHLCV columns
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# Calculate missing indicators
required = ['RSI_14', 'SMA_20', 'MACD_12_26_9']
df_updated, calculated = calculator.calculate_missing_indicators(
    df, required, inplace=True
)

print(f"Calculated: {calculated}")
# Output: Calculated: ['RSI_14', 'SMA_20', 'MACD_12_26_9']
```

**Supported Indicators**:

| Category | Indicators |
|----------|-----------|
| Momentum | RSI, MACD |
| Trend | SMA, EMA, Rolling High/Low |
| Volatility | ATR, Bollinger Bands |
| Volume | Volume SMA |

**Naming Convention**:
- `RSI_14` = RSI with period 14
- `SMA_20` = SMA with period 20
- `MACD_12_26_9` = MACD with fast=12, slow=26, signal=9
- `ATR_14` = ATR with period 14

---

### Phase 4: Advanced Features

#### Strategy Combination

**Purpose**: Combine multiple strategies for better signals

**Example**:
```python
from project.strategy.strategy_combiner import StrategyCombiner, CombinationMethod

combiner = StrategyCombiner()

# Load multiple strategies
strategies, errors = combiner.load_strategies([
    "config/strategies/rsi_strategy.yaml",
    "config/strategies/macd_strategy.yaml",
    "config/strategies/bb_strategy.yaml"
])

# Combine using AND method (all must agree)
results = combiner.combine_strategies(
    strategies=strategies,
    data=data,
    method=CombinationMethod.AND,
    calculate_indicators=True
)

# Access combined signals
for symbol, signal_data in results['combined_signals'].items():
    entry = signal_data['entry']
    print(f"{symbol}: {signal_data['total_entry_signals']} combined signals")
```

**Combination Methods**:

| Method | Description | Use Case |
|--------|-------------|----------|
| AND | All strategies must agree | Conservative, high confidence |
| OR | Any strategy can signal | Aggressive, catch all opportunities |
| WEIGHTED | Weighted voting (custom weights) | Prioritize certain strategies |
| MAJORITY | Majority vote (>50%) | Balanced approach |

**Weighted Example**:
```python
results = combiner.combine_strategies(
    strategies=strategies,
    data=data,
    method=CombinationMethod.WEIGHTED,
    weights=[0.5, 0.3, 0.2],  # Must sum to 1.0
    calculate_indicators=True
)
```

#### Parameter Optimization

**Purpose**: Find optimal strategy parameters using grid search

**Example**:
```python
from project.strategy.parameter_optimizer import ParameterOptimizer

optimizer = ParameterOptimizer(max_workers=4)

# Define parameter search space
parameter_ranges = {
    # RSI oversold threshold
    'entry.conditions.0.rules.0.value': [25, 30, 35],

    # RSI period
    'indicators.0.parameters.period': [10, 14, 20],

    # Profit target
    'exit.profit_target.value': [0.08, 0.10, 0.12]
}

# Run optimization
results = optimizer.optimize(
    yaml_path="config/strategies/rsi_strategy.yaml",
    data=data,
    parameter_ranges=parameter_ranges,
    optimization_metric='sharpe_ratio',
    top_n=10
)

# Get best parameters
best_params = results['best_parameters']
best_sharpe = results['best_performance']['sharpe_ratio']

print(f"Best Sharpe Ratio: {best_sharpe:.2f}")
print(f"Best Parameters: {best_params}")

# Create optimized YAML file
optimizer.create_optimized_yaml(
    base_yaml_path="config/strategies/rsi_strategy.yaml",
    optimal_parameters=best_params,
    output_path="config/strategies/rsi_optimized.yaml"
)
```

**Optimization Metrics**:
- `sharpe_ratio`: Risk-adjusted returns (default)
- `total_return`: Absolute returns
- `max_drawdown`: Maximum loss from peak (lower is better)
- `win_rate`: Percentage of winning trades

**Parameter Path Format**:
- Dot-separated nested path
- Use integer indices for lists
- Examples:
  - `entry.conditions.0.rules.0.value`
  - `indicators.0.parameters.period`
  - `exit.profit_target.value`

---

## Complete Workflow Example

```python
"""
Complete workflow: Load strategy, optimize, backtest, analyze
"""

from project.strategy.yaml_strategy_loader import YAMLStrategyLoader
from project.strategy.parameter_optimizer import ParameterOptimizer
from project.service.yaml_backtest_service import YAMLBacktestService
import pandas as pd

# ========================================
# Step 1: Load Strategy
# ========================================
loader = YAMLStrategyLoader()
success, strategy, errors = loader.load_from_file("config/strategies/my_strategy.yaml")

if not success:
    print(f"Failed to load strategy: {errors}")
    exit(1)

print(f"Loaded: {strategy.name} v{strategy.version}")

# ========================================
# Step 2: Prepare Data
# ========================================
# Load your market data (OHLCV)
data = {
    'AAPL': pd.DataFrame({...}),
    'MSFT': pd.DataFrame({...}),
    'GOOGL': pd.DataFrame({...})
}

# ========================================
# Step 3: Optimize Parameters (Optional)
# ========================================
optimizer = ParameterOptimizer(max_workers=4)

param_ranges = {
    'entry.conditions.0.rules.0.value': [25, 30, 35],  # RSI threshold
    'indicators.0.parameters.period': [10, 14, 20]     # RSI period
}

opt_results = optimizer.optimize(
    yaml_path="config/strategies/my_strategy.yaml",
    data=data,
    parameter_ranges=param_ranges,
    optimization_metric='sharpe_ratio',
    top_n=5
)

print(f"\nTop 5 Combinations:")
for i, result in enumerate(opt_results['top_results'][:5]):
    print(f"{i+1}. Sharpe: {result['performance']['sharpe_ratio']:.2f}, Params: {result['parameters']}")

# Save optimized strategy
best_params = opt_results['best_parameters']
optimizer.create_optimized_yaml(
    base_yaml_path="config/strategies/my_strategy.yaml",
    optimal_parameters=best_params,
    output_path="config/strategies/my_strategy_optimized.yaml"
)

# ========================================
# Step 4: Run Backtest
# ========================================
service = YAMLBacktestService()

results = service.backtest_from_file(
    yaml_path="config/strategies/my_strategy_optimized.yaml",
    data=data,
    store_results=True
)

# ========================================
# Step 5: Analyze Results
# ========================================
if results['success']:
    bt_result = results['backtest_result']
    perf = bt_result.performance_metrics

    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Strategy: {results['strategy_name']} v{results['strategy_version']}")
    print(f"Execution Time: {results['execution_time']:.2f}s")
    print(f"\nPerformance:")
    print(f"  Total Trades: {len(bt_result.trades)}")
    print(f"  Final Value: ${perf['final_value']:,.2f}")
    print(f"  Total Return: {perf['total_return']:.2%}")
    print(f"  Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {perf['max_drawdown']:.2%}")
    print(f"  Win Rate: {perf['win_rate']:.2%}")

    # Show sample trades
    print(f"\nSample Trades:")
    for trade in bt_result.trades[:5]:
        print(f"  {trade.symbol}: Entry ${trade.entry_price:.2f} -> Exit ${trade.exit_price:.2f} = {trade.profit_loss:.2%}")
else:
    print(f"Backtest failed: {results.get('errors', [])}")
```

---

## API Reference

### YAMLStrategyLoader

```python
class YAMLStrategyLoader:
    def load_from_file(yaml_path: str) -> Tuple[bool, Optional[LoadedStrategy], List[str]]:
        """
        Load strategy from YAML file

        Returns:
            Tuple of (success, strategy, errors)
        """
```

### YAMLStrategyExecutor

```python
class YAMLStrategyExecutor:
    def execute_strategy(
        strategy: LoadedStrategy,
        data: Dict[str, pd.DataFrame],
        calculate_indicators: bool = True
    ) -> Dict[str, Any]:
        """
        Execute strategy and generate signals

        Args:
            strategy: Loaded strategy object
            data: Dict of {symbol: DataFrame with OHLCV}
            calculate_indicators: Auto-calculate missing indicators

        Returns:
            Dictionary with signals and metadata
        """
```

### YAMLBacktestService

```python
class YAMLBacktestService:
    def backtest_from_file(
        yaml_path: str,
        data: Dict[str, pd.DataFrame],
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run backtest from YAML file

        Args:
            yaml_path: Path to strategy YAML
            data: Market data
            store_results: Store results in MongoDB

        Returns:
            Dictionary with backtest results
        """

    def backtest_strategy(
        strategy: LoadedStrategy,
        data: Dict[str, pd.DataFrame],
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run backtest from LoadedStrategy object
        """
```

### IndicatorCalculator

```python
class IndicatorCalculator:
    def calculate_missing_indicators(
        df: pd.DataFrame,
        required_indicators: List[str],
        inplace: bool = False
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Calculate missing indicators

        Args:
            df: DataFrame with OHLCV data
            required_indicators: List of indicator names (e.g., ['RSI_14', 'SMA_20'])
            inplace: Modify DataFrame in-place

        Returns:
            Tuple of (updated_df, calculated_indicators)
        """
```

### StrategyCombiner

```python
class StrategyCombiner:
    def combine_strategies(
        strategies: List[LoadedStrategy],
        data: Dict[str, pd.DataFrame],
        method: CombinationMethod = CombinationMethod.AND,
        weights: Optional[List[float]] = None,
        calculate_indicators: bool = True
    ) -> Dict[str, Any]:
        """
        Combine multiple strategies

        Args:
            strategies: List of loaded strategies
            data: Market data
            method: AND, OR, WEIGHTED, MAJORITY
            weights: Weights for WEIGHTED method (must sum to 1.0)
            calculate_indicators: Auto-calculate missing indicators

        Returns:
            Dictionary with combined signals
        """
```

### ParameterOptimizer

```python
class ParameterOptimizer:
    def optimize(
        yaml_path: str,
        data: Dict[str, pd.DataFrame],
        parameter_ranges: Dict[str, List[Any]],
        optimization_metric: str = 'sharpe_ratio',
        top_n: int = 10,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters

        Args:
            yaml_path: Path to base YAML strategy
            data: Market data
            parameter_ranges: Dict of parameter_path -> list of values
            optimization_metric: Metric to optimize
            top_n: Number of top results to return
            parallel: Use parallel processing

        Returns:
            Dictionary with optimization results
        """

    def create_optimized_yaml(
        base_yaml_path: str,
        optimal_parameters: Dict,
        output_path: str
    ):
        """
        Create new YAML file with optimized parameters
        """
```

---

## Data Format Requirements

### Input Data (OHLCV)

Your data must be a dictionary of pandas DataFrames with DatetimeIndex:

```python
data = {
    'AAPL': pd.DataFrame({
        'open': [...],
        'high': [...],
        'low': [...],
        'close': [...],
        'volume': [...]
    }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02', ...]))
}
```

**Requirements**:
- Index must be DatetimeIndex
- Required columns: `open`, `high`, `low`, `close`, `volume`
- All columns must be numeric (float or int)
- No missing values in OHLCV columns

### Loading from MongoDB

```python
from project.database.mongodb_operations import MongoDBOperations

db = MongoDBOperations(db_address="MONGODB_LOCAL")

data = {}
for symbol in ['AAPL', 'MSFT', 'GOOGL']:
    df = db.execute_query(db_name="NasDataBase_D", collection_name=symbol)
    # DataFrame automatically has DatetimeIndex
    data[symbol] = df
```

---

## YAML Strategy File Format

See detailed format in `docs/interfaces/STRATEGY_YAML_INTERFACE.md`

**Minimal Example**:

```yaml
strategy:
  name: "Simple_Strategy"
  version: "1.0"
  author: "Your Name"
  created: "2025-11-05"
  description: "Description"
  category: "mean_reversion"

indicators:
  - name: "RSI"
    parameters:
      period: 14
    output_column: "RSI_14"

entry:
  conditions:
    - group: "entry_rules"
      operator: "AND"
      rules:
        - indicator: "RSI_14"
          operator: "<"
          value: 30

  logic: "entry_rules"

exit:
  profit_target:
    enabled: true
    type: "percentage"
    value: 0.10

  stop_loss:
    enabled: true
    type: "stepped_trailing"
    initial_stop: 0.03
    risk_unit: 0.05
```

---

## Troubleshooting

### Issue: "Column 'XXX' not found in DataFrame"

**Cause**: Strategy references an indicator that doesn't exist in data and can't be auto-calculated.

**Solution**:
1. Add the indicator to your YAML `indicators` section
2. Or provide the indicator in your input data
3. Or remove the indicator from conditions/filters

### Issue: "Strategy validation failed"

**Cause**: YAML file doesn't match JSON schema.

**Solution**:
1. Check YAML syntax (indentation, colons, dashes)
2. Ensure all required fields are present
3. Validate against schema: `config/schemas/strategy_schema.json`

### Issue: "No signals generated"

**Cause**: Market data doesn't meet strategy conditions.

**Solution**:
1. This is expected - not all strategies signal on all data
2. Check your entry conditions are realistic
3. Use wider date ranges or more symbols
4. Test with known historical patterns

### Issue: "MongoDB connection failed"

**Cause**: MongoDB not running or wrong connection string.

**Solution**:
```bash
# Check MongoDB is running
sc query MongoDB

# Start MongoDB if not running (Windows)
net start MongoDB

# Or configure connection in code
db = MongoDBOperations(db_address="MONGODB_LOCAL")
```

### Issue: "Backtest runs but 0 trades"

**Cause**: Strategy conditions never trigger on test data.

**Solution**:
1. Check your entry conditions are achievable
2. Verify data quality (no NaN values)
3. Check filters aren't too restrictive
4. Use `calculate_indicators=True` to ensure all indicators present

### Issue: "Optimization takes too long"

**Cause**: Too many parameter combinations.

**Solution**:
1. Reduce parameter search space
2. Use fewer values per parameter
3. Enable parallel processing: `parallel=True`
4. Optimize on shorter data period first

---

## Best Practices

### Strategy Design

1. **Start Simple**: Begin with 1-2 indicators and clear conditions
2. **Validate First**: Test on known historical patterns
3. **Progressive Complexity**: Add filters and conditions incrementally
4. **Document Everything**: Use descriptions in YAML for all rules

### Optimization

1. **Don't Overfit**: Use reasonable parameter ranges
2. **Out-of-Sample Testing**: Test optimized strategy on new data
3. **Multiple Metrics**: Don't optimize on Sharpe alone
4. **Robustness**: Best strategy should work across multiple periods

### Production Use

1. **Version Control**: Track YAML files in git
2. **Naming Convention**: Use descriptive strategy names
3. **Parameter Documentation**: Document why you chose specific values
4. **Regular Review**: Monitor strategy performance over time

---

## Testing

### Run All Tests

```bash
# Complete E2E workflow test
python Test/test_complete_e2e_workflow.py

# Phase 4 advanced features
python Test/test_phase4_advanced_features.py

# Indicator auto-calculation
python Test/test_indicator_auto_calculation.py
```

### Unit Testing Your Strategy

```python
# Create test with known patterns
dates = pd.date_range('2024-01-01', periods=100, freq='D')

# Create oversold RSI condition
close_prices = [100] * 50 + [80] * 10 + [100] * 40  # Dip in middle

df = pd.DataFrame({
    'open': close_prices,
    'high': [p * 1.02 for p in close_prices],
    'low': [p * 0.98 for p in close_prices],
    'close': close_prices,
    'volume': [1000000] * 100
}, index=dates)

data = {'TEST': df}

# Test your strategy
results = executor.execute_strategy(strategy, data, calculate_indicators=True)

# Verify signals in expected period
entry_signals = results['signals']['TEST']['entry']
assert entry_signals.iloc[50:60].sum() > 0, "Should have signals during dip"
```

---

## Performance Tips

1. **Use `inplace=True`**: When calculating indicators on large DataFrames
   ```python
   calculator.calculate_missing_indicators(df, required, inplace=True)
   ```

2. **Parallel Optimization**: For large parameter spaces
   ```python
   optimizer = ParameterOptimizer(max_workers=8)
   results = optimizer.optimize(..., parallel=True)
   ```

3. **Limit Symbols**: Start with fewer symbols when testing
   ```python
   data = {symbol: df for symbol, df in full_data.items() if symbol in ['AAPL', 'MSFT']}
   ```

4. **Store Results**: Store backtest results for later analysis
   ```python
   service.backtest_from_file(..., store_results=True)
   ```

---

## Example Strategies

### RSI Mean Reversion

Location: `config/strategies/rsi_mean_reversion_v1.yaml`

**Logic**:
- Entry: RSI < 30 (oversold)
- Exit: 10% profit target or stepped trailing stop

### MACD Trend Following (Template)

```yaml
strategy:
  name: "MACD_Trend"
  version: "1.0"

indicators:
  - name: "MACD"
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9
    output_column: "MACD_12_26_9"

entry:
  conditions:
    - group: "bullish_cross"
      operator: "AND"
      rules:
        - indicator: "MACD_12_26_9"
          operator: "crosses_above"
          reference: "MACD_Signal_9"

exit:
  signal_exit:
    enabled: true
    conditions:
      - group: "bearish_cross"
        operator: "OR"
        rules:
          - indicator: "MACD_12_26_9"
            operator: "crosses_below"
            reference: "MACD_Signal_9"
```

---

## Support and Documentation

### Documentation Files

- **Interface Spec**: `docs/interfaces/STRATEGY_YAML_INTERFACE.md`
- **Code Quality**: `docs/rules/CODE_QUALITY.md`
- **Agent Collaboration**: `docs/rules/AGENT_COLLABORATION.md`
- **MongoDB Rules**: `docs/rules/MONGODB_RULES.md`

### Getting Help

1. Check this README first
2. Review interface documentation
3. Run test examples
4. Check logs for detailed error messages

---

## License

Internal use only - AI Assistant Multi-Agent Trading System

---

**System Status**: Production Ready
**Last Tested**: 2025-11-05
**Test Status**: All phases passing (0.27s execution time)
