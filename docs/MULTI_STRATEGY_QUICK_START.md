# Multi-Strategy Trading System - Quick Start Guide

**Version**: 1.0
**Last Updated**: 2025-10-18

---

## Overview

This trading system now supports **4 pre-defined strategies** with different risk profiles. All signal conditions are stored in `config/strategy_signal_config.yaml` and can be easily switched without modifying code.

---

## Available Strategies

### 1. Conservative Strategy
**Profile**: Large Cap, High Growth, Strict Filters
- **Market Cap**: 10B+ USD
- **Revenue/EPS Growth**: 15%+ required
- **RS Threshold**: 95 (top 5%)
- **Stop Loss**: 2%
- **Target**: Stable returns with elite stocks

### 2. Balanced Strategy (Default)
**Profile**: Mid Cap, Moderate Growth, Balanced Risk
- **Market Cap**: 2B+ USD
- **Revenue/EPS Growth**: 10%+ required
- **RS Threshold**: 90 (top 10%)
- **Stop Loss**: 3%
- **Target**: Balance of risk and return

### 3. Aggressive Strategy
**Profile**: Small/Mid Cap, Relaxed Filters, High Risk
- **Market Cap**: 500M+ USD
- **Revenue/EPS Growth**: 5%+ required
- **RS Threshold**: 80 (top 20%)
- **Stop Loss**: 5%
- **Target**: High risk, high return, many stocks

### 4. Custom Strategy
**Profile**: User-Defined, Fully Adjustable
- All parameters can be freely adjusted
- Start with balanced defaults
- Customize based on your preferences

---

## Quick Start

### Step 1: Check Current Strategy

```bash
python project/strategy/strategy_manager_cli.py
```

Select option `1` to view the current active strategy.

### Step 2: Switch Strategy

**Option A: Using CLI (Recommended)**
```bash
python project/strategy/strategy_manager_cli.py
```

Select option `3`, then choose your desired strategy.

**Option B: Manual YAML Edit**
```bash
# Edit config/strategy_signal_config.yaml
nano config/strategy_signal_config.yaml
```

Change line 9:
```yaml
active_strategy: "balanced"  # Change to: conservative, balanced, aggressive, or custom
```

### Step 3: Restart Application

After switching strategies, restart the trading application for changes to take effect:
```bash
python main_auto_trade.py
```

---

## Strategy Manager CLI Features

### 1. Show Current Active Strategy
Displays all parameters of the currently active strategy.

### 2. List All Available Strategies
Shows a summary of all 4 strategies with key parameters.

### 3. Switch Strategy
Interactive menu to switch between strategies with confirmation.

### 4. Compare Strategies
Side-by-side comparison of Conservative, Balanced, and Aggressive strategies.

### 5. Show Strategy Details
Complete detailed view of all parameters for a selected strategy.

---

## Key Parameters Explained

### Fundamental Signal (F)
- **market_cap.min**: Minimum market capitalization (USD)
- **revenue.min_yoy**: Minimum revenue year-over-year growth (decimal, 0.10 = 10%)
- **eps.min_yoy**: Minimum EPS year-over-year growth (decimal)
- **growth_logic**: "OR" (revenue OR eps) or "AND" (revenue AND eps)

### Weekly Signal (W)
- **high_stability.factor**: 52-week high stability tolerance (1.05 = 5% tolerance)
- **low_distance.factor**: Distance from 52-week low (1.3 = 30% above)
- **high_distance.factor**: Distance from 52-week high (0.7 = 70% of high)

### RS Signal (Relative Strength)
- **threshold**: Minimum RS_4W value (90 = top 10%, 95 = top 5%)

### Daily Signal (D)
- **losscut_ratio**: Stop loss ratio (0.97 = 3% stop loss)
- **breakout.timeframes**: Timeframes to check for breakout (['2Y', '1Y', '6M', '3M', '1M'])
- **rs.threshold**: RS threshold for daily signal base conditions

---

## Strategy Switching Examples

### Example 1: Switch to Conservative for Bear Market

```bash
# Use CLI
python project/strategy/strategy_manager_cli.py

# Select option 3 (Switch Strategy)
# Choose 1 (Conservative)
# Confirm with 'y'
# Restart application
```

**Result**: System will now select only large-cap (10B+) stocks with high growth (15%+) and strict filters.

### Example 2: Switch to Aggressive for Bull Market

```bash
# Use CLI
python project/strategy/strategy_manager_cli.py

# Select option 3 (Switch Strategy)
# Choose 3 (Aggressive)
# Confirm with 'y'
# Restart application
```

**Result**: System will now select more stocks including small/mid-cap (500M+) with relaxed filters (5%+).

### Example 3: Customize Your Own Strategy

```bash
# Edit YAML directly
nano config/strategy_signal_config.yaml

# Scroll to 'custom:' section (line 312)
# Adjust parameters as desired
# Change active_strategy to "custom"
# Save and restart application
```

---

## Parameter Tuning Guide

### To Get MORE Stocks:
- **Decrease** market_cap.min (e.g., 2B → 1B)
- **Decrease** revenue/eps min_yoy (e.g., 10% → 5%)
- **Increase** weekly factors (e.g., high_stability 1.05 → 1.10)
- **Decrease** RS threshold (e.g., 90 → 80)

### To Get FEWER Stocks:
- **Increase** market_cap.min (e.g., 2B → 5B)
- **Increase** revenue/eps min_yoy (e.g., 10% → 15%)
- **Decrease** weekly factors (e.g., high_stability 1.05 → 1.03)
- **Increase** RS threshold (e.g., 90 → 95)

### To Increase Risk:
- **Increase** losscut_ratio (e.g., 0.97 → 0.95, meaning 3% → 5% stop loss)
- **Decrease** fundamental filters
- **Include** more volatile small-cap stocks

### To Decrease Risk:
- **Decrease** losscut_ratio (e.g., 0.97 → 0.98, meaning 3% → 2% stop loss)
- **Increase** fundamental filters
- **Focus** on large-cap stocks only

---

## Validation & Testing

### Step 1: Validate Configuration
```bash
python project/strategy/strategy_signal_config_loader.py
```

This will load and validate your YAML configuration.

### Step 2: Run Backtest
```bash
python main_auto_trade.py
# Select Menu 1: Run Backtest
```

Run a backtest to verify the strategy generates expected results.

### Step 3: Check Signal Generation
```bash
python main_auto_trade.py
# Select Menu 2: Check Individual Symbol
# Enter a ticker (e.g., AAPL)
```

Verify that signals are generated correctly for specific stocks.

---

## Important Notes

### Signal Enable/Disable Flags

Each signal can be individually enabled or disabled:

```yaml
fundamental_signal:
  enabled: true   # Set to false to disable this signal entirely

weekly_signal:
  enabled: true

rs_signal:
  enabled: true

daily_signal:
  enabled: true

earnings_signal:
  enabled: false  # Disabled by default
```

When a signal is disabled:
- **Menu 1 & 4** (Backtest, Timeline): All symbols pass through that stage
- **Menu 2 & 3** (Individual check, Live): Signal is skipped

### Final Signal Requirements

In `final_signal` section, you can specify which signals are **required** for BUY:

```yaml
final_signal:
  required_signals:
    weekly: true       # W signal MUST be 1
    daily_rs: true     # D signal MUST be 1
    rs: true           # RS signal MUST be 1
    fundamental: true  # F signal MUST be 1
    earnings: false    # E signal optional
```

If `weekly: true`, stocks without W signal will NOT generate BUY, even if other signals are strong.

### Percentage vs Decimal Format

- **Percentages** in YAML are in decimal format:
  - `0.10` = 10%
  - `0.15` = 15%
  - `0.05` = 5%
- **Dollar amounts** are in actual USD:
  - `2000000000` = 2 Billion USD
  - `10000000000` = 10 Billion USD

### Restart Required

After changing `strategy_signal_config.yaml`, you **must restart** the application:
```bash
# Stop current process (Ctrl+C)
# Restart
python main_auto_trade.py
```

Configuration is loaded at application startup and cached in memory.

---

## Troubleshooting

### Problem: Strategy Switch Not Taking Effect

**Solution**: Ensure you restarted the application after switching strategies.

### Problem: Too Few Stocks Selected

**Solution**:
- Switch to Aggressive strategy, OR
- Manually relax filters in Custom strategy (decrease thresholds)

### Problem: Too Many Stocks Selected

**Solution**:
- Switch to Conservative strategy, OR
- Manually tighten filters in Custom strategy (increase thresholds)

### Problem: YAML Syntax Error

**Solution**:
- Check indentation (use spaces, not tabs)
- Validate YAML syntax at https://www.yamllint.com/
- Restore from backup if needed

---

## Advanced Usage

### Creating a Custom Strategy Profile

1. Copy one of the existing strategies in `strategy_signal_config.yaml`
2. Add a new section under `strategies:`
3. Name it (e.g., `my_custom_strategy:`)
4. Adjust all parameters as desired
5. Update `active_strategy: "my_custom_strategy"`
6. Restart application

### Backtesting All Strategies

```bash
# Conservative
python main_auto_trade.py
# Menu 1, review results

# Switch to Balanced
python project/strategy/strategy_manager_cli.py
# Option 3, select Balanced
# Restart and run Menu 1

# Switch to Aggressive
python project/strategy/strategy_manager_cli.py
# Option 3, select Aggressive
# Restart and run Menu 1

# Compare results
```

### Seasonal Strategy Switching

**Bull Market** → Aggressive Strategy
**Bear Market** → Conservative Strategy
**Sideways Market** → Balanced Strategy

Monitor market conditions and switch strategies accordingly for optimal performance.

---

## Summary Commands

```bash
# View current strategy
python project/strategy/strategy_manager_cli.py  # Option 1

# Switch strategy
python project/strategy/strategy_manager_cli.py  # Option 3

# Compare strategies
python project/strategy/strategy_manager_cli.py  # Option 4

# View strategy details
python project/strategy/strategy_manager_cli.py  # Option 5

# Validate config
python project/strategy/strategy_signal_config_loader.py

# Run backtest
python main_auto_trade.py  # Menu 1

# Check individual stock
python main_auto_trade.py  # Menu 2
```

---

## References

- **Configuration File**: `config/strategy_signal_config.yaml`
- **Detailed Guide**: `docs/HOW_TO_CHANGE_SIGNAL_CONDITIONS.md`
- **Current Conditions**: `docs/CURRENT_SIGNAL_CONDITIONS.md`
- **Strategy CLI**: `project/strategy/strategy_manager_cli.py`
- **Config Loader**: `project/strategy/strategy_signal_config_loader.py`

---

**Happy Trading!**
**Remember**: Always backtest before using a new strategy in live trading.
