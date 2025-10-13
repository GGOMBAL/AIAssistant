# Signal Generation Detailed Specification

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Strategy Agent

---

## 1. Algorithm Details

### 1.1. 종합 신호 생성 알고리즘

Strategy Layer의 핵심은 다중 타임프레임 분석을 통한 종합 매매 신호 생성입니다.

#### Flow Chart:
```
Input: df_daily, df_weekly, df_rs, df_fundamental, df_earnings
    ↓
[Step 1] Weekly Signal Generation (주봉 신호)
    ↓
[Step 2] RS Signal Generation (상대강도 신호)
    ↓
[Step 3] Fundamental Signal Generation (펀더멘털 신호)
    ↓
[Step 4] Earnings Signal Generation (어닝스 신호)
    ↓
[Step 5] Daily + RS Combined Signal (일봉+RS 결합)
    ↓
[Step 6] Signal Combination (최종 신호 결합)
    ↓
Output: {final_signal, signal_strength, components, target_price, losscut_price}
```

---

### 1.2. 주봉 신호 생성 알고리즘 (Weekly Signal)

**목적**: 장기 추세 확인 및 구조적 강세 판단

**입력**: df_weekly (DataFrame with columns: Wopen, Whigh, Wlow, Wclose, 52_H, 52_L, 1Year_H, 1Year_L, 2Year_H, 2Year_L)

**알고리즘**:
```python
def _generate_weekly_signals(df_weekly: pd.DataFrame) -> int:
    """
    5가지 조건을 모두 만족해야 신호 발생
    """
    if len(df_weekly) < 3:
        return 0

    latest = df_weekly.iloc[-1]
    prev_1 = df_weekly.iloc[-2]
    prev_2 = df_weekly.iloc[-3]

    # Condition 1: 1년 고점 == 2년 고점 (신고가 갱신)
    w_condition1 = latest['1Year_H'] == latest['2Year_H']

    # Condition 2: 2년 저점 < 1년 저점 (상승 추세)
    w_condition2 = latest['2Year_L'] < latest['1Year_L']

    # Condition 3: 52주 고점이 안정적 (급등 후 조정 아님)
    w_condition3 = latest['52_H'] <= prev_2['52_H'] * 1.05

    # Condition 4: 전주 종가가 52주 저점보다 30% 이상 높음
    w_condition4 = prev_1['Wclose'] > latest['52_L'] * 1.3

    # Condition 5: 전주 종가가 52주 고점 대비 70% 이상
    w_condition5 = prev_1['Wclose'] > latest['52_H'] * 0.7

    # 모든 조건 AND 결합
    if all([w_condition1, w_condition2, w_condition3, w_condition4, w_condition5]):
        return 1
    else:
        return 0
```

**조건 상세 설명**:

1. **w_condition1**: `1Year_H == 2Year_H`
   - 1년 최고가 = 2년 최고가 → 최근 1년 내 신고가 갱신
   - 의미: 장기 상승 추세 확인

2. **w_condition2**: `2Year_L < 1Year_L`
   - 2년 최저가 < 1년 최저가 → 저점이 계속 높아짐
   - 의미: Higher Lows 패턴 (상승 추세)

3. **w_condition3**: `52_H <= 52_H.shift(2) * 1.05`
   - 52주 고점이 2주 전 대비 5% 이내 상승
   - 의미: 급등 후 조정이 아닌 안정적 상승

4. **w_condition4**: `Wclose.shift(1) > 52_L * 1.3`
   - 전주 종가 > 52주 저점 × 1.3
   - 의미: 저점 대비 최소 30% 이상 회복 (충분한 상승)

5. **w_condition5**: `Wclose.shift(1) > 52_H * 0.7`
   - 전주 종가 > 52주 고점 × 0.7
   - 의미: 고점 대비 30% 이내 조정 (강한 추세)

**반환**: 0 (조건 미충족) 또는  1 (조건 충족)

**시간 복잡도**: O(1)

---

### 1.3. RS 신호 생성 알고리즘 (Relative Strength Signal)

**목적**: 시장 대비 상대적 강세 확인

**입력**: df_rs (DataFrame with columns: RS_4W, RS_12W, Sector, Industry, Sector_RS_4W)

**알고리즘**:
```python
def _generate_rs_signals(df_rs: pd.DataFrame) -> int:
    """
    RS 4주 기준 상위 10% 이내 종목 선정
    """
    if df_rs.empty:
        return 0

    latest = df_rs.iloc[-1]
    rs_4w = latest['RS_4W']

    # RS >= 90: 상위 10% 이내
    if rs_4w >= 90:
        return 1
    else:
        return 0
```

**RS 계산 방법** (Indicator Layer에서 계산됨):
```
RS_4W = (현재 가격 / 4주 전 가격) 대비 시장 전체 종목 순위 백분위
```

**임계값 설명**:
- `RS >= 90`: 상위 10% → 매우 강한 상대 강도
- `RS >= 80`: 상위 20% → 강한 상대 강도 (옵션)
- `RS >= 70`: 상위 30% → 보통 상대 강도 (옵션)

**반환**: 0 또는 1

**시간 복잡도**: O(1)

---

### 1.4. 펀더멘털 신호 생성 알고리즘 (Fundamental Signal)

**목적**: 기업의 재무 건전성 및 성장성 확인

**입력**: df_fundamental (DataFrame with columns: MarketCapitalization, REV_YOY, EPS_YOY, revenue, PBR, ROE)

**알고리즘** (미국 시장):
```python
def _generate_fundamental_signals(df_fundamental: pd.DataFrame, area: str) -> int:
    """
    시가총액, 매출 성장, EPS 성장 기준 필터링
    """
    if df_fundamental.empty:
        return 0

    latest = df_fundamental.iloc[-1]

    if area == 'US':
        market_cap = latest['MarketCapitalization']
        rev_yoy = latest['REV_YOY']
        eps_yoy = latest['EPS_YOY']
        revenue = latest['revenue']

        # 이전 분기 데이터
        if len(df_fundamental) >= 2:
            prev = df_fundamental.iloc[-2]
            prev_rev_yoy = prev['REV_YOY']
            prev_eps_yoy = prev['EPS_YOY']
        else:
            prev_rev_yoy = 0
            prev_eps_yoy = 0

        # 6가지 조건
        f_condition1 = market_cap >= 2_000_000_000     # 시가총액 >= $2B
        f_condition2 = market_cap <= 20_000_000_000_000  # 시가총액 <= $20T
        f_condition3 = rev_yoy >= 0.1                  # 매출 YoY >= 10%
        f_condition4 = prev_rev_yoy >= 0               # 전기 매출 YoY >= 0%
        f_condition6 = eps_yoy >= 0.1                  # EPS YoY >= 10%
        f_condition7 = prev_eps_yoy >= 0               # 전기 EPS YoY >= 0%
        f_condition9 = revenue > 0                     # 매출 > 0

        # 최종 조건: (매출 성장) OR (EPS 성장) + 기본 조건
        if f_condition1 and f_condition9:
            if (f_condition3 and f_condition4) or (f_condition6 and f_condition7):
                return 1

    elif area == 'KR':
        market_cap = latest['capital']
        eps = latest['eps']

        # 한국 시장 조건
        condition1 = market_cap >= 100_000_000_000     # 시가총액 >= 1000억원
        condition2 = market_cap <= 20_000_000_000_000  # 시가총액 <= 20조원
        condition3 = eps > 0                           # EPS > 0

        if all([condition1, condition2, condition3]):
            return 1

    return 0
```

**조건 상세**:

미국 시장 (US):
1. **시가총액 필터**: $2B ~ $20T (중대형주 중심)
2. **매출 성장**: 현재 분기 YoY >= 10% AND 전 분기 YoY >= 0%
3. **EPS 성장**: 현재 분기 YoY >= 10% AND 전 분기 YoY >= 0%
4. **매출 조건**: OR 로직 - 매출 또는 EPS 중 하나라도 성장하면 OK

한국 시장 (KR):
1. **시가총액 필터**: 1000억원 ~ 20조원
2. **수익성**: EPS > 0 (흑자 기업)

**반환**: 0 또는 1

**시간 복잡도**: O(1)

---

### 1.5. 어닝스 신호 생성 알고리즘 (Earnings Signal)

**목적**: 실적 발표 후 긍정적 서프라이즈 확인

**입력**: df_earnings (DataFrame with columns: EarningDate, eps, eps_yoy, revenue, rev_yoy)

**알고리즘**:
```python
def _generate_earnings_signals(df_earnings: pd.DataFrame) -> int:
    """
    최근 어닝스 대비 성장 확인
    """
    if df_earnings.empty or len(df_earnings) < 2:
        return 0

    latest = df_earnings.iloc[-1]
    previous = df_earnings.iloc[-2]

    # 매출 성장 조건
    rev_condition1 = previous['rev_yoy'] >= 0
    rev_condition2 = latest['rev_yoy'] > previous['rev_yoy']

    # EPS 성장 조건
    eps_condition1 = previous['eps_yoy'] >= 0
    eps_condition2 = latest['eps_yoy'] > previous['eps_yoy']

    # 둘 중 하나라도 성장
    if (rev_condition1 and rev_condition2) or (eps_condition1 and eps_condition2):
        return 1
    else:
        return 0
```

**조건 상세**:
1. **매출 성장 패턴**:
   - 이전 분기 rev_yoy >= 0% (적어도 전년 동기 대비 유지)
   - 현재 분기 rev_yoy > 이전 분기 (가속 성장)

2. **EPS 성장 패턴**:
   - 이전 분기 eps_yoy >= 0%
   - 현재 분기 eps_yoy > 이전 분기 (가속 성장)

**의미**: 분기별 성장률이 가속되는 종목 선호 (Earnings Momentum)

**반환**: 0 또는 1

**시간 복잡도**: O(1)

---

### 1.6. 일봉 + RS 결합 신호 알고리즘 (Daily + RS Combined)

**목적**: 단기 브레이크아웃 타이밍 포착 및 목표가/손절가 계산

**입력**: df_daily, df_rs

**알고리즘**:
```python
def _generate_daily_rs_combined_signals(df_daily, df_rs) -> Dict:
    """
    다양한 타임프레임 브레이크아웃 감지
    우선순위: 2Y > 1Y > 6M > 3M > 1M
    """
    if df_daily.empty:
        return {'signal': 0, 'target_price': 0, 'losscut_price': 0, 'signal_type': None}

    latest = df_daily.iloc[-1]

    # RS 조건
    rs_condition = 0
    rs_12w_condition = 0
    if df_rs is not None and not df_rs.empty:
        rs_latest = df_rs.iloc[-1]
        rs_condition = 1 if rs_latest['RS_4W'] >= 90 else 0
        rs_12w_condition = 1 if rs_latest['RS_12W'] >= 90 else 0

    # 일봉 기본 조건
    sma200_momentum = latest['SMA200_M'] > 0    # SMA200 상승 추세
    sma_condition = latest['SMA200'] < latest['SMA50']  # SMA50 > SMA200

    base_conditions = sma200_momentum and sma_condition and rs_condition

    if not base_conditions and not rs_12w_condition:
        return {'signal': 0, 'target_price': 0, 'losscut_price': 0, 'signal_type': None}

    # 브레이크아웃 체크 (우선순위 순서)
    current_high = latest['Dhigh']
    timeframes = ['2Y', '1Y', '6M', '3M', '1M']

    for tf in timeframes:
        highest_col = f'Highest_{tf}'
        highest_value = latest[highest_col]

        if highest_value == 0:
            continue

        # 백테스트 모드: 브레이크아웃 완료 (<=)
        # 실거래 모드: 브레이크아웃 직전 (>)
        if trading_mode:
            breakout = highest_value > current_high
        else:
            breakout = highest_value <= current_high

        if base_conditions and breakout:
            return {
                'signal': 1,
                'target_price': float(highest_value),
                'losscut_price': float(highest_value * 0.97),  # -3% 손절
                'signal_type': f'Breakout_{tf}'
            }

    # RS_12W + 1M 추가 조건
    if rs_12w_condition:
        highest_1m = latest['Highest_1M']
        if trading_mode:
            condition_1m = highest_1m > current_high
        else:
            condition_1m = highest_1m <= current_high

        if condition_1m and highest_1m > 0:
            return {
                'signal': 1,
                'target_price': float(highest_1m),
                'losscut_price': float(highest_1m * 0.97),
                'signal_type': 'RS_12W_1M'
            }

    return {'signal': 0, 'target_price': 0, 'losscut_price': 0, 'signal_type': None}
```

**기본 조건**:
1. `SMA200_M > 0`: SMA200이 상승 추세 (장기 상승)
2. `SMA50 > SMA200`: 단기 이동평균이 장기 이동평균 위 (Golden Cross)
3. `RS_4W >= 90`: 상대 강도 상위 10%

**브레이크아웃 타입** (우선순위 순서):
1. **Breakout_2Y**: 2년 신고가 돌파 → 가장 강력한 신호
2. **Breakout_1Y**: 1년 신고가 돌파
3. **Breakout_6M**: 6개월 신고가 돌파
4. **Breakout_3M**: 3개월 신고가 돌파
5. **Breakout_1M**: 1개월 신고가 돌파
6. **RS_12W_1M**: RS_12W >= 90 + 1개월 신고가 돌파

**목표가 계산**:
```
target_price = 브레이크아웃 기준가 (Highest_XX)
```

**손절가 계산**:
```
losscut_price = target_price × 0.97  (기준가 대비 -3%)
```

**반환**: Dict with keys: signal, target_price, losscut_price, signal_type

**시간 복잡도**: O(1) (최대 5회 루프)

---

### 1.7. 최종 신호 결합 알고리즘 (Signal Combination)

**목적**: 개별 신호를 결합하여 최종 BUY/HOLD 결정

**입력**: signal_components (Dict with keys: weekly, rs, fundamental, earnings, daily_rs)

**알고리즘**:
```python
def _combine_signals(signal_components: Dict, area: str) -> Dict:
    """
    미국 시장: 4개 신호 모두 충족 시 BUY
    한국 시장: 3개 신호 모두 충족 시 BUY
    """
    weekly = signal_components['weekly']
    daily_rs = signal_components['daily_rs']
    rs = signal_components['rs']
    fundamental = signal_components.get('fundamental', 0)
    earnings = signal_components.get('earnings', 0)

    # 최종 매수 조건
    if area == 'US':
        # 미국: 4개 필수 조건 (weekly + daily_rs + rs + fundamental)
        buy_condition = (weekly == 1 and
                        daily_rs == 1 and
                        rs == 1 and
                        fundamental == 1)
        max_signals = 5
    else:
        # 한국: 3개 필수 조건 (weekly + daily_rs + rs)
        buy_condition = (weekly == 1 and
                        daily_rs == 1 and
                        rs == 1)
        max_signals = 3

    # 신호 강도 계산
    total_signals = sum([weekly, daily_rs, rs, fundamental, earnings])
    signal_strength = total_signals / max_signals

    # 신뢰도 계산
    if buy_condition:
        confidence = 0.7  # 모든 조건 만족 시 70% 신뢰도
    else:
        confidence = signal_strength * 0.5  # 부분 신호는 최대 50%

    # 최종 신호
    final_signal = SignalType.BUY if buy_condition else SignalType.HOLD

    return {
        'signal': final_signal,
        'strength': signal_strength,
        'confidence': confidence
    }
```

**매수 조건 요약**:

**미국 시장 (US)**:
```
BUY = weekly(1) AND daily_rs(1) AND rs(1) AND fundamental(1)
```
- 4개 필수 조건 모두 충족 (earnings는 선택)

**한국 시장 (KR)**:
```
BUY = weekly(1) AND daily_rs(1) AND rs(1)
```
- 3개 필수 조건 모두 충족 (fundamental, earnings는 선택)

**신호 강도** (Signal Strength):
```
signal_strength = (발생한 신호 개수) / (최대 신호 개수)
```
- US: 최대 5개 (weekly, daily_rs, rs, fundamental, earnings)
- KR: 최대 3개 (weekly, daily_rs, rs)

**신뢰도** (Confidence):
```
confidence = 0.7 if buy_condition else signal_strength * 0.5
```
- BUY 조건 충족: 70%
- 부분 신호: 최대 50%

**반환**: Dict with keys: signal, strength, confidence

**시간 복잡도**: O(1)

---

## 2. Performance Characteristics

### 2.1. 시간 복잡도 분석

| 메서드 | 시간 복잡도 | 설명 |
|--------|------------|------|
| generate_comprehensive_signals | O(1) | 모든 하위 메서드 O(1) |
| _generate_weekly_signals | O(1) | 최근 3개 데이터만 접근 |
| _generate_rs_signals | O(1) | 최근 1개 데이터만 접근 |
| _generate_fundamental_signals | O(1) | 최근 2개 데이터만 접근 |
| _generate_earnings_signals | O(1) | 최근 2개 데이터만 접근 |
| _generate_daily_rs_combined | O(1) | 최대 5회 루프 (상수) |
| _combine_signals | O(1) | 단순 사칙연산 |

**전체 시간 복잡도**: O(1) - 상수 시간

### 2.2. 공간 복잡도 분석

| 데이터 | 메모리 사용량 | 설명 |
|--------|-------------|------|
| df_daily | ~1 MB | 500일 × 20컬럼 |
| df_weekly | ~100 KB | 104주 × 15컬럼 |
| df_rs | ~50 KB | 52주 × 10컬럼 |
| df_fundamental | ~10 KB | 4분기 × 15컬럼 |
| df_earnings | ~10 KB | 4분기 × 10컬럼 |
| **합계** | **~1.2 MB/종목** | |

**500개 종목**: ~600 MB

### 2.3. 처리 속도

| 작업 | 소요 시간 | 환경 |
|------|----------|------|
| 단일 종목 신호 생성 | < 10 ms | Intel i7, 16GB RAM |
| 100개 종목 배치 처리 | < 1초 | 순차 처리 |
| 500개 종목 배치 처리 | < 5초 | 순차 처리 |
| 500개 종목 (병렬) | < 2초 | ThreadPoolExecutor(8) |

### 2.4. 최적화 전략

1. **캐싱**:
   ```python
   self.signals_cache[symbol] = signal_result
   ```
   - 동일 종목 중복 계산 방지

2. **병렬 처리**:
   ```python
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=8) as executor:
       results = executor.map(generate_signal, symbols)
   ```

3. **조기 종료** (Early Exit):
   ```python
   if df_daily.empty:
       return default_signal  # 불필요한 계산 생략
   ```

---

## 3. Data Flow

### 3.1. 전체 데이터 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                    Indicator Layer                          │
│  (DataFrameGenerator)                                       │
│                                                             │
│  df_D: Daily Data (OHLCV + Indicators)                     │
│  df_W: Weekly Data (52W High/Low, 1Y/2Y High/Low)         │
│  df_RS: Relative Strength (RS_4W, RS_12W)                 │
│  df_F: Fundamental (MarketCap, REV_YOY, EPS_YOY)          │
│  df_E: Earnings (eps_yoy, rev_yoy)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Strategy Layer (SignalGenerationService)       │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐         │
│  │  Weekly    │  │     RS     │  │ Fundamental  │         │
│  │  Signal    │  │   Signal   │  │   Signal     │         │
│  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘         │
│        │                │                │                 │
│        └────────────────┼────────────────┘                 │
│                         │                                  │
│               ┌─────────┴─────────┐                        │
│               │  Daily + RS       │                        │
│               │  Combined Signal  │                        │
│               └─────────┬─────────┘                        │
│                         │                                  │
│               ┌─────────┴─────────┐                        │
│               │  Signal           │                        │
│               │  Combination      │                        │
│               └─────────┬─────────┘                        │
│                         │                                  │
│                         ↓                                  │
│      final_signal, signal_strength, target_price,         │
│      losscut_price, signal_type, confidence               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
│  (DailyBacktestService / OrderManager)                     │
│                                                             │
│  - 포지션 크기 계산                                          │
│  - 주문 실행                                                │
│  - 백테스트 실행                                            │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. 상태 전이도 (State Transition)

```
[HOLD 상태]
     │
     │ (weekly=1 AND daily_rs=1 AND rs=1 AND fundamental=1)
     │
     ↓
[BUY Signal 발생]
     │
     │ target_price, losscut_price 설정
     │
     ↓
[Position 진입 대기]
     │
     │ Service Layer에서 실제 매수
     │
     ↓
[Position 보유 중]
     │
     ├─→ (현재가 <= losscut_price) → [SELL - Loss Cut]
     │
     ├─→ (현재가 >= target_price) → [SELL - Profit Taking]
     │
     └─→ (daily_rs=0 OR rs=0) → [SELL - Signal Weakening]
```

---

## 4. Configuration

### 4.1. 신호 생성 파라미터

Strategy Layer는 설정 파일을 직접 사용하지 않고, 초기화 파라미터로 제어합니다.

```python
signal_service = SignalGenerationService(
    area='US',           # 'US' or 'KR'
    trading_mode=False   # False: 백테스트, True: 실거래
)
```

### 4.2. 파라미터 설명

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| area | str | 'US' | 시장 지역 ('US', 'KR') |
| trading_mode | bool | False | 실거래 모드 (True: 브레이크아웃 직전 매수) |

### 4.3. 조정 가능한 임계값

코드 내부에서 조정 가능한 임계값들:

```python
# RS 신호 임계값
RS_THRESHOLD = 90  # 상위 10%

# 펀더멘털 임계값 (미국)
MIN_MARKET_CAP = 2_000_000_000        # $2B
MAX_MARKET_CAP = 20_000_000_000_000   # $20T
MIN_REV_YOY = 0.1                     # 10%
MIN_EPS_YOY = 0.1                     # 10%

# 손절가 비율
LOSSCUT_RATIO = 0.97  # -3%

# 주봉 안정성 조건
WEEKLY_HIGH_TOLERANCE = 1.05   # 52주 고점 5% 이내
WEEKLY_LOW_MULTIPLIER = 1.3    # 52주 저점 대비 30%
WEEKLY_HIGH_THRESHOLD = 0.7    # 52주 고점 대비 70%
```

### 4.4. 권장 설정값

**보수적 전략** (False Positive 최소화):
```python
RS_THRESHOLD = 95          # 상위 5%
MIN_REV_YOY = 0.2          # 20%
MIN_EPS_YOY = 0.2          # 20%
LOSSCUT_RATIO = 0.95       # -5% 손절
```

**공격적 전략** (True Positive 최대화):
```python
RS_THRESHOLD = 85          # 상위 15%
MIN_REV_YOY = 0.05         # 5%
MIN_EPS_YOY = 0.05         # 5%
LOSSCUT_RATIO = 0.98       # -2% 손절
```

---

## 5. Testing Strategy

### 5.1. 단위 테스트

각 신호 생성 메서드별 독립 테스트:

```python
# Test/test_signal_generation_service.py

def test_weekly_signal_all_conditions_met():
    """주봉 신호 - 모든 조건 충족"""
    df_weekly = create_mock_weekly_data(
        latest={'1Year_H': 100, '2Year_H': 100, '2Year_L': 50, '1Year_L': 60,
                '52_H': 95, 'Wclose': 90, '52_L': 55},
        prev_1={'Wclose': 85},
        prev_2={'52_H': 92}
    )

    service = SignalGenerationService()
    signal = service._generate_weekly_signals(df_weekly)

    assert signal == 1

def test_rs_signal_threshold():
    """RS 신호 - 임계값 테스트"""
    df_rs = pd.DataFrame({'RS_4W': [90]})

    service = SignalGenerationService()
    signal = service._generate_rs_signals(df_rs)

    assert signal == 1

    df_rs = pd.DataFrame({'RS_4W': [89.9]})
    signal = service._generate_rs_signals(df_rs)

    assert signal == 0
```

### 5.2. 통합 테스트

전체 신호 생성 흐름 테스트:

```python
def test_comprehensive_signal_buy_condition():
    """종합 신호 - BUY 조건 테스트"""
    service = SignalGenerationService(area='US')

    result = service.generate_comprehensive_signals(
        df_daily=create_mock_daily(),
        df_weekly=create_mock_weekly(),
        df_rs=create_mock_rs(),
        df_fundamental=create_mock_fundamental(),
        df_earnings=create_mock_earnings()
    )

    assert result['final_signal'] == SignalType.BUY
    assert result['signal_strength'] >= 0.8
    assert result['target_price'] > 0
    assert result['losscut_price'] > 0
```

### 5.3. 백테스트 검증

실제 과거 데이터로 신호 정확도 검증:

```python
def test_backtest_signal_accuracy():
    """백테스트 - 신호 정확도"""
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    start_date = '2023-01-01'
    end_date = '2023-12-31'

    # 실제 데이터 로드
    generator = DataFrameGenerator(symbols, start_day=start_date, end_day=end_date)
    generator.load_data_from_database()

    service = SignalGenerationService(area='US')

    buy_signals = []
    for symbol in symbols:
        result = service.generate_comprehensive_signals(
            df_daily=generator.df_D[symbol],
            df_weekly=generator.df_W[symbol],
            df_rs=generator.df_RS[symbol],
            df_fundamental=generator.df_F[symbol]
        )

        if result['final_signal'] == SignalType.BUY:
            buy_signals.append((symbol, result))

    # 신호 발생 종목 수 검증
    assert len(buy_signals) > 0

    # 신호 강도 검증
    for symbol, signal in buy_signals:
        assert signal['signal_strength'] >= 0.6
```

### 5.4. 주요 테스트 케이스

| 테스트 케이스 | 입력 | 예상 출력 | 목적 |
|-------------|------|----------|------|
| 모든 조건 충족 | weekly=1, rs=1, daily_rs=1, fundamental=1 | BUY, strength=0.8 | 정상 BUY 신호 |
| Weekly 조건 실패 | weekly=0, others=1 | HOLD, strength=0.6 | Weekly 필수 확인 |
| RS 조건 실패 | rs=0, others=1 | HOLD, strength=0.6 | RS 필수 확인 |
| Fundamental 조건 실패 | fundamental=0, others=1 | HOLD, strength=0.6 | Fundamental 필수 (US) |
| 빈 데이터 | df_daily=empty | HOLD, strength=0.0 | 에러 처리 |
| 불충분한 데이터 | len(df_weekly)=2 | HOLD, strength=0.0 | 데이터 검증 |

---

## 6. Known Limitations

### 6.1. 데이터 요구사항

| 제약사항 | 최소 요구 | 이유 |
|---------|---------|------|
| 일간 데이터 | 200일 | SMA200 계산 필요 |
| 주간 데이터 | 3주 | shift(2) 연산 필요 |
| RS 데이터 | 1주 | 최신 RS 필요 |
| Fundamental 데이터 | 2분기 | YoY 비교 필요 |
| Earnings 데이터 | 2분기 | 성장률 비교 필요 |

### 6.2. 알려진 이슈

1. **주봉 조건 5 (w_condition5) 과도한 제한**:
   ```python
   w_condition5 = prev_1['Wclose'] > latest['52_H'] * 0.7
   ```
   - 문제: 52주 고점 대비 70% 이상 요구 → 너무 엄격
   - 영향: 정상적인 조정 후 반등 종목도 필터링됨
   - 해결방안: 60% 또는 50%로 완화 검토

2. **Fundamental MarketCap 임계값**:
   ```python
   market_cap >= 2_000_000_000  # $2B
   ```
   - 문제: 중소형 성장주 배제
   - 영향: 초기 성장 단계 종목 누락
   - 해결방안: $500M ~ $1B로 하향 조정 검토

3. **RS 데이터 의존성**:
   - 문제: RS 데이터 없으면 daily_rs 신호 0 처리
   - 영향: MongoDB에 RS 데이터 없는 종목은 매수 불가
   - 해결방안: RS 없을 시 대체 지표 사용 (Relative Momentum 등)

### 6.3. 성능 병목

1. **순차 처리**:
   - 현재: 500개 종목 → 5초
   - 병렬 처리 적용 시 → 2초 (60% 개선)

2. **중복 계산**:
   - 캐싱 미적용 시 동일 종목 재계산 발생
   - 해결: signals_cache 활용

---

## 7. Future Enhancements

### 7.1. 단기 개선사항 (1-3개월)

- [ ] **머신러닝 기반 신호 강도 예측**
  - 과거 신호 데이터 학습
  - 신호 강도를 0.0 ~ 1.0 범위로 예측
  - 기대 효과: 신호 정확도 15% 향상

- [ ] **동적 임계값 조정**
  - 시장 상황(Bull/Bear)에 따라 RS_THRESHOLD 자동 조정
  - POOR 시장: RS >= 95, GOOD 시장: RS >= 85

- [ ] **신호 백테스팅 자동화**
  - 각 신호 타입별 승률, 평균 수익률 추적
  - 저성과 신호 타입 자동 필터링

### 7.2. 중기 개선사항 (3-6개월)

- [ ] **멀티 타임프레임 최적화**
  - 15분봉, 60분봉 단기 시그널 추가
  - 장 중 실시간 신호 생성

- [ ] **섹터 로테이션 전략**
  - 섹터 RS 기반 우선순위 조정
  - 강한 섹터 내 종목 가중치 증가

- [ ] **실시간 신호 스트리밍**
  - WebSocket 기반 실시간 신호 푸시
  - 브레이크아웃 직전 알림

### 7.3. 장기 개선사항 (6개월+)

- [ ] **커스텀 전략 플러그인 시스템**
  - 사용자 정의 신호 조건 추가
  - YAML 기반 전략 설정

- [ ] **AI 기반 패턴 인식**
  - 차트 패턴 자동 감지 (Cup & Handle, Flag 등)
  - 신호 신뢰도 향상

---

## 8. Related Documents

- **STRATEGY_LAYER_INTERFACE.md**: 입출력 인터페이스 명세
- **STRATEGY_MODULES.md**: 모듈 설명 및 사용법
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스
- **docs/architecture/STRATEGY_AGENT_ARCHITECTURE.md**: Strategy Agent 아키텍처
- **refer/Strategy/Strategy_A.py**: 원본 전략 코드 (참고용)

---

**Last Updated**: 2025-10-09
**Managed by**: Strategy Agent
**Document Version**: 1.0
