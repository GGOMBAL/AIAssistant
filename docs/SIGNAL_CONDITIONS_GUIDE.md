# Signal Conditions Complete Guide

**Version**: 1.0
**Last Updated**: 2025-10-18
**Purpose**: Signal 조건 완전 가이드 - 이해, 변경, 테스트

---

## 목차

1. [빠른 시작](#빠른-시작)
2. [현재 Signal 조건 상세](#현재-signal-조건-상세)
3. [Signal 조건 변경 방법](#signal-조건-변경-방법)
4. [변경 시나리오 예시](#변경-시나리오-예시)
5. [테스트 및 검증](#테스트-및-검증)
6. [주의사항](#주의사항)
7. [FAQ](#faq)

---

## 빠른 시작

### 현재 시스템 구조

```
메뉴 1 (백테스트)     → StagedPipelineService → StagedSignalService
메뉴 2 (종목 확인)    → SignalGenerationService
메뉴 3 (실시간 거래)  → SignalGenerationService
메뉴 4 (타임라인)     → StagedPipelineService → StagedSignalService
```

**중요**: 모든 메뉴는 **동일한 Signal 조건**을 사용합니다.

### Signal 처리 순서

```
E (Earnings) → F (Fundamental) → W (Weekly) → RS (Relative Strength) → D (Daily)
```

각 단계를 통과한 종목만 다음 단계로 진행합니다.

---

## 현재 Signal 조건 상세

### 1️⃣ Earnings Signal (E)

**파일**: `project/strategy/signal_generation_service.py:461-502`
**파일**: `project/strategy/staged_signal_service.py:148-244`

#### 조건식:
```python
# Revenue Growth Condition
(prev_rev_yoy >= 0) AND (latest_rev_yoy > prev_rev_yoy)

# OR

# EPS Growth Condition
(prev_eps_yoy >= 0) AND (latest_eps_yoy > prev_eps_yoy)
```

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_prev_rev_yoy` | `0` | 이전 분기 최소 매출 성장률 |
| `min_prev_eps_yoy` | `0` | 이전 분기 최소 EPS 성장률 |
| `require_growth` | `True` | 이전 대비 성장 필수 여부 |

#### 통과 조건:
- **매출 성장**: 이전 분기 >= 0% AND 현재 분기 > 이전 분기
- **OR EPS 성장**: 이전 분기 >= 0% AND 현재 분기 > 이전 분기

#### Return:
- `1` (통과) if 조건 만족
- `0` (탈락) otherwise

---

### 2️⃣ Fundamental Signal (F)

**파일**: `project/strategy/signal_generation_service.py:392-459`
**파일**: `project/strategy/staged_signal_service.py:247-351`

#### 조건식 (US Market):
```python
# Market Capitalization
(market_cap >= 2,000,000,000) AND (market_cap <= 20,000,000,000,000)

# Growth Conditions (OR logic)
AND (
    # Revenue Growth
    (REV_YOY >= 0.1 AND prev_REV_YOY >= 0)
    OR
    # EPS Growth
    (EPS_YOY >= 0.1 AND prev_EPS_YOY >= 0)
)

# Revenue Positive
AND (revenue > 0)
```

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_market_cap` | `2,000,000,000` USD | 최소 시가총액 (2B USD) |
| `max_market_cap` | `20,000,000,000,000` USD | 최대 시가총액 (20T USD) |
| `min_rev_yoy` | `0.1` (10%) | 최소 매출 YoY 성장률 |
| `min_prev_rev_yoy` | `0.0` (0%) | 이전 분기 최소 매출 YoY |
| `min_eps_yoy` | `0.1` (10%) | 최소 EPS YoY 성장률 |
| `min_prev_eps_yoy` | `0.0` (0%) | 이전 분기 최소 EPS YoY |
| `min_revenue` | `0` | 최소 매출액 |

#### 통과 조건:
1. **시가총액**: 2B USD ~ 20T USD 범위
2. **성장성**: (매출 10% 성장 + 이전 분기 >= 0) OR (EPS 10% 성장 + 이전 분기 >= 0)
3. **매출 양수**: revenue > 0

#### Return:
- `1` (통과) if 모든 조건 만족
- `0` (탈락) otherwise

**코드 위치**:
- `signal_generation_service.py:443-453`
- `staged_signal_service.py:286-340`

---

### 3️⃣ Weekly Signal (W)

**파일**: `project/strategy/signal_generation_service.py:298-343`
**파일**: `project/strategy/staged_signal_service.py:354-453`

#### 조건식:
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

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_1y_eq_2y_high` | `True` | 1년 고점 = 2년 고점 필수 |
| `require_2y_lt_1y_low` | `True` | 2년 저점 < 1년 저점 필수 |
| `high_stability_factor` | `1.05` | 52주 고점 안정성 계수 (5%) |
| `low_distance_factor` | `1.3` | 52주 저점 거리 계수 (30%) |
| `high_distance_factor` | `0.7` | 52주 고점 거리 계수 (70%) |
| `shift_periods` | `2` | shift 주기 (2주) |

#### 통과 조건:
- 모든 5가지 조건을 **AND**로 결합
- 하나라도 실패하면 탈락

#### Return:
- `1` (통과) if 모든 조건 만족
- `0` (탈락) otherwise

**코드 위치**:
- `signal_generation_service.py:320-337`
- `staged_signal_service.py:412-445`

---

### 4️⃣ RS Signal (Relative Strength)

**파일**: `project/strategy/signal_generation_service.py:345-390`
**파일**: `project/strategy/staged_signal_service.py:456-540`

#### 조건식:
```python
# RS 4-Week Threshold
RS_4W >= 90  # (T-1 data: iloc[-2])
```

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `rs_threshold` | `90` | RS_4W 최소값 |
| `use_t_minus_1` | `True` | T-1 데이터 사용 (iloc[-2]) |

#### 통과 조건:
- RS_4W >= 90 (상위 10%)
- 전날(T-1) 데이터 사용

#### Return:
- `1` (통과) if RS_4W >= 90
- `0` (탈락) otherwise

**코드 위치**:
- `signal_generation_service.py:366` (config에서 임계값 로드)
- `staged_signal_service.py:527` (하드코딩 90)

---

### 5️⃣ Daily + RS Combined Signal (D)

**파일**: `project/strategy/signal_generation_service.py:504-615`
**파일**: `project/strategy/staged_signal_service.py:543-700`

#### 기본 조건 (Base Conditions):
```python
# Condition 1: SMA200 Momentum
SMA200_M > 0 OR SMA200_M == 0  # Positive or zero momentum

# Condition 2: SMA Downtrend
AND SMA200 < SMA50

# Condition 3: RS >= 90
AND RS_4W >= 90
```

#### 브레이크아웃 조건 (Breakout Conditions):
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

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_sma200_momentum` | `True` | SMA200 모멘텀 체크 |
| `require_sma_downtrend` | `True` | SMA200 < SMA50 체크 |
| `require_rs` | `True` | RS >= 90 체크 |
| `rs_threshold` | `90` | RS 최소값 |
| `losscut_ratio` | `0.97` | 손절 비율 (3%) |
| `breakout_timeframes` | `['2Y', '1Y', '6M', '3M', '1M']` | 브레이크아웃 검사 타임프레임 |
| `use_t_minus_1` | `True` | T-1 데이터 사용 |

#### 통과 조건:
1. **기본 조건**: SMA200 모멘텀 + SMA 추세 + RS >= 90
2. **브레이크아웃**: 하나 이상의 타임프레임에서 고점 돌파

#### Return:
- `signal`: `1` (통과) or `0` (탈락)
- `target_price`: 목표가 (Highest value)
- `losscut_price`: 손절가 (Highest * 0.97)
- `signal_type`: 브레이크아웃 타임프레임 (예: "Breakout_1Y")

**코드 위치**:
- `signal_generation_service.py:516-586`
- `staged_signal_service.py:577-661`

---

### 6️⃣ Final Signal Combination

**파일**: `project/strategy/signal_generation_service.py:617-658`

#### US Market 최종 매수 조건:
```python
BUY = (
    weekly_signal == 1
    AND daily_rs_signal == 1
    AND rs_signal == 1
    AND fundamental_signal == 1
)
```

#### 현재 설정값:
| Parameter | Value | Description |
|-----------|-------|-------------|
| `require_weekly` | `True` | Weekly Signal 필수 |
| `require_daily_rs` | `True` | Daily+RS Signal 필수 |
| `require_rs` | `True` | RS Signal 필수 |
| `require_fundamental` | `True` | Fundamental Signal 필수 |
| `require_earnings` | `False` | Earnings Signal 선택 |

#### Signal Strength:
```python
total_signals = weekly + daily_rs + rs + fundamental + earnings
signal_strength = total_signals / 5  # US 기준
```

#### Confidence:
```python
confidence = 0.7 if BUY_SIGNAL else signal_strength * 0.5
```

**코드 위치**:
- `signal_generation_service.py:631-648`

---

## Signal 조건 변경 방법

### 현재 구현 상태 (중요!)

#### ✅ Config에서 읽는 값:
- RS threshold (기본값 90)
- Signal enabled/disabled flags

#### ❌ 하드코딩된 값 (코드 수정 필요):
- Fundamental conditions (MarketCap, REV_YOY, EPS_YOY)
- Weekly conditions (1Year_H, 52_H factors)
- Earnings conditions (growth requirements)
- Daily breakout timeframes

### 방법 1: 코드 직접 수정 (현재 유일한 방법)

#### Step 1: 수정할 파일 확인

**양쪽 파일 모두 수정해야 함**:
1. `project/strategy/signal_generation_service.py` (Menu 2, 3용)
2. `project/strategy/staged_signal_service.py` (Menu 1, 4용)

#### Step 2: 조건 수정 예시

**예시 1: Fundamental - 시가총액 조건 변경 (2B → 5B USD)**

**파일 1**: `signal_generation_service.py:443`
```python
# Before
f_condition1 = market_cap >= 2000000000  # 2B USD

# After
f_condition1 = market_cap >= 5000000000  # 5B USD
```

**파일 2**: `staged_signal_service.py:310`
```python
# Before
f_condition1 = market_cap >= 2000000000  # 2B USD

# After
f_condition1 = market_cap >= 5000000000  # 5B USD
```

**예시 2: Fundamental - 성장률 조건 완화 (10% → 5%)**

**파일 1**: `signal_generation_service.py:445,447`
```python
# Before
f_condition3 = rev_yoy >= 0.1  # 10%
f_condition6 = eps_yoy >= 0.1  # 10%

# After
f_condition3 = rev_yoy >= 0.05  # 5%
f_condition6 = eps_yoy >= 0.05  # 5%
```

**파일 2**: `staged_signal_service.py:312,314`
```python
# Before
f_condition3 = rev_yoy >= 0.1  # 10%
f_condition6 = eps_yoy >= 0.1  # 10%

# After
f_condition3 = rev_yoy >= 0.05  # 5%
f_condition6 = eps_yoy >= 0.05  # 5%
```

**예시 3: Weekly - 52주 고점 안정성 완화 (5% → 10%)**

**파일 1**: `signal_generation_service.py:327`
```python
# Before
w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.05

# After
w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.10
```

**파일 2**: `staged_signal_service.py:427`
```python
# Before
w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.05

# After
w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.10
```

**예시 4: RS - 임계값 변경 (90 → 80)**

**이 경우는 config 파일만 수정하면 됩니다!**

`config/signal_config.yaml:16` 또는 `config/strategy_signal_config.yaml:89`
```yaml
# Before
rs_signal:
  threshold: 90

# After
rs_signal:
  threshold: 80
```

#### Step 3: 저장 및 재시작

```bash
# 파일 저장 후 프로그램 재시작
python main_auto_trade.py
```

---

## 변경 시나리오 예시

### 시나리오 1: Fundamental Signal 완화 (더 많은 종목 선정)

**목표**: 성장률 기준을 10% → 5%로 낮춰서 더 많은 종목 통과

**수정 파일**:
- `signal_generation_service.py:445,447`
- `staged_signal_service.py:312,314`

**변경 내용**:
```python
f_condition3 = rev_yoy >= 0.05  # 10% → 5%
f_condition6 = eps_yoy >= 0.05  # 10% → 5%
```

**효과**:
- ✅ 성장률 5~10% 종목도 통과
- ⚠️ 종목 수 증가 → 리스크 증가 가능

---

### 시나리오 2: Fundamental Signal 강화 (더 엄격한 선정)

**목표**: 시가총액 기준을 2B → 5B USD로 높여서 대형주만 선정

**수정 파일**:
- `signal_generation_service.py:443`
- `staged_signal_service.py:310`

**변경 내용**:
```python
f_condition1 = market_cap >= 5000000000  # 2B → 5B USD
```

**효과**:
- ✅ 대형주만 선정 → 리스크 감소
- ⚠️ 종목 수 감소 → 기회 감소

---

### 시나리오 3: Weekly Signal 조정

**목표**: 52주 고점 안정성 조건 완화 (5% → 10%)

**수정 파일**:
- `signal_generation_service.py:327`
- `staged_signal_service.py:427`

**변경 내용**:
```python
w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.10  # 1.05 → 1.10
```

**효과**:
- ✅ 변동성 높은 종목도 통과
- ⚠️ 불안정한 종목 증가 가능

---

### 시나리오 4: RS Signal 조정

**목표**: RS 임계값을 90 → 80으로 낮춰서 더 많은 종목 통과

**수정 파일**:
- `config/signal_config.yaml:16` (또는 `config/strategy_signal_config.yaml:89`)

**변경 내용**:
```yaml
rs_signal:
  threshold: 80  # 90 → 80
```

**효과**:
- ✅ 상대 강도 80~90 종목도 통과
- ⚠️ 시장 대비 약한 종목도 포함될 수 있음

---

### 시나리오 5: Daily Signal 손절 비율 조정

**목표**: 손절 비율을 3% → 5%로 완화

**수정 파일**:
- `signal_generation_service.py:575`
- `staged_signal_service.py:653`

**변경 내용**:
```python
# Before
signal_result['losscut_price'] = float(highest_value * 0.97)  # 3% 손절

# After
signal_result['losscut_price'] = float(highest_value * 0.95)  # 5% 손절
```

**효과**:
- ✅ 손절 여유 증가
- ⚠️ 손실 폭 증가 가능

---

## 테스트 및 검증

### Step 1: 코드 수정 후 테스트

#### 테스트 1: Fundamental Signal 통일 테스트
```bash
python Test/test_fundamental_signal_unified.py
```

**기대 결과**:
```
[SUCCESS] All signals match!
Both services use identical Fundamental Signal logic.
```

#### 테스트 2: Menu 일관성 테스트
```bash
python Test/test_menu_consistency.py
```

**기대 결과**:
```
[SUCCESS] Results are CONSISTENT!
Both methods returned: [BUY/HOLD]
```

### Step 2: 백테스트 실행

```bash
python main_auto_trade.py
# 메뉴 1번 선택 (백테스트)
```

**확인 사항**:
- 종목 수 변화 확인
- 수익률 변화 확인
- 리스크 지표 확인

### Step 3: 개별 종목 확인

```bash
python main_auto_trade.py
# 메뉴 2번 선택 (종목 확인)
# 종목 코드 입력 (예: AAPL)
```

**확인 사항**:
- 각 Signal 값 (E, F, W, RS, D) 확인
- 최종 매수/매도 신호 확인

---

## 주의사항

### 1. 변경 후 반드시 테스트

**필수 테스트**:
```bash
# 1. 통일성 테스트
python Test/test_fundamental_signal_unified.py

# 2. Menu 일관성 테스트
python Test/test_menu_consistency.py

# 3. 백테스트로 검증
python main_auto_trade.py  # 메뉴 1번
```

### 2. 조건 완화 시 위험

- ✅ 종목 수 증가
- ⚠️ 저품질 종목 포함 가능
- ⚠️ 리스크 증가

### 3. 조건 강화 시 위험

- ✅ 고품질 종목만 선정
- ⚠️ 종목 수 감소
- ⚠️ 기회 손실

### 4. 반드시 양쪽 파일 동시 수정

**중요**: 한 쪽만 수정하면 Menu 2와 백테스트 결과가 달라집니다!

**수정 필수 파일**:
1. `project/strategy/signal_generation_service.py`
2. `project/strategy/staged_signal_service.py`

### 5. 권장하지 않는 변경

| 항목 | 이유 |
|------|------|
| `use_t_minus_1` | 데이터 타이밍 로직, 변경 시 오류 가능 |
| `shift_periods` | 기술 지표 계산 로직, 변경 시 오류 가능 |
| `combination_logic` | Signal 결합 로직, 변경 시 예상치 못한 결과 |

---

## FAQ

### Q1: RS threshold만 변경하고 싶은데, 코드를 수정해야 하나요?

**A**: 아니요! RS threshold는 YAML 파일만 수정하면 됩니다.

```yaml
# config/signal_config.yaml 또는 config/strategy_signal_config.yaml
rs_signal:
  threshold: 80  # 원하는 값으로 변경
```

### Q2: Fundamental 조건을 변경했는데 백테스트 결과가 안 바뀝니다.

**A**: 양쪽 파일을 모두 수정했는지 확인하세요.

**수정 필수**:
1. `signal_generation_service.py:443-453`
2. `staged_signal_service.py:310-340`

### Q3: 변경 후 테스트는 어떻게 하나요?

**A**: 3단계 테스트를 권장합니다.

```bash
# 1. 통일성 테스트
python Test/test_fundamental_signal_unified.py

# 2. Menu 일관성 테스트
python Test/test_menu_consistency.py

# 3. 실제 백테스트
python main_auto_trade.py  # 메뉴 1번
```

### Q4: 왜 YAML 설정이 전부 적용되지 않나요?

**A**: 현재 부분적으로만 구현되어 있습니다.

**Config에서 읽는 값**:
- ✅ RS threshold
- ✅ Signal enabled flags

**하드코딩된 값 (코드 수정 필요)**:
- ❌ Fundamental conditions
- ❌ Weekly conditions
- ❌ Earnings conditions
- ❌ Daily breakout timeframes

향후 전체 YAML 통합 예정입니다.

### Q5: Menu 2와 백테스트 결과가 다릅니다.

**A**: 두 서비스가 다른 로직을 사용하고 있는지 확인하세요.

```bash
# Menu 일관성 테스트 실행
python Test/test_menu_consistency.py
```

결과가 `[SUCCESS] Results are CONSISTENT!`여야 정상입니다.

### Q6: 보수적 전략으로 바꾸고 싶습니다.

**A**: 다음과 같이 조건을 강화하세요.

```python
# Fundamental: 대형주 + 고성장
f_condition1 = market_cap >= 10000000000  # 10B USD
f_condition3 = rev_yoy >= 0.15            # 15% 성장
f_condition6 = eps_yoy >= 0.15            # 15% 성장

# RS: 상위 5%만
rs_threshold = 95
```

### Q7: 공격적 전략으로 바꾸고 싶습니다.

**A**: 다음과 같이 조건을 완화하세요.

```python
# Fundamental: 중소형주 + 중성장
f_condition1 = market_cap >= 500000000   # 500M USD
f_condition3 = rev_yoy >= 0.05           # 5% 성장
f_condition6 = eps_yoy >= 0.05           # 5% 성장

# RS: 상위 20%
rs_threshold = 80
```

### Q8: 변경 후 프로그램이 오류가 납니다.

**A**: 다음을 확인하세요.

1. **문법 오류**: Python 문법이 맞는지 확인
2. **들여쓰기**: Python은 들여쓰기에 민감함
3. **변수명**: 오타가 없는지 확인
4. **조건식**: 논리 연산자 (`and`, `or`, `not`) 확인

### Q9: 어떤 조건을 먼저 변경해야 하나요?

**A**: 영향도 순서로 권장합니다.

1. **RS threshold** (가장 쉬움, YAML만 수정)
2. **Fundamental 성장률** (REV_YOY, EPS_YOY)
3. **Fundamental 시가총액** (MarketCap)
4. **Weekly 안정성** (52_H factor)
5. **Daily 손절 비율** (losscut_price)

### Q10: 변경 사항을 되돌리고 싶습니다.

**A**: Git을 사용하면 쉽게 되돌릴 수 있습니다.

```bash
# 최근 변경 취소
git checkout -- project/strategy/signal_generation_service.py
git checkout -- project/strategy/staged_signal_service.py
```

또는 이 문서의 "현재 Signal 조건 상세"를 참고하여 원래 값으로 수정하세요.

---

## 부록: 전체 Signal 조건 요약

### Threshold Summary

| Stage | Threshold | Signal Type | Description |
|-------|-----------|-------------|-------------|
| **E (Earnings)** | `1.0` | Binary (0/1) | 이전 대비 성장 필수 |
| **F (Fundamental)** | `1.0` | Binary (0/1) | MarketCap + 성장률 10% |
| **W (Weekly)** | `1.0` | Binary (0/1) | 5가지 조건 모두 만족 |
| **RS (Relative Strength)** | `1.0` | Binary (0/1) | RS_4W >= 90 |
| **D (Daily)** | `0.5` | Weighted (0~1) | 브레이크아웃 + 기본 조건 |

### 코드 위치 빠른 참조

| Signal | signal_generation_service.py | staged_signal_service.py |
|--------|------------------------------|--------------------------|
| **E** | Lines 461-502 | Lines 148-244 |
| **F** | Lines 392-459 | Lines 247-351 |
| **W** | Lines 298-343 | Lines 354-453 |
| **RS** | Lines 345-390 | Lines 456-540 |
| **D** | Lines 504-615 | Lines 543-700 |
| **Final** | Lines 617-658 | - |

### 문서 위치

- **종합 가이드**: `docs/SIGNAL_CONDITIONS_GUIDE.md` (본 문서)
- **상세 명세**: `docs/CURRENT_SIGNAL_CONDITIONS.md`
- **변경 방법**: `docs/HOW_TO_CHANGE_SIGNAL_CONDITIONS.md`
- **Signal 규칙**: `docs/interfaces/STRATEGY_SIGNAL_RULES.md`

### 테스트 파일

- **Fundamental 통일 테스트**: `Test/test_fundamental_signal_unified.py`
- **Menu 일관성 테스트**: `Test/test_menu_consistency.py`

---

**조건 변경은 신중하게!**
**변경 후 반드시 테스트로 검증하세요!**

---

*Version: 1.0 | Last Updated: 2025-10-18*
