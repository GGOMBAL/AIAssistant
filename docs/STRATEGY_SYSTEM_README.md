# Multi-Strategy Trading System

**Version**: 1.0
**Status**: Production Ready ✅

---

## What is This?

A complete trading system with **4 pre-defined strategies** that you can switch between **without touching code**. Each strategy has different risk profiles suited for different market conditions.

---

## The 4 Strategies

| Strategy | Risk Level | Market Cap | Growth Required | Expected Stocks | Best For |
|----------|-----------|------------|-----------------|-----------------|----------|
| **Conservative** | 🟢 Low | $10B+ | 15%+ | Few (10-30) | Bear markets, safety first |
| **Balanced** | 🟡 Medium | $2B+ | 10%+ | Moderate (30-60) | Normal markets, default |
| **Aggressive** | 🔴 High | $500M+ | 5%+ | Many (60-100+) | Bull markets, high growth |
| **Custom** | 🔵 Adjustable | User-defined | User-defined | Variable | Experimentation |

---

## Quick Start (3 Steps)

### Step 1: Check Current Strategy
```bash
python project/strategy/strategy_manager_cli.py
```
Select option `1` to see current active strategy.

### Step 2: Switch Strategy (if needed)
In the CLI, select option `3`, then:
- Press `1` for Conservative
- Press `2` for Balanced (default)
- Press `3` for Aggressive
- Press `4` for Custom

Confirm with `y`.

### Step 3: Restart & Run
```bash
python main_auto_trade.py
```
Run your backtest or trading - it will use the new strategy!

---

## When to Use Each Strategy

### Use Conservative When:
- 🐻 Market is in downtrend
- 💰 You want stable, low-risk returns
- 📉 Volatility is high
- ⏰ You prefer holding fewer, elite stocks

**Example**: During market corrections, recession fears, or bear markets.

### Use Balanced When:
- ↔️ Market is neutral or mixed
- ⚖️ You want balanced risk/return
- 📊 Normal volatility
- 🎯 Default choice for most situations

**Example**: Normal market conditions, steady growth periods.

### Use Aggressive When:
- 🐂 Market is in strong uptrend
- 🚀 You want maximum growth potential
- 📈 You can handle higher volatility
- 🎲 You want to catch more opportunities

**Example**: Bull markets, tech booms, growth-focused periods.

### Use Custom When:
- 🔬 You want to experiment
- 🛠️ You have specific requirements
- 📝 You're testing new ideas
- 🎓 You're learning strategy tuning

**Example**: Research, testing, custom portfolio requirements.

---

## What Changes When You Switch?

### Conservative vs Balanced Example:

| Parameter | Conservative | Balanced | Impact |
|-----------|-------------|----------|--------|
| Market Cap Min | $10B | $2B | Conservative: Only large-cap stocks |
| Revenue Growth | 15%+ | 10%+ | Conservative: Only high-growth companies |
| RS Threshold | 95 (top 5%) | 90 (top 10%) | Conservative: Only strongest performers |
| Stop Loss | 2% | 3% | Conservative: Tighter risk control |

**Result**: Conservative selects ~10-30 elite stocks vs Balanced's ~30-60 stocks.

---

## Common Tasks

### Task: Compare All Strategies
```bash
python project/strategy/strategy_manager_cli.py
# Select option 4
```
See side-by-side comparison of all strategies.

### Task: See Detailed Settings
```bash
python project/strategy/strategy_manager_cli.py
# Select option 5
# Choose strategy to view
```
View ALL parameters for a strategy.

### Task: Create Custom Strategy
```bash
# 1. Edit config file
nano config/strategy_signal_config.yaml

# 2. Scroll to 'custom:' section (around line 312)

# 3. Adjust values:
fundamental_signal:
  market_cap:
    min: 5000000000     # Change to 5B for mid-large cap
  revenue:
    min_yoy: 0.12       # Change to 12% growth

# 4. Save and activate
active_strategy: "custom"

# 5. Restart application
python main_auto_trade.py
```

### Task: Test Strategy with Backtest
```bash
# 1. Switch strategy
python project/strategy/strategy_manager_cli.py
# Option 3, select strategy

# 2. Run backtest
python main_auto_trade.py
# Menu 1: Run Backtest

# 3. Review results
# Check stock count, returns, risk metrics
```

---

## Understanding the Parameters

### Market Cap (시가총액)
- **What**: Total company value
- **Conservative**: $10B+ (only mega-caps)
- **Balanced**: $2B+ (large & mid-caps)
- **Aggressive**: $500M+ (includes small-caps)
- **Impact**: Higher = more stable, fewer stocks

### Revenue/EPS Growth (매출/EPS 성장률)
- **What**: Year-over-year growth percentage
- **Conservative**: 15%+ (high growth only)
- **Balanced**: 10%+ (moderate growth)
- **Aggressive**: 5%+ (any growth acceptable)
- **Impact**: Higher = fewer stocks, stronger companies

### RS Threshold (상대 강도)
- **What**: Stock strength vs market (0-100)
- **Conservative**: 95 (top 5% strongest)
- **Balanced**: 90 (top 10%)
- **Aggressive**: 80 (top 20%)
- **Impact**: Higher = fewer stocks, strongest performers only

### Stop Loss (손절 비율)
- **What**: Maximum loss before auto-sell
- **Conservative**: 2% (tight control)
- **Balanced**: 3% (normal)
- **Aggressive**: 5% (room for volatility)
- **Impact**: Tighter = less loss per trade, but more frequent exits

---

## Troubleshooting

### Problem: "Too few stocks selected"
**Solutions**:
1. Switch to Aggressive strategy
2. Or manually relax Custom strategy filters

### Problem: "Too many stocks selected"
**Solutions**:
1. Switch to Conservative strategy
2. Or manually tighten Custom strategy filters

### Problem: "Strategy switch didn't work"
**Solution**: Did you restart the application?
```bash
# Must restart after switching!
python main_auto_trade.py
```

### Problem: "YAML syntax error"
**Solution**: Check indentation (use spaces, not tabs)
- Or restore from Git: `git checkout config/strategy_signal_config.yaml`

### Problem: "How do I know which strategy is active?"
**Solution**: Check in multiple ways:
```bash
# Option 1: CLI
python project/strategy/strategy_manager_cli.py
# Option 1

# Option 2: Check YAML
head -n 10 config/strategy_signal_config.yaml
# Look for "active_strategy: ..."
```

---

## Advanced Tips

### Tip 1: Seasonal Strategies
```
Q1 (Jan-Mar): Conservative (volatile period)
Q2 (Apr-Jun): Balanced (earnings season)
Q3 (Jul-Sep): Aggressive (summer rally)
Q4 (Oct-Dec): Balanced (holiday season)
```

### Tip 2: Market Condition Based
```
VIX > 30: Conservative (high volatility)
VIX 15-30: Balanced (normal)
VIX < 15: Aggressive (low volatility)
```

### Tip 3: Portfolio Mixing
```
50% Balanced + 30% Conservative + 20% Aggressive
= Diversified multi-strategy portfolio
```

### Tip 4: Custom Strategy Templates
```yaml
# Growth-focused Custom
market_cap: min: 1B
revenue_yoy: 0.20 (20%+)
rs_threshold: 92
losscut: 0.96 (4%)

# Value-focused Custom
market_cap: min: 10B
revenue_yoy: 0.05 (5%+)
rs_threshold: 85
losscut: 0.98 (2%)
```

---

## Files Reference

### Main Files
- **Config**: `config/strategy_signal_config.yaml` (edit strategies)
- **CLI Tool**: `project/strategy/strategy_manager_cli.py` (manage strategies)
- **Quick Start**: `docs/MULTI_STRATEGY_QUICK_START.md` (detailed guide)

### For Developers
- **Config Loader**: `project/strategy/strategy_signal_config_loader.py`
- **Signal Service 1**: `project/strategy/signal_generation_service.py`
- **Signal Service 2**: `project/strategy/staged_signal_service.py`
- **Tests**: `Test/test_multi_strategy_system.py`

---

## FAQ

**Q: Can I create more than 4 strategies?**
A: Yes! Edit `strategy_signal_config.yaml` and add new strategy sections.

**Q: Do I need to restart after switching?**
A: Yes, always restart the application for changes to take effect.

**Q: Which strategy is best for beginners?**
A: Start with **Balanced** (default), then adjust based on results.

**Q: Can I switch strategies mid-trading?**
A: Not recommended. Complete current positions, then switch.

**Q: How do I backup my custom settings?**
A: Copy `config/strategy_signal_config.yaml` to a safe location.

**Q: What if I break the YAML file?**
A: Restore from Git: `git checkout config/strategy_signal_config.yaml`

**Q: Can I use multiple strategies at once?**
A: Not directly, but you can run separate instances with different configs.

**Q: Does strategy affect existing positions?**
A: No, only affects NEW stock selection. Existing positions continue.

---

## Support

### Documentation
- 📖 Quick Start Guide: `docs/MULTI_STRATEGY_QUICK_START.md`
- 📋 Implementation Summary: `docs/MULTI_STRATEGY_IMPLEMENTATION_SUMMARY.md`
- 🔧 How to Change Conditions: `docs/HOW_TO_CHANGE_SIGNAL_CONDITIONS.md`

### Testing
```bash
# Validate configuration
python project/strategy/strategy_signal_config_loader.py

# Run test suite
python Test/test_multi_strategy_system.py
```

### Community
- 💬 GitHub Issues: Report problems or suggestions
- 📧 Email: Contact project maintainer

---

## Summary

✅ **4 pre-defined strategies** for different market conditions
✅ **No code modification needed** - just switch and restart
✅ **CLI tool included** for easy management
✅ **Fully tested** - all validation tests passing
✅ **Production ready** - use with confidence

**Remember**: Always backtest before live trading!

---

**Version**: 1.0
**Last Updated**: 2025-10-18
**Status**: Production Ready ✅
