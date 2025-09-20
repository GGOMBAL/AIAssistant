# Strategy Agent Architecture Documentation

**버전**: 1.0
**작성일**: 2025-09-21
**업데이트**: Strategy Layer 구현 완료 기준

---

## 🎯 Strategy Agent 개요

Strategy Agent는 **전략 개발 및 신호 생성을 전담**하는 에이전트로, 거래 신호 생성, 포지션 사이징, 계좌 분석의 핵심 기능을 담당합니다.

### 주요 책임
- 다중 타임프레임 기술적 분석을 통한 매매 신호 생성
- 포지션 사이징 및 리스크 관리 계산
- 계좌 현황 분석 및 포트폴리오 평가
- 매도 신호 및 손절가 계산

---

## 📁 파일 접근 권한

### EXCLUSIVE (읽기/쓰기/실행)
Strategy Agent는 다음 파일들에 대해 **독점적 권한**을 가집니다:

```
Project/strategy/
├── signal_generation_service.py     # 신호 생성 서비스
├── position_sizing_service.py       # 포지션 사이징 서비스
├── account_analysis_service.py      # 계좌 분석 서비스
├── trading_strategy_*.py           # 자동 생성된 전략 파일들
└── __init__.py                     # 패키지 초기화
```

### READ-ONLY (읽기 전용)
다른 레이어의 데이터를 읽을 수 있지만 수정할 수 없습니다:

```
Project/indicator/                  # Data Agent 영역 (읽기만 가능)
Project/database/                   # 데이터베이스 스키마 (읽기만 가능)
config/risk_management.yaml         # 리스크 관리 설정
config/broker_config.yaml          # 브로커 설정
storage/agent_interactions/         # 에이전트 상호작용 로그
```

---

## 🏗️ 서비스 아키텍처

### 1. Signal Generation Service

**파일**: `signal_generation_service.py`
**클래스**: `SignalGenerationService`
**기능**: 다중 타임프레임 기술적 분석을 통한 매매 신호 생성

#### 핵심 컴포넌트
```python
# Enums
class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class BreakoutType(Enum):
    BREAKOUT_2Y = "Breakout_2Y"
    BREAKOUT_1Y = "Breakout_1Y"
    BREAKOUT_6M = "Breakout_6M"
    BREAKOUT_3M = "Breakout_3M"
    BREAKOUT_1M = "Breakout_1M"
    RS_12W_1M = "RS_12W_1M"
```

#### 주요 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `generate_comprehensive_signals()` | DataFrame 세트 | Dict[str, Any] | 종합 신호 생성 |
| `_generate_weekly_signals()` | 주봉 데이터 | int | 주간 신호 점수 |
| `_generate_rs_signals()` | RS 데이터 | int | 상대강도 신호 |
| `_generate_daily_rs_combined_signals()` | 일봉+RS 데이터 | Dict[str, Any] | 핵심 결합 신호 |
| `calculate_signal_strength()` | 신호 데이터 | float | 신호 강도 계산 |

### 2. Position Sizing Service

**파일**: `position_sizing_service.py`
**클래스**: `PositionSizingService`
**기능**: 포지션 사이징, 리스크 관리, 포트폴리오 최적화

#### 핵심 컴포넌트
```python
# Enums & DataClasses
class MarketCondition(Enum):
    POOR = 1
    MODERATE = 2
    GOOD = 3

@dataclass
class PositionSizeConfig:
    std_risk: float = 0.05
    max_stock_list: int = 10
    min_loss_cut_percentage: float = 0.03
    max_single_stock_ratio: float = 0.4
    pyramiding_ratio: float = 0.1
    enable_pyramiding: bool = True
    enable_half_sell: bool = True

@dataclass
class CandidateStock:
    ticker: str
    sorting_metric: float
    target_price: float
    signal_strength: float
    market_code: str = 'US'
```

#### 주요 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `calculate_position_size()` | ADR, 잔고, 시장상황 | Dict[str, Any] | 포지션 크기 계산 |
| `calculate_losscut_price()` | 현재가격, 수익률, 리스크 | Dict[str, Any] | 손절가 계산 |
| `calculate_win_loss_ratio()` | 거래 내역 | Dict[str, Any] | 승률 분석 |
| `select_candidate_stocks_single()` | 신호 데이터, 설정 | List[CandidateStock] | 단일 후보주 선택 |
| `calculate_pyramid_parameters()` | 보유 정보 | Dict[str, Any] | 피라미딩 계산 |

### 3. Account Analysis Service

**파일**: `account_analysis_service.py`
**클래스**: `AccountAnalysisService`
**기능**: 계좌 분석, 포트폴리오 평가, 리스크 평가

#### 핵심 컴포넌트
```python
# Enums & DataClasses
class HoldingStatus(Enum):
    HOLDING = "HOLDING"
    SELL_SIGNAL = "SELL_SIGNAL"
    LOSS_CUT = "LOSS_CUT"
    PROFIT_TAKING = "PROFIT_TAKING"

@dataclass
class StockHolding:
    ticker: str
    market: str = 'US'
    exchange: str = 'Stock'
    amount: float = 0.0
    avg_price: float = 0.0
    current_price: float = 0.0
    gain_percent: float = 0.0
    target_price: float = 0.0
    losscut_price: float = 0.0
    weight: float = 0.0
    # ... 추가 기술적 지표 필드들

@dataclass
class AccountSummary:
    total_asset: float = 0.0
    cash_balance: float = 0.0
    stock_value: float = 0.0
    total_gain_loss: float = 0.0
    total_gain_percent: float = 0.0
    cash_ratio: float = 0.0
    stock_count: int = 0
    concentration_risk: float = 0.0

@dataclass
class SellRecommendation:
    ticker: str
    reason: str
    priority: int = 1
    target_ratio: float = 1.0
```

#### 주요 메서드
| 메서드 | 입력 | 출력 | 설명 |
|--------|------|------|------|
| `analyze_account()` | 보유정보, 잔고, 시장데이터 | Dict[str, Any] | 종합 계좌 분석 |
| `_analyze_holdings()` | 보유정보, 시장데이터 | List[StockHolding] | 보유종목 분석 |
| `_calculate_concentration()` | 보유종목 리스트 | float | 집중도 리스크 계산 |
| `_generate_sell_recommendations()` | 보유종목 리스트 | List[SellRecommendation] | 매도 추천 생성 |
| `_calculate_portfolio_metrics()` | 보유정보, 요약정보 | Dict[str, Any] | 포트폴리오 지표 |

---

## 🔗 인터페이스 정의

### 입력 인터페이스

#### 1. 시장 데이터 (from Data Agent)
```python
{
    "daily_data": pd.DataFrame,     # 일봉 데이터
    "weekly_data": pd.DataFrame,    # 주봉 데이터
    "rs_data": pd.DataFrame,        # 상대강도 데이터
    "fundamental_data": pd.DataFrame, # 기본정보 데이터
    "earnings_data": pd.DataFrame   # 실적 데이터
}
```

#### 2. 계좌 데이터 (from Helper Agent)
```python
{
    "holdings": List[Dict],         # 보유종목 정보
    "balance": Dict[str, float],    # 계좌 잔고 정보
    "trading_history": List[Dict]   # 거래 내역
}
```

### 출력 인터페이스

#### 1. 신호 결과 (to Service Agent)
```python
{
    "signal_type": "BUY|SELL|HOLD",
    "signal_strength": float,       # 0.0 ~ 1.0
    "breakout_types": List[str],    # 돌파 유형들
    "target_price": float,
    "confidence": float,
    "timeframe_scores": {
        "weekly": int,
        "rs": int,
        "fundamental": int,
        "daily_rs_combined": Dict
    }
}
```

#### 2. 포지션 사이징 결과 (to Service Agent)
```python
{
    "position_ratio": float,        # 포지션 비율
    "target_amount": float,         # 목표 투자금
    "losscut_price": float,         # 손절가
    "market_condition": str,        # 시장 상황
    "candidate_stocks": List[CandidateStock],
    "risk_metrics": {
        "adr_range": float,
        "volatility_adjustment": float,
        "concentration_limit": float
    }
}
```

#### 3. 계좌 분석 결과 (to Orchestrator)
```python
{
    "account_summary": AccountSummary,
    "holdings": List[StockHolding],
    "sell_recommendations": List[SellRecommendation],
    "portfolio_risk": {
        "concentration_risk": float,
        "sector_concentration": Dict[str, float],
        "volatility_risk": float,
        "liquidity_risk": float
    },
    "portfolio_metrics": {
        "sharpe_ratio": float,
        "max_drawdown": float,
        "win_rate": float,
        "profit_factor": float
    }
}
```

---

## ⚙️ 설정 파일 연동

### 1. 리스크 관리 설정
**파일**: `config/risk_management.yaml`
```yaml
position_sizing:
  std_risk: 0.05
  max_stock_list: 10
  min_loss_cut_percentage: 0.03
  max_single_stock_ratio: 0.4

pyramiding:
  enable: true
  ratio: 0.1
  max_levels: 3
```

### 2. 에이전트 모델 설정
**파일**: `config/agent_model.yaml`
```yaml
agents:
  strategy_agent:
    primary_model: "gemini-2.5-flash"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.1
```

---

## 🔄 워크플로우

### 1. 신호 생성 워크플로우
```
[Data Agent] → Market Data → [Strategy Agent]
                ↓
        Signal Generation Service
                ↓
        Position Sizing Service
                ↓
[Service Agent] ← Trading Orders ← [Strategy Agent]
```

### 2. 계좌 분석 워크플로우
```
[Helper Agent] → Account Data → [Strategy Agent]
                 ↓
        Account Analysis Service
                 ↓
[Orchestrator] ← Analysis Results ← [Strategy Agent]
```

---

## 🚨 제약사항 및 규칙

### 1. 파일 접근 제한
- **절대 금지**: `Project/service/`, `Project/Helper/`, `Project/indicator/` 수정
- **읽기만 허용**: 설정 파일들 (`config/*.yaml`)
- **독점 권한**: `Project/strategy/` 내 모든 파일

### 2. 백테스트 실행 제한
- **Strategy Layer**: 전략 로직과 계산만 담당
- **Service Layer**: 실제 주문 실행 및 백테스트 실행
- **분리된 함수**: `buy_stock()`, `sell_stock()`, `half_sell_stock()` 등은 Service Layer로 이관

### 3. 데이터 의존성
- **입력 데이터**: Data Agent가 제공하는 정제된 시장 데이터만 사용
- **계좌 데이터**: Helper Agent가 제공하는 실시간 계좌 정보만 사용
- **직접 API 호출 금지**: 모든 외부 데이터는 다른 에이전트를 통해 수신

---

## 📊 성능 지표

### 1. 신호 품질
- **신호 정확도**: > 60%
- **신호 생성 시간**: < 2초
- **False Positive 비율**: < 30%

### 2. 리스크 관리
- **손실 제한**: 단일 포지션 최대 5%
- **집중도 리스크**: HHI < 0.3
- **포트폴리오 변동성**: < 20% (연율화)

### 3. 응답 성능
- **계좌 분석 시간**: < 5초
- **포지션 계산 시간**: < 1초
- **메모리 사용량**: < 500MB

---

## 🔧 개발 및 유지보수

### 1. 테스트 커버리지
- **단위 테스트**: 각 서비스별 80% 이상
- **통합 테스트**: 에이전트간 인터페이스 검증
- **성능 테스트**: 대용량 데이터 처리 검증

### 2. 로깅 및 모니터링
- **모든 신호 생성 로깅**: 디버깅을 위한 상세 기록
- **성능 메트릭 추적**: 응답 시간, 메모리 사용량
- **에러 추적**: 자동 복구 및 알림 시스템

### 3. 버전 관리
- **하위 호환성**: 인터페이스 변경 시 점진적 업그레이드
- **A/B 테스트**: 새로운 전략 알고리즘 검증
- **롤백 지원**: 문제 발생 시 이전 버전으로 즉시 복구

---

**📝 문서 상태**: Strategy Layer 구현 완료 (2025-09-21)
**다음 업데이트**: Service Layer 백테스트 함수 이관 완료 시