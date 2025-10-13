# 백테스트 vs 오토 트레이딩 데이터 사용 검증

## ✅ 올바른 데이터 사용 규칙

### 데이터 타입별 사용 시점:

| 데이터 타입 | 백테스트 | 오토 트레이딩 | 이유 |
|------------|----------|---------------|------|
| **RS** (상대강도) | T-1 (전날) | T-1 (전날) | 당일 RS는 장 마감 후 계산되므로 전날 값 사용 |
| **D** (일봉) | T-1 (전날) | T-1 (전날) | 당일 종가는 장 마감 후에만 확정되므로 전날 값 사용 |
| **W** (주봉) | T (최신) | T (최신) | 주봉은 금요일 종가 기준, 충분히 확정된 데이터 |
| **F** (펀더멘털) | T (최신) | T (최신) | 분기별 데이터, 이미 공시된 확정 데이터 |
| **E** (어닝스) | T (최신) | T (최신) | 분기별 실적, 이미 발표된 확정 데이터 |

### 중요한 차이점:

**RS와 D는 항상 T-1 사용**:
- 백테스트든 실거래든 상관없이 **전날 데이터** 사용
- 이유: 당일 종가와 RS는 장 마감 후에야 확정되므로, 당일 아침 매매 판단 시 사용 불가

**W, F, E는 항상 T 사용**:
- 백테스트든 실거래든 상관없이 **최신 데이터** 사용
- 이유: 이미 충분히 과거에 확정된 데이터 (주간, 분기별)

## 백테스트 특별 요구사항

### 시계열 신호 생성:
백테스트는 **단일 시점 신호가 아닌 전체 기간의 시계열 신호**를 생성해야 함

```python
# 오토 트레이딩 (단일 시점)
signal = generate_signal(symbol, date='2024-10-12')
# 결과: {'signal': 1, 'strength': 0.8, ...}

# 백테스트 (시계열)
signals = generate_signals_timeseries(symbol, start='2023-01-01', end='2024-10-12')
# 결과: DataFrame with columns ['Date', 'signal', 'strength', 'target_price', 'losscut_price', ...]
#       2023-01-01    0       0.0        0.0           0.0
#       2023-01-02    1       0.8      150.0         140.0
#       ...
```

## 현재 구현 상태

### 1. 수정 필요한 내용

#### ❌ 잘못된 접근:
현재 `backtest_mode` 파라미터로 T vs T-1 구분 시도
→ **불필요함! RS/D는 항상 T-1, W/F/E는 항상 T**

#### ✅ 올바른 접근:
1. **데이터 타입별로 고정된 오프셋 사용**
   - RS, D: 항상 `iloc[-2]` (T-1)
   - W, F, E: 항상 `iloc[-1]` (T)

2. **백테스트는 시계열 신호 생성 함수 별도 구현**
   - `generate_comprehensive_signals()`: 단일 시점 신호 (오토 트레이딩용)
   - `generate_signals_timeseries()`: 전체 기간 시계열 신호 (백테스트용) ← **신규 필요**

### 2. 수정 필요한 함수들

#### RS와 D (항상 T-1):
- `_generate_rs_signals()`: `iloc[-2]` 고정
- `_generate_daily_rs_combined_signals()`: `iloc[-2]` 고정

#### W, F, E (항상 T):
- `_generate_weekly_signals()`: `iloc[-1]` 유지
- `_generate_fundamental_signals()`: `iloc[-1]` 유지
- `_generate_earnings_signals()`: `iloc[-1]` 유지

### 3. Main 파일 수정 필요

**main_auto_trade.py**:

```python
# 백테스트 시
signal_service = SignalGenerationService(
    config,
    backtest_mode=True  # ← 추가 필요
)

# 오토 트레이딩 시
signal_service = SignalGenerationService(
    config,
    backtest_mode=False  # ← 추가 필요 (또는 생략 가능, default=False)
)
```

## 올바른 데이터 사용

### 백테스트 (backtest_mode=True)
- **목적**: 과거 데이터로 전략 검증
- **데이터 사용**: `iloc[-2]` (T-1, 전날 종가)
- **시그널**: 전날 종가 기준으로 오늘 매매 시그널 생성
- **예시**:
  - 2024-10-11 종가로 → 2024-10-12 매수/매도 결정
  - 2024-10-12 종가로 → 2024-10-13 매수/매도 결정

### 오토 트레이딩 (backtest_mode=False)
- **목적**: 실시간 매매
- **데이터 사용**: `iloc[-1]` (T, 최신 데이터)
- **시그널**: 최신 데이터 기준으로 내일 매매 시그널 생성
- **예시**:
  - 2024-10-12 종가로 → 2024-10-13 매수/매도 결정 (장 전 준비)

## 다음 단계

1. **나머지 signal 함수들 수정**:
   - _generate_weekly_signals()
   - _generate_rs_signals()
   - _generate_fundamental_signals()
   - _generate_earnings_signals()
   - _generate_sell_signals()

2. **main_auto_trade.py 수정**:
   - run_auto_backtest(): backtest_mode=True 전달
   - run_auto_trading(): backtest_mode=False 전달

3. **테스트**:
   - 백테스트 실행하여 T-1 데이터 사용 확인
   - 오토 트레이딩에서 T 데이터 사용 확인

## 중요 노트

**Look-ahead bias 방지**:
- 백테스트에서 `iloc[-1]` (오늘 종가)을 사용하면 미래 정보를 이용한 것이 되어 부정확한 결과 발생
- 반드시 `iloc[-2]` (전날 종가)를 사용하여 실제 거래 환경 모사
