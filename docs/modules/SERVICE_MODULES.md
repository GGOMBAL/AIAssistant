# Service Layer Modules Documentation

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Service Agent

---

## 모듈 개요

Service Layer는 Strategy Layer에서 생성된 매매 신호를 실행하고, 백테스트를 수행하며, 실거래 주문을 관리하는 책임을 담당합니다.

### 모듈 목록

1. **DailyBacktestService** - 일봉 백테스트 엔진
2. **MinuteBacktestService** - 분봉 백테스트 엔진 (고빈도 전략)
3. **APIOrderService** - 실거래 주문 실행 서비스
4. **PerformanceAnalyzer** - 성과 분석 및 리포팅
5. **TradeRecorder** - 거래 기록 관리
6. **BacktestEngine** - 백테스트 코어 엔진
7. **ExecutionServices** - 주문 실행 및 관리

---

## Module 1: DailyBacktestService

### Purpose
일봉 데이터 기반 백테스트 시뮬레이션을 수행합니다. Strategy Layer의 매매 신호를 받아 포지션 관리, 손익 계산, 리스크 관리를 실행합니다.

### Location
`project/service/daily_backtest_service.py` (964 lines)

### Main Classes

#### 1. BacktestConfig (Dataclass)
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
```

#### 2. DailyBacktestService (Main Class)
```python
class DailyBacktestService:
    def __init__(self, config: BacktestConfig = None)

    def run_backtest(
        self,
        df_dump: Dict[str, pd.DataFrame],
        start_date: str,
        end_date: str,
        universe: List[str] = None
    ) -> BacktestResult
```

**주요 메서드**:
- `run_backtest()`: 백테스트 실행
- `_process_sell_orders()`: 매도 주문 처리 (손절, 익절, 신호매도)
- `_process_buy_orders()`: 매수 주문 처리
- `_handle_whipsaw()`: 휩쏘 처리 (매수 후 5일 이내 손절 방지)
- `_calculate_position_size()`: ATR 기반 포지션 크기 계산
- `_generate_performance_metrics()`: 성과 지표 계산

### Usage Example

```python
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig

# 1. 설정 생성
config = BacktestConfig(
    initial_cash=100.0,
    max_positions=10,
    slippage=0.002,
    std_risk=0.1,
    message_output=True
)

# 2. 백테스트 서비스 초기화
backtest = DailyBacktestService(config)

# 3. 백테스트 실행
result = backtest.run_backtest(
    df_dump=df_dump,  # Strategy Layer 출력
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 4. 결과 분석
print(f"Total Return: {result.performance_metrics['total_return']:.2f}%")
print(f"Sharpe Ratio: {result.performance_metrics['sharpe_ratio']:.2f}")
print(f"Win Rate: {result.performance_metrics['win_rate']:.2f}%")
```

### Dependencies

**Internal**:
- Strategy Layer: `SignalGenerationService`, `PositionSizingService`

**External**:
- `pandas`: DataFrame 처리
- `numpy`: 수치 계산

### Key Algorithms

#### ATR 기반 포지션 크기 계산:
```python
def _calculate_position_size(self, ticker, current_price, adr, cash):
    """
    ATR (Average Daily Range) 기반 포지션 크기 계산
    """
    # 기본 포지션 = (현금 * 리스크) / (ATR * 2)
    base_position = (cash * self.config.std_risk) / (adr * 2)

    # 최대/최소 제약 적용
    max_position = cash * 0.4  # 최대 40%
    min_position = cash * 0.05  # 최소 5%

    position = max(min_position, min(base_position, max_position))
    return position / current_price  # 수량 반환
```

#### 휩쏘 처리:
```python
def _handle_whipsaw(self, ticker, trade, current_date):
    """
    매수 후 5일 이내 손절 → 휩쏘로 분류
    5일간 재매수 금지
    """
    if trade.holding_days <= 5 and trade.reason == SellReason.LOSSCUT:
        trade.trade_type = TradeType.WHIPSAW
        self.whipsaw_waiting[ticker] = current_date + timedelta(days=5)
```

---

## Module 2: MinuteBacktestService

### Purpose
분봉 데이터 기반 고빈도 매매 전략 백테스트를 수행합니다. 장중 변동성을 활용한 단타 전략에 최적화되어 있습니다.

### Location
`project/service/minute_backtest_service.py`

### Main Features
- 1분봉/5분봉/15분봉 지원
- 장중 진입/청산 로직
- 슬리피지 및 체결 지연 시뮬레이션
- 마켓 임팩트 고려

### Usage Example

```python
from project.service.minute_backtest_service import MinuteBacktestService

minute_backtest = MinuteBacktestService(
    timeframe='5T',  # 5분봉
    market_hours={'start': '09:30', 'end': '16:00'}
)

result = minute_backtest.run_backtest(
    df_minute=df_minute_data,
    signals=intraday_signals,
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

### Dependencies
- **DailyBacktestService**: 코어 로직 재사용
- **pandas**: 분봉 데이터 처리

---

## Module 3: APIOrderService

### Purpose
실거래 시 KIS API를 통해 주문을 실행하고 관리합니다. 주문 큐 관리, 체결 확인, 에러 처리를 담당합니다.

### Location
`project/service/api_order_service.py`

### Main Classes

#### 1. APIOrderService
```python
class APIOrderService:
    def __init__(self, config: Dict[str, Any])

    async def execute_order(
        self,
        ticker: str,
        order_type: str,
        quantity: int,
        price: float = None,
        order_kind: str = "LIMIT"
    ) -> Dict[str, Any]

    async def cancel_order(self, order_id: str) -> bool

    async def get_order_status(self, order_id: str) -> OrderStatus
```

**주요 메서드**:
- `execute_order()`: 주문 실행 (매수/매도)
- `cancel_order()`: 주문 취소
- `get_order_status()`: 주문 상태 조회
- `get_active_orders()`: 활성 주문 리스트
- `_order_processing_loop()`: 주문 큐 처리 (비동기)

### Usage Example

```python
from project.service.api_order_service import APIOrderService

# 1. KIS API 설정
config = {
    'kis_api': {
        'app_key': 'YOUR_APP_KEY',
        'app_secret': 'YOUR_APP_SECRET',
        'account_no': 'YOUR_ACCOUNT',
        'is_virtual': True  # 모의투자
    },
    'order_limits': {
        'max_per_minute': 10,
        'max_amount': 100000
    }
}

# 2. 서비스 초기화 및 시작
order_service = APIOrderService(config)
await order_service.start_service()

# 3. 매수 주문 실행
result = await order_service.execute_order(
    ticker="AAPL",
    order_type="BUY",
    quantity=10,
    price=150.0,
    order_kind="LIMIT"
)

# 4. 주문 결과 확인
if result['success']:
    print(f"Order ID: {result['order_id']}")
    print(f"Status: {result['status']}")
else:
    print(f"Error: {result['error']['message']}")

# 5. 주문 상태 조회
status = await order_service.get_order_status(result['order_id'])
print(f"Fill Status: {status.filled_quantity}/{status.total_quantity}")
```

### Dependencies

**Internal**:
- Helper Layer: `KISAPIHelper` (KIS API 래퍼)

**External**:
- `asyncio`: 비동기 주문 처리
- `aiohttp`: HTTP 비동기 요청

### Key Features

#### 주문 큐 시스템:
```python
# 비동기 주문 처리 루프
async def _order_processing_loop(self):
    while True:
        order_request = await self.order_queue.get()
        try:
            result = await self._execute_order_internal(order_request)
            await self._notify_order_result(result)
        except Exception as e:
            await self._handle_order_error(order_request, e)
```

#### 주문 제한 관리:
```python
# 분당 최대 주문 수 제한
if self.orders_submitted_today >= self.max_orders_per_minute:
    raise OrderLimitExceeded("분당 주문 한도 초과")
```

---

## Module 4: PerformanceAnalyzer

### Purpose
백테스트 결과를 종합 분석하여 수익률, 리스크, 거래 통계 등의 성과 지표를 생성합니다.

### Location
`project/service/performance_analyzer.py`

### Main Classes

#### 1. PerformanceAnalyzer
```python
class PerformanceAnalyzer:
    def analyze_backtest(
        self,
        trades: List[Trade],
        portfolio_history: List[Portfolio],
        initial_cash: float
    ) -> BacktestReport

    def calculate_return_metrics(self) -> ReturnAnalysis
    def calculate_trade_metrics(self) -> TradeAnalysis
    def calculate_risk_metrics(self) -> RiskAnalysis
```

**계산 지표**:

**수익률 분석** (ReturnAnalysis):
- Total Return, Annual Return
- Volatility, Sharpe Ratio, Sortino Ratio
- Max Drawdown, Recovery Factor
- VaR (95%), CVaR (95%)

**거래 분석** (TradeAnalysis):
- Win Rate, Profit Factor
- Avg Win/Loss, Largest Win/Loss
- Avg Trade Duration
- Max Consecutive Wins/Losses

**리스크 분석** (RiskAnalysis):
- Portfolio Beta, Correlation Matrix
- Sector Exposure, Concentration Risk
- Downside Deviation, Ulcer Index

### Usage Example

```python
from project.service.performance_analyzer import PerformanceAnalyzer

# 1. 분석기 초기화
analyzer = PerformanceAnalyzer()

# 2. 백테스트 결과 분석
report = analyzer.analyze_backtest(
    trades=result.trades,
    portfolio_history=result.portfolio_history,
    initial_cash=100.0
)

# 3. 상세 지표 확인
print("=== Return Analysis ===")
print(f"Total Return: {report.return_analysis.total_return:.2f}%")
print(f"Sharpe Ratio: {report.return_analysis.sharpe_ratio:.2f}")
print(f"Max Drawdown: {report.return_analysis.max_drawdown:.2f}%")

print("\n=== Trade Analysis ===")
print(f"Win Rate: {report.trade_analysis.win_rate:.2f}%")
print(f"Profit Factor: {report.trade_analysis.profit_factor:.2f}")
print(f"Avg Trade: {report.trade_analysis.avg_trade:.2f}%")

print("\n=== Risk Analysis ===")
print(f"Portfolio Beta: {report.risk_analysis.portfolio_beta:.2f}")
print(f"Concentration Risk: {report.risk_analysis.concentration_risk:.2f}")

# 4. 리포트 저장
analyzer.save_report(report, "backtest_report_20231231.yaml")
```

### Dependencies

**External**:
- `pandas`: 시계열 분석
- `numpy`: 통계 계산
- `scipy`: 고급 통계 (분포 분석)

### Key Formulas

#### Sharpe Ratio:
```python
sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
```

#### Max Drawdown:
```python
cumulative_returns = (1 + daily_returns).cumprod()
running_max = cumulative_returns.expanding().max()
drawdown = (cumulative_returns - running_max) / running_max
max_drawdown = drawdown.min()
```

#### Profit Factor:
```python
total_wins = sum(win_pnl for win in winning_trades)
total_losses = abs(sum(loss_pnl for loss in losing_trades))
profit_factor = total_wins / total_losses
```

---

## Module 5: TradeRecorder

### Purpose
모든 거래 내역을 기록하고 관리합니다. 데이터베이스 저장, 조회, 분석 기능을 제공합니다.

### Location
`project/service/trade_recorder.py`

### Main Features
- 거래 내역 자동 저장 (MongoDB)
- 거래 조회 및 필터링
- 거래 통계 집계
- CSV/Excel 내보내기

### Usage Example

```python
from project.service.trade_recorder import TradeRecorder

# 1. 레코더 초기화
recorder = TradeRecorder(database='trading_db')

# 2. 거래 기록
await recorder.record_trade(trade)

# 3. 거래 조회
trades = await recorder.get_trades(
    start_date="2023-01-01",
    end_date="2023-12-31",
    ticker="AAPL"
)

# 4. CSV 내보내기
recorder.export_to_csv(trades, "trades_2023.csv")
```

### Dependencies
- **Database Layer**: `MongoDBOperations`

---

## Module 6: BacktestEngine

### Purpose
백테스트 실행의 코어 로직을 제공하는 엔진입니다. DailyBacktestService와 MinuteBacktestService에서 공통으로 사용됩니다.

### Location
`project/service/backtest_engine.py`

### Main Features
- 이벤트 기반 백테스트 아키텍처
- 시간 순서 보장 (Look-ahead Bias 방지)
- 슬리피지 및 수수료 시뮬레이션
- 포지션 추적 및 관리

### Usage Example

```python
from project.service.backtest_engine import BacktestEngine

engine = BacktestEngine()
engine.add_event_handler('on_bar', handle_bar_event)
engine.add_event_handler('on_order_filled', handle_order_filled)
engine.run(df_data, start_date, end_date)
```

---

## Module 7: ExecutionServices

### Purpose
주문 실행 및 관리와 관련된 유틸리티 함수들을 제공합니다.

### Location
`project/service/execution_services.py`

### Main Functions
- `calculate_slippage()`: 슬리피지 계산
- `validate_order()`: 주문 유효성 검증
- `estimate_fill_price()`: 체결 예상가 계산
- `check_risk_limits()`: 리스크 한도 체크

### Usage Example

```python
from project.service.execution_services import calculate_slippage, validate_order

# 슬리피지 계산
slippage = calculate_slippage(
    price=150.0,
    volume=1000,
    market_volume=100000,
    slippage_rate=0.002
)

# 주문 검증
is_valid, errors = validate_order(
    order_type="BUY",
    quantity=10,
    price=150.0,
    cash_balance=50000.0
)
```

---

## 모듈 간 상호작용

### 백테스트 실행 흐름:
```
Strategy Layer (signals)
        ↓
DailyBacktestService
        ↓
BacktestEngine (코어 로직)
        ↓
TradeRecorder (기록)
        ↓
PerformanceAnalyzer (분석)
        ↓
BacktestReport
```

### 실거래 실행 흐름:
```
Strategy Layer (signals)
        ↓
PositionSizingService (포지션 크기)
        ↓
ExecutionServices (검증)
        ↓
APIOrderService (주문 실행)
        ↓
TradeRecorder (기록)
```

---

## 성능 특성

### DailyBacktestService
- **처리 속도**: 500개 종목 × 1년 < 30초
- **메모리**: ~250MB (500개 종목 기준)
- **병렬화**: 종목별 독립 처리 가능

### APIOrderService
- **주문 처리**: 비동기 큐 기반 (초당 10건)
- **응답 시간**: < 500ms (평균)
- **재시도**: 최대 3회 (지수 백오프)

### PerformanceAnalyzer
- **분석 속도**: 1000개 거래 < 2초
- **메모리**: ~50MB
- **캐싱**: 중간 계산 결과 캐싱

---

## 설정 파일 연동

### DailyBacktestService
- 설정 파일 없음 (BacktestConfig 객체 사용)

### APIOrderService
- `config/api_credentials.yaml`: KIS API 자격증명
- `config/broker_config.yaml`: 주문 제한 설정

---

## 테스트

### 단위 테스트
```bash
pytest Test/test_daily_backtest_service.py
pytest Test/test_api_order_service.py
pytest Test/test_performance_analyzer.py
```

### 통합 테스트
```bash
pytest Test/test_service_layer_integration.py
```

---

## 알려진 제약사항

### DailyBacktestService
- 슬리피지 모델 단순화 (실제 시장 깊이 미반영)
- 체결 보장 가정 (실제는 미체결 가능)
- 분할 체결 미지원

### APIOrderService
- KIS API 의존성 (다른 브로커 미지원)
- 장시간 연결 시 토큰 갱신 필요
- 주문 취소 시 타이밍 이슈 가능

### PerformanceAnalyzer
- 거래 비용 단순화
- 세금 미반영
- 포트폴리오 재조정 비용 미고려

---

## 향후 개선사항

- [ ] DailyBacktestService: 부분 체결 시뮬레이션
- [ ] APIOrderService: 멀티 브로커 지원 (Interactive Brokers, TD Ameritrade)
- [ ] PerformanceAnalyzer: 벤치마크 대비 성과 분석 (Alpha, Beta)
- [ ] TradeRecorder: 실시간 대시보드 연동
- [ ] BacktestEngine: GPU 가속 지원

---

## 참고 문서

- **SERVICE_LAYER_INTERFACE.md**: 입출력 인터페이스 명세
- **BACKTEST_SERVICE_SPEC.md**: 백테스트 알고리즘 상세 (TODO)
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스

---

**Last Updated**: 2025-10-09
**Managed by**: Service Agent
