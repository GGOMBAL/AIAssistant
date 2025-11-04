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

## Notes

- All indicator output columns referenced in conditions must be defined in the `indicators` section
- Entry logic expression must reference valid group names
- Dates must be in `YYYY-MM-DD` format
- Percentages are expressed as decimals (0.10 = 10%)
