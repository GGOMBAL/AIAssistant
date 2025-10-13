# Service Layer Interface Specification

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Service Agent
**Status**: Active

---

## 1. Overview

### Purpose
Service Layer는 Strategy Layer에서 생성된 매매 신호를 받아 백테스트를 실행하고, 실거래 시 주문을 관리하며, 성과를 분석하는 책임을 담당합니다.

### Main Responsibilities
- 백테스트 시뮬레이션 (일봉, 분봉)
- 주문 생성 및 실행 (매수/매도)
- 포트폴리오 관리 및 리밸런싱
- 거래 기록 및 성과 분석
- 리스크 관리 (손절, 익절)

### Key Components
- `DailyBacktestService`: 일봉 백테스트 엔진
- `MinuteBacktestService`: 분봉 백테스트 엔진
- `APIOrderService`: 실거래 주문 서비스
- `PerformanceAnalyzer`: 성과 분석기
- `TradeRecorder`: 거래 기록 관리

---

## 2. Input Interface

### 2.1. DailyBacktestService 초기화

```python
@dataclass
class BacktestConfig:
    initial_cash: float = 100.0         # 초기 현금 (억원)
    max_positions: int = 10             # 최대 보유 종목수
    slippage: float = 0.002             # 슬리피지 (0.2%)
    std_risk: float = 0.1               # 표준 리스크 (10%)
    init_risk: float = 0.03             # 초기 손절 리스크 (3%)
    half_sell_threshold: float = 0.20   # 50% 매도 임계값 (20%)
    enable_whipsaw: bool = True         # 휩쏘 처리 활성화
    enable_half_sell: bool = True       # 50% 매도 활성화
    enable_rebuying: bool = True        # 재매수 허용
    message_output: bool = False        # 거래 메시지 출력

def __init__(self, config: BacktestConfig = None)
```

**Parameters**:
- `config` (BacktestConfig, optional): 백테스트 설정 (기본값: BacktestConfig())

**Constraints**:
- `initial_cash` > 0
- `max_positions` >= 1
- `slippage` >= 0.0 and <= 0.05 (최대 5%)

### 2.2. 백테스트 실행 메서드

```python
def run_backtest(
    self,
    df_dump: Dict[str, pd.DataFrame],  # Strategy Layer 출력
    start_date: str,                   # 시작일 (YYYY-MM-DD)
    end_date: str,                     # 종료일 (YYYY-MM-DD)
    universe: List[str] = None         # 종목 리스트 (선택)
) -> BacktestResult
```

**Parameters**:
- `df_dump` (Dict[str, pd.DataFrame], **required**): Strategy Layer의 매매 후보 데이터
  - Key: Ticker symbol (str)
  - Value: DataFrame with columns:
    - `open`, `high`, `low`, `close`: OHLC 데이터
    - `BuySig`: 매수 신호 (1 or 0)
    - `SellSig`: 매도 신호 (1 or 0)
    - `LossCutPrice`: 손절가
    - `TargetPrice`: 목표가
    - `signal`: 신호 강도
    - `Type`: 신호 타입 (Breakout_2Y, RS_12W_1M 등)

- `start_date` (str, **required**): 백테스트 시작일 (ISO 8601 형식: "2023-01-01")

- `end_date` (str, **required**): 백테스트 종료일 (ISO 8601 형식: "2023-12-31")

- `universe` (List[str], optional): 백테스트 대상 종목 리스트 (None이면 df_dump의 모든 종목)

**Constraints**:
- `start_date < end_date`
- `df_dump`의 모든 DataFrame은 DatetimeIndex 사용
- 최소 30일 이상의 데이터 필요

### 2.3. 실거래 주문 실행

```python
def execute_order(
    self,
    ticker: str,
    order_type: str,        # "BUY" or "SELL"
    quantity: int,
    price: float = None,    # None이면 시장가
    order_kind: str = "LIMIT"  # "LIMIT" or "MARKET"
) -> Dict[str, Any]
```

**Parameters**:
- `ticker` (str, **required**): 종목 심볼
- `order_type` (str, **required**): 주문 타입 ("BUY", "SELL")
- `quantity` (int, **required**): 주문 수량
- `price` (float, optional): 주문 가격 (None이면 시장가)
- `order_kind` (str, optional): 주문 종류 ("LIMIT", "MARKET")

**Constraints**:
- `quantity` > 0
- `order_type` in ["BUY", "SELL"]
- `order_kind` in ["LIMIT", "MARKET"]

---

## 3. Output Interface

### 3.1. 백테스트 결과 구조

```python
@dataclass
class BacktestResult:
    trades: List[Trade]                    # 거래 내역
    portfolio_history: List[Portfolio]     # 포트폴리오 변화
    daily_results: List[DayTradingResult]  # 일별 결과
    performance_metrics: Dict[str, float]  # 성과 지표
    execution_time: float                  # 실행 시간 (초)
    config: BacktestConfig                 # 백테스트 설정
```

### 3.2. Performance Metrics (성과 지표)

```python
{
    'total_return': 0.36,           # 총 수익률 (%)
    'sharpe_ratio': 0.603,          # 샤프 비율
    'max_drawdown': 0.89,           # 최대 낙폭 (%)
    'win_rate': 46.43,              # 승률 (%)
    'total_trades': 61,             # 총 거래 수
    'avg_holding_days': 15.2,       # 평균 보유 기간 (일)
    'profit_factor': 1.25,          # 수익 팩터
    'avg_win': 8.5,                 # 평균 수익 (%)
    'avg_loss': -4.2,               # 평균 손실 (%)
    'max_consecutive_wins': 5,      # 최대 연속 승
    'max_consecutive_losses': 3,    # 최대 연속 패
    'final_portfolio_value': 100.36 # 최종 포트폴리오 가치 (억원)
}
```

### 3.3. Trade 구조

```python
@dataclass
class Trade:
    ticker: str                      # 종목 심볼
    trade_type: TradeType            # BUY | SELL | HALF_SELL | WHIPSAW
    quantity: float                  # 거래 수량
    price: float                     # 거래 가격
    timestamp: pd.Timestamp          # 거래 시각
    reason: Optional[SellReason]     # 매도 사유 (LOSSCUT | SIGNAL_SELL | HALF_SELL_PROFIT)
    pnl: float                       # 손익
    again: float                     # 누적 수익률
    buy_date: Optional[pd.Timestamp] # 매수일
    buy_price: Optional[float]       # 매수가
    holding_days: Optional[float]    # 보유 기간
    risk: Optional[float]            # 리스크 레벨
```

### 3.4. Portfolio 구조

```python
@dataclass
class Portfolio:
    cash: float                         # 현금 잔고 (억원)
    positions: Dict[str, Position]      # 보유 포지션 {ticker: Position}
    win_count: float                    # 승리 횟수
    loss_count: float                   # 패배 횟수
    win_gain: float                     # 승리 수익 합계
    loss_gain: float                    # 패배 손실 합계

    # Properties
    stock_value: float                  # 주식 평가액
    total_value: float                  # 총 자산
    position_count: int                 # 보유 종목수
    cash_ratio: float                   # 현금 비율 (%)
```

### 3.5. Position 구조

```python
@dataclass
class Position:
    ticker: str                  # 종목 심볼
    balance: float               # 투자 금액 (억원)
    avg_price: float             # 평균 단가
    again: float                 # 누적 수익률 (1.0 = break-even)
    duration: float              # 보유 기간 (일)
    losscut_price: float         # 손절가
    risk: float                  # 리스크 레벨

    # Properties
    quantity: float              # 보유 수량 (계산됨)
    market_value: float          # 시장 가치 (계산됨)
    unrealized_pnl: float        # 미실현 손익 (계산됨)
```

---

## 4. Service Layer Logic

### 4.1. 백테스트 실행 흐름

```
[1] 초기화
    - Portfolio 생성 (cash = initial_cash)
    - Positions = {}

[2] 날짜별 순회 (start_date ~ end_date)
    For each day:
        [2-1] 매도 처리
            - 손절가 도달 → LOSSCUT 매도
            - 목표가 도달 → HALF_SELL (50% 매도)
            - 매도 신호 발생 → SIGNAL_SELL

        [2-2] 휩쏘 처리 (선택)
            - 매수 후 5일 이내 손절 → WHIPSAW
            - 재매수 대기 리스트 추가

        [2-3] 매수 처리
            - BuySig = 1인 종목 필터링
            - 최대 보유 종목수 확인
            - 포지션 크기 계산 (ATR 기반)
            - 매수 실행

[3] 성과 분석
    - 거래 내역 집계
    - 수익률, 샤프 비율, MDD 계산
    - 승률, 평균 수익/손실 계산

[4] 결과 반환
    - BacktestResult 객체 생성
```

### 4.2. 포지션 크기 계산 로직

**ATR 기반 리스크 조절**:
```python
position_size = (portfolio.cash * std_risk) / (adr * 2)
```

**변수 설명**:
- `std_risk`: 표준 리스크 (기본 10%)
- `adr`: Average Daily Range (평균 일일 변동폭)
- `portfolio.cash`: 현재 현금 잔고

**제약 조건**:
- 단일 종목 최대 비중: 40%
- 최대 보유 종목수: `max_positions` (기본 10개)
- 최소 주문 금액: 1억원

### 4.3. 손절 및 익절 로직

**손절 (Loss Cut)**:
```python
if current_price <= position.losscut_price:
    execute_sell(ticker, reason=SellReason.LOSSCUT)
```

**50% 익절 (Half Sell)**:
```python
if position.again >= (1 + half_sell_threshold):  # 20% 이익
    execute_half_sell(ticker)
    position.losscut_price = position.avg_price  # 손절가를 매수가로 상향
```

**신호 매도 (Signal Sell)**:
```python
if df[ticker]['SellSig'] == 1:
    execute_sell(ticker, reason=SellReason.SIGNAL_SELL)
```

### 4.4. 휩쏘 처리 (Whipsaw Protection)

```python
if enable_whipsaw:
    if holding_days <= 5 and reason == SellReason.LOSSCUT:
        # 휩쏘로 분류
        trade.trade_type = TradeType.WHIPSAW

        # 재매수 대기 리스트에 추가 (5일간 대기)
        whipsaw_waiting[ticker] = current_date + timedelta(days=5)
```

**의미**: 매수 후 5일 이내 손절된 경우, 5일간 재매수 금지하여 연속 손실 방지

---

## 5. Error Handling

### 5.1. Exception Types

| Exception | Condition | Recovery |
|-----------|-----------|----------|
| `InvalidDateRangeError` | start_date >= end_date | ValueError 발생 |
| `InsufficientDataError` | 데이터 부족 (< 30일) | ValueError 발생 |
| `InvalidConfigError` | 설정 값 오류 (예: cash < 0) | ValueError 발생 |
| `PositionSizeError` | 포지션 크기 계산 실패 | 해당 종목 매수 건너뜀 |
| `OrderExecutionError` | 주문 실행 실패 (실거래) | 재시도 후 실패 시 로그 기록 |

### 5.2. Error Response Format

백테스트 실패 시:
```python
{
    'success': False,
    'error': {
        'code': 'INVALID_DATE_RANGE',
        'message': 'Start date must be before end date',
        'start_date': '2023-01-01',
        'end_date': '2022-12-31'
    },
    'partial_results': None
}
```

주문 실행 실패 시:
```python
{
    'order_id': None,
    'success': False,
    'error': {
        'code': 'INSUFFICIENT_FUNDS',
        'message': 'Not enough cash to execute order',
        'required': 100.0,
        'available': 50.0
    }
}
```

---

## 6. Examples

### 6.1. Basic Backtest Usage

```python
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig
from project.strategy.signal_generation_service import SignalGenerationService
from project.indicator.data_frame_generator import DataFrameGenerator

# 1. 데이터 로드 (Indicator Layer)
generator = DataFrameGenerator(
    universe=["AAPL", "MSFT", "GOOGL"],
    market="US",
    area="US"
)
generator.load_data_from_database()

# 2. 신호 생성 (Strategy Layer)
signal_service = SignalGenerationService(area='US')

df_dump = {}
for ticker in ["AAPL", "MSFT", "GOOGL"]:
    # 종합 신호 생성
    signal = signal_service.generate_comprehensive_signals(
        df_daily=generator.df_D[ticker],
        df_weekly=generator.df_W[ticker],
        df_rs=generator.df_RS[ticker]
    )

    # df_dump에 신호 추가
    df_dump[ticker] = generator.df_D[ticker].copy()
    df_dump[ticker]['BuySig'] = 1 if signal['final_signal'] == 'BUY' else 0
    df_dump[ticker]['SellSig'] = 0
    df_dump[ticker]['LossCutPrice'] = signal['losscut_price']
    df_dump[ticker]['TargetPrice'] = signal['target_price']
    df_dump[ticker]['signal'] = signal['signal_strength']
    df_dump[ticker]['Type'] = signal['signal_type']

# 3. 백테스트 실행 (Service Layer)
config = BacktestConfig(
    initial_cash=100.0,
    max_positions=10,
    slippage=0.002,
    message_output=True
)

backtest_service = DailyBacktestService(config)

result = backtest_service.run_backtest(
    df_dump=df_dump,
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 4. 결과 출력
print(f"Total Return: {result.performance_metrics['total_return']:.2f}%")
print(f"Sharpe Ratio: {result.performance_metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result.performance_metrics['max_drawdown']:.2f}%")
print(f"Win Rate: {result.performance_metrics['win_rate']:.2f}%")
print(f"Total Trades: {result.performance_metrics['total_trades']}")
```

### 6.2. Custom Configuration

```python
# 보수적인 설정
conservative_config = BacktestConfig(
    initial_cash=100.0,
    max_positions=5,          # 최대 5개 종목만 보유
    slippage=0.003,           # 0.3% 슬리피지
    std_risk=0.05,            # 5% 리스크 (보수적)
    init_risk=0.05,           # 5% 손절
    half_sell_threshold=0.15, # 15% 익절
    enable_whipsaw=True,
    enable_half_sell=True
)

result = backtest_service.run_backtest(
    df_dump=df_dump,
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### 6.3. Analyzing Trade Details

```python
# 거래 내역 분석
for trade in result.trades:
    if trade.trade_type == TradeType.SELL:
        print(f"{trade.ticker}:")
        print(f"  Buy: {trade.buy_price:.2f} ({trade.buy_date})")
        print(f"  Sell: {trade.price:.2f} ({trade.timestamp})")
        print(f"  PnL: {trade.pnl:.2f}%")
        print(f"  Holding Days: {trade.holding_days:.0f}")
        print(f"  Reason: {trade.reason.value}")
        print()

# 포트폴리오 변화 추적
for portfolio in result.portfolio_history[::30]:  # 매 30일마다
    print(f"Date: {portfolio.date}")
    print(f"  Total Value: {portfolio.total_value:.2f} 억원")
    print(f"  Cash: {portfolio.cash:.2f} 억원 ({portfolio.cash_ratio:.1f}%)")
    print(f"  Positions: {portfolio.position_count}")
    print()
```

### 6.4. Real Trading Order Execution

```python
from project.service.api_order_service import APIOrderService

# 실거래 주문 서비스 초기화
order_service = APIOrderService(
    broker='KIS',
    account_type='real',  # 'real' or 'virtual'
    area='US'
)

# 매수 주문
order_result = order_service.execute_order(
    ticker="AAPL",
    order_type="BUY",
    quantity=10,
    price=150.0,
    order_kind="LIMIT"
)

if order_result['success']:
    print(f"Order ID: {order_result['order_id']}")
    print(f"Status: {order_result['status']}")
else:
    print(f"Error: {order_result['error']['message']}")
```

---

## 7. Dependencies

### 7.1. Internal Dependencies

- **Strategy Layer**: 매매 신호 생성
  - `SignalGenerationService`: BUY/SELL 신호
  - `PositionSizingService`: 포지션 크기 계산
  - `AccountAnalysisService`: 계좌 분석

- **Indicator Layer**: 기술지표 데이터
  - `DataFrameGenerator`: df_D, df_W, df_RS 제공

- **Helper Layer**: 외부 API 통합
  - `KISAPIHelper`: KIS API 주문 실행
  - `LSAPIHelper`: LS Securities API

### 7.2. External Libraries

- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 수치 계산
- `yaml`: 설정 파일 로드
- `logging`: 로깅

### 7.3. Data Flow

```
Strategy Layer (df_dump with signals)
        ↓
Service Layer (DailyBacktestService)
        ↓
Performance Metrics + Trade History
```

---

## 8. Performance Characteristics

### 8.1. Processing Time

| 작업 | 소요 시간 | 환경 |
|------|----------|------|
| 100개 종목 × 1년 백테스트 | < 5초 | Intel i7, 16GB RAM |
| 500개 종목 × 1년 백테스트 | < 30초 | 순차 처리 |
| 500개 종목 × 3년 백테스트 | < 90초 | 순차 처리 |

### 8.2. Memory Usage

| 데이터 | 메모리 사용량 |
|--------|-------------|
| 100개 종목 × 1년 | ~50 MB |
| 500개 종목 × 1년 | ~250 MB |
| 500개 종목 × 3년 | ~750 MB |

### 8.3. Optimization Tips

1. **병렬 처리**: 종목별 신호 생성을 병렬화
2. **데이터 필터링**: 불필요한 컬럼 제거
3. **캐싱**: 반복 계산 결과 캐싱

---

## 9. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-09 | Initial version | Service Agent |

---

## 10. Notes

### Known Limitations

- 백테스트는 과거 데이터 기반 → 미래 성과 보장 불가
- 슬리피지 및 거래 비용 단순화
- 유동성 제약 미반영
- 체결 보장 가정 (실제는 미체결 가능)

### Future Enhancements

- [ ] 분봉 백테스트 지원 (MinuteBacktestService)
- [ ] 실시간 거래 모니터링
- [ ] 리스크 관리 강화 (포트폴리오 VaR)
- [ ] 멀티 마켓 동시 백테스트
- [ ] 거래 비용 최적화

### Related Documents

- **SERVICE_MODULES.md**: 서비스 모듈 상세 설명 (TODO)
- **BACKTEST_SERVICE_SPEC.md**: 백테스트 알고리즘 상세 (TODO)
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스

---

**Last Updated**: 2025-10-09
**Managed by**: Service Agent
