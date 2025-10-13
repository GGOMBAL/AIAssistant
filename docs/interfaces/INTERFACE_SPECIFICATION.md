# AI Assistant Trading System - Interface Specification

**Version**: 1.0
**Date**: 2025-10-06
**Purpose**: Standard interfaces between Indicator Layer and Strategy Layer

**Related Documentation**:
- [Agent Interfaces](AGENT_INTERFACES.md) - Inter-agent communication protocols
- [Data Layer Interfaces](DATA_LAYER_INTERFACES.md) - Column specifications for data layers
- [CLAUDE.md](../CLAUDE.md) - Project rules and standards

---

## Overview

This document defines the standard data interfaces for the AI Assistant Trading System. It complements the [AGENT_INTERFACES.md](AGENT_INTERFACES.md) which defines agent-to-agent communication protocols, while this document focuses on **data structure** interfaces between system layers.

### Document Relationship

```
AGENT_INTERFACES.md     ←→  INTERFACE_SPECIFICATION.md
(Communication Protocol)    (Data Structure)
         ↓                           ↓
  How agents talk           What data they exchange
  Message formats          DataFrame/Dict formats
  RPC-style calls          Layer-to-layer data flow
```

---

## 1. Indicator Layer to Strategy Layer Interface

The Indicator Layer provides calculated technical indicators to the Strategy Layer through standardized dictionary structures.

### 1.1 Daily Data (df_D)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "Dvolume",           # Daily volume
            "dividend_factor",   # Dividend adjustment factor
            "split_factor",      # Stock split factor
            "adfac",            # Adjustment factor
            "Cumadfac",         # Cumulative adjustment factor
            "Dopen",            # Daily open price
            "Dhigh",            # Daily high price
            "Dlow",             # Daily low price
            "Dclose",           # Daily close price
            "Highest_2Y",       # 2-year high
            "Highest_1Y",       # 1-year high
            "Highest_6M",       # 6-month high
            "Highest_3M",       # 3-month high
            "Highest_1M",       # 1-month high
            "SMA200_M",         # 200-day SMA monthly
            "SMA20",            # 20-day simple moving average
            "SMA50",            # 50-day simple moving average
            "SMA200",           # 200-day simple moving average
            "H-L",              # High minus Low
            "H-C",              # High minus Close
            "L-C",              # Low minus Close
            "True Range",       # True Range indicator
            "ADR_P",            # Average Daily Range percentage
            "ADR"               # Average Daily Range
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # ISO 8601 datetime strings
        "data": [[value1, value2, ...], ...]         # Nested arrays of values
    }
}
```

### 1.2 Weekly Data (df_W)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "Wopen",            # Weekly open price
            "Whigh",            # Weekly high price
            "Wlow",             # Weekly low price
            "Wclose",           # Weekly close price
            "Wvolume",          # Weekly volume
            "adfac",            # Adjustment factor
            "52_H",             # 52-week high
            "52_L",             # 52-week low
            "1Year_H",          # 1-year high
            "2Year_H",          # 2-year high
            "1Year_L",          # 1-year low
            "2Year_L"           # 2-year low
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # Weekly Friday dates
        "data": [[value1, value2, ...], ...]
    }
}
```

### 1.3 Relative Strength Data (df_RS)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "RS_4W",            # 4-week relative strength
            "RS_12W",           # 12-week relative strength
            "Sector",           # Sector classification
            "Industry",         # Industry classification
            "Sector_RS_4W",     # Sector 4-week relative strength
            "Industry_RS_4W",   # Industry 4-week relative strength
            "Sector_RS_12W",    # Sector 12-week relative strength
            "Industry_RS_12W",  # Industry 12-week relative strength
            "RS_SMA5",          # 5-day RS moving average
            "RS_SMA20"          # 20-day RS moving average
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    }
}
```

### 1.4 Earnings Data (df_E)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "EarningDate",      # Earnings announcement date
            "index",            # Quarter index
            "eps",              # Earnings per share
            "eps_guidence",     # EPS guidance
            "eps_sup",          # EPS surprise percentage
            "eps_qoq",          # EPS quarter-over-quarter growth
            "eps_yoy",          # EPS year-over-year growth
            "revenue",          # Revenue
            "rev_qoq",          # Revenue quarter-over-quarter growth
            "rev_yoy"           # Revenue year-over-year growth
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # Quarterly dates
        "data": [[value1, value2, ...], ...]
    }
}
```

### 1.5 Fundamental Data (df_F)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "close",                 # Weekly close price
            "revenue",              # Revenue
            "EPS",                  # Earnings per share
            "EPS_YOY",              # EPS year-over-year growth
            "EPS_QOQ",              # EPS quarter-over-quarter growth
            "REV_YOY",              # Revenue year-over-year growth
            "REV_QOQ",              # Revenue quarter-over-quarter growth
            "MarketCapitalization", # Market capitalization
            "PBR",                  # Price-to-Book ratio
            "PSR",                  # Price-to-Sales ratio
            "ROE",                  # Return on Equity
            "ROA",                  # Return on Assets
            "GPA",                  # Gross Profit margin
            "OPM",                  # Operating Profit margin
            "EBITDA",               # EBITDA
            "EV",                   # Enterprise Value
            "EV/EBITDA"             # EV to EBITDA ratio
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # Weekly dates
        "data": [[value1, value2, ...], ...]
    }
}
```

---

## 2. Strategy Layer Output Interface

The Strategy Layer generates trading signals and outputs candidate stocks with signals.

### 2.1 Trading Candidates (df_dump)

**Structure**: Dictionary with ticker symbols as keys

```python
{
    "TICKER": {
        "columns": [
            "open",             # Open price
            "high",             # High price
            "low",              # Low price
            "close",            # Close price
            "ADR",              # Average Daily Range
            "LossCutPrice",     # Stop loss price
            "TargetPrice",      # Target price for profit
            "BuySig",           # Buy signal (1/0)
            "SellSig",          # Sell signal (1/0)
            "signal",           # Combined signal strength
            "Type",             # Signal type (e.g., "B" for buy)
            "RS_4W",            # 4-week relative strength
            "Rev_Yoy_Growth",   # Revenue year-over-year growth
            "Eps_Yoy_Growth",   # EPS year-over-year growth
            "Sector",           # Sector classification
            "Industry"          # Industry classification
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # Daily dates
        "data": [[value1, value2, ...], ...]
    }
}
```

### 2.2 Universe Output

**Structure**: Simple list of selected ticker symbols

```python
{
    "Universe": [
        "TICKER1",
        "TICKER2",
        "TICKER3",
        ...
    ],
    "count": 58  # Number of stocks in universe
}
```

---

## 3. Data Type Specifications

### 3.1 Common Data Types

- **Datetime**: ISO 8601 format string `"YYYY-MM-DDTHH:MM:SS.mmm"`
- **Price**: Float, precision 2-4 decimal places
- **Volume**: Integer
- **Percentage**: Float, typically -100 to 100
- **Ratio**: Float, typically 0 to 10
- **Signal**: Integer (0 or 1)
- **Classification**: String

### 3.2 Missing Data Handling

- Numeric fields: Use `null` or `NaN`
- String fields: Use empty string `""`
- Maintain consistent handling across all layers

---

## 4. Interface Usage Guidelines

### 4.1 Data Flow

1. **MongoDB → Indicator Layer**: Raw market data loaded
2. **Indicator Layer Processing**: Calculate technical indicators (df_D, df_W, df_RS, df_E, df_F)
3. **Indicator → Strategy Layer**: Pass standardized dictionaries
4. **Strategy Layer Processing**: Generate trading signals
5. **Strategy Layer Output**: Return df_dump with candidates and Universe list

### 4.2 Performance Considerations

- Use dictionary structure for O(1) ticker lookup
- Minimize data copying between layers
- Process in batches when possible
- Cache frequently used calculations

### 4.3 Error Handling

```python
# Example error handling pattern
def process_indicator_data(df_dict):
    required_columns = {
        'df_D': ['Dclose', 'ADR', 'SMA20', 'SMA50', 'SMA200'],
        'df_W': ['Wclose', '52_H', '52_L'],
        'df_RS': ['RS_4W', 'RS_12W', 'Sector', 'Industry']
    }

    for df_name, columns in required_columns.items():
        if df_name not in df_dict:
            raise ValueError(f"Missing required dataframe: {df_name}")

        for ticker in df_dict[df_name]:
            missing_cols = set(columns) - set(df_dict[df_name][ticker]['columns'])
            if missing_cols:
                raise ValueError(f"Missing columns in {df_name}[{ticker}]: {missing_cols}")
```

---

## 5. Implementation Example

### 5.1 Loading Indicator Data

```python
import json
from typing import Dict, List

def load_indicator_data(base_path: str) -> Dict[str, Dict]:
    """Load all indicator dataframes from JSON files"""
    indicator_data = {}

    indicators = ['df_D', 'df_W', 'df_RS', 'df_E', 'df_F']
    for indicator in indicators:
        file_path = f"{base_path}/{indicator}.json"
        with open(file_path, 'r') as f:
            indicator_data[indicator] = json.load(f)

    return indicator_data
```

### 5.2 Generating Trading Signals

```python
def generate_signals(indicator_data: Dict) -> Dict:
    """Generate trading signals from indicator data"""
    df_dump = {}

    # Get list of all tickers
    tickers = set()
    for df in indicator_data.values():
        tickers.update(df.keys())

    for ticker in tickers:
        # Process each ticker
        signals = calculate_signals(
            daily=indicator_data['df_D'].get(ticker),
            weekly=indicator_data['df_W'].get(ticker),
            rs=indicator_data['df_RS'].get(ticker),
            fundamental=indicator_data['df_F'].get(ticker)
        )

        if signals and has_buy_signal(signals):
            df_dump[ticker] = format_output(signals)

    return df_dump
```

### 5.3 Creating Universe

```python
def create_universe(df_dump: Dict, max_stocks: int = 60) -> Dict:
    """Create universe from trading candidates"""
    # Sort by signal strength or other criteria
    ranked_tickers = rank_candidates(df_dump)

    # Select top candidates
    universe = ranked_tickers[:max_stocks]

    return {
        "Universe": universe,
        "count": len(universe)
    }
```

---

## 6. Version History

| Version | Date       | Changes                                    |
|---------|------------|--------------------------------------------|
| 1.0     | 2025-10-06 | Initial interface specification           |

---

## 7. References

- MongoDB Collections: NasDataBase_D, NysDataBase_D
- Reference Implementation: refer/debug_json/*.json
- Backtest System: project/service/refer_compatible_backtest.py

---

*This specification defines the standard data interfaces for the AI Assistant Trading System. All components must conform to these interfaces to ensure compatibility and maintainability.*