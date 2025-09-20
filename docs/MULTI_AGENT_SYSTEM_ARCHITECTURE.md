# Multi-Agent System Architecture Documentation

**프로젝트**: AI Assistant Multi-Agent Trading System
**버전**: 2.0
**작성일**: 2025-09-21
**업데이트**: 전체 에이전트 아키텍처 통합 분석 완료

---

## 🎯 시스템 개요

AI Assistant 프로젝트는 **5개의 전문화된 에이전트가 협업하는 분산 트레이딩 시스템**입니다. 각 에이전트는 명확하게 분리된 책임을 가지며, 정의된 인터페이스를 통해 안전하게 협업합니다.

### 핵심 설계 원칙
- **관심사의 분리**: 각 에이전트는 특정 도메인만 담당
- **느슨한 결합**: 에이전트간 최소한의 의존성 유지
- **보안 격리**: 파일 접근 권한 매트릭스로 보안 보장
- **확장성**: 새로운 기능은 해당 에이전트에만 추가

---

## 🏗️ 전체 시스템 아키텍처

### 멀티 에이전트 계층 구조
```
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent                        │
│                   (전체 워크플로우 관리)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   • 에이전트간 작업 할당 및 조정                          │   │
│  │   • 프롬프트 생성 및 응답 수집                           │   │
│  │   │   • 품질 평가 및 교정                              │   │
│  │   • 시스템 상태 모니터링                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│ Data  │    │Strategy│    │Service│    │Helper │
│Agent  │    │ Agent │    │ Agent │    │Agent  │
└───┬───┘    └───┬───┘    └───┬───┘    └───┬───┘
    │            │            │            │
┌───▼───────┐┌──▼─────────┐┌─▼──────────┐┌▼──────────────┐
│Indicator  ││Strategy    ││Backtest    ││Broker API     │
│Technical  ││Signal Gen  ││Order Exec  ││Data Provider  │
│Database   ││Position    ││Risk Mgmt   ││Notification   │
│Manager    ││Account     ││Performance ││Authentication │
│           ││Analysis    ││Reporting   ││               │
└───────────┘└────────────┘└────────────┘└───────────────┘
```

---

## 🤖 에이전트별 상세 구조

### 1. Orchestrator Agent
**역할**: 전체 시스템의 지휘탑
**모델**: Claude-3-Opus (고성능 의사결정용)

#### 핵심 기능
- **워크플로우 조정**: 전체 거래 프로세스 오케스트레이션
- **프롬프트 관리**: 각 서브 에이전트별 최적화된 프롬프트 생성
- **품질 관리**: 서브 에이전트 응답 품질 평가 및 교정
- **상태 모니터링**: 시스템 전체 상태 추적 및 알림

#### 접근 권한
- **읽기 전용**: 모든 에이전트의 출력 결과
- **쓰기 권한**: 워크플로우 설정, 시스템 로그

### 2. Data Agent
**역할**: 데이터 수집, 처리, 관리의 전문가
**모델**: Gemini-2.5-Flash (대용량 데이터 처리용)

#### 핵심 서비스
```
Project/indicator/
├── TechnicalIndicatorGenerator    # 기술적 지표 계산 엔진
│   ├── 가격 지표 (SMA, EMA, Bollinger)
│   ├── 모멘텀 지표 (RSI, MACD, Stochastic)
│   ├── 볼륨 지표 (Volume SMA, OBV)
│   └── 커스텀 지표 (RS, ADR, Breakout)
└── DataFrameGenerator           # 데이터프레임 생성 관리
    ├── 다중 소스 데이터 통합
    ├── 시계열 데이터 정규화
    ├── 결측값 처리 및 품질 검증
    └── 메모리 최적화 및 캐싱

Project/database/
├── DatabaseManager              # 통합 데이터베이스 관리자
├── MongoDBOperations           # MongoDB CRUD 연산
├── USMarketDataManager         # 미국 시장 전용 관리
├── HistoricalDataManager       # 계좌/거래 내역 관리
└── DatabaseNameCalculator      # DB 명명 규칙 관리
```

#### 접근 권한
- **독점 권한**: `Project/indicator/`, `Project/database/`
- **읽기 전용**: `config/api_credentials.yaml`, `config/broker_config.yaml`

### 3. Strategy Agent
**역할**: 거래 전략 개발 및 신호 생성의 핵심
**모델**: Gemini-2.5-Flash (전략 계산용)

#### 핵심 서비스
```
Project/strategy/
├── SignalGenerationService      # 매매 신호 생성 엔진
│   ├── 다중 타임프레임 분석 (2Y, 1Y, 6M, 3M, 1M)
│   ├── 상대강도(RS) 신호 (4주, 12주)
│   ├── 펀더멘털 필터링
│   ├── 돌파 패턴 인식
│   └── 신호 강도 계산
├── PositionSizingService        # 포지션 사이징 및 리스크 관리
│   ├── ADR 기반 포지션 계산
│   ├── 동적 손절가 계산
│   ├── 피라미딩 전략
│   ├── 승률 분석
│   └── 포트폴리오 집중도 관리
└── AccountAnalysisService       # 계좌 분석 및 평가
    ├── 보유 종목 상세 분석
    ├── 포트폴리오 리스크 평가
    ├── 매도 추천 생성
    ├── 집중도 리스크 계산 (HHI)
    └── 성과 지표 계산
```

#### 접근 권한
- **독점 권한**: `Project/strategy/`
- **읽기 전용**: `Project/indicator/`, `config/risk_management.yaml`

### 4. Service Agent
**역할**: 백테스팅, 주문 실행, 성과 분석
**모델**: Gemini-2.5-Flash (서비스 실행용)

#### 핵심 서비스
```
Project/service/
├── BacktestEngine              # 백테스트 실행 엔진
│   ├── buy_stock()            # 매수 실행 (Strategy Layer에서 이관)
│   ├── sell_stock()           # 매도 실행 (Strategy Layer에서 이관)
│   ├── half_sell_stock()      # 부분 매도 (Strategy Layer에서 이관)
│   ├── pyramid_buy()          # 피라미딩 매수
│   └── whipsaw_protection()   # 휩소 방지
├── OrderExecutionService       # 실제 주문 실행
│   ├── 실시간 주문 처리
│   ├── 주문 상태 추적
│   ├── 체결 확인 및 알림
│   └── 오류 처리 및 재시도
├── RiskManagementService       # 리스크 관리
│   ├── 실시간 리스크 모니터링
│   ├── 포지션 한도 검증
│   ├── 손실 제한 적용
│   └── 응급 청산 로직
└── PerformanceAnalyzer        # 성과 분석
    ├── 수익률 계산
    ├── 샤프 비율, 최대 낙폭
    ├── 거래 통계 분석
    └── 벤치마크 비교
```

#### 접근 권한
- **독점 권한**: `Project/service/`
- **읽기 전용**: `Project/strategy/`, `Project/database/`

### 5. Helper Agent
**역할**: 외부 세계와의 모든 연결 담당
**모델**: Gemini-2.5-Flash (API 통신용)

#### 핵심 서비스
```
Project/Helper/
├── DataProviderAPI             # 외부 데이터 제공자 통합
│   ├── AlphaVantageAPI        # 고품질 시장 데이터
│   ├── YahooFinanceAPI        # 무료 시장 데이터
│   ├── DataProviderManager    # 다중 제공자 관리
│   └── Rate Limiting & Caching
├── BrokerAPIConnector          # 브로커 API 통합
│   ├── KISBrokerAPI          # 한국투자증권 API
│   ├── KISUSHelper           # 미국 거래 전용
│   ├── BrokerAPIManager      # 다중 브로커 관리
│   └── Authentication & Security
└── NotificationService         # 알림 서비스
    ├── TelegramBot           # 기본 텔레그램 기능
    ├── TelegramNotificationService  # 거래 알림 특화
    ├── TelegramCommandHandler     # 명령어 처리
    └── Template Management
```

#### 접근 권한
- **독점 권한**: `Project/Helper/`, `myStockInfo.yaml`
- **읽기 전용**: `config/api_credentials.yaml`, `config/broker_config.yaml`

---

## 🔗 에이전트간 인터페이스 매트릭스

### 데이터 플로우 인터페이스
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│             │ Orchestrator│ Data Agent  │Strategy Agt │Service Agt  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│Orchestrator │      -      │ 작업할당    │ 작업할당    │ 작업할당    │
│Data Agent   │ 데이터상태  │      -      │ 기술지표    │ 데이터조회  │
│Strategy Agt │ 신호결과    │ 데이터요청  │      -      │ 주문신호    │
│Service Agt  │ 실행결과    │ 거래저장    │ 성과피드백  │      -      │
│Helper Agent │ API상태     │ 시장데이터  │ 계좌정보    │ 주문실행    │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### 주요 인터페이스 정의

#### 1. Market Data Interface (Helper → Data)
```python
{
    "symbols": List[str],
    "data_type": "ohlcv|fundamental|earnings",
    "timeframe": "1min|1h|1d|1w",
    "start_date": datetime,
    "end_date": datetime,
    "provider": "alpha_vantage|yahoo_finance"
}
```

#### 2. Technical Analysis Interface (Data → Strategy)
```python
{
    "daily_indicators": Dict[str, pd.DataFrame],
    "weekly_indicators": Dict[str, pd.DataFrame],
    "rs_indicators": Dict[str, pd.DataFrame],
    "fundamental_data": Dict[str, pd.DataFrame],
    "metadata": {
        "last_update": datetime,
        "data_quality": float,
        "coverage_ratio": float
    }
}
```

#### 3. Trading Signal Interface (Strategy → Service)
```python
{
    "signal_type": "BUY|SELL|HOLD",
    "signal_strength": float,  # 0.0 ~ 1.0
    "position_size": float,
    "target_price": float,
    "stop_loss": float,
    "confidence": float,
    "reasoning": str
}
```

#### 4. Order Execution Interface (Service → Helper)
```python
{
    "order_id": str,
    "symbol": str,
    "side": "BUY|SELL",
    "quantity": int,
    "price": float,
    "order_type": "MARKET|LIMIT",
    "account_type": "REAL|VIRTUAL"
}
```

#### 5. Account Status Interface (Helper → Strategy)
```python
{
    "balance": {
        "cash": float,
        "total_asset": float,
        "buying_power": float
    },
    "holdings": List[Dict[str, Any]],
    "trading_status": {
        "is_market_open": bool,
        "last_sync": datetime
    }
}
```

---

## 🗂️ 파일 소유권 및 권한 매트릭스

### 전체 권한 매트릭스
```
┌─────────────────────────┬─────┬──────┬──────────┬─────────┬────────┐
│ 파일/디렉토리           │ Orch│ Data │ Strategy │ Service │ Helper │
├─────────────────────────┼─────┼──────┼──────────┼─────────┼────────┤
│ Project/indicator/      │  R  │  RW  │    R     │    R    │   -    │
│ Project/database/       │  R  │  RW  │    R     │    R    │   -    │
│ Project/strategy/       │  R  │  -   │    RW    │    R    │   -    │
│ Project/service/        │  R  │  -   │    R     │   RW    │   -    │
│ Project/Helper/         │  R  │  -   │    -     │    -    │   RW   │
│ myStockInfo.yaml        │  -  │  -   │    -     │    -    │   RW   │
│ config/*.yaml           │  R  │  R   │    R     │    R    │   R    │
│ storage/                │  RW │  RW  │    R     │   RW    │   RW   │
│ outputs/                │  RW │  R   │    R     │   RW    │   R    │
└─────────────────────────┴─────┴──────┴──────────┴─────────┴────────┘

범례: R=읽기, W=쓰기, RW=읽기+쓰기, -=접근금지
```

### 상세 권한 정의

#### 독점 권한 (EXCLUSIVE)
- **Data Agent**: `Project/indicator/`, `Project/database/`
- **Strategy Agent**: `Project/strategy/`
- **Service Agent**: `Project/service/`
- **Helper Agent**: `Project/Helper/`, `myStockInfo.yaml`

#### 공유 읽기 권한 (SHARED READ)
- **모든 에이전트**: `config/*.yaml` (설정 파일)
- **Data, Service, Helper**: `storage/` (데이터 저장소)

#### 크로스 에이전트 접근
- **Strategy → Data**: 기술지표 데이터 읽기
- **Service → Strategy**: 신호 데이터 읽기
- **Service → Database**: 거래 내역 저장

---

## ⚙️ 설정 파일 아키텍처

### 설정 파일 계층구조
```
config/
├── agent_model.yaml           # 에이전트별 LLM 모델 설정
├── api_credentials.yaml       # 외부 API 자격증명 (암호화)
├── broker_config.yaml        # 브로커 설정 및 시장 정보
├── risk_management.yaml      # 리스크 관리 정책
├── mcp_integration.yaml      # MCP 통합 설정 (신규)
├── agent_interfaces.yaml     # 에이전트간 인터페이스 정의 (신규)
└── file_ownership.yaml       # 파일 접근 권한 매트릭스 (신규)
```

#### 1. agent_model.yaml
```yaml
agents:
  orchestrator:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.1

  data_agent:
    primary_model: "gemini-2.5-flash"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 8000
    temperature: 0.0

  strategy_agent:
    primary_model: "gemini-2.5-flash"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.1

  service_agent:
    primary_model: "gemini-2.5-flash"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.0

  helper_agent:
    primary_model: "gemini-2.5-flash"
    fallback_model: "claude-3-sonnet-20240229"
    max_tokens: 4000
    temperature: 0.0
```

#### 2. agent_interfaces.yaml (신규)
```yaml
interfaces:
  market_data:
    provider: "helper_agent"
    consumer: "data_agent"
    schema: "market_data_schema_v1"
    validation: true

  technical_indicators:
    provider: "data_agent"
    consumer: "strategy_agent"
    schema: "indicators_schema_v1"
    validation: true

  trading_signals:
    provider: "strategy_agent"
    consumer: "service_agent"
    schema: "signals_schema_v1"
    validation: true

  order_execution:
    provider: "service_agent"
    consumer: "helper_agent"
    schema: "orders_schema_v1"
    validation: true

schemas:
  market_data_schema_v1:
    required_fields: ["symbol", "timestamp", "ohlcv"]
    data_types: {"price": "float", "volume": "int"}

  indicators_schema_v1:
    required_fields: ["symbol", "indicator_type", "value", "timestamp"]
    data_types: {"value": "float"}
```

#### 3. file_ownership.yaml (신규)
```yaml
ownership:
  data_agent:
    exclusive:
      - "Project/indicator/"
      - "Project/database/"
    read_only:
      - "config/api_credentials.yaml"
      - "config/broker_config.yaml"

  strategy_agent:
    exclusive:
      - "Project/strategy/"
    read_only:
      - "Project/indicator/"
      - "config/risk_management.yaml"

  service_agent:
    exclusive:
      - "Project/service/"
    read_only:
      - "Project/strategy/"
      - "Project/database/"

  helper_agent:
    exclusive:
      - "Project/Helper/"
      - "myStockInfo.yaml"
    read_only:
      - "config/api_credentials.yaml"
      - "config/broker_config.yaml"

access_matrix:
  orchestrator_agent: ["R", "R", "R", "R", "R"]
  data_agent: ["RW", "-", "R", "R", "-"]
  strategy_agent: ["R", "RW", "R", "-", "-"]
  service_agent: ["R", "R", "RW", "-", "-"]
  helper_agent: ["-", "-", "-", "RW", "RW"]
```

---

## 🔄 시스템 워크플로우

### 1. 전체 거래 워크플로우
```
1. [Helper] 시장 데이터 수집
     ↓
2. [Data] 기술적 지표 계산
     ↓
3. [Strategy] 매매 신호 생성
     ↓
4. [Strategy] 포지션 사이징
     ↓
5. [Service] 백테스트 검증
     ↓
6. [Service] 실제 주문 실행
     ↓
7. [Helper] 브로커 API 호출
     ↓
8. [Helper] 체결 알림 발송
     ↓
9. [Orchestrator] 전체 결과 정리
```

### 2. 에러 처리 워크플로우
```
에러 감지 → 해당 Agent 내부 처리 → 실패 시 Orchestrator 에스컬레이션
     ↓              ↓                        ↓
로그 기록 → 자동 복구 시도 → 대체 방안 실행 → 사용자 알림
```

### 3. 모니터링 워크플로우
```
각 Agent 성능 지표 수집 → Orchestrator 집계 → 대시보드 업데이트
         ↓                       ↓                 ↓
    임계치 확인 → 알림 발송 → 자동 조치 실행
```

---

## 📊 성능 및 품질 지표

### 시스템 레벨 KPI
```yaml
availability:
  target: 99.9%
  measurement: "시스템 가동시간 / 전체시간"

latency:
  data_processing: "<10초 (1000종목 기준)"
  signal_generation: "<5초"
  order_execution: "<3초"

throughput:
  concurrent_agents: 5
  max_symbols: 1000
  orders_per_minute: 100

quality:
  data_accuracy: ">99.5%"
  signal_precision: ">60%"
  order_success_rate: ">99%"
```

### 에이전트별 성능 목표
| 에이전트 | 응답시간 | 처리량 | 정확도 | 가용성 |
|----------|----------|--------|--------|--------|
| Data | <10초 | 1000종목 | >99.5% | >99.5% |
| Strategy | <5초 | 100신호 | >60% | >99.8% |
| Service | <3초 | 50주문 | >99% | >99.9% |
| Helper | <2초 | API제한 | >99% | >99.5% |

---

## 🔒 보안 아키텍처

### 보안 계층
```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Agent Isolation                    │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │           File Access Control           │   │   │
│  │  │  ┌─────────────────────────────────┐   │   │   │
│  │  │  │        API Authentication        │   │   │   │
│  │  │  │  ┌─────────────────────────┐   │   │   │   │
│  │  │  │  │    Data Encryption       │   │   │   │   │
│  │  │  │  └─────────────────────────┘   │   │   │   │
│  │  │  └─────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 보안 정책
1. **에이전트 격리**: 각 에이전트는 할당된 파일만 접근
2. **API 키 암호화**: 모든 외부 API 키는 암호화 저장
3. **접근 로깅**: 모든 파일 접근은 로그에 기록
4. **정기 감사**: 주간 보안 검토 및 권한 점검

---

## 🚀 확장성 및 유지보수

### 확장 포인트
1. **새로운 전략**: Strategy Agent에 신규 전략 클래스 추가
2. **새로운 브로커**: Helper Agent에 브로커 API 모듈 추가
3. **새로운 지표**: Data Agent에 기술지표 함수 추가
4. **새로운 알림**: Helper Agent에 알림 채널 추가

### 버전 관리
- **스키마 버전**: 인터페이스 변경 시 버전 관리
- **하위 호환성**: 기존 인터페이스 유지하며 점진적 업그레이드
- **롤백 지원**: 문제 발생 시 이전 버전으로 즉시 복구

---

## 📋 체크리스트

### 시스템 시작 전
- [ ] 모든 설정 파일 검증 완료
- [ ] 에이전트별 권한 매트릭스 확인
- [ ] 외부 API 연결 테스트 통과
- [ ] 데이터베이스 연결 확인

### 운영 중 모니터링
- [ ] 각 에이전트 응답 시간 모니터링
- [ ] 파일 접근 권한 위반 체크
- [ ] API 사용량 및 한도 확인
- [ ] 시스템 리소스 사용량 추적

### 정기 점검 (주간)
- [ ] 보안 감사 및 권한 검토
- [ ] 성능 지표 분석 및 최적화
- [ ] 에러 로그 분석 및 개선
- [ ] 백업 및 복구 테스트

---

**📝 문서 상태**: 멀티 에이전트 아키텍처 통합 분석 완료 (2025-09-21)
**다음 업데이트**: Service Agent 백테스트 함수 이관 및 실제 운영 시작 시