# Data Layer Interface Specification

**Version**: 1.0
**Last Updated**: 2025-10-06
**Managed by**: Data Agent & Strategy Agent

**Related Documentation**:
- [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md) - Overall system interfaces
- [AGENT_INTERFACES.md](AGENT_INTERFACES.md) - Agent communication protocols
- [architecture/DATABASE_ARCHITECTURE.md](architecture/DATABASE_ARCHITECTURE.md) - MongoDB structure
- [CLAUDE.md](../CLAUDE.md) - Project rules and standards

---

## Overview

This document defines the **standardized column specifications** for data flow between layers:
1. **Market DB → Indicator Layer**: Raw market data columns
2. **Indicator Layer → Strategy Layer**: Processed data with technical indicators

### Universal Rule for All Data Types

**모든 데이터 타입(df_D, df_W, df_RS, df_E, df_F)에 동일한 규칙이 적용됩니다**:

```
Market DB → Indicator Layer
  ↓ 컬럼 스펙 정의 파일: df_*_columns_before_TRD.json

Indicator Layer → Strategy Layer
  ↓ 컬럼 스펙 정의 파일: df_*_columns_after_TRD.json
```

All column specifications are maintained as JSON files in `refer/debug_json/` directory:
- **`df_*_columns_before_TRD.json`**: Market DB output (Indicator Layer input)
  - `df_D_columns_before_TRD.json` (Daily)
  - `df_W_columns_before_TRD.json` (Weekly)
  - `df_RS_columns_before_TRD.json` (Relative Strength)
  - `df_E_columns_before_TRD.json` (Earnings)
  - `df_F_columns_before_TRD.json` (Fundamental)

- **`df_*_columns_after_TRD.json`**: Indicator Layer output (Strategy Layer input)
  - `df_D_columns_after_TRD.json` (Daily with indicators)
  - `df_W_columns_after_TRD.json` (Weekly with indicators)
  - `df_RS_columns_after_TRD.json` (RS with indicators)
  - `df_E_columns_after_TRD.json` (Earnings with indicators)
  - `df_F_columns_after_TRD.json` (Fundamental with indicators)

---

## Layer Data Flow

```
MongoDB (Market DB)
     ↓ [before_TRD columns]
Indicator Layer (Technical Indicators Calculation)
     ↓ [after_TRD columns]
Strategy Layer (Signal Generation)
```

---

## 1. Daily Data (df_D)

### 1.1 Market DB → Indicator Layer

**Source File**: `refer/debug_json/df_D_columns_before_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "volume",              // Daily trading volume
  "dividend_factor",     // Dividend adjustment factor
  "split_factor",        // Stock split factor
  "adfac",              // Adjustment factor
  "Cumadfac",           // Cumulative adjustment factor
  "ad_open",            // Adjusted open price
  "ad_high",            // Adjusted high price
  "ad_low",             // Adjusted low price
  "ad_close"            // Adjusted close price
]
```

**Data Types**:
- `volume`: Integer
- `*_factor`: Float (typically around 1.0)
- `ad_*`: Float (price values)

### 1.2 Indicator Layer → Strategy Layer

**Source File**: `refer/debug_json/df_D_columns_after_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "Dvolume",            // Daily volume (renamed from volume)
  "dividend_factor",    // Dividend adjustment factor (unchanged)
  "split_factor",       // Stock split factor (unchanged)
  "adfac",             // Adjustment factor (unchanged)
  "Cumadfac",          // Cumulative adjustment factor (unchanged)
  "Dopen",             // Daily open (renamed from ad_open)
  "Dhigh",             // Daily high (renamed from ad_high)
  "Dlow",              // Daily low (renamed from ad_low)
  "Dclose",            // Daily close (renamed from ad_close)

  // Added by Indicator Layer:
  "Highest_2Y",        // 2-year high price
  "Highest_1Y",        // 1-year high price
  "Highest_6M",        // 6-month high price
  "Highest_3M",        // 3-month high price
  "Highest_1M",        // 1-month high price
  "SMA200_M",          // 200-day SMA (monthly basis)
  "SMA20",             // 20-day simple moving average
  "SMA50",             // 50-day simple moving average
  "SMA200",            // 200-day simple moving average
  "H-L",               // High minus Low
  "H-C",               // High minus Close (previous)
  "L-C",               // Low minus Close (previous)
  "True Range",        // True Range indicator
  "ADR_P",             // Average Daily Range (percentage)
  "ADR"                // Average Daily Range (absolute)
]
```

**Added Columns by Indicator Layer** (15 columns):
1. **Highest Prices** (5): Highest_2Y, Highest_1Y, Highest_6M, Highest_3M, Highest_1M
2. **Moving Averages** (4): SMA200_M, SMA20, SMA50, SMA200
3. **Range Indicators** (6): H-L, H-C, L-C, True Range, ADR_P, ADR

**Helper Layer APIs Used**:
- None (all calculated from historical price data)

---

## 2. Weekly Data (df_W)

### 2.1 Market DB → Indicator Layer

**Source File**: `refer/debug_json/df_W_columns_before_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "open",              // Weekly open price
  "high",              // Weekly high price
  "low",               // Weekly low price
  "close",             // Weekly close price
  "volume",            // Weekly volume
  "adfac"              // Adjustment factor
]
```

### 2.2 Indicator Layer → Strategy Layer

**Source File**: `refer/debug_json/df_W_columns_after_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "Wopen",             // Weekly open (renamed from open)
  "Whigh",             // Weekly high (renamed from high)
  "Wlow",              // Weekly low (renamed from low)
  "Wclose",            // Weekly close (renamed from close)
  "Wvolume",           // Weekly volume (renamed from volume)
  "adfac",             // Adjustment factor (unchanged)

  // Added by Indicator Layer:
  "52_H",              // 52-week high
  "52_L",              // 52-week low
  "1Year_H",           // 1-year high
  "2Year_H",           // 2-year high
  "1Year_L",           // 1-year low
  "2Year_L"            // 2-year low
]
```

**Added Columns by Indicator Layer** (6 columns):
- **High/Low Tracking**: 52_H, 52_L, 1Year_H, 2Year_H, 1Year_L, 2Year_L

**Helper Layer APIs Used**:
- None (all calculated from historical price data)

---

## 3. Relative Strength Data (df_RS)

### 3.1 Market DB → Indicator Layer

**Source File**: `refer/debug_json/df_RS_columns_before_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "RS_4W",             // 4-week relative strength
  "RS_12W",            // 12-week relative strength
  "Sector",            // Sector classification
  "Industry",          // Industry classification
  "Sector_RS_4W",      // Sector 4-week RS
  "Industry_RS_4W",    // Industry 4-week RS
  "Sector_RS_12W",     // Sector 12-week RS
  "Industry_RS_12W"    // Industry 12-week RS
]
```

### 3.2 Indicator Layer → Strategy Layer

**Source File**: `refer/debug_json/df_RS_columns_after_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "RS_4W",             // 4-week relative strength (unchanged)
  "RS_12W",            // 12-week relative strength (unchanged)
  "Sector",            // Sector classification (unchanged)
  "Industry",          // Industry classification (unchanged)
  "Sector_RS_4W",      // Sector 4-week RS (unchanged)
  "Industry_RS_4W",    // Industry 4-week RS (unchanged)
  "Sector_RS_12W",     // Sector 12-week RS (unchanged)
  "Industry_RS_12W",   // Industry 12-week RS (unchanged)

  // Added by Indicator Layer:
  "RS_SMA5",           // 5-day RS moving average
  "RS_SMA20"           // 20-day RS moving average
]
```

**Added Columns by Indicator Layer** (2 columns):
- **RS Moving Averages**: RS_SMA5, RS_SMA20

**Helper Layer APIs Used**:
- None (calculated from RS_4W and RS_12W data)

---

## 4. Earnings Data (df_E)

### 4.1 Market DB → Indicator Layer

**Source File**: `refer/debug_json/df_E_columns_before_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "EarningDate",       // Earnings announcement date
  "index",             // Quarter index
  "eps",               // Earnings per share
  "eps_guidence",      // EPS guidance
  "eps_sup",           // EPS surprise percentage
  "eps_qoq",           // EPS quarter-over-quarter growth
  "eps_yoy",           // EPS year-over-year growth
  "revenue",           // Revenue
  "rev_qoq",           // Revenue QoQ growth
  "rev_yoy"            // Revenue YoY growth
]
```

### 4.2 Indicator Layer → Strategy Layer

**Source File**: `refer/debug_json/df_E_columns_after_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "EarningDate",       // Earnings announcement date (unchanged)
  "index",             // Quarter index (unchanged)
  "eps",               // Earnings per share (unchanged)
  "eps_guidence",      // EPS guidance (unchanged)
  "eps_sup",           // EPS surprise percentage (unchanged)
  "eps_qoq",           // EPS QoQ growth (unchanged)
  "eps_yoy",           // EPS YoY growth (unchanged)
  "revenue",           // Revenue (unchanged)
  "rev_qoq",           // Revenue QoQ growth (unchanged)
  "rev_yoy"            // Revenue YoY growth (unchanged)
]
```

**Added Columns by Indicator Layer**: None (earnings data passed through unchanged)

**Helper Layer APIs Used**:
- Earnings data may be fetched via Helper Layer external APIs (e.g., Alpha Vantage)

---

## 5. Fundamental Data (df_F)

### 5.1 Market DB → Indicator Layer

**Source File**: `refer/debug_json/df_F_columns_before_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "close",                                    // Weekly close price
  "grossProfit",                              // Gross profit
  "totalRevenue",                             // Total revenue
  "operatingIncome",                          // Operating income
  "depreciationAndAmortization",              // D&A
  "ebitda",                                   // EBITDA
  "netIncome",                                // Net income
  "totalAssets",                              // Total assets
  "cashAndCashEquivalentsAtCarryingValue",    // Cash & equivalents
  "totalLiabilities",                         // Total liabilities
  "totalShareholderEquity",                   // Shareholder equity
  "commonStockSharesOutstanding",             // Shares outstanding
  "longTermDebt",                             // Long-term debt
  "shortTermDebt",                            // Short-term debt
  "commonStock",                              // Common stock
  "retainedEarnings",                         // Retained earnings
  "revenue",                                  // Revenue
  "EPS",                                      // Earnings per share
  "EPS_YOY",                                  // EPS YoY growth
  "EPS_QOQ",                                  // EPS QoQ growth
  "REV_YOY",                                  // Revenue YoY growth
  "REV_QOQ"                                   // Revenue QoQ growth
]
```

### 5.2 Indicator Layer → Strategy Layer

**Source File**: `refer/debug_json/df_F_columns_after_TRD.json`

**Standard Columns** (all tickers):
```json
[
  "close",             // Weekly close price (unchanged)
  "revenue",           // Revenue (unchanged)
  "EPS",               // Earnings per share (unchanged)
  "EPS_YOY",           // EPS YoY growth (unchanged)
  "EPS_QOQ",           // EPS QoQ growth (unchanged)
  "REV_YOY",           // Revenue YoY growth (unchanged)
  "REV_QOQ",           // Revenue QoQ growth (unchanged)

  // Added by Indicator Layer:
  "MarketCapitalization",  // Market cap
  "PBR",                   // Price-to-Book ratio
  "PSR",                   // Price-to-Sales ratio
  "ROE",                   // Return on Equity
  "ROA",                   // Return on Assets
  "GPA",                   // Gross Profit margin
  "OPM",                   // Operating Profit margin
  "EBITDA",                // EBITDA (processed)
  "EV",                    // Enterprise Value
  "EV/EBITDA"              // EV to EBITDA ratio
]
```

**Added Columns by Indicator Layer** (10 columns):
1. **Valuation Ratios** (5): MarketCapitalization, PBR, PSR, EV, EV/EBITDA
2. **Profitability Ratios** (4): ROE, ROA, GPA, OPM
3. **Processed Metrics** (1): EBITDA

**Helper Layer APIs Used**:
- Fundamental data fetched via Helper Layer external APIs (e.g., Alpha Vantage, Financial Modeling Prep)
- Some ratios calculated from raw fundamental data

---

## Column Naming Conventions

### Renaming Pattern (Market DB → Indicator Layer)

**Daily Data (df_D)**:
- `volume` → `Dvolume`
- `ad_open` → `Dopen`
- `ad_high` → `Dhigh`
- `ad_low` → `Dlow`
- `ad_close` → `Dclose`

**Weekly Data (df_W)**:
- `open` → `Wopen`
- `high` → `Whigh`
- `low` → `Wlow`
- `close` → `Wclose`
- `volume` → `Wvolume`

**Rationale**: Prefix `D` for Daily, `W` for Weekly to avoid naming conflicts and clarify timeframe.

---

## Interface Validation

### Required Checks

**Before Processing (Indicator Layer)**:
```python
def validate_market_db_columns(df_dict, data_type):
    """
    Validate columns from Market DB match expected schema

    Args:
        df_dict: Dictionary with ticker as key, DataFrame as value
        data_type: 'D', 'W', 'RS', 'E', or 'F'

    Returns:
        bool: True if valid, raises ValueError if invalid
    """
    expected_columns = load_columns_schema(f"df_{data_type}_columns_before_TRD.json")

    for ticker in df_dict:
        actual_columns = list(df_dict[ticker].columns)
        if actual_columns != expected_columns[ticker]:
            raise ValueError(
                f"Column mismatch for {ticker} in df_{data_type}: "
                f"expected {expected_columns[ticker]}, got {actual_columns}"
            )

    return True
```

**After Processing (Strategy Layer)**:
```python
def validate_indicator_layer_columns(df_dict, data_type):
    """
    Validate columns from Indicator Layer match expected schema

    Args:
        df_dict: Dictionary with ticker as key, DataFrame as value
        data_type: 'D', 'W', 'RS', 'E', or 'F'

    Returns:
        bool: True if valid, raises ValueError if invalid
    """
    expected_columns = load_columns_schema(f"df_{data_type}_columns_after_TRD.json")

    for ticker in df_dict:
        actual_columns = list(df_dict[ticker].columns)
        if actual_columns != expected_columns[ticker]:
            raise ValueError(
                f"Column mismatch for {ticker} in df_{data_type}: "
                f"expected {expected_columns[ticker]}, got {actual_columns}"
            )

    return True
```

---

## Column Update Procedures

### Adding New Columns

**When Indicator Layer needs new calculated columns**:

1. **Update JSON Schema**:
   ```bash
   # Edit refer/debug_json/df_*_columns_after_TRD.json
   # Add new column name to all tickers
   ```

2. **Implement Calculation**:
   ```python
   # In Indicator Layer code
   def calculate_new_indicator(df):
       df['NewColumn'] = calculation_logic(df)
       return df
   ```

3. **Update Documentation**:
   ```bash
   # Update this file (DATA_LAYER_INTERFACES.md)
   # Document new column, data type, calculation method
   ```

4. **Validate**:
   ```python
   # Run validation tests
   pytest tests/test_indicator_layer_columns.py
   ```

### Removing Deprecated Columns

**Deprecation process** (gradual removal):

1. **Mark as Deprecated** (Version N):
   - Add `@deprecated` tag in documentation
   - Continue calculating but log warning

2. **Remove from Strategy Layer** (Version N+1):
   - Strategy Layer should not use deprecated columns
   - Still calculated by Indicator Layer

3. **Full Removal** (Version N+2):
   - Remove from `after_TRD.json` schema
   - Remove calculation code
   - Update all documentation

---

## Performance Considerations

### Column Calculation Order

Indicator Layer should calculate columns in dependency order:

**df_D Calculation Order**:
1. Basic renaming: `ad_open` → `Dopen`, etc.
2. Price ranges: `H-L`, `H-C`, `L-C`, `True Range`
3. Moving averages: `SMA20`, `SMA50`, `SMA200`, `SMA200_M`
4. Historical highs: `Highest_1M` → `Highest_3M` → `Highest_6M` → `Highest_1Y` → `Highest_2Y`
5. Range metrics: `ADR`, `ADR_P`

**Optimization**:
- Cache frequently used calculations (SMAs)
- Vectorize operations using pandas/numpy
- Parallelize ticker-level calculations

---

## Error Handling

### Missing Columns

```python
def handle_missing_columns(df, expected_columns, ticker):
    """Handle case where Market DB data is missing columns"""
    missing = set(expected_columns) - set(df.columns)

    if missing:
        logger.warning(f"Missing columns for {ticker}: {missing}")

        # Add missing columns with NaN
        for col in missing:
            df[col] = np.nan

    return df
```

### Data Type Mismatches

```python
def enforce_column_types(df, column_types):
    """Enforce expected data types for columns"""
    for col, dtype in column_types.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except ValueError as e:
                logger.error(f"Cannot convert {col} to {dtype}: {e}")
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
```

---

## Testing Requirements

### Unit Tests

**Test Column Schemas**:
```python
def test_column_schemas():
    """Verify all JSON schema files are valid"""
    for data_type in ['D', 'W', 'RS', 'E', 'F']:
        before = load_json(f"df_{data_type}_columns_before_TRD.json")
        after = load_json(f"df_{data_type}_columns_after_TRD.json")

        assert isinstance(before, dict)
        assert isinstance(after, dict)
        assert len(before) > 0
        assert len(after) > 0
```

**Test Column Calculations**:
```python
def test_indicator_layer_calculations():
    """Verify Indicator Layer produces correct columns"""
    # Load sample Market DB data
    sample_data = load_sample_market_data()

    # Run Indicator Layer
    processed = indicator_layer.process(sample_data)

    # Validate output columns
    validate_indicator_layer_columns(processed['df_D'], 'D')
    validate_indicator_layer_columns(processed['df_W'], 'W')
    # ... etc
```

---

## Summary: All Data Types Interface

### Complete File Mapping

| Data Type | Before TRD (Market DB → Indicator) | After TRD (Indicator → Strategy) |
|-----------|-----------------------------------|----------------------------------|
| **Daily (D)** | `df_D_columns_before_TRD.json` | `df_D_columns_after_TRD.json` |
| **Weekly (W)** | `df_W_columns_before_TRD.json` | `df_W_columns_after_TRD.json` |
| **Relative Strength (RS)** | `df_RS_columns_before_TRD.json` | `df_RS_columns_after_TRD.json` |
| **Earnings (E)** | `df_E_columns_before_TRD.json` | `df_E_columns_after_TRD.json` |
| **Fundamental (F)** | `df_F_columns_before_TRD.json` | `df_F_columns_after_TRD.json` |

### Columns Added by Indicator Layer

| Data Type | Added Columns Count | Key Additions |
|-----------|---------------------|---------------|
| **df_D** | 15 columns | SMA20, SMA50, SMA200, Highest_*, ADR, True Range |
| **df_W** | 6 columns | 52_H, 52_L, 1Year_H/L, 2Year_H/L |
| **df_RS** | 2 columns | RS_SMA5, RS_SMA20 |
| **df_E** | 0 columns | Pass-through (no changes) |
| **df_F** | 10 columns | PBR, PSR, ROE, ROA, GPA, OPM, EBITDA, EV, EV/EBITDA |

### Data Flow Consistency Rule

**모든 데이터 타입에 동일하게 적용**:
```
Market DB
    ↓ [before_TRD.json 스펙]
Indicator Layer
    ↓ 계산 및 변환
    ↓ [after_TRD.json 스펙]
Strategy Layer
```

### Critical Implementation Rules

1. **JSON 파일이 단일 진실의 원천(Single Source of Truth)**
   - 모든 코드는 JSON 파일 스펙을 따라야 함
   - 컬럼 추가/삭제 시 JSON 파일 먼저 업데이트

2. **Validation은 필수**
   - Indicator Layer 입력: `validate_market_db_columns()`
   - Indicator Layer 출력: `validate_indicator_layer_columns()`

3. **5가지 데이터 타입 모두 동일한 패턴**
   - before_TRD: Market DB raw 데이터
   - after_TRD: Indicator Layer 처리 후 데이터

---

## Version History

| Version | Date       | Changes                                    |
|---------|------------|--------------------------------------------|
| 1.0     | 2025-10-06 | Initial data layer interface specification |

---

## References

- **JSON Schema Files**: `refer/debug_json/*_columns_*.json`
- **Indicator Layer Implementation**: `project/indicator/`
- **Strategy Layer Implementation**: `project/strategy/`
- **Helper Layer APIs**: `project/Helper/`

---

*This specification is the **authoritative source** for data column standards. All code must conform to these interfaces.*

**⚠️ 중요**: 모든 데이터 타입(D, W, RS, E, F)에 대해 before_TRD.json과 after_TRD.json 파일이 존재하며, 동일한 규칙이 적용됩니다.
