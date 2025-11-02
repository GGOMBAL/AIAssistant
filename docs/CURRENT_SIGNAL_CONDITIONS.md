# Current Signal Conditions - Detailed Specification

**Last Updated**: 2025-10-18
**Version**: 1.0

---

## 📋 Overview

모든 Signal 조건의 상세 명세 및 현재 설정값

---

## 1️⃣ Earnings Signal (E)

**파일**: `signal_generation_service.py::_generate_earnings_signals()`

### 조건식:
```python
# Revenue Growth Condition
prev_rev_yoy >= 0
AND latest_rev_yoy > prev_rev_yoy

# OR

# EPS Growth Condition
prev_eps_yoy >= 0
AND latest_eps_yoy > prev_eps_yoy
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_prev_rev_yoy` | `0` | 이전 분기 최소 매출 성장률 |
| `min_prev_eps_yoy` | `0` | 이전 분기 최소 EPS 성장률 |
| `require_growth` | `True` | 이전 대비 성장 필수 여부 |

### 통과 조건:
- **매출 성장**: 이전 분기 >= 0% AND 현재 분기 > 이전 분기
- **OR EPS 성장**: 이전 분기 >= 0% AND 현재 분기 > 이전 분기

### Return:
- `1` (통과) if 조건 만족
- `0` (탈락) otherwise

---

## 2️⃣ Fundamental Signal (F)

**파일**: `signal_generation_service.py::_generate_fundamental_signals()`

### 조건식 (US Market):
```python
# Market Capitalization
market_cap >= 2_000_000_000          # 2 Billion USD
AND market_cap <= 20_000_000_000_000 # 20 Trillion USD

# Growth Conditions (OR)
(
    # Revenue Growth
    (REV_YOY >= 0.1 AND prev_REV_YOY >= 0)
    OR
    # EPS Growth
    (EPS_YOY >= 0.1 AND prev_EPS_YOY >= 0)
)

# Revenue Positive
AND revenue > 0
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_market_cap` | `2,000,000,000` USD | 최소 시가총액 (2B USD) |
| `max_market_cap` | `20,000,000,000,000` USD | 최대 시가총액 (20T USD) |
| `min_rev_yoy` | `0.1` (10%) | 최소 매출 YoY 성장률 |
| `min_prev_rev_yoy` | `0.0` (0%) | 이전 분기 최소 매출 YoY |
| `min_eps_yoy` | `0.1` (10%) | 최소 EPS YoY 성장률 |
| `min_prev_eps_yoy` | `0.0` (0%) | 이전 분기 최소 EPS YoY |
| `min_revenue` | `0` | 최소 매출액 |

### 통과 조건:
1. **시가총액**: 2B USD ~ 20T USD 범위
2. **성장성**: (매출 10% 성장 + 이전 분기 >= 0) OR (EPS 10% 성장 + 이전 분기 >= 0)
3. **매출 양수**: revenue > 0

### Return:
- `1` (통과) if 모든 조건 만족
- `0` (탈락) otherwise

---

## 3️⃣ Weekly Signal (W)

**파일**: `signal_generation_service.py::_generate_weekly_signals()`

### 조건식:
```python
# Condition 1: 1Year High == 2Year High
1Year_H == 2Year_H

# Condition 2: 2Year Low < 1Year Low
AND 2Year_L < 1Year_L

# Condition 3: 52-week High Stability
AND 52_H <= 52_H.shift(2) * 1.05

# Condition 4: Close above 52-week Low
AND Wclose.shift(1) > 52_L * 1.3

# Condition 5: Close above 52-week High
AND Wclose.shift(1) > 52_H * 0.7
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_1y_eq_2y_high` | `True` | 1년 고점 = 2년 고점 필수 |
| `require_2y_lt_1y_low` | `True` | 2년 저점 < 1년 저점 필수 |
| `high_stability_factor` | `1.05` | 52주 고점 안정성 계수 (5%) |
| `low_distance_factor` | `1.3` | 52주 저점 거리 계수 (30%) |
| `high_distance_factor` | `0.7` | 52주 고점 거리 계수 (70%) |
| `shift_periods` | `2` | shift 주기 (2주) |

### 통과 조건:
- 모든 5가지 조건을 **AND**로 결합
- 하나라도 실패하면 탈락

### Return:
- `1` (통과) if 모든 조건 만족
- `0` (탈락) otherwise

---

## 4️⃣ RS Signal (Relative Strength)

**파일**: `signal_generation_service.py::_generate_rs_signals()`

### 조건식:
```python
# RS 4-Week Threshold
RS_4W >= 90  # (T-1 data: iloc[-2])
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `rs_threshold` | `90` | RS_4W 최소값 |
| `use_t_minus_1` | `True` | T-1 데이터 사용 (iloc[-2]) |

### 통과 조건:
- RS_4W >= 90 (상위 10%)
- 전날(T-1) 데이터 사용

### Return:
- `1` (통과) if RS_4W >= 90
- `0` (탈락) otherwise

---

## 5️⃣ Daily + RS Combined Signal (D)

**파일**: `signal_generation_service.py::_generate_daily_rs_combined_signals()`

### 기본 조건 (Base Conditions):
```python
# Condition 1: SMA200 Momentum
SMA200_M > 0 OR SMA200_M == 0  # Positive or zero momentum

# Condition 2: SMA Downtrend
AND SMA200 < SMA50

# Condition 3: RS >= 90
AND RS_4W >= 90
```

### 브레이크아웃 조건 (Breakout Conditions):
```python
# Timeframes: 2Y, 1Y, 6M, 3M, 1M
for timeframe in ['2Y', '1Y', '6M', '3M', '1M']:
    # Backtest Mode (trading_mode = False)
    if Dhigh >= Highest_{timeframe}:
        signal = 1
        target_price = Highest_{timeframe}
        losscut_price = Highest_{timeframe} * 0.97
        break

    # Live Trading Mode (trading_mode = True)
    if Dhigh < Highest_{timeframe}:
        signal = 1
        target_price = Highest_{timeframe}
        losscut_price = Highest_{timeframe} * 0.97
        break
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_sma200_momentum` | `True` | SMA200 모멘텀 체크 |
| `require_sma_downtrend` | `True` | SMA200 < SMA50 체크 |
| `require_rs` | `True` | RS >= 90 체크 |
| `rs_threshold` | `90` | RS 최소값 |
| `losscut_ratio` | `0.97` | 손절 비율 (3%) |
| `breakout_timeframes` | `['2Y', '1Y', '6M', '3M', '1M']` | 브레이크아웃 검사 타임프레임 |
| `use_t_minus_1` | `True` | T-1 데이터 사용 |

### 통과 조건:
1. **기본 조건**: SMA200 모멘텀 + SMA 추세 + RS >= 90
2. **브레이크아웃**: 하나 이상의 타임프레임에서 고점 돌파

### Return:
- `signal`: `1` (통과) or `0` (탈락)
- `target_price`: 목표가 (Highest value)
- `losscut_price`: 손절가 (Highest * 0.97)
- `signal_type`: 브레이크아웃 타임프레임 (예: "Breakout_1Y")

---

## 🔄 Final Signal Combination

**파일**: `signal_generation_service.py::_combine_signals()`

### US Market 최종 매수 조건:
```python
BUY = (
    weekly_signal == 1
    AND daily_rs_signal == 1
    AND rs_signal == 1
    AND fundamental_signal == 1
)
```

### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_weekly` | `True` | Weekly Signal 필수 |
| `require_daily_rs` | `True` | Daily+RS Signal 필수 |
| `require_rs` | `True` | RS Signal 필수 |
| `require_fundamental` | `True` | Fundamental Signal 필수 |
| `require_earnings` | `False` | Earnings Signal 선택 |

### Signal Strength:
```python
total_signals = weekly + daily_rs + rs + fundamental + earnings
signal_strength = total_signals / 5  # US 기준
```

### Confidence:
```python
confidence = 0.7 if BUY_SIGNAL else signal_strength * 0.5
```

---

## 📊 Threshold Summary

| Stage | Current Threshold | Signal Type | Description |
|-------|------------------|-------------|-------------|
| **E (Earnings)** | `1.0` | Binary (0/1) | 이전 대비 성장 필수 |
| **F (Fundamental)** | `1.0` | Binary (0/1) | MarketCap + 성장률 10% |
| **W (Weekly)** | `1.0` | Binary (0/1) | 5가지 조건 모두 만족 |
| **RS (Relative Strength)** | `1.0` | Binary (0/1) | RS_4W >= 90 |
| **D (Daily)** | `0.5` | Weighted (0~1) | 브레이크아웃 + 기본 조건 |

---

## 🎯 조건 변경 시 영향도

### 1. Fundamental Signal 조건 변경
**영향받는 파일**:
- `signal_generation_service.py::_generate_fundamental_signals()`
- `staged_signal_service.py::_stage_fundamental_signal()`

**변경 가능한 값**:
- `min_market_cap`: 최소 시가총액
- `min_rev_yoy`: 매출 성장률 임계값 (현재 10%)
- `min_eps_yoy`: EPS 성장률 임계값 (현재 10%)

### 2. Weekly Signal 조건 변경
**영향받는 파일**:
- `signal_generation_service.py::_generate_weekly_signals()`
- `staged_signal_service.py::_stage_weekly_signal()`

**변경 가능한 값**:
- `high_stability_factor`: 52주 고점 안정성 (현재 1.05 = 5%)
- `low_distance_factor`: 52주 저점 거리 (현재 1.3 = 30%)
- `high_distance_factor`: 52주 고점 거리 (현재 0.7 = 70%)

### 3. RS Signal 조건 변경
**영향받는 파일**:
- `signal_generation_service.py::_generate_rs_signals()`
- `staged_signal_service.py::_stage_rs_signal()`

**변경 가능한 값**:
- `rs_threshold`: RS 임계값 (현재 90)

### 4. Daily Signal 조건 변경
**영향받는 파일**:
- `signal_generation_service.py::_generate_daily_rs_combined_signals()`
- `staged_signal_service.py::_stage_daily_signal()`

**변경 가능한 값**:
- `losscut_ratio`: 손절 비율 (현재 0.97 = 3%)
- `breakout_timeframes`: 브레이크아웃 검사 기간

---

## ⚠️ 주의사항

1. **양쪽 파일 동시 수정 필수**
   - `signal_generation_service.py`
   - `staged_signal_service.py`

2. **테스트 실행 필수**
   - `test_fundamental_signal_unified.py`
   - `test_menu_consistency.py`

3. **문서 업데이트**
   - `STRATEGY_SIGNAL_RULES.md`
   - `CURRENT_SIGNAL_CONDITIONS.md`

---

**이 문서는 모든 Signal 조건의 상세 명세입니다.**
**조건 변경 시 반드시 이 문서를 업데이트하세요.**
