# Strategy Layer Signal Generation Rules

**Version**: 1.0
**Last Updated**: 2025-10-18
**Author**: Strategy Agent

---

## 📋 Overview

이 문서는 **Strategy Layer에서 생성하는 모든 매매 신호의 통일된 규칙**을 정의합니다.

**핵심 원칙**:
- 모든 메뉴(백테스트, 개별 종목 확인, 실시간 트레이딩)에서 **동일한 Signal 로직** 사용
- Signal 생성은 **Strategy Layer**에서만 수행
- 다른 Layer는 Strategy Layer의 Signal을 사용만 할 수 있음

---

## 🎯 Signal Types

### 1. Fundamental Signal (F Signal)

**목적**: 펀더멘털 건전성 검증

**적용 파일**:
- `project/strategy/signal_generation_service.py::_generate_fundamental_signals()`
- `project/strategy/staged_signal_service.py::_stage_fundamental_signal()`

**US 시장 조건** (모든 조건 AND):

```python
# 1. Market Capitalization (시가총액)
market_cap >= 2,000,000,000 USD           # >= 2B USD
market_cap <= 20,000,000,000,000 USD      # <= 20T USD

# 2. Growth Conditions (성장 조건) - 둘 중 하나 충족
# 2-1. Revenue Growth (매출 성장)
REV_YOY >= 0.1                            # 현재 분기 매출 YoY >= 10%
AND prev_REV_YOY >= 0                     # 이전 분기 매출 YoY >= 0%

# OR

# 2-2. EPS Growth (순이익 성장)
EPS_YOY >= 0.1                            # 현재 분기 EPS YoY >= 10%
AND prev_EPS_YOY >= 0                     # 이전 분기 EPS YoY >= 0%

# 3. Revenue Positive (매출 양수)
revenue > 0
```

**최종 조건**:
```python
f_signal = 1 if (
    f_condition1 AND f_condition2 AND
    ((f_condition3 AND f_condition4) OR (f_condition6 AND f_condition7)) AND
    f_condition9
) else 0
```

**Return**: `0` (탈락) 또는 `1` (통과)

---

### 2. Weekly Signal (W Signal)

**목적**: 주봉 기술적 분석

**적용 파일**:
- `project/strategy/signal_generation_service.py::_generate_weekly_signals()`
- `project/strategy/staged_signal_service.py::_stage_weekly_signal()`

**조건** (모든 조건 AND):

```python
# 1. 1Year High == 2Year High (52주 신고가 = 2년 신고가)
1Year_H == 2Year_H

# 2. 2Year Low < 1Year Low (2년 저점 < 1년 저점)
2Year_L < 1Year_L

# 3. 52-week High 안정성
52_H <= 52_H.shift(2) * 1.05             # 2주 전 대비 5% 이내 상승

# 4. 주봉 종가 > 52주 저점 * 1.3
Wclose.shift(1) > 52_L * 1.3

# 5. 주봉 종가 > 52주 고점 * 0.7
Wclose.shift(1) > 52_H * 0.7
```

**Return**: `0` (탈락) 또는 `1` (통과)

---

### 3. RS Signal (Relative Strength)

**목적**: 상대 강도 검증

**적용 파일**:
- `project/strategy/signal_generation_service.py::_generate_rs_signals()`
- `project/strategy/staged_signal_service.py::_stage_rs_signal()`

**조건**:

```python
# RS_4W (4주 상대강도) >= 90
RS_4W >= 90
```

**Note**:
- RS는 항상 **T-1 (전날) 데이터** 사용 (`iloc[-2]`)
- `signal_config.yaml`에서 threshold 설정 가능

**Return**: `0` (탈락) 또는 `1` (통과)

---

### 4. Earnings Signal (E Signal)

**목적**: 실적 성장성 검증

**적용 파일**:
- `project/strategy/signal_generation_service.py::_generate_earnings_signals()`
- `project/strategy/staged_signal_service.py::_stage_earnings_signal()`

**조건** (둘 중 하나 충족):

```python
# 1. Revenue Growth (매출 성장)
prev_rev_yoy >= 0
AND latest_rev_yoy > prev_rev_yoy

# OR

# 2. EPS Growth (순이익 성장)
prev_eps_yoy >= 0
AND latest_eps_yoy > prev_eps_yoy
```

**Return**: `0` (탈락) 또는 `1` (통과)

---

### 5. Daily + RS Combined Signal (D Signal)

**목적**: 일봉 브레이크아웃 + RS 결합 신호

**적용 파일**:
- `project/strategy/signal_generation_service.py::_generate_daily_rs_combined_signals()`
- `project/strategy/staged_signal_service.py::_stage_daily_signal()`

**기본 조건** (모든 조건 AND):

```python
# 1. SMA200 Momentum > 0 (또는 SMA200_M == 0)
SMA200_M > 0 OR SMA200_M == 0

# 2. SMA Downtrend
SMA200 < SMA50

# 3. RS >= 90
RS_4W >= 90
```

**브레이크아웃 조건** (다중 타임프레임):

```python
# Timeframes: 2Y, 1Y, 6M, 3M, 1M
for timeframe in ['2Y', '1Y', '6M', '3M', '1M']:
    # Backtest mode (trading_mode=False):
    if Dhigh >= Highest_{timeframe}:
        signal = 1
        target_price = Highest_{timeframe}
        losscut_price = Highest_{timeframe} * 0.97
        break

    # Live trading mode (trading_mode=True):
    if Dhigh < Highest_{timeframe}:
        signal = 1
        target_price = Highest_{timeframe}
        losscut_price = Highest_{timeframe} * 0.97
        break
```

**Return**:
- `signal`: `0` (탈락) 또는 `1` (통과)
- `target_price`: 목표가
- `losscut_price`: 손절가
- `signal_type`: 브레이크아웃 타임프레임 (예: "Breakout_1Y")

---

## 🔄 Final Signal Combination

**적용 파일**:
- `project/strategy/signal_generation_service.py::_combine_signals()`

**US 시장 최종 매수 조건** (모든 조건 AND):

```python
BUY_SIGNAL = (
    weekly_signal == 1 AND
    daily_rs_signal == 1 AND
    rs_signal == 1 AND
    fundamental_signal == 1
)
```

**Signal Strength** (신호 강도):

```python
total_signals = weekly + daily_rs + rs + fundamental + earnings
signal_strength = total_signals / 5  # US 시장 기준
```

**Confidence** (신뢰도):

```python
confidence = 0.7 if BUY_SIGNAL else signal_strength * 0.5
```

---

## 📊 Staged Pipeline Flow

백테스트 및 실시간 트레이딩에서 사용하는 단계별 필터링:

```
E (Earnings) → F (Fundamental) → W (Weekly) → RS (Relative Strength) → D (Daily)
```

**각 단계에서**:
- 해당 Signal이 `1`인 종목만 다음 단계로 전달
- Signal이 `0`인 종목은 즉시 탈락

**최종 후보**:
- D 단계까지 통과한 종목 = **매수 대기 종목**

---

## 🔐 Signal Consistency Rules

### 1. **Single Source of Truth**
- Signal 로직은 **Strategy Layer에서만 정의**
- 다른 Layer는 Strategy Layer의 결과만 사용

### 2. **Unified Logic**
- `SignalGenerationService`와 `StagedSignalService`는 **동일한 조건** 사용
- 한쪽을 수정하면 **반드시 다른 쪽도 동일하게 수정**

### 3. **No Hardcoded Values in Other Layers**
- Service Layer, Helper Layer에서 Signal 조건을 재정의 금지
- 백테스트 코드에서 `BuySig=1` 강제 설정 금지

### 4. **Version Control**
- Signal 조건 변경 시 **반드시 이 문서 업데이트**
- Git commit message에 변경 사유 명시

---

## 📝 Implementation Checklist

Signal 로직 수정 시 확인사항:

- [ ] `signal_generation_service.py` 수정 완료
- [ ] `staged_signal_service.py` 동일하게 수정 완료
- [ ] 단위 테스트 작성 및 통과
- [ ] 백테스트로 검증
- [ ] 이 문서 업데이트
- [ ] Git commit 및 push

---

## 🚨 Common Pitfalls

### ❌ 잘못된 예시:

```python
# main_auto_trade.py (백테스트 코드)
if col in ['BuySig', 'SellSig']:
    df_D[col] = 1  # ❌ 강제로 BuySig=1 설정 (금지!)
```

**문제**: Strategy Layer의 Signal을 무시하고 강제로 설정

### ✅ 올바른 예시:

```python
# main_auto_trade.py (백테스트 코드)
# Strategy Layer의 Signal을 그대로 사용
if 'BuySig' not in df_D.columns:
    df_D['BuySig'] = 0  # ✅ 기본값만 설정, Signal은 Strategy Layer에서 생성
```

---

## 📞 Contact

**담당 Agent**: Strategy Agent
**문서 위치**: `docs/interfaces/STRATEGY_SIGNAL_RULES.md`
**관련 파일**:
- `project/strategy/signal_generation_service.py`
- `project/strategy/staged_signal_service.py`
- `project/service/staged_pipeline_service.py`

**변경 이력**:
- 2025-10-18: 초안 작성 (Fundamental Signal 통일)
- 2025-10-18: Threshold 규칙 명확화 (F=1.0 고정)

---

**이 문서는 모든 Signal 생성의 Single Source of Truth입니다.**
**모든 코드 작성 및 수정 시 이 문서를 참조하세요.**
