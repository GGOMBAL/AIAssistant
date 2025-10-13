# Strategy Layer Modules Documentation

**Version**: 1.0
**Last Updated**: 2025-10-09
**Managed by**: Strategy Agent

---

## 모듈 개요

Strategy Layer는 Indicator Layer에서 제공된 기술지표 데이터를 분석하여 매매 신호를 생성하고, 포지션 크기를 계산하며, 계좌를 분석하는 책임을 담당합니다.

### 모듈 목록

1. **SignalGenerationService** - 매매 신호 생성
2. **PositionSizingService** - 포지션 사이징 및 리스크 관리
3. **AccountAnalysisService** - 계좌 분석 및 포트폴리오 평가

---

## Module 1: SignalGenerationService

### Purpose
다중 타임프레임 분석을 통한 종합적인 매매 신호 생성. 일봉, 주봉, RS, 펀더멘털, 어닝스 데이터를 결합하여 BUY/SELL/HOLD 신호를 생성합니다.

### Location
`project/strategy/signal_generation_service.py` (536 lines)

### Main Classes

#### 1. SignalType (Enum)
```python
class SignalType(Enum):
    BUY = "BUY"      # 매수 신호
    SELL = "SELL"    # 매도 신호
    HOLD = "HOLD"    # 관망
```

#### 2. BreakoutType (Enum)
```python
class BreakoutType(Enum):
    BREAKOUT_2Y = "Breakout_2Y"    # 2년 신고가 돌파
    BREAKOUT_1Y = "Breakout_1Y"    # 1년 신고가 돌파
    BREAKOUT_6M = "Breakout_6M"    # 6개월 신고가 돌파
    BREAKOUT_3M = "Breakout_3M"    # 3개월 신고가 돌파
    BREAKOUT_1M = "Breakout_1M"    # 1개월 신고가 돌파
    RS_12W_1M = "RS_12W_1M"        # RS 기반 신호
```

#### 3. SignalGenerationService (Main Class)

**초기화**:
```python
def __init__(self, area: str = 'US', trading_mode: bool = False):
    self.area = area                 # 시장 지역 ('US', 'KR' 등)
    self.trading_mode = trading_mode # 실거래 모드 활성화 여부
    self.signals_cache = {}          # 신호 캐싱
```

**주요 메서드**:

1. **generate_comprehensive_signals()**: 종합 신호 생성
   - 입력: df_daily (필수), df_weekly, df_rs, df_fundamental, df_earnings (선택)
   - 출력: 종합 신호 딕셔너리

2. **_generate_weekly_signals()**: 주봉 신호 생성
   - 5가지 조건 검증 (1Year_H == 2Year_H, 52주 범위 등)
   - 반환: 0 또는 1

3. **_generate_rs_signals()**: 상대강도 신호 생성
   - RS_4W >= 90 조건 검증
   - 반환: 0 또는 1

4. **_generate_fundamental_signals()**: 펀더멘털 신호 생성
   - MarketCap >= $2B, REV_YOY >= 10%, EPS_YOY >= 10% 검증
   - 반환: 0 또는 1

5. **_generate_earnings_signals()**: 어닝스 신호 생성
   - 최근 실적 발표 긍정적 서프라이즈 검증
   - 반환: 0 또는 1

6. **_generate_daily_rs_combined_signals()**: 일봉+RS 결합 신호
   - 신고가 돌파 타입 분류
   - 목표가 및 손절가 계산
   - 반환: 신호, 목표가, 손절가, 신호타입

7. **_combine_signals()**: 최종 신호 결합
   - 2개 이상 신호 발생 시 BUY
   - 신호 강도 및 신뢰도 계산

### Usage Example

```python
from project.strategy.signal_generation_service import SignalGenerationService
from project.indicator.data_frame_generator import DataFrameGenerator

# 1. 데이터 로드
generator = DataFrameGenerator(
    universe=["AAPL", "MSFT"],
    market="US",
    area="US"
)
generator.load_data_from_database()

# 2. 신호 생성 서비스 초기화
signal_service = SignalGenerationService(area='US', trading_mode=False)

# 3. 종합 신호 생성
for symbol in ["AAPL", "MSFT"]:
    result = signal_service.generate_comprehensive_signals(
        df_daily=generator.df_D.get(symbol),
        df_weekly=generator.df_W.get(symbol),
        df_rs=generator.df_RS.get(symbol),
        df_fundamental=generator.df_F.get(symbol),
        df_earnings=generator.df_E.get(symbol)
    )

    print(f"{symbol}:")
    print(f"  Final Signal: {result['final_signal'].value}")
    print(f"  Signal Strength: {result['signal_strength']:.2f}")
    print(f"  Target Price: ${result['target_price']:.2f}")
    print(f"  Losscut Price: ${result['losscut_price']:.2f}")
    print(f"  Components: {result['signal_components']}")
```

### Dependencies

**Internal**:
- Indicator Layer: `DataFrameGenerator` (df_D, df_W, df_RS, df_F, df_E 제공)

**External**:
- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 수치 계산
- `logging`: 로깅

### Key Algorithms

#### 주봉 신호 생성 (5가지 조건):
```python
cond1 = df['1Year_H'] == df['2Year_H']
cond2 = df['2Year_L'] < df['1Year_L']
cond3 = df['52_H'] <= df['52_H'].shift(2) * 1.05
cond4 = df['Wclose'].shift(1) > df['52_L'] * 1.3
cond5 = df['Wclose'].shift(1) > df['52_H'] * 0.7

weekly_signal = 1 if all([cond1, cond2, cond3, cond4, cond5]) else 0
```

#### 최종 신호 결합:
```python
if (weekly + rs + daily_rs) >= 2:
    final_signal = SignalType.BUY
    signal_strength = (weekly + rs + fundamental + earnings + daily_rs) / 5.0
else:
    final_signal = SignalType.HOLD
```

---

## Module 2: PositionSizingService

### Purpose
포지션 크기 계산, 리스크 관리, 포트폴리오 최적화를 담당합니다. ATR 기반 리스크 조절 및 시장 상황에 따른 동적 포지션 조정을 수행합니다.

### Location
`project/strategy/position_sizing_service.py` (591 lines)

### Main Classes

#### 1. MarketCondition (Enum)
```python
class MarketCondition(Enum):
    POOR = 1       # 불량한 시장 상황 (포지션 축소)
    MODERATE = 2   # 보통 시장 상황 (기본 포지션)
    GOOD = 3       # 좋은 시장 상황 (포지션 확대)
```

#### 2. PositionSizeConfig (Dataclass)
```python
@dataclass
class PositionSizeConfig:
    std_risk: float = 0.05                      # 표준 리스크 (5%)
    max_stock_list: int = 10                    # 최대 보유 종목 수
    min_loss_cut_percentage: float = 0.03       # 최소 손절 비율 (3%)
    max_single_stock_ratio: float = 0.4         # 단일 종목 최대 비중 (40%)
    pyramiding_ratio: float = 0.1               # 피라미딩 비율 (10%)
    enable_pyramiding: bool = True              # 피라미딩 활성화
    enable_half_sell: bool = True               # 분할 매도 활성화
```

#### 3. CandidateStock (Dataclass)
```python
@dataclass
class CandidateStock:
    ticker: str                  # 종목 심볼
    sorting_metric: float        # 정렬 기준 (RS, 신호 강도 등)
    target_price: float          # 목표가
    signal_strength: float       # 신호 강도
    market_code: str = 'US'      # 시장 코드
```

#### 4. PositionSizingService (Main Class)

**초기화**:
```python
def __init__(self,
             std_risk: float = 0.05,
             market: str = 'US',
             area: str = 'US',
             max_stock_list: int = 10,
             slippage: float = 0.001):
```

**주요 메서드**:

1. **calculate_position_size()**: 포지션 크기 계산
   - ATR 기반 리스크 조절
   - 계좌 잔고 대비 최적 포지션 크기
   - 반환: 매수 수량 (int)

2. **calculate_atr_based_position()**: ATR 기반 포지션
   - ATR(Average True Range) 계산
   - 변동성 고려 포지션 사이징
   - 반환: 매수 금액 (float)

3. **adjust_position_for_market_condition()**: 시장 상황별 포지션 조정
   - POOR: 포지션 50% 축소
   - MODERATE: 100% 기본 포지션
   - GOOD: 포지션 150% 확대

4. **evaluate_market_condition()**: 시장 상황 평가
   - 신호 발생 종목 수 기준
   - >= 20개: GOOD, 10-19개: MODERATE, < 10개: POOR

5. **filter_and_sort_candidates()**: 후보 종목 필터링 및 정렬
   - 신호 강도 기준 정렬
   - RS 순위 기준 정렬
   - Top N 종목 선정

6. **calculate_pyramiding_size()**: 피라미딩 수량 계산
   - 기존 포지션 대비 추가 매수 수량
   - 최대 비중 제한 적용

7. **should_half_sell()**: 분할 매도 여부 판단
   - 목표가 50% 도달 시 절반 매도
   - 리스크 감소 전략

### Usage Example

```python
from project.strategy.position_sizing_service import PositionSizingService, CandidateStock

# 1. 서비스 초기화
position_service = PositionSizingService(
    std_risk=0.05,
    market='US',
    area='US',
    max_stock_list=10,
    slippage=0.001
)

# 2. 매수 후보 종목 리스트
candidates = [
    CandidateStock(
        ticker="AAPL",
        sorting_metric=95.5,  # RS 점수
        target_price=180.0,
        signal_strength=0.85
    ),
    CandidateStock(
        ticker="MSFT",
        sorting_metric=92.3,
        target_price=350.0,
        signal_strength=0.78
    )
]

# 3. 시장 상황 평가
market_condition = position_service.evaluate_market_condition(
    num_signals=15,
    total_candidates=50
)
print(f"Market Condition: {market_condition.name}")

# 4. 후보 필터링 및 정렬
top_candidates = position_service.filter_and_sort_candidates(
    candidates,
    sort_by='sorting_metric',
    max_count=10
)

# 5. 포지션 크기 계산
for candidate in top_candidates:
    position_size = position_service.calculate_position_size(
        current_price=150.0,
        target_price=candidate.target_price,
        account_balance=100000.0,
        atr=2.5,
        num_existing_positions=3
    )
    print(f"{candidate.ticker}: {position_size} shares")
```

### Dependencies

**Internal**:
- `config/risk_management.yaml`: 리스크 관리 설정

**External**:
- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 수치 계산
- `yaml`: 설정 파일 로드
- `logging`: 로깅

### Key Formulas

#### ATR 기반 포지션 크기:
```python
position_amount = (account_balance * std_risk) / (atr * 2)
position_shares = int(position_amount / current_price)
```

#### 시장 상황별 조정:
```python
if market_condition == MarketCondition.GOOD:
    position_size *= 1.5
elif market_condition == MarketCondition.POOR:
    position_size *= 0.5
```

---

## Module 3: AccountAnalysisService

### Purpose
현재 계좌 상태를 분석하고, 보유 종목을 평가하며, 매도 추천을 생성합니다. 포트폴리오 리밸런싱 및 리스크 관리를 지원합니다.

### Location
`project/strategy/account_analysis_service.py` (644 lines)

### Main Classes

#### 1. HoldingStatus (Enum)
```python
class HoldingStatus(Enum):
    HOLDING = "HOLDING"              # 보유 중
    SELL_SIGNAL = "SELL_SIGNAL"      # 매도 신호 발생
    LOSS_CUT = "LOSS_CUT"            # 손절 필요
    PROFIT_TAKING = "PROFIT_TAKING"  # 익절 추천
```

#### 2. AssetType (Enum)
```python
class AssetType(Enum):
    STOCK = "Stock"  # 주식
    ETF = "ETF"      # ETF
    CASH = "Cash"    # 현금
```

#### 3. StockHolding (Dataclass)
```python
@dataclass
class StockHolding:
    ticker: str                        # 종목 심볼
    market: str = 'US'                 # 시장 코드
    exchange: str = 'Stock'            # 거래소
    amount: float = 0.0                # 보유 수량
    avg_price: float = 0.0             # 평균 매수가
    current_price: float = 0.0         # 현재가
    gain_percent: float = 0.0          # 수익률 (%)
    target_price: float = 0.0          # 목표가
    losscut_price: float = 0.0         # 손절가
    weight: float = 0.0                # 포트폴리오 비중 (%)

    # 기술적 지표
    rs_4w: float = 0.0                 # 4주 RS
    sector_rs: float = 0.0             # 섹터 RS
    industry_rs: float = 0.0           # 산업 RS

    # 펀더멘털
    rev_yoy: float = 0.0               # 매출 성장률
    eps_yoy: float = 0.0               # EPS 성장률
    sector: str = 'Unknown'            # 섹터
    industry: str = 'Unknown'          # 산업
    signal_type: str = 'Unknown'       # 신호 타입

    status: HoldingStatus = HoldingStatus.HOLDING
    asset_type: AssetType = AssetType.STOCK
```

#### 4. AccountSummary (Dataclass)
```python
@dataclass
class AccountSummary:
    total_balance: float = 0.0              # 총 잔고
    cash_balance: float = 0.0               # 현금 잔고
    stock_value: float = 0.0                # 주식 평가액
    total_gain_percent: float = 0.0         # 총 수익률
    daily_gain_percent: float = 0.0         # 일일 수익률
    num_holdings: int = 0                   # 보유 종목 수
    num_stocks: int = 0                     # 주식 수
    num_etfs: int = 0                       # ETF 수

    # 리스크 지표
    portfolio_concentration: float = 0.0    # 포트폴리오 집중도
    max_position_weight: float = 0.0        # 최대 종목 비중
    sector_concentration: Dict[str, float]  # 섹터별 집중도
```

#### 5. SellRecommendation (Dataclass)
```python
@dataclass
class SellRecommendation:
    ticker: str                          # 종목 심볼
    reason: str                          # 매도 사유
    urgency: str                         # 긴급도 (HIGH/MEDIUM/LOW)
    current_gain: float                  # 현재 수익률
    target_price: float                  # 목표가
    losscut_price: float                 # 손절가
    recommendation_type: str             # LOSS_CUT | PROFIT_TAKING | SIGNAL_SELL
```

#### 6. AccountAnalysisService (Main Class)

**초기화**:
```python
def __init__(self, area: str = 'US', market: str = 'US'):
    self.area = area
    self.market = market
    self.holdings_cache = {}
```

**주요 메서드**:

1. **analyze_account()**: 계좌 종합 분석
   - 보유 종목 리스트 분석
   - 계좌 요약 정보 생성
   - 반환: AccountSummary

2. **evaluate_holdings()**: 보유 종목 평가
   - 각 종목 수익률 계산
   - RS, 펀더멘털 지표 업데이트
   - 매도 신호 검증

3. **generate_sell_recommendations()**: 매도 추천 생성
   - 손절가 도달 종목 (HIGH urgency)
   - 목표가 도달 종목 (MEDIUM urgency)
   - 신호 약화 종목 (LOW urgency)

4. **check_rebalancing_needed()**: 리밸런싱 필요 여부
   - 단일 종목 비중 > 40%
   - 섹터 집중도 > 50%
   - 현금 비중 < 10%

5. **calculate_portfolio_metrics()**: 포트폴리오 지표 계산
   - 샤프 비율
   - 최대 낙폭 (MDD)
   - 변동성

6. **get_underperforming_holdings()**: 저성과 종목 조회
   - 수익률 하위 20%
   - RS 하락 종목
   - 매도 후보 선정

### Usage Example

```python
from project.strategy.account_analysis_service import (
    AccountAnalysisService,
    StockHolding,
    AssetType
)

# 1. 서비스 초기화
account_service = AccountAnalysisService(area='US', market='US')

# 2. 보유 종목 리스트
holdings = [
    StockHolding(
        ticker="AAPL",
        amount=100,
        avg_price=150.0,
        current_price=165.0,
        target_price=180.0,
        losscut_price=140.0,
        rs_4w=92.5,
        sector="Technology",
        industry="Consumer Electronics"
    ),
    StockHolding(
        ticker="MSFT",
        amount=50,
        avg_price=300.0,
        current_price=320.0,
        target_price=360.0,
        losscut_price=280.0,
        rs_4w=88.3,
        sector="Technology",
        industry="Software"
    )
]

# 3. 계좌 분석
account_summary = account_service.analyze_account(
    holdings=holdings,
    cash_balance=50000.0
)

print(f"Total Balance: ${account_summary.total_balance:,.2f}")
print(f"Total Gain: {account_summary.total_gain_percent:.2f}%")
print(f"Holdings: {account_summary.num_holdings}")
print(f"Max Position Weight: {account_summary.max_position_weight:.2f}%")

# 4. 매도 추천 생성
sell_recommendations = account_service.generate_sell_recommendations(
    holdings=holdings
)

for rec in sell_recommendations:
    print(f"{rec.ticker} - {rec.recommendation_type}")
    print(f"  Reason: {rec.reason}")
    print(f"  Urgency: {rec.urgency}")
    print(f"  Current Gain: {rec.current_gain:.2f}%")

# 5. 리밸런싱 확인
need_rebalancing = account_service.check_rebalancing_needed(
    account_summary=account_summary
)

if need_rebalancing:
    print("⚠️ Portfolio rebalancing recommended")
    print(f"Sector concentration: {account_summary.sector_concentration}")
```

### Dependencies

**Internal**:
- Strategy Layer: `SignalGenerationService` (보유 종목 재평가)
- Indicator Layer: `DataFrameGenerator` (현재 가격 조회)

**External**:
- `pandas >= 1.5.0`: DataFrame 처리
- `numpy >= 1.23.0`: 통계 계산
- `logging`: 로깅
- `json`: 데이터 직렬화
- `pathlib`: 파일 경로 처리

### Key Calculations

#### 수익률 계산:
```python
gain_percent = ((current_price - avg_price) / avg_price) * 100
```

#### 포트폴리오 비중:
```python
weight = (amount * current_price) / total_balance * 100
```

#### 섹터 집중도:
```python
sector_concentration[sector] = sum(holdings in sector) / total_balance
```

---

## 모듈 간 상호작용

### 데이터 흐름:
```
Indicator Layer (DataFrameGenerator)
        ↓
SignalGenerationService → 매매 신호 생성
        ↓
PositionSizingService → 포지션 크기 계산
        ↓
AccountAnalysisService → 계좌 분석 및 평가
        ↓
Service Layer (DailyBacktestService / OrderManager)
```

### 협업 패턴:
1. **신호 생성 후 포지션 계산**:
   ```python
   signal = signal_service.generate_comprehensive_signals(...)
   if signal['final_signal'] == SignalType.BUY:
       position_size = position_service.calculate_position_size(...)
   ```

2. **계좌 분석 후 리밸런싱**:
   ```python
   account_summary = account_service.analyze_account(...)
   if account_service.check_rebalancing_needed(account_summary):
       sell_recommendations = account_service.generate_sell_recommendations(...)
   ```

3. **시장 상황 평가 후 포지션 조정**:
   ```python
   market_condition = position_service.evaluate_market_condition(...)
   adjusted_size = position_service.adjust_position_for_market_condition(
       position_size, market_condition
   )
   ```

---

## 성능 특성

### SignalGenerationService
- **처리 시간**: 단일 종목 < 10ms
- **메모리**: 종목당 ~1MB
- **병렬 처리**: ThreadPoolExecutor 지원

### PositionSizingService
- **처리 시간**: 후보 종목 정렬 < 5ms
- **메모리**: 최소 (설정 파일만 로드)
- **확장성**: 1000+ 후보 종목 처리 가능

### AccountAnalysisService
- **처리 시간**: 100개 보유 종목 분석 < 50ms
- **메모리**: 보유 종목당 ~0.5MB
- **리스크 계산**: 실시간 포트폴리오 지표 업데이트

---

## 설정 파일 연동

### PositionSizingService
- `config/risk_management.yaml` 로드
- 시장별 리스크 파라미터 적용

### AccountAnalysisService
- `config/broker_config.yaml` (선택)
- 계좌별 설정 적용

---

## 테스트

### 단위 테스트
각 모듈별 단위 테스트:
```bash
pytest Test/test_signal_generation_service.py
pytest Test/test_position_sizing_service.py
pytest Test/test_account_analysis_service.py
```

### 통합 테스트
Strategy Layer 전체 통합 테스트:
```bash
pytest Test/test_strategy_layer_integration.py
```

---

## 알려진 제약사항

### SignalGenerationService
- 일간 데이터 최소 200일 필요 (SMA200 계산)
- RS 데이터 없을 시 RS 신호 0 처리
- 주봉 데이터 최소 3개 필요

### PositionSizingService
- ATR 계산 최소 14일 데이터 필요
- 설정 파일 없을 시 기본값 사용
- 피라미딩 최대 3회 제한

### AccountAnalysisService
- 실시간 가격 업데이트 필요 (Indicator Layer 의존)
- 포트폴리오 지표 계산 시 최소 30일 기록 필요

---

## 향후 개선사항

- [ ] SignalGenerationService: 머신러닝 기반 신호 강도 예측
- [ ] PositionSizingService: 켈리 기준 (Kelly Criterion) 포지션 사이징
- [ ] AccountAnalysisService: 실시간 리스크 알림 시스템
- [ ] 전체: 멀티 마켓 동시 분석 지원 (US, KR, JP)

---

## 참고 문서

- **STRATEGY_LAYER_INTERFACE.md**: 입출력 인터페이스 명세
- **SIGNAL_GENERATION_SPEC.md**: 신호 생성 알고리즘 상세 (TODO)
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스
- **docs/architecture/STRATEGY_AGENT_ARCHITECTURE.md**: Strategy Agent 아키텍처

---

**Last Updated**: 2025-10-09
**Managed by**: Strategy Agent
