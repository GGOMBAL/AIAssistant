# Strategy Signal Config Conversion Guide

## Overview

This document describes the conversion of strategies from `strategy_signal_config.yaml` (E/F/W/RS/D signal system) to the new YAML strategy format.

**Conversion Date**: 2025-11-05
**Source**: `config/strategy_signal_config.yaml`
**Target**: YAML Strategy Files in `config/strategies/`

---

## Converted Strategies

### 1. Conservative Strategy
**File**: `config/strategies/Conservative_Strategy.yaml`
**Name**: Conservative_Large_Cap_Growth

**Original Target**:
- Large cap stocks (>$10B market cap)
- High growth requirements (5% revenue/EPS YoY)
- Elite stocks with strong fundamentals

**Conversion Mapping**:
```
Original Signal System (E/F/W/RS/D) → YAML Strategy

[F] Fundamental Signal:
  - Market cap >= $10B                → Filter (commented)
  - Revenue growth >= 5%              → Filter (commented)
  - EPS growth >= 5%                  → Filter (commented)

[W] Weekly Signal:
  - 52W high/low position             → Entry condition (price_position)
  - High stability factor: 1.1        → Approximated via 52W high
  - Low distance factor: 1.4          → Entry: close > Low_52W × 1.4
  - High distance factor: 0.7         → Entry: close > High_52W × 0.7

[RS] RS Signal:
  - RS_4W >= 90 (top 10%)             → Filter (commented)

[D] Daily Signal:
  - SMA200 >= SMA50 (uptrend)         → Entry condition (trend_uptrend)
  - Breakout confirmation             → Entry logic
  - Losscut ratio: 0.97 (2%)          → Stop loss: 2%

Exit:
  - Profit target: N/A in original    → Exit: 10% profit target
  - Stop loss: 2%                     → Exit: 2% stepped trailing
```

**Key Parameters**:
- Initial stop: 2% (conservative)
- Profit target: 10%
- Risk unit: 5% (stepped trailing)

---

### 2. Balanced Strategy (DEFAULT)
**File**: `config/strategies/Balanced_Strategy.yaml`
**Name**: Balanced_Mid_Cap_Growth

**Original Target**:
- Mid cap stocks ($2B - $20T)
- Moderate growth (10% revenue/EPS YoY)
- **This was the default strategy** (`active_strategy: "balanced"`)

**Conversion Mapping**:
```
Original Signal System → YAML Strategy

[F] Fundamental Signal:
  - Market cap: $2B - $20T            → Filter (commented)
  - Revenue growth >= 10%             → Filter (commented)
  - EPS growth >= 10%                 → Filter (commented)

[W] Weekly Signal:
  - High stability factor: 1.05       → Approximated
  - Low distance factor: 1.3          → Entry: close > Low_52W × 1.3
  - High distance factor: 0.7         → Entry: close > High_52W × 0.7

[RS] RS Signal:
  - RS_4W >= 90                       → Filter (commented)

[D] Daily Signal:
  - SMA200 >= SMA50                   → Entry condition
  - Losscut ratio: 0.97 (3%)          → Stop loss: 3%

Exit:
  - Profit target: N/A                → Exit: 10%
  - Stop loss: 3%                     → Exit: 3% stepped trailing
```

**Key Parameters**:
- Initial stop: 3% (moderate)
- Profit target: 10%
- Risk unit: 5%

**Original Thresholds**:
- E: 1.0, F: 1.0, W: 1.0, RS: 1.0, D: 0.5

---

### 3. Aggressive Strategy
**File**: `config/strategies/Aggressive_Strategy.yaml`
**Name**: Aggressive_Small_Mid_Cap_Growth

**Original Target**:
- Small/mid cap stocks ($500M - $20T)
- Relaxed growth requirements (5%)
- More trading opportunities, higher risk

**Conversion Mapping**:
```
Original Signal System → YAML Strategy

[F] Fundamental Signal:
  - Market cap: $500M - $20T          → Filter (commented)
  - Revenue growth >= 5% (relaxed)    → Filter (commented)
  - EPS growth >= 5% (relaxed)        → Filter (commented)

[W] Weekly Signal:
  - High stability factor: 1.10       → Approximated
  - Low distance factor: 1.2          → Entry: close > Low_52W × 1.2
  - High distance factor: 0.6         → Entry: close > High_52W × 0.6

[RS] RS Signal:
  - RS_4W >= 80 (top 20%, relaxed)    → Filter (commented)

[D] Daily Signal:
  - SMA200 >= SMA50                   → Entry condition
  - Losscut ratio: 0.95 (5%)          → Stop loss: 5%

Exit:
  - Profit target: N/A                → Exit: 10%
  - Stop loss: 5%                     → Exit: 5% stepped trailing
```

**Key Parameters**:
- Initial stop: 5% (aggressive - wider stop)
- Profit target: 10%
- Risk unit: 5%
- Max portfolio risk: 25% (vs 20% in others)
- Max position size: 8% (vs 10% in others)

---

## Strategy Comparison Table

| Feature | Conservative | Balanced (Default) | Aggressive |
|---------|-------------|-------------------|------------|
| **Target Market Cap** | >$10B | $2B-$20T | $500M-$20T |
| **Growth Requirement** | 5% YoY | 10% YoY | 5% YoY (relaxed) |
| **RS Rating** | >=90 (top 10%) | >=90 (top 10%) | >=80 (top 20%) |
| **Initial Stop Loss** | 2% | 3% | 5% |
| **Profit Target** | 10% | 10% | 10% |
| **Price vs 52W High** | >70% | >70% | >60% (relaxed) |
| **Price vs 52W Low** | >140% | >130% | >120% (relaxed) |
| **Max Portfolio Risk** | 20% | 20% | 25% |
| **Max Position Size** | 10% | 10% | 8% |
| **Trading Frequency** | Low | Medium | High |
| **Risk Level** | Low | Medium | High |

---

## Implementation Notes

### Commented Filters

All fundamental filters (market_cap, revenue_yoy, eps_yoy, RS_Rating) are **commented out** in the YAML files because:

1. These require additional data columns not in standard OHLCV data
2. The validation system requires these columns to be defined in `indicators` section
3. Users need to ensure their data source includes these columns before enabling

**To enable filters**:
1. Ensure your DataFrame includes: `market_cap`, `revenue_yoy`, `eps_yoy`, `RS_Rating`
2. Uncomment the `filters:` section in the YAML file
3. Re-run validation

### 52-Week High/Low Approximation

The YAML strategies use SMA with period=252 (trading days in a year) as approximation:
```yaml
- name: SMA
  parameters:
    period: 252
  output_column: High_52W
  input_column: high
```

**Note**: This is an approximation. For exact 52-week high/low:
- Use `df['high'].rolling(252).max()` for High_52W
- Use `df['low'].rolling(252).min()` for Low_52W
- Pre-calculate and add to DataFrame before strategy execution

### Signal Exit

Original system didn't have explicit signal-based exits. The YAML strategies add:
```yaml
signal_exit:
  enabled: true
  conditions:
    - indicator: close
      operator: crosses_below
      reference: SMA_50
      description: Trend breakdown exit
```

This provides additional protection against trend reversals.

---

## Original System Features Not Converted

### 1. Earnings Signal (E)
- Disabled in original config for Balanced/Aggressive strategies
- Only enabled for Conservative with `E: 0.0` threshold (not enforced)
- **Converted to**: Commented filters for revenue/EPS growth

### 2. Breakout Timeframes
Original system checked multiple timeframes:
```yaml
timeframes:
  - '2Y'
  - '1Y'
  - '6M'
  - '3M'
  - '1M'
stop_at_first: true
```

**Not directly converted** - YAML strategies use 52-week high/low as proxy

### 3. SMA200 Momentum
Original: `SMA200_M > 0 OR SMA200_M == 0`
**Converted to**: `SMA_200 >= SMA_50` (uptrend confirmation)

### 4. Signal Strength Calculation
Original system calculated signal strength (0.0-1.0) based on:
```yaml
weights:
  earnings: 0.20
  fundamental: 0.20
  weekly: 0.20
  rs: 0.20
  daily_rs: 0.20
```

**Not converted** - YAML strategies use binary entry/exit logic

---

## Validation Results

All 3 strategies passed validation:

```bash
$ python Test/test_signal_config_strategies.py

[OK] Conservative_Strategy.yaml
[OK] Balanced_Strategy.yaml
[OK] Aggressive_Strategy.yaml

Total: 3/3 strategies validated successfully
```

**Indicators Required**:
- SMA_50 (50-day moving average)
- SMA_200 (200-day moving average)
- High_52W (52-week high approximation)
- Low_52W (52-week low approximation)

---

## Usage Recommendations

### For Conservative Investors
Use: `Conservative_Strategy.yaml`
- Best for: Capital preservation, stable returns
- Targets: Large-cap growth stocks
- Risk tolerance: Low
- Expected trades: Fewer, higher quality

### For Balanced Portfolios (Recommended Default)
Use: `Balanced_Strategy.yaml`
- Best for: Balance of risk and return
- Targets: Mid-cap growth stocks
- Risk tolerance: Medium
- Expected trades: Moderate frequency
- **This matches the original default strategy**

### For Aggressive Growth
Use: `Aggressive_Strategy.yaml`
- Best for: Maximum growth opportunities
- Targets: Small/mid-cap stocks
- Risk tolerance: High
- Expected trades: More frequent

---

## Future Enhancements

To fully replicate the original system, consider:

1. **Add Fundamental Data Pipeline**
   - Integrate data source for market_cap, revenue_yoy, eps_yoy
   - Enable commented filters

2. **Implement RS Rating Calculation**
   - Add RS_Rating indicator to indicator registry
   - Calculate based on relative price performance

3. **Add Multi-Timeframe Breakout Detection**
   - Create indicator for detecting breakouts across 2Y/1Y/6M/3M/1M
   - Add to entry conditions

4. **Implement Signal Strength Scoring**
   - Add weighted signal strength calculation
   - Use for position sizing or confidence levels

5. **Add Sector Exposure Limits**
   - Original config mentioned `max_sector_exposure: 0.30`
   - Not yet implemented in YAML system

---

## Migration Path

### Step 1: Test with Current YAML Strategies (No Filters)
```bash
python Test/test_signal_config_strategies.py
```

### Step 2: Add Fundamental Data to Your Pipeline
Ensure DataFrames include:
- `market_cap`
- `revenue_yoy`
- `eps_yoy`
- `RS_Rating`

### Step 3: Enable Filters
Uncomment `filters:` section in chosen strategy YAML

### Step 4: Backtest
```bash
python -m project.service.yaml_backtest_service \
  --strategy config/strategies/Balanced_Strategy.yaml \
  --start-date 2020-01-01 \
  --end-date 2024-12-31
```

### Step 5: Compare Results
Compare backtest results with original signal_config system

---

## Contact & Support

For questions about:
- **YAML Strategy Format**: See `docs/interfaces/STRATEGY_YAML_INTERFACE.md`
- **Original Signal System**: See `config/strategy_signal_config.yaml`
- **Conversion Issues**: Check this document

---

**Generated**: 2025-11-05
**System Version**: Multi-Agent Trading System v3.1
**Strategy Schema Version**: 1.0
