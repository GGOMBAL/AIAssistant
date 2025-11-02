# 백테스트 vs 오토트레이딩 모드 구분

**최종 업데이트**: 2025-10-21
**적용 대상**: Indicator Agent, Strategy Agent, Service Agent

---

## 핵심 차이점

**백테스트와 오토트레이딩은 Highest 계산 방식이 다릅니다**

### 백테스트 모드 (is_backtest=True)
- **D-1 데이터로 Highest 계산** (미래 참조 방지)
- `.shift(1)`을 사용하여 당일 high 제외
- **목적**: 과거 데이터로 전략 검증
- **Look-ahead Bias 방지**: 당일 데이터로 당일 매매 결정 불가

### 오토트레이딩 모드 (is_backtest=False)
- **당일 데이터 포함하여 Highest 계산**
- `.shift(1)` 사용 안 함
- **목적**: 실시간 최고가 기준으로 거래
- **실시간 거래**: 당일 데이터를 포함하여 즉시 매매 판단

---

## 1. Highest 계산 방식 차이

### Highest_1M, Highest_3M, Highest_6M, Highest_1Y, Highest_2Y

#### 백테스트 모드:
```python
# is_backtest=True일 때

# Highest_1M = 과거 20일(D-20 ~ D-1)의 최고가
df['Highest_1M'] = df['Dhigh'].shift(1).rolling(window=20, min_periods=1).max()

# Highest_3M = 과거 50일(D-50 ~ D-1)의 최고가
df['Highest_3M'] = df['Dhigh'].shift(1).rolling(window=50, min_periods=1).max()

# Highest_6M = 과거 100일(D-100 ~ D-1)의 최고가
df['Highest_6M'] = df['Dhigh'].shift(1).rolling(window=100, min_periods=1).max()

# Highest_1Y = 과거 200일(D-200 ~ D-1)의 최고가
df['Highest_1Y'] = df['Dhigh'].shift(1).rolling(window=200, min_periods=1).max()

# Highest_2Y = 과거 400일(D-400 ~ D-1)의 최고가
df['Highest_2Y'] = df['Dhigh'].shift(1).rolling(window=400, min_periods=1).max()
```

#### 오토트레이딩 모드:
```python
# is_backtest=False일 때

# Highest_1M = 최근 20일(D-19 ~ D)의 최고가
df['Highest_1M'] = df['Dhigh'].rolling(window=20, min_periods=1).max()

# Highest_3M = 최근 50일(D-49 ~ D)의 최고가
df['Highest_3M'] = df['Dhigh'].rolling(window=50, min_periods=1).max()

# Highest_6M = 최근 100일(D-99 ~ D)의 최고가
df['Highest_6M'] = df['Dhigh'].rolling(window=100, min_periods=1).max()

# Highest_1Y = 최근 200일(D-199 ~ D)의 최고가
df['Highest_1Y'] = df['Dhigh'].rolling(window=200, min_periods=1).max()

# Highest_2Y = 최근 400일(D-399 ~ D)의 최고가
df['Highest_2Y'] = df['Dhigh'].rolling(window=400, min_periods=1).max()
```

---

## 2. 구현 방법

### DataFrameGenerator 초기화

```python
# project/indicator/data_frame_generator.py

from project.indicator.data_frame_generator import DataFrameGenerator

# 백테스트 모드
generator = DataFrameGenerator(
    universe=symbols,
    market='US',
    area='US',
    start_day=start_date,
    end_day=end_date,
    is_backtest=True  # ✅ 백테스트 모드: 미래 참조 방지
)

# 오토트레이딩 모드
generator = DataFrameGenerator(
    universe=symbols,
    market='US',
    area='US',
    start_day=start_date,
    end_day=end_date,
    is_backtest=False  # ✅ 트레이딩 모드: 당일 데이터 포함
)
```

### _post_process_dataframes 메서드 내부

```python
# project/indicator/data_frame_generator.py (라인 584-601)

def _post_process_dataframes(self):
    """Post-process dataframes to add calculated columns"""

    for symbol, df in self.df_D.items():
        if 'Dhigh' in df.columns:
            if self.is_backtest:
                # 백테스트 모드: shift(1) 사용 (D-1 데이터)
                df['Highest_1M'] = df['Dhigh'].shift(1).rolling(window=20, min_periods=1).max()
                df['Highest_3M'] = df['Dhigh'].shift(1).rolling(window=50, min_periods=1).max()
                df['Highest_6M'] = df['Dhigh'].shift(1).rolling(window=100, min_periods=1).max()
                df['Highest_1Y'] = df['Dhigh'].shift(1).rolling(window=200, min_periods=1).max()
                df['Highest_2Y'] = df['Dhigh'].shift(1).rolling(window=400, min_periods=1).max()
            else:
                # 오토트레이딩 모드: 당일 데이터 포함
                df['Highest_1M'] = df['Dhigh'].rolling(window=20, min_periods=1).max()
                df['Highest_3M'] = df['Dhigh'].rolling(window=50, min_periods=1).max()
                df['Highest_6M'] = df['Dhigh'].rolling(window=100, min_periods=1).max()
                df['Highest_1Y'] = df['Dhigh'].rolling(window=200, min_periods=1).max()
                df['Highest_2Y'] = df['Dhigh'].rolling(window=400, min_periods=1).max()

        # 다른 지표들...
```

---

## 3. 데이터 흐름

### 백테스트 모드 데이터 흐름:

```
main_auto_trade.py (run_backtest_staged)
  ↓ is_backtest=True
StagedPipelineService(is_backtest=True)
  ↓
StagedDataLoader(is_backtest=True)
  ↓
DataFrameGenerator(is_backtest=True)
  ↓
_post_process_dataframes()
  ↓ if is_backtest
Highest_1M = Dhigh.shift(1).rolling(20).max()  # D-1 데이터 사용
```

### 오토트레이딩 모드 데이터 흐름:

```
main_auto_trade.py (run_auto_trading)
  ↓ is_backtest=False
DataFrameGenerator(is_backtest=False)
  ↓
_post_process_dataframes()
  ↓ if not is_backtest
Highest_1M = Dhigh.rolling(20).max()  # 당일 데이터 포함
```

---

## 4. Breakout 신호 예시

### 백테스트 모드:

```python
# 2024-10-09 기준

Date:       2024-10-09
Dhigh:      150.0 (당일)
Highest_1M: 145.0 (2024-10-08까지의 최고가) ← shift(1) 적용

# Breakout 판단
if 150.0 > 145.0:  # Dhigh > Highest_1M
    signal = True  # ✅ Breakout 감지
```

**결과**: 당일 고가(150.0)가 전일까지의 최고가(145.0)를 돌파했으므로 매수 신호

### 오토트레이딩 모드:

```python
# 2024-10-09 실시간

Date:       2024-10-09 (실시간)
Dhigh:      150.0 (당일)
Highest_1M: 150.0 (2024-10-09까지의 최고가) ← shift(1) 미적용

# Breakout 판단
if 150.0 > 150.0:  # Dhigh > Highest_1M
    signal = False  # ❌ 아직 돌파 아님
```

**결과**: 당일 고가가 현재까지의 최고가와 같으므로 아직 돌파하지 않음

---

## 5. 관련 파일

### 1. `project/indicator/data_frame_generator.py`

**라인 38-55**: `__init__` 메서드에서 `is_backtest` 파라미터 수신
```python
def __init__(
    self,
    universe: List[str],
    market: str,
    area: str,
    start_day: datetime,
    end_day: datetime,
    is_backtest: bool = True  # ✅ 기본값 True (백테스트 모드)
):
    self.is_backtest = is_backtest
    # ...
```

**라인 584-601**: `_post_process_dataframes` 메서드에서 Highest 계산
```python
def _post_process_dataframes(self):
    """Calculate Highest columns based on is_backtest flag"""
    for symbol, df in self.df_D.items():
        if 'Dhigh' in df.columns:
            if self.is_backtest:
                # 백테스트: shift(1) 사용
                df['Highest_1M'] = df['Dhigh'].shift(1).rolling(20).max()
                # ...
            else:
                # 트레이딩: shift 없음
                df['Highest_1M'] = df['Dhigh'].rolling(20).max()
                # ...
```

### 2. `project/indicator/staged_data_loader.py`

**라인 30-46**: `__init__` 메서드
```python
def __init__(
    self,
    config: dict,
    market: str,
    area: str,
    start_day: datetime,
    end_day: datetime,
    is_backtest: bool = True  # ✅ is_backtest 파라미터 전달
):
    self.is_backtest = is_backtest
    # ...
```

**라인 73-81**: DataFrameGenerator 초기화
```python
def load_stage_data(self, stage: str, symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """Load data for specific stage"""

    generator = DataFrameGenerator(
        universe=symbols,
        market=self.market,
        area=self.area,
        start_day=self.start_day,
        end_day=self.end_day,
        is_backtest=self.is_backtest  # ✅ is_backtest 전달
    )
    # ...
```

### 3. `project/service/staged_pipeline_service.py`

**라인 35-61**: `__init__` 메서드
```python
def __init__(
    self,
    config: dict,
    market: str,
    area: str,
    start_day: datetime,
    end_day: datetime,
    is_backtest: bool = True  # ✅ is_backtest 파라미터
):
    self.is_backtest = is_backtest

    # StagedDataLoader 초기화
    self.data_loader = StagedDataLoader(
        config=config,
        market=market,
        area=area,
        start_day=start_day,
        end_day=end_day,
        is_backtest=is_backtest  # ✅ is_backtest 전달
    )
    # ...
```

### 4. `main_auto_trade.py`

**라인 690-697**: 백테스트 실행 (run_backtest_staged)
```python
async def run_backtest_staged(...):
    """Run backtest with staged pipeline"""

    pipeline = StagedPipelineService(
        config=config,
        market='US',
        area='US',
        start_day=data_start,
        end_day=end_date_dt,
        is_backtest=True  # ✅ 백테스트 모드
    )
    # ...
```

**라인 1573-1580**: 오토 트레이딩 실행 (run_auto_trading) - 향후 구현
```python
async def run_auto_trading(...):
    """Run auto trading in live mode"""

    generator = DataFrameGenerator(
        universe=symbols,
        market='US',
        area='US',
        start_day=start_date,
        end_day=end_date,
        is_backtest=False  # ✅ 트레이딩 모드
    )
    # ...
```

---

## 6. Look-ahead Bias 방지

### Look-ahead Bias란?
**미래 데이터를 사용하여 과거 의사결정을 하는 오류**

### 백테스트에서 Look-ahead Bias 예시:

```python
# ❌ 잘못된 예 - Look-ahead Bias 발생
# 2024-10-09에 매수 결정을 하는데, 2024-10-09의 최고가를 포함하여 계산
Highest_1M = df['Dhigh'].rolling(20).max()  # 당일 포함

# 당일(2024-10-09)의 최고가가 150.0이고,
# 전일까지의 최고가가 145.0일 때,
# Highest_1M = 150.0 (당일 포함)

# 매수 판단
if df['Dhigh'] > Highest_1M:  # 150.0 > 150.0
    buy_signal = False  # 돌파하지 못함

# 하지만 실제로는 전일까지의 최고가(145.0)를 돌파했으므로 매수해야 함!
```

```python
# ✅ 올바른 예 - Look-ahead Bias 방지
# 2024-10-09에 매수 결정을 할 때, 2024-10-08까지의 데이터만 사용
Highest_1M = df['Dhigh'].shift(1).rolling(20).max()  # 당일 제외

# Highest_1M = 145.0 (2024-10-08까지의 최고가)

# 매수 판단
if df['Dhigh'] > Highest_1M:  # 150.0 > 145.0
    buy_signal = True  # ✅ 올바른 돌파 신호
```

### 핵심 원칙:
**백테스트에서는 "당일 오픈 시점에 알 수 있는 정보"만 사용해야 합니다**

- ✅ **사용 가능**: D-1, D-2, ... 까지의 데이터
- ❌ **사용 불가**: D (당일)의 high, low, close 데이터

---

## 7. 테스트 검증

### 백테스트 모드 검증:
```python
def test_backtest_mode_highest_calculation():
    """Test Highest calculation in backtest mode"""

    # 테스트 데이터
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=30),
        'Dhigh': [100, 101, 102, 103, 104, 105, 110, 108, 107, 106] + [105] * 20
    })

    # 백테스트 모드
    generator = DataFrameGenerator(
        universe=['TEST'],
        market='US',
        area='US',
        start_day=df['Date'].min(),
        end_day=df['Date'].max(),
        is_backtest=True
    )

    # Highest_1M 계산
    highest = df['Dhigh'].shift(1).rolling(20).max()

    # 검증: 7번째 행 (2024-01-07)
    # Dhigh = 110
    # Highest_1M = 최고가(D-1 ~ D-20) = 105 (2024-01-06까지의 최고가)
    assert highest.iloc[6] == 105

    # Breakout 신호 발생
    assert df['Dhigh'].iloc[6] > highest.iloc[6]  # 110 > 105
```

### 오토트레이딩 모드 검증:
```python
def test_trading_mode_highest_calculation():
    """Test Highest calculation in trading mode"""

    # 테스트 데이터 동일

    # 트레이딩 모드
    generator = DataFrameGenerator(
        universe=['TEST'],
        market='US',
        area='US',
        start_day=df['Date'].min(),
        end_day=df['Date'].max(),
        is_backtest=False
    )

    # Highest_1M 계산
    highest = df['Dhigh'].rolling(20).max()

    # 검증: 7번째 행 (2024-01-07)
    # Dhigh = 110
    # Highest_1M = 최고가(D ~ D-19) = 110 (당일 포함)
    assert highest.iloc[6] == 110

    # Breakout 신호 발생하지 않음
    assert not (df['Dhigh'].iloc[6] > highest.iloc[6])  # 110 > 110 = False
```

---

## 참조 문서

- **MongoDB 규칙**: `docs/rules/MONGODB_RULES.md`
- **Indicator Layer 인터페이스**: `docs/interfaces/INDICATOR_LAYER_INTERFACE.md`
- **Strategy Layer 인터페이스**: `docs/interfaces/STRATEGY_LAYER_INTERFACE.md`
- **테스트 요약**: `Test/BACKTEST_VS_LIVE_TRADING_FIX_SUMMARY.md`
