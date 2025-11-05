# Strategy YAML Interface

**Version**: 1.0
**Last Updated**: 2025-11-05
**Owner**: Strategy Agent

## Overview

This document defines the interface for YAML-based strategy definitions. Strategies are defined in YAML format and validated against a JSON schema.

## File Location

```
config/strategies/{strategy_name}.yaml
```

## Schema Location

```
config/schemas/strategy_schema.json
```

## YAML Structure

### 1. Strategy Metadata

```yaml
strategy:
  name: "Strategy_Name"
  version: "1.0"
  author: "Orchestrator Agent"
  created: "2025-11-05"
  description: |
    Multi-line description of the strategy
  category: "mean_reversion"  # or trend_following, momentum, etc.
  market_type: "stocks"
  timeframe: "daily"
  tags: ["rsi", "sma", "volume"]
```

### 2. Indicators

```yaml
indicators:
  - name: "RSI"
    parameters:
      period: 14
    output_column: "RSI_14"
    description: "Momentum oscillator"
```

### 3. Entry Conditions

```yaml
entry:
  conditions:
    - group: "group_name"
      operator: "AND"  # or "OR"
      rules:
        - indicator: "RSI_14"
          operator: "<"
          value: 30
          description: "RSI oversold"

        - indicator: "close"
          operator: ">"
          reference: "SMA_20"
          description: "Price above SMA20"

  logic: "group1 AND group2"

  constraints:
    max_positions: 10
    position_sizing: "risk_parity"
    risk_per_trade: 0.05
```

### 4. Exit Conditions

```yaml
exit:
  profit_target:
    enabled: true
    type: "percentage"
    value: 0.10  # 10%

  stop_loss:
    enabled: true
    type: "stepped_trailing"
    initial_stop: 0.03
    risk_unit: 0.05

  signal_exit:
    enabled: true
    conditions:
      - group: "exit_signals"
        operator: "OR"
        rules:
          - indicator: "RSI_14"
            operator: ">"
            value: 70
```

### 5. Filters

```yaml
filters:
  - name: "rs_filter"
    indicator: "RS_Rating"
    operator: ">="
    value: 70
```

### 6. Risk Management

```yaml
risk_management:
  initial_capital: 100000000.0
  max_portfolio_risk: 0.20
  max_position_size: 0.10
  position_sizing:
    method: "risk_parity"
    base_risk: 0.05
```

### 7. Backtest Parameters

```yaml
backtest:
  start_date: "2020-01-01"
  end_date: "2024-12-31"
  costs:
    commission: 0.001
    slippage: 0.0005
  benchmark: "SPY"
```

## Supported Operators

### Comparison Operators
- `>` - Greater than
- `>=` - Greater than or equal
- `<` - Less than
- `<=` - Less than or equal
- `==` - Equal
- `!=` - Not equal

### Special Operators
- `crosses_above` - Indicator crosses above reference
- `crosses_below` - Indicator crosses below reference
- `between` - Value in range [min, max]
- `in_list` - Value in predefined list

### Logical Operators
- `AND` - All conditions must be true
- `OR` - At least one condition must be true
- `NOT` - Negation

## Validation

Use `StrategyValidator` class to validate YAML files:

```python
from project.strategy.strategy_validator import validate_strategy_file

is_valid = validate_strategy_file("config/strategies/my_strategy.yaml")
```

## Example

See `config/strategies/rsi_mean_reversion_v1.yaml` for a complete example.

## Phase 2: YAML Strategy Execution (COMPLETED)

### Python API Usage

```python
from project.service.yaml_backtest_service import YAMLBacktestService

# Initialize service
service = YAMLBacktestService()

# Run backtest from YAML file
results = service.backtest_from_file(
    yaml_path="config/strategies/my_strategy.yaml",
    data={"AAPL": df_aapl, "MSFT": df_msft},
    store_results=True  # Store in MongoDB
)

# Access results
if results['success']:
    print(f"Strategy: {results['strategy_name']}")
    print(f"Total trades: {len(results['backtest_result'].trades)}")
    print(f"Final value: {results['backtest_result'].performance_metrics['final_value']}")
```

### Components

#### 1. YAMLStrategyLoader
- **Location**: `project/strategy/yaml_strategy_loader.py`
- **Purpose**: Load and parse YAML strategies into LoadedStrategy objects
- **Key Classes**: LoadedStrategy, IndicatorSpec, ConditionRule, ConditionGroup

#### 2. ConditionEvaluator
- **Location**: `project/strategy/condition_evaluator.py`
- **Purpose**: Evaluate conditions against DataFrame data
- **Supported Operators**:
  - Basic: >, <, ==, !=, >=, <=
  - Special: crosses_above, crosses_below, between, in_list
  - Functions: rolling_mean, rolling_std, rolling_max, rolling_min, ewm

#### 3. YAMLStrategyExecutor
- **Location**: `project/strategy/yaml_strategy_executor.py`
- **Purpose**: Execute strategies and generate signals
- **Output**: Entry/exit signals with metadata

#### 4. YAMLBacktestService
- **Location**: `project/service/yaml_backtest_service.py`
- **Purpose**: Integrate YAML strategies with backtest engine
- **Features**:
  - Convert signals to backtest format
  - Run backtest using DailyBacktestService
  - Store results in MongoDB

### Testing

Run Phase 2 integration test:
```bash
python Test/test_yaml_strategy_phase2.py
```

## Notes

- All indicator output columns referenced in conditions must be defined in the `indicators` section
- Entry logic expression must reference valid group names
- Dates must be in `YYYY-MM-DD` format
- Percentages are expressed as decimals (0.10 = 10%)
- Phase 2 completed: YAML strategies can now be fully executed and backtested

## Phase 3: Indicator Auto-Calculation (COMPLETED)

### Automatic Indicator Calculation

When executing strategies, missing indicators can be automatically calculated:

```python
from project.strategy.yaml_strategy_executor import YAMLStrategyExecutor

executor = YAMLStrategyExecutor()

# Data without indicators (only OHLCV)
data = {'AAPL': df_without_indicators}

# Execute with auto-calculation
results = executor.execute_strategy(
    strategy=strategy,
    data=data,
    calculate_indicators=True  # Automatically calculate missing indicators
)
```

### Supported Indicators (Auto-Calculation)

The IndicatorCalculator can automatically calculate:

**Momentum:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

**Trend:**
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- Rolling High/Low

**Volatility:**
- ATR (Average True Range)
- Bollinger Bands

**Volume:**
- Volume SMA

### Templates Available

Template-based generation for:
- `momentum/rsi.template` - RSI with configurable period
- `momentum/macd.template` - MACD with fast/slow/signal periods
- `trend/sma.template` - SMA with configurable period
- `trend/ema.template` - EMA with configurable period
- `volatility/atr.template` - ATR with configurable period

### Testing

Test auto-calculation:
```bash
python Test/test_indicator_auto_calculation.py
```

### Components

#### IndicatorCalculator
- **Location**: `project/indicator/indicator_calculator.py`
- **Purpose**: Automatically calculate missing technical indicators
- **Features**:
  - Parse indicator names (e.g., "RSI_14" -> RSI with period=14)
  - Calculate from OHLCV data
  - Support 12+ indicator types
  - Validate required columns

## Phase 4: Advanced Features (COMPLETED)

### Strategy Combiner

Combine multiple YAML strategies into composite strategies:

```python
from project.strategy.strategy_combiner import StrategyCombiner, CombinationMethod

combiner = StrategyCombiner()

# Load multiple strategies
strategies, errors = combiner.load_strategies([
    "config/strategies/rsi_strategy.yaml",
    "config/strategies/macd_strategy.yaml"
])

# Combine using different methods
results = combiner.combine_strategies(
    strategies=strategies,
    data=data,
    method=CombinationMethod.AND,  # ALL strategies must agree
    calculate_indicators=True
)
```

**Combination Methods:**
- `AND`: All strategies must signal (conservative)
- `OR`: Any strategy can signal (aggressive)
- `WEIGHTED`: Weighted voting system
- `MAJORITY`: Majority vote

### Parameter Optimizer

Optimize strategy parameters using grid search:

```python
from project.strategy.parameter_optimizer import ParameterOptimizer

optimizer = ParameterOptimizer(max_workers=4)

# Define parameter search space
param_ranges = {
    'entry.conditions.0.rules.0.value': [25, 30, 35],  # RSI oversold levels
    'indicators.0.parameters.period': [10, 14, 20]     # RSI periods
}

# Run optimization
results = optimizer.optimize(
    yaml_path="config/strategies/rsi_strategy.yaml",
    data=data,
    parameter_ranges=param_ranges,
    optimization_metric='sharpe_ratio',
    top_n=10
)

# Get best parameters
best_params = results['best_parameters']
best_sharpe = results['best_performance']['sharpe_ratio']

# Create optimized YAML
optimizer.create_optimized_yaml(
    base_yaml_path="config/strategies/rsi_strategy.yaml",
    optimal_parameters=best_params,
    output_path="config/strategies/rsi_optimized.yaml"
)
```

### Components

#### StrategyCombiner
- **Location**: `project/strategy/strategy_combiner.py`
- **Purpose**: Combine multiple strategies
- **Methods**: AND, OR, WEIGHTED, MAJORITY
- **Features**:
  - Load multiple YAML strategies
  - Execute all strategies on same data
  - Combine signals intelligently
  - Track individual strategy votes
  - Auto indicator calculation

#### ParameterOptimizer
- **Location**: `project/strategy/parameter_optimizer.py`
- **Purpose**: Find optimal strategy parameters
- **Features**:
  - Grid search over parameter space
  - Backtest each combination
  - Rank by performance metric
  - Parallel processing support
  - Generate optimized YAML files

### Testing

Test Phase 4 features:
```bash
python Test/test_phase4_advanced_features.py
```
