# Fundamental Filters Implementation Guide

## Overview

This document describes the implementation of Fundamental (F) filters in the YAML strategy system, enabling strategies to filter stocks based on market cap, revenue growth, EPS growth, and RS rating.

**Implementation Date**: 2025-11-05
**System Version**: Multi-Agent Trading System v3.1

---

## What are Fundamental Filters?

Fundamental filters are pre-entry screening criteria based on company fundamentals and market data. They filter out stocks that don't meet minimum requirements before entry signals are evaluated.

### Filter Types

1. **Market Cap Filter** - Company size filter
2. **Revenue Growth Filter** - Sales growth requirement
3. **EPS Growth Filter** - Earnings growth requirement
4. **RS Rating Filter** - Relative strength ranking
5. **Price Filter** - Minimum price threshold

---

## Implementation Details

### 1. Strategy Validator Update

**File**: `project/strategy/strategy_validator.py`

Added fundamental indicators to `common_indicators` list:

```python
common_indicators = {
    'RS_Rating', 'avg_dollar_volume_20d',
    # Fundamental data columns (from external data sources)
    'market_cap', 'revenue_yoy', 'eps_yoy',
    'revenue_prev_yoy', 'eps_prev_yoy',
    'revenue_qoq', 'eps_qoq'
}
```

**Why**: These indicators are not calculated but come from external data sources (fundamentals database, API, etc.). The validator now recognizes them as valid filter indicators without requiring definition in the `indicators` section.

### 2. Strategy YAML Files

All three strategies now have active filters:

#### Conservative Strategy
```yaml
filters:
  - name: market_cap_filter
    indicator: market_cap
    operator: ">="
    value: 10000000000        # $10B minimum (large cap)

  - name: rs_rating_filter
    indicator: RS_Rating
    operator: ">="
    value: 90                 # Top 10%

  - name: revenue_growth_filter
    indicator: revenue_yoy
    operator: ">="
    value: 0.05               # 5% minimum

  - name: eps_growth_filter
    indicator: eps_yoy
    operator: ">="
    value: 0.05               # 5% minimum
```

#### Balanced Strategy (Default)
```yaml
filters:
  - name: market_cap_min_filter
    indicator: market_cap
    operator: ">="
    value: 2000000000         # $2B minimum (mid cap)

  - name: market_cap_max_filter
    indicator: market_cap
    operator: "<="
    value: 20000000000000     # $20T maximum

  - name: revenue_growth_filter
    indicator: revenue_yoy
    operator: ">="
    value: 0.10               # 10% minimum (moderate)
```

#### Aggressive Strategy
```yaml
filters:
  - name: market_cap_min_filter
    indicator: market_cap
    operator: ">="
    value: 500000000          # $500M minimum (small cap)

  - name: rs_rating_filter
    indicator: RS_Rating
    operator: ">="
    value: 80                 # Top 20% (relaxed)

  - name: revenue_growth_filter
    indicator: revenue_yoy
    operator: ">="
    value: 0.05               # 5% minimum (relaxed)
```

---

## Required Data Columns

For filters to work, your DataFrame must include these columns:

| Column Name | Type | Description | Example Value |
|------------|------|-------------|---------------|
| `market_cap` | float | Market capitalization (USD) | 500000000000.0 ($500B) |
| `revenue_yoy` | float | Revenue YoY growth (decimal) | 0.15 (15% growth) |
| `eps_yoy` | float | EPS YoY growth (decimal) | 0.20 (20% growth) |
| `RS_Rating` | float | Relative strength rating (0-100) | 85.5 (top 15%) |
| `revenue_prev_yoy` | float | Previous quarter revenue YoY | 0.12 (12% growth) |
| `eps_prev_yoy` | float | Previous quarter EPS YoY | 0.10 (10% growth) |

### Data Format Examples

```python
# Sample DataFrame with fundamental data
import pandas as pd

df = pd.DataFrame({
    # Standard OHLCV
    'open': [100.0, 101.0, 102.0],
    'high': [105.0, 106.0, 107.0],
    'low': [99.0, 100.0, 101.0],
    'close': [104.0, 105.0, 106.0],
    'volume': [1000000, 1100000, 1200000],

    # Fundamental data
    'market_cap': [50000000000, 51000000000, 52000000000],  # $50B+
    'revenue_yoy': [0.15, 0.18, 0.20],                      # 15%, 18%, 20%
    'eps_yoy': [0.12, 0.15, 0.18],                          # 12%, 15%, 18%
    'RS_Rating': [85, 88, 90],                              # Top 15%, 12%, 10%
}, index=pd.date_range('2024-01-01', periods=3))
```

---

## Data Source Integration

### Option 1: Database Integration

If using MongoDB with fundamental data:

```python
from project.database.mongodb_operations import MongoDBOperations

# Load price data
db = MongoDBOperations(db_address="MONGODB_LOCAL")
df_price = db.execute_query(db_name="NasDataBase_D", collection_name="AAPL")

# Load fundamental data
df_fundamental = db.execute_query(
    db_name="FundamentalDatabase",
    collection_name="AAPL_fundamentals"
)

# Merge
df = df_price.merge(df_fundamental, left_index=True, right_index=True, how='left')
```

### Option 2: API Integration

Example using external API:

```python
import yfinance as yf
import pandas as pd

# Get stock data
ticker = yf.Ticker("AAPL")

# Get price data
df = ticker.history(period="1y")

# Add fundamental data
info = ticker.info
df['market_cap'] = info.get('marketCap', 0)

# Get quarterly earnings
earnings = ticker.quarterly_earnings
if not earnings.empty:
    # Calculate YoY growth
    df['revenue_yoy'] = earnings['Revenue'].pct_change(4)  # 4 quarters
    df['eps_yoy'] = earnings['Earnings'].pct_change(4)

# Forward fill missing values
df = df.fillna(method='ffill')
```

### Option 3: Pre-calculated File

Load from CSV/Parquet with fundamental data:

```python
import pandas as pd

# Load combined data
df = pd.read_parquet('data/AAPL_with_fundamentals.parquet')

# Ensure required columns exist
required_columns = ['market_cap', 'revenue_yoy', 'eps_yoy', 'RS_Rating']
missing = [col for col in required_columns if col not in df.columns]
if missing:
    print(f"Warning: Missing columns: {missing}")
```

---

## Filter Execution Flow

### 1. Strategy Loading
```
YAML Strategy File
    ↓
Strategy Validator (validates filter indicators)
    ↓
LoadedStrategy object (with filters)
```

### 2. Backtest Execution
```
DataFrame with OHLCV + Fundamental Data
    ↓
YAMLStrategyExecutor.execute()
    ↓
ConditionEvaluator.evaluate_filters()  ← Filters applied here
    ↓
ConditionEvaluator.evaluate_conditions()  ← Entry conditions
    ↓
Filtered signals returned
```

### 3. Filter Application

**When**: Before entry conditions are evaluated
**Where**: `project/strategy/condition_evaluator.py`

```python
# Pseudo-code
for date in dates:
    # Step 1: Apply filters
    for filter in strategy.filters:
        if not meets_filter_criteria(df.loc[date], filter):
            continue  # Skip this stock

    # Step 2: Evaluate entry conditions (only if filters pass)
    if evaluate_entry_conditions(df.loc[date]):
        generate_signal()
```

---

## Testing Filters

### Test Script

```python
from project.strategy.yaml_strategy_loader import YAMLStrategyLoader

# Load strategy
loader = YAMLStrategyLoader()
success, strategy, errors = loader.load_from_file(
    'config/strategies/Balanced_Strategy.yaml'
)

if success:
    print(f"Loaded: {strategy.name}")
    print(f"Filters: {len(strategy.filters)}")
    for f in strategy.filters:
        print(f"  - {f.name}: {f.indicator} {f.operator} {f.value}")
else:
    print(f"Errors: {errors}")
```

### Manual Filter Testing

```python
import pandas as pd
from project.strategy.condition_evaluator import ConditionEvaluator

# Create test data
df = pd.DataFrame({
    'close': [100.0],
    'market_cap': [5000000000],   # $5B
    'revenue_yoy': [0.08],          # 8% growth
    'eps_yoy': [0.12],              # 12% growth
    'RS_Rating': [85],              # Top 15%
}, index=['2024-01-01'])

# Define filter
filter_rule = {
    'name': 'market_cap_filter',
    'indicator': 'market_cap',
    'operator': '>=',
    'value': 2000000000  # $2B minimum
}

# Evaluate
evaluator = ConditionEvaluator()
result = evaluator.evaluate_filter(df.iloc[0], filter_rule)
print(f"Filter passed: {result}")  # True if market_cap >= $2B
```

---

## Filter Comparison: Conservative vs Balanced vs Aggressive

| Filter | Conservative | Balanced | Aggressive |
|--------|-------------|----------|------------|
| **Market Cap** | ≥$10B (Large cap only) | $2B - $20T (Mid cap) | $500M - $20T (Small/Mid) |
| **RS Rating** | ≥90 (Top 10%) | ≥90 (Top 10%) | ≥80 (Top 20%) |
| **Revenue Growth** | ≥5% YoY | ≥10% YoY | ≥5% YoY |
| **EPS Growth** | ≥5% YoY | ≥10% YoY | ≥5% YoY |
| **Min Price** | >$10 | >$10 | >$5 |
| **Expected Results** | Fewer, elite stocks | Moderate, quality stocks | More, diverse stocks |
| **Risk Level** | Low | Medium | High |

---

## Validation Results

All strategies validated successfully with filters enabled:

```bash
$ python Test/test_signal_config_strategies.py

[OK] Conservative_Strategy.yaml
  Filters: 5
    - market_cap_filter
    - rs_rating_filter
    - revenue_growth_filter

[OK] Balanced_Strategy.yaml
  Filters: 6
    - market_cap_min_filter
    - market_cap_max_filter
    - rs_rating_filter

[OK] Aggressive_Strategy.yaml
  Filters: 6
    - market_cap_min_filter
    - market_cap_max_filter
    - rs_rating_filter

Total: 3/3 strategies validated successfully
```

---

## Best Practices

### 1. Data Quality

**Ensure data freshness**:
```python
# Check data age
latest_fundamental_date = df['fundamental_update_date'].max()
days_old = (pd.Timestamp.now() - latest_fundamental_date).days

if days_old > 90:
    print(f"Warning: Fundamental data is {days_old} days old")
```

### 2. Missing Data Handling

**Option A: Drop stocks with missing fundamentals**
```python
required_cols = ['market_cap', 'revenue_yoy', 'eps_yoy', 'RS_Rating']
df = df.dropna(subset=required_cols)
```

**Option B: Forward fill (use with caution)**
```python
# Only for slowly-changing metrics like market cap
df['market_cap'] = df['market_cap'].fillna(method='ffill')
```

**Option C: Set default values**
```python
# Conservative: Assume worst case for missing data
df['revenue_yoy'] = df['revenue_yoy'].fillna(-1.0)  # Negative growth
df['RS_Rating'] = df['RS_Rating'].fillna(0.0)        # Lowest rating
```

### 3. Performance Optimization

**Pre-filter universe before backtest**:
```python
# Filter universe once before running backtest
from project.strategy.condition_evaluator import ConditionEvaluator

evaluator = ConditionEvaluator()
filtered_symbols = []

for symbol in all_symbols:
    df = get_data(symbol)
    latest = df.iloc[-1]

    # Check filters
    if all(evaluator.evaluate_filter(latest, f) for f in strategy.filters):
        filtered_symbols.append(symbol)

print(f"Filtered: {len(all_symbols)} → {len(filtered_symbols)} stocks")
```

### 4. Filter Logging

**Track filter rejection reasons**:
```python
rejection_stats = {
    'market_cap': 0,
    'revenue_growth': 0,
    'eps_growth': 0,
    'rs_rating': 0,
    'price': 0
}

for symbol in symbols:
    for filter in strategy.filters:
        if not evaluate_filter(symbol, filter):
            rejection_stats[filter.name] += 1

print(f"Rejection breakdown: {rejection_stats}")
```

---

## Troubleshooting

### Issue 1: "Filter references undefined indicator"

**Cause**: Indicator not in `common_indicators` list or `indicators` section

**Solution**:
```python
# Check if validator includes your indicator
# File: project/strategy/strategy_validator.py
common_indicators = {
    'RS_Rating', 'avg_dollar_volume_20d',
    'market_cap', 'revenue_yoy', 'eps_yoy',  # ← Should be here
    ...
}
```

### Issue 2: All stocks filtered out

**Cause**: Filters too strict or data quality issues

**Solution**:
1. Check data distribution:
```python
print(df['revenue_yoy'].describe())
print(df['RS_Rating'].describe())
```

2. Temporarily relax filters:
```yaml
# Test with relaxed values
- name: revenue_growth_filter
  indicator: revenue_yoy
  operator: ">="
  value: 0.01  # 1% instead of 10%
```

### Issue 3: KeyError on fundamental columns

**Cause**: DataFrame missing required columns

**Solution**:
```python
# Add missing columns with default values (for testing)
if 'market_cap' not in df.columns:
    df['market_cap'] = 10000000000  # Default $10B
if 'revenue_yoy' not in df.columns:
    df['revenue_yoy'] = 0.10  # Default 10% growth
```

---

## Future Enhancements

### 1. Sector-based Filters
```yaml
filters:
  - name: sector_filter
    indicator: sector
    operator: in_list
    value: ['Technology', 'Healthcare', 'Finance']
```

### 2. Dynamic Thresholds
```yaml
filters:
  - name: revenue_growth_filter
    indicator: revenue_yoy
    operator: ">"
    reference: sector_median_revenue_yoy
    multiplier: 1.2  # 20% above sector median
```

### 3. Composite Filters
```yaml
filters:
  - name: growth_quality_filter
    type: composite
    logic: (revenue_yoy > 0.10 AND eps_yoy > 0.15) OR RS_Rating > 95
```

### 4. Time-varying Filters
```yaml
filters:
  - name: market_cap_filter
    indicator: market_cap
    operator: ">="
    value:
      bull_market: 2000000000   # $2B in bull
      bear_market: 10000000000  # $10B in bear (flight to quality)
```

---

## Summary

### ✅ What's Implemented

1. **Validator Support**: Fundamental indicators recognized in filters
2. **3 Strategy Files**: Conservative, Balanced, Aggressive with active filters
3. **Filter Types**: Market cap, revenue growth, EPS growth, RS rating, price
4. **Validation**: All strategies pass with filters enabled

### 📊 Filter Statistics

- **Conservative**: 5 filters (strictest)
- **Balanced**: 6 filters (default)
- **Aggressive**: 6 filters (most relaxed)

### 🎯 Next Steps

1. **Integrate Fundamental Data Source**
   - Database, API, or file-based

2. **Test with Real Data**
   - Run backtest with actual fundamental data

3. **Monitor Filter Performance**
   - Track rejection rates
   - Optimize thresholds

4. **Extend Filter Types**
   - Add sector, industry, country filters
   - Implement composite filters

---

**Documentation**: `docs/FUNDAMENTAL_FILTERS_GUIDE.md`
**Test File**: `Test/test_signal_config_strategies.py`
**Modified Files**:
- `project/strategy/strategy_validator.py` (validator update)
- `config/strategies/Conservative_Strategy.yaml` (filters enabled)
- `config/strategies/Balanced_Strategy.yaml` (filters enabled)
- `config/strategies/Aggressive_Strategy.yaml` (filters enabled)

**Generated**: 2025-11-05
**System Version**: Multi-Agent Trading System v3.1
