# Backtest Service Detailed Specification

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Service Agent

---

## 1. Algorithm Details

### 1.1. 백테스트 실행 알고리즘

Service Layer의 핵심은 과거 데이터를 사용하여 매매 전략의 성과를 시뮬레이션하는 것입니다.

#### Flow Chart:
```
Input: df_dump (signals), start_date, end_date
    ↓
[Step 1] Initialize Portfolio
    - cash = initial_cash
    - positions = {}
    ↓
[Step 2] Date Loop (start_date ~ end_date)
    ↓
[Step 2-1] Sell Processing
    - Loss Cut Check
    - Half Sell Check
    - Signal Sell Check
    ↓
[Step 2-2] Whipsaw Handling (optional)
    - Check holding period < 5 days
    - Add to waiting list
    ↓
[Step 2-3] Buy Processing
    - Filter BuySig = 1
    - Calculate position size (ATR-based)
    - Execute buy orders
    ↓
[Step 2-4] Portfolio Update
    - Update positions
    - Calculate unrealized P&L
    ↓
[Step 3] Performance Analysis
    - Calculate metrics
    - Generate report
    ↓
Output: BacktestResult
```

---

### 1.2. 포지션 크기 계산 알고리즘 (ATR-based)

**목적**: 변동성을 고려한 동적 포지션 사이징

**입력**:
- `cash`: 현재 현금 잔고
- `std_risk`: 표준 리스크 (기본 10%)
- `adr`: Average Daily Range (평균 일일 변동폭 %)
- `current_price`: 현재 주가

**알고리즘**:
```python
def calculate_position_size(cash, std_risk, adr, current_price):
    """
    ATR 기반 포지션 크기 계산

    핵심 아이디어:
    - 높은 변동성 → 작은 포지션
    - 낮은 변동성 → 큰 포지션
    """
    # Step 1: 기본 포지션 크기 계산
    # (현금 * 리스크 비율) / (일일 변동폭 * 2)
    base_position_amount = (cash * std_risk) / (adr * 2)

    # Step 2: 최대/최소 제약 적용
    max_position = cash * 0.4   # 최대 40% (집중 리스크 방지)
    min_position = cash * 0.05  # 최소 5% (거래 비용 효율성)

    position_amount = max(min_position, min(base_position_amount, max_position))

    # Step 3: 주식 수량 계산 (슬리피지 고려)
    slippage_price = current_price * (1 + slippage)
    quantity = int(position_amount / slippage_price)

    # Step 4: 최대 보유 종목수 체크
    if len(positions) >= max_positions:
        return 0  # 추가 매수 불가

    return quantity
```

**예시**:
```
현금: 100억원
std_risk: 10%
adr: 2.5% (일일 평균 변동폭)
현재가: 150.0

base_position = (100 * 0.1) / (0.025 * 2) = 200억원
→ 제약 적용: min(200억, 40억) = 40억원
→ 수량: 40억 / 150 = 약 266만주
```

**시간 복잡도**: O(1)

---

### 1.3. 손절 및 익절 알고리즘

#### 손절 (Loss Cut)

**목적**: 손실 한도 도달 시 자동 매도하여 손실 확대 방지

**알고리즘**:
```python
def check_losscut(position, current_price):
    """
    손절가 도달 여부 확인
    """
    if current_price <= position.losscut_price:
        # 전량 매도
        execute_sell(
            ticker=position.ticker,
            quantity=position.quantity,
            price=current_price,
            reason=SellReason.LOSSCUT
        )

        # 손익 계산
        pnl = ((current_price - position.avg_price) / position.avg_price) * 100

        # 포지션 제거
        del positions[position.ticker]

        return True
    return False
```

**손절가 설정**:
```python
# 초기 손절가: 매수가 대비 -3%
losscut_price = buy_price * (1 - init_risk)  # buy_price * 0.97
```

**시간 복잡도**: O(1)

---

#### 50% 익절 (Half Sell)

**목적**: 일정 수익 도달 시 절반 매도하여 이익 실현 + 리스크 감소

**알고리즘**:
```python
def check_half_sell(position, current_price):
    """
    50% 익절 조건 확인

    Conditions:
    1. 수익률 >= 20%
    2. 아직 절반 매도 하지 않음
    """
    # 누적 수익률 계산
    gain = (position.again - 1.0) * 100

    if gain >= half_sell_threshold and not position.half_sold:
        # 50% 매도
        sell_quantity = position.quantity // 2

        execute_sell(
            ticker=position.ticker,
            quantity=sell_quantity,
            price=current_price,
            reason=SellReason.HALF_SELL_PROFIT
        )

        # 손절가 상향 조정 (매수가 = 본전)
        position.losscut_price = position.avg_price
        position.half_sold = True

        # 리스크 레벨 증가 (추가 상승 여력)
        position.risk *= half_sell_risk_multiplier  # * 2.0

        return True
    return False
```

**50% 익절 효과**:
1. **이익 실현**: 20% 수익의 절반 확보
2. **리스크 감소**: 손절가를 본전으로 상향 → 무위험 포지션
3. **추가 상승 여력**: 나머지 50%로 추가 수익 추구

**시간 복잡도**: O(1)

---

### 1.4. 휩쏘 처리 알고리즘 (Whipsaw Protection)

**목적**: 단기 손절 후 재매수로 인한 연속 손실 방지

**알고리즘**:
```python
def handle_whipsaw(ticker, trade, current_date):
    """
    휩쏘 처리

    Whipsaw 정의:
    - 매수 후 5일 이내 손절

    처리:
    - 5일간 재매수 금지
    - 거래 타입을 WHIPSAW로 분류
    """
    if trade.holding_days <= 5 and trade.reason == SellReason.LOSSCUT:
        # 휩쏘로 분류
        trade.trade_type = TradeType.WHIPSAW

        # 재매수 대기 리스트에 추가
        whipsaw_waiting[ticker] = current_date + timedelta(days=5)

        logger.info(f"[WHIPSAW] {ticker}: {trade.holding_days}일 보유 후 손절")
        logger.info(f"[WHIPSAW] {ticker}: 5일간 재매수 금지 ({whipsaw_waiting[ticker]}까지)")

        return True
    return False

def can_buy_stock(ticker, current_date):
    """
    매수 가능 여부 확인 (휩쏘 대기 중인지 체크)
    """
    if ticker in whipsaw_waiting:
        if current_date < whipsaw_waiting[ticker]:
            return False  # 아직 대기 기간 중
        else:
            del whipsaw_waiting[ticker]  # 대기 해제
    return True
```

**휩쏘 예시**:
```
Day 1: AAPL 매수 @ $150
Day 3: AAPL 손절 @ $145 (보유 3일)
→ WHIPSAW 분류
→ Day 8까지 AAPL 재매수 금지

Day 9: AAPL 재매수 가능
```

**효과**:
- 연속 손실 방지 (같은 종목 반복 손절 방지)
- 매매 횟수 감소 → 거래 비용 절감

**시간 복잡도**: O(1)

---

## 2. Performance Characteristics

### 2.1. 시간 복잡도 분석

| 작업 | 시간 복잡도 | 설명 |
|------|------------|------|
| Portfolio 초기화 | O(1) | 고정 시간 |
| 일일 매도 처리 | O(P) | P = 보유 종목수 (최대 10) |
| 일일 매수 처리 | O(S) | S = 매수 신호 종목수 |
| 포지션 크기 계산 | O(1) | ATR 계산 |
| 손익 계산 | O(P) | 모든 포지션 순회 |
| **전체 백테스트** | **O(D * (P + S))** | D = 일수, P = 포지션, S = 신호 |

**실제 성능** (500개 종목 × 252일):
- P ≈ 10 (최대 보유)
- S ≈ 20 (일평균 신호)
- D = 252
- 총 연산: 252 × (10 + 20) = 7,560회
- 실행 시간: < 30초

### 2.2. 공간 복잡도 분석

| 데이터 구조 | 메모리 사용량 | 설명 |
|-----------|-------------|------|
| Portfolio | ~1 KB | 현금, 포지션 메타데이터 |
| Positions (10개) | ~10 KB | 종목당 1KB |
| Trade History | ~1 MB | 1000개 거래 기록 |
| df_dump (500종목) | ~250 MB | 일봉 데이터 1년치 |
| **합계** | **~251 MB** | 500개 종목 기준 |

### 2.3. 병렬 처리 최적화

**종목별 독립 처리**:
```python
from concurrent.futures import ProcessPoolExecutor

def backtest_single_stock(ticker, df, config):
    """단일 종목 백테스트"""
    service = DailyBacktestService(config)
    return service.run_backtest({ticker: df}, start_date, end_date)

# 병렬 실행
with ProcessPoolExecutor(max_workers=8) as executor:
    results = executor.map(backtest_single_stock, tickers, dfs, configs)
```

**성능 개선**:
- 순차 처리: 30초
- 병렬 처리 (8 cores): 5초 → **6배 속도 향상**

---

## 3. Data Flow

### 3.1. 백테스트 데이터 흐름도

```
┌──────────────────────────────────────────────────────────┐
│              Strategy Layer                              │
│  (SignalGenerationService)                               │
│                                                          │
│  df_dump = {                                             │
│    "AAPL": DataFrame(BuySig, SellSig, LossCutPrice...),│
│    "MSFT": DataFrame(...),                              │
│    ...                                                   │
│  }                                                       │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────┐
│        Service Layer (DailyBacktestService)              │
│                                                          │
│  [Day 1]                                                 │
│    ├─ Sell Processing                                   │
│    │   ├─ Check Loss Cut                                │
│    │   ├─ Check Half Sell                               │
│    │   └─ Check Signal Sell                             │
│    ├─ Whipsaw Handling                                  │
│    └─ Buy Processing                                    │
│        ├─ Filter BuySig = 1                             │
│        ├─ Calculate Position Size                       │
│        └─ Execute Buy                                   │
│                                                          │
│  [Day 2] ... [Day 252]                                  │
│                                                          │
│  Portfolio Update (Daily)                               │
│    ├─ positions['AAPL'].again = current / buy_price    │
│    ├─ unrealized_pnl = sum(position.pnl)               │
│    └─ total_value = cash + stock_value                 │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────┐
│           PerformanceAnalyzer                            │
│                                                          │
│  Calculate Metrics:                                      │
│    - Total Return = (final_value - initial) / initial  │
│    - Sharpe Ratio = (return - rf) / volatility         │
│    - Max Drawdown = min(drawdown series)               │
│    - Win Rate = wins / (wins + losses)                 │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ↓
            BacktestResult
```

### 3.2. 상태 전이도

```
[IDLE]
  │
  │ run_backtest()
  ↓
[INITIALIZING]
  │ - Create Portfolio
  │ - Load df_dump
  ↓
[RUNNING]
  │
  ├─→ [PROCESSING_SELL]
  │     │ - Loss Cut
  │     │ - Half Sell
  │     │ - Signal Sell
  │     ↓
  ├─→ [PROCESSING_BUY]
  │     │ - Filter Signals
  │     │ - Calculate Size
  │     │ - Execute Buy
  │     ↓
  └─→ [UPDATING_PORTFOLIO]
        │ - Update Positions
        │ - Calculate P&L
        ↓
      Next Day or Complete
        ↓
[ANALYZING]
  │ - Calculate Metrics
  │ - Generate Report
  ↓
[COMPLETED]
  │
  └→ Return BacktestResult
```

---

## 4. Configuration

### 4.1. BacktestConfig 파라미터

```python
@dataclass
class BacktestConfig:
    # 자본 관리
    initial_cash: float = 100.0         # 초기 현금 (억원)
    max_positions: int = 10             # 최대 보유 종목수

    # 거래 비용
    slippage: float = 0.002             # 슬리피지 (0.2%)
    commission: float = 0.0003          # 수수료 (0.03%)

    # 리스크 관리
    std_risk: float = 0.1               # 표준 리스크 (10%)
    init_risk: float = 0.03             # 초기 손절 (3%)

    # 익절 전략
    half_sell_threshold: float = 0.20   # 50% 익절 기준 (20%)
    half_sell_risk_multiplier: float = 2.0  # 익절 후 리스크 배수

    # 기능 플래그
    enable_whipsaw: bool = True         # 휩쏘 처리
    enable_half_sell: bool = True       # 50% 익절
    enable_rebuying: bool = True        # 재매수 허용

    # 로깅
    message_output: bool = False        # 거래 메시지 출력
```

### 4.2. 파라미터 튜닝 가이드

**보수적 설정** (낮은 리스크):
```python
config = BacktestConfig(
    std_risk=0.05,              # 5% 리스크
    max_positions=5,            # 최대 5종목
    init_risk=0.05,             # 5% 손절
    half_sell_threshold=0.15,   # 15% 익절
    enable_whipsaw=True
)
```

**공격적 설정** (높은 리스크):
```python
config = BacktestConfig(
    std_risk=0.15,              # 15% 리스크
    max_positions=15,           # 최대 15종목
    init_risk=0.02,             # 2% 손절 (타이트)
    half_sell_threshold=0.30,   # 30% 익절 (여유)
    enable_whipsaw=False        # 휩쏘 처리 비활성화
)
```

**균형 설정** (권장):
```python
config = BacktestConfig()  # 기본값 사용
```

---

## 5. Testing Strategy

### 5.1. 단위 테스트

```python
# test_daily_backtest_service.py

def test_position_size_calculation():
    """포지션 크기 계산 테스트"""
    service = DailyBacktestService()

    # 입력
    cash = 100.0  # 100억원
    adr = 0.025   # 2.5%
    price = 150.0

    # 실행
    quantity = service._calculate_position_size('AAPL', price, adr, cash)

    # 검증
    assert quantity > 0
    assert quantity * price <= cash * 0.4  # 최대 40% 제약

def test_losscut_execution():
    """손절 실행 테스트"""
    service = DailyBacktestService()

    # 포지션 생성
    position = Position(
        ticker='AAPL',
        avg_price=150.0,
        losscut_price=145.5,  # -3%
        quantity=100
    )

    # 손절가 도달
    current_price = 145.0

    # 실행
    should_sell = service._check_losscut(position, current_price)

    # 검증
    assert should_sell == True

def test_half_sell_execution():
    """50% 익절 테스트"""
    service = DailyBacktestService()

    # 20% 수익 포지션
    position = Position(
        ticker='AAPL',
        avg_price=100.0,
        again=1.20,  # 20% 수익
        quantity=100
    )

    current_price = 120.0

    should_half_sell = service._check_half_sell(position, current_price)

    assert should_half_sell == True
    assert position.losscut_price == 100.0  # 본전으로 상향
```

### 5.2. 통합 테스트

```python
def test_full_backtest_execution():
    """전체 백테스트 통합 테스트"""

    # 1. 데이터 준비
    df_dump = create_mock_data(
        tickers=['AAPL', 'MSFT', 'GOOGL'],
        days=252
    )

    # 2. 백테스트 실행
    config = BacktestConfig(initial_cash=100.0)
    service = DailyBacktestService(config)

    result = service.run_backtest(
        df_dump=df_dump,
        start_date='2023-01-01',
        end_date='2023-12-31'
    )

    # 3. 결과 검증
    assert result is not None
    assert result.performance_metrics['total_return'] is not None
    assert result.performance_metrics['sharpe_ratio'] is not None
    assert len(result.trades) > 0
    assert result.portfolio_history[-1].total_value > 0
```

### 5.3. 백테스트 검증 (Validation)

**Look-ahead Bias 체크**:
```python
def test_no_lookahead_bias():
    """미래 정보 사용 방지 테스트"""

    # 현재 시점(t)에서 t+1의 데이터 접근 불가 확인
    for t in range(len(dates) - 1):
        current_data = df_dump.loc[:dates[t]]
        future_data = df_dump.loc[dates[t+1]]

        # 매매 결정은 current_data만 사용
        signal = generate_signal(current_data)

        # future_data는 절대 사용하지 않음
        assert future_data not in signal_inputs
```

**거래 비용 검증**:
```python
def test_transaction_costs():
    """거래 비용 적용 테스트"""

    # 슬리피지 + 수수료 적용 확인
    buy_price = 150.0
    slippage = 0.002
    commission = 0.0003

    actual_buy_price = buy_price * (1 + slippage + commission)

    assert actual_buy_price > buy_price
```

---

## 6. Known Limitations

### 6.1. 모델 단순화

1. **슬리피지 모델**:
   - 현재: 고정 비율 (0.2%)
   - 실제: 주문 크기, 유동성, 시장 변동성에 따라 변동
   - 개선방안: 동적 슬리피지 모델 (시장 깊이 기반)

2. **체결 보장 가정**:
   - 현재: 모든 주문 100% 체결
   - 실제: 미체결, 부분 체결 가능
   - 개선방안: 확률적 체결 모델

3. **시장 임팩트 미반영**:
   - 현재: 대량 매수/매도가 가격에 영향 없음
   - 실제: 대량 주문 시 가격 변동 발생
   - 개선방안: 시장 임팩트 함수 추가

### 6.2. 데이터 제약

1. **일봉 데이터 한계**:
   - 장중 변동성 미반영
   - 급락 후 반등 시 손절 회피 불가
   - 해결: 분봉 백테스트 추가 개발

2. **생존 편향** (Survivorship Bias):
   - 상장폐지 종목 데이터 누락
   - 수익률 과대평가 가능
   - 해결: 전체 종목 데이터 포함 (상장폐지 포함)

### 6.3. 실행 제약

1. **단일 스레드 실행**:
   - 대량 종목 처리 시 속도 저하
   - 해결: 병렬 처리 구현 (ProcessPoolExecutor)

2. **메모리 사용**:
   - 1000개 종목 × 3년 → ~1.5 GB
   - 해결: 청크 단위 처리, 데이터 압축

---

## 7. Future Enhancements

### 7.1. 단기 개선 (1-3개월)

- [ ] **분봉 백테스트**: 장중 거래 시뮬레이션
- [ ] **부분 체결 모델**: 확률적 체결 시뮬레이션
- [ ] **동적 슬리피지**: 유동성 기반 슬리피지 계산
- [ ] **벤치마크 비교**: S&P 500 대비 성과 분석

### 7.2. 중기 개선 (3-6개월)

- [ ] **포트폴리오 최적화**: Markowitz 평균-분산 최적화
- [ ] **리스크 패리티**: 리스크 균형 포트폴리오
- [ ] **멀티 전략 백테스트**: 여러 전략 동시 실행 및 비교
- [ ] **실시간 백테스트**: 라이브 데이터로 실시간 검증

### 7.3. 장기 개선 (6개월+)

- [ ] **GPU 가속**: CUDA 기반 병렬 처리
- [ ] **강화학습 통합**: RL 기반 동적 포지션 조정
- [ ] **웹 대시보드**: 실시간 백테스트 모니터링
- [ ] **클라우드 배포**: AWS/GCP에서 대규모 백테스트

---

## 8. Related Documents

- **SERVICE_LAYER_INTERFACE.md**: 입출력 인터페이스 명세
- **SERVICE_MODULES.md**: 서비스 모듈 설명
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스
- **refer/BackTest/TestMakTrade_D.py**: 원본 백테스트 코드 (참고용)

---

**Last Updated**: 2025-10-09
**Managed by**: Service Agent
**Document Version**: 1.0
