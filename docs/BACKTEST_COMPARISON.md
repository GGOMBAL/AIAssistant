# Backtest System Comparison

## Overview

This document compares the backtest functionality between:
1. **`main_auto_trade.py`** - Original signal-based backtest system
2. **`project/workflow/automated_strategy_workflow.py`** - New YAML strategy workflow

**Last Updated**: 2025-11-05

---

## Architecture Comparison

### 1. main_auto_trade.py (Original System)

```
User Input
    ↓
StagedPipelineService
    ├─ E (Earnings) Signal → Filter
    ├─ F (Fundamental) Signal → Filter
    ├─ W (Weekly) Signal → Filter
    ├─ RS (Relative Strength) Signal → Filter
    └─ D (Daily) Signal → Filter
         ↓
Final Candidates
    ↓
SignalGenerationService (generates BuySig/SellSig)
    ↓
DailyBacktestService (runs backtest engine)
    ↓
BacktestResult
```

**Configuration**: `config/strategy_signal_config.yaml`
**Strategy Type**: E/F/W/RS/D signal system
**Filtering**: Multi-stage cascading filters

---

### 2. automated_strategy_workflow.py (YAML System)

```
YAML Strategy File
    ↓
YAMLStrategyLoader (loads + validates)
    ↓
LoadedStrategy Object
    ↓
YAMLStrategyExecutor (calculates indicators + evaluates conditions)
    ↓
Entry/Exit Signals
    ↓
YAMLBacktestService (converts signals to backtest format)
    ↓
DailyBacktestService (runs backtest engine)
    ↓
BacktestResult
```

**Configuration**: Individual YAML strategy files
**Strategy Type**: Rule-based conditions with filters
**Filtering**: Pre-entry filters + entry/exit conditions

---

## Key Differences

### 1. Signal Generation Method

| Aspect | main_auto_trade.py | automated_strategy_workflow.py |
|--------|-------------------|--------------------------------|
| **Signal Source** | StagedPipelineService | YAMLStrategyExecutor |
| **Configuration** | strategy_signal_config.yaml | Individual YAML strategy files |
| **Signal Logic** | E/F/W/RS/D stages | Entry/exit condition groups |
| **Filtering** | Multi-stage cascade | Single-pass filters |

### 2. Signal Generation Code

**main_auto_trade.py**:
```python
# Uses StagedPipelineService
pipeline = StagedPipelineService(
    config=pipeline_config,
    market='US',
    area='US',
    start_day=data_start,
    end_day=end_date_dt,
    is_backtest=True,
    execution_mode='analysis'
)

pipeline_results = pipeline.run_staged_pipeline(symbols)
final_candidates = pipeline_results.get('final_candidates', [])

# Signals are in DataFrame columns: BuySig, SellSig
```

**automated_strategy_workflow.py**:
```python
# Uses YAMLStrategyExecutor
executor = YAMLStrategyExecutor()
execution_results = executor.execute_strategy(
    strategy,
    data,
    calculate_indicators=True
)

# Signals are in execution_results['signals'][symbol]['entry']
# Then converted to BuySig/SellSig format
```

### 3. Backtest Configuration

**main_auto_trade.py**:
```python
backtest_config = BacktestConfig()
backtest_config.initial_cash = initial_cash / 1_000_000  # Convert to M
backtest_config.max_positions = 10
backtest_config.slippage = 0.002
backtest_config.message_output = True
backtest_config.enable_whipsaw = False

# Uses values from strategy_signal_config.yaml
# E.g., losscut_ratio: 0.97 (3% stop)
```

**automated_strategy_workflow.py**:
```python
# BacktestConfig created from YAML strategy file
backtest_config = _create_backtest_config_from_strategy(strategy)

# Uses values from YAML strategy:
# - initial_capital: 100000000.0
# - max_positions: 10
# - slippage: 0.0005
# - stop_loss.initial_stop: 0.03
```

### 4. Data Flow

**main_auto_trade.py** (Multi-stage):
```
All Symbols (e.g., 500 stocks)
    ↓ E Filter
Passed E (e.g., 300 stocks)
    ↓ F Filter
Passed F (e.g., 200 stocks)
    ↓ W Filter
Passed W (e.g., 100 stocks)
    ↓ RS Filter
Passed RS (e.g., 50 stocks)
    ↓ D Signal
Final Candidates (e.g., 20 stocks)
    ↓ Backtest
```

**automated_strategy_workflow.py** (Single-pass):
```
All Symbols (e.g., 500 stocks)
    ↓ Load Data
All Data Loaded
    ↓ Execute Strategy (filters + conditions evaluated together)
Signals Generated (e.g., 20 stocks)
    ↓ Backtest
```

---

## Common Components

Both systems share the **same backtest engine**:

### DailyBacktestService

```python
# Same code path for both systems
backtest_service = DailyBacktestService(config=backtest_config)

backtest_results = backtest_service.run_backtest(
    universe=list(backtest_data.keys()),
    df_data=backtest_data,  # Must have: BuySig, SellSig, signal columns
    market='US',
    area='US'
)
```

**Expected DataFrame Format** (both systems):
```python
df.columns = [
    'open', 'high', 'low', 'close', 'volume',  # OHLCV
    'BuySig',      # Entry signals (1/0)
    'SellSig',     # Exit signals (1/0)
    'signal',      # Combined (-1/0/1)
    'ADR',         # Average daily range
    'LossCutPrice',  # Stop loss price
    'TargetPrice',   # Profit target price
    'Type'           # Strategy type
]
```

---

## Functional Comparison

### main_auto_trade.py Advantages

✅ **Multi-stage filtering reduces computation**
   - Early stages eliminate unsuitable stocks
   - Only loads data for candidates that pass filters

✅ **Proven signal system**
   - Based on strategy_signal_config.yaml
   - Well-tested E/F/W/RS/D methodology

✅ **Stage-specific thresholds**
   - Different thresholds per strategy (Conservative/Balanced/Aggressive)
   - Fine-grained control over each filter

✅ **Integrated with existing workflow**
   - Used in live trading (Menu 3)
   - Used in signal timeline (Menu 4)

### automated_strategy_workflow.py Advantages

✅ **Declarative strategy definition**
   - YAML files are easy to read and modify
   - No code changes needed for new strategies

✅ **Portable strategies**
   - Single file contains all strategy logic
   - Easy to version control and share

✅ **Flexible condition logic**
   - AND/OR combinations
   - Group-based conditions
   - Advanced operators (crosses_above, crosses_below, between)

✅ **Schema validation**
   - JSON schema ensures correctness
   - Validates before execution

✅ **Automated workflow**
   - Generation → Validation → Backtest → Report
   - End-to-end automation

---

## Performance Comparison

### Execution Speed

| System | Data Loading | Signal Generation | Backtest | Total |
|--------|-------------|-------------------|----------|-------|
| **main_auto_trade** | Staged (faster) | SignalGeneration | Same | ~0.5-1s |
| **automated_workflow** | All upfront | YAMLExecutor | Same | ~0.2-0.3s |

**Note**: Times depend on universe size and data availability

### Memory Usage

| System | Memory Profile |
|--------|---------------|
| **main_auto_trade** | Lower (staged loading) |
| **automated_workflow** | Higher (all data loaded) |

---

## Signal Conversion Details

### main_auto_trade.py Signal Format

```python
# DataFrame from StagedPipelineService
df.columns = [
    'Dopen', 'Dhigh', 'Dlow', 'Dclose',  # Daily OHLC
    'BuySig',      # Generated by D stage
    'wBuySig',     # Weekly signal contribution
    'dBuySig',     # Daily signal contribution
    'rsBuySig',    # RS signal contribution
    'fBuySig',     # Fundamental signal contribution
    'eBuySig',     # Earnings signal contribution
    'LossCutPrice',   # Calculated from losscut_ratio
    'TargetPrice',    # Calculated from target_multiplier
    ...
]
```

### automated_strategy_workflow.py Signal Format

```python
# execution_results from YAMLStrategyExecutor
execution_results = {
    'signals': {
        'AAPL': {
            'entry': pd.Series([0, 0, 1, 0, ...]),      # Entry signals
            'exit': {
                'signal_exit': pd.Series([0, 0, 0, 1, ...]),  # Exit signals
                'profit_target': pd.Series([...]),
                'stop_loss': pd.Series([...])
            }
        }
    }
}

# Converted to backtest format:
df['BuySig'] = execution_results['signals']['AAPL']['entry']
df['SellSig'] = execution_results['signals']['AAPL']['exit']['signal_exit']
```

---

## Use Case Recommendations

### Use main_auto_trade.py when:

1. **Large universe screening**
   - Need to filter 500+ stocks efficiently
   - Multi-stage filtering saves computation

2. **Using existing E/F/W/RS/D methodology**
   - Already have strategy_signal_config.yaml configured
   - Familiar with signal-based approach

3. **Live trading**
   - Integrated with KIS API
   - Real-time monitoring

4. **Need stage-specific insights**
   - Want to see how many passed each filter
   - Debug signal generation stage by stage

### Use automated_strategy_workflow.py when:

1. **Developing new strategies**
   - Quick iteration with YAML files
   - No code changes needed

2. **Strategy research & optimization**
   - Test multiple parameter combinations
   - Compare different strategies

3. **Sharing strategies**
   - YAML files are portable
   - Easy to version control

4. **Automated backtesting**
   - End-to-end workflow
   - Generate reports automatically

5. **Complex condition logic**
   - Need AND/OR combinations
   - Use advanced operators

---

## Migration Path

### From main_auto_trade.py to YAML strategies

**Step 1**: Extract parameters from strategy_signal_config.yaml
```yaml
# conservative strategy from config
earnings_signal:
  enabled: true
  revenue:
    min_prev_yoy: 0.05
```

**Step 2**: Convert to YAML strategy filters
```yaml
filters:
  - name: revenue_growth_filter
    indicator: revenue_yoy
    operator: ">="
    value: 0.05
```

**Step 3**: Map W/RS/D signals to entry conditions
```yaml
entry:
  conditions:
    - group: price_position
      rules:
        - indicator: close
          operator: ">"
          reference: SMA_20
```

**Step 4**: Test both systems on same data
```python
# Run both and compare
result_original = await run_backtest_staged(...)
result_yaml = workflow.run_workflow(...)

# Compare results
assert abs(result_original['total_return'] - result_yaml['total_return']) < 0.01
```

---

## Integration Opportunities

### Hybrid Approach

Combine the best of both systems:

```python
# Use StagedPipeline for screening
pipeline = StagedPipelineService(...)
final_candidates = pipeline.run_staged_pipeline(symbols)

# Use YAML strategy for signal generation
yaml_strategy = YAMLStrategyLoader().load_from_file('strategy.yaml')
signals = YAMLStrategyExecutor().execute_strategy(
    yaml_strategy,
    final_candidates_data
)

# Run backtest
backtest_service.run_backtest(...)
```

### Shared Configuration

Extract common config:
```yaml
# common_backtest_config.yaml
backtest:
  initial_capital: 100000000.0
  max_positions: 10
  slippage: 0.002

risk_management:
  std_risk: 0.05
  init_risk: 0.03
```

Use in both systems.

---

## Conclusion

### Summary Table

| Feature | main_auto_trade.py | automated_strategy_workflow.py |
|---------|-------------------|--------------------------------|
| **Primary Use** | Live trading + backtest | Strategy research + backtest |
| **Config Format** | strategy_signal_config.yaml | Individual YAML files |
| **Signal Method** | E/F/W/RS/D stages | Condition groups |
| **Filtering** | Multi-stage cascade | Single-pass filters |
| **Speed** | Fast (staged loading) | Very fast (simple logic) |
| **Flexibility** | Medium (code changes) | High (YAML editing) |
| **Complexity** | High | Low |
| **Backtest Engine** | DailyBacktestService | DailyBacktestService (same) |
| **Live Trading** | ✅ Supported | ❌ Not integrated |
| **Automation** | Manual steps | ✅ Fully automated |

### Key Insight

**Both systems use the same backtest engine (`DailyBacktestService`)** but differ in how they generate signals:

- **main_auto_trade.py**: Multi-stage filtering with signal accumulation
- **automated_strategy_workflow.py**: Direct condition evaluation

The choice depends on:
- **Production use** → main_auto_trade.py (proven, live trading)
- **Research & development** → automated_strategy_workflow.py (flexible, automated)

---

**Related Documentation**:
- `docs/SIGNAL_CONFIG_STRATEGY_CONVERSION.md` - Converting between systems
- `docs/FUNDAMENTAL_FILTERS_GUIDE.md` - Filter implementation
- `docs/interfaces/SERVICE_LAYER_INTERFACE.md` - Backtest service interface

**Files**:
- `main_auto_trade.py` - Original backtest system
- `project/workflow/automated_strategy_workflow.py` - YAML workflow
- `project/service/daily_backtest_service.py` - Shared backtest engine
- `project/service/yaml_backtest_service.py` - YAML backtest wrapper
