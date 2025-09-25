# AI Assistant Multi-Agent Trading System Architecture

**Version**: 2.0
**Last Updated**: 2025-09-26
**Status**: Production Ready

## 시스템 개요

AI Assistant는 4개의 전문 에이전트가 협업하는 멀티 에이전트 트레이딩 시스템입니다. 각 에이전트는 명확히 정의된 역할과 책임을 가지며, 표준화된 인터페이스를 통해 통신합니다.

## 에이전트 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                Orchestrator Agent (메인 관리자)               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ • 전체 워크플로우 조정                                      │ │
│  │ • 각 서브 에이전트 작업 할당                                │ │
│  │ • 에이전트간 통신 중재                                      │ │
│  │ • 시스템 상태 모니터링                                      │ │
│  │ • 실시간 거래 실행                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
              │           │           │           │
              ▼           ▼           ▼           ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │Data Agent   │ │Strategy     │ │Service      │ │Helper       │
    │(데이터 관리) │ │Agent        │ │Agent        │ │Agent        │
    │             │ │(전략 개발)   │ │(백테스트/DB)│ │(외부 API)   │
    └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## 1. Orchestrator Agent (오케스트레이터)

### 📁 파일 위치
- `project/orchestrator_agent.py` - 메인 오케스트레이터
- `project/core/auto_trade_orchestrator.py` - 실시간 거래 실행
- `project/multi_agent_trading_system.py` - 시스템 통합

### 🎯 주요 책임
- **워크플로우 관리**: 전체 거래 프로세스 조정
- **에이전트 협업**: 서브 에이전트 작업 할당 및 결과 수집
- **실시간 실행**: 실제 거래 주문 실행 및 모니터링
- **시스템 상태**: 건강성 체크 및 오류 처리
- **위험 관리**: 실시간 리스크 모니터링

### 🔧 핵심 컴포넌트
- `SignalEngine`: 매매 신호 엔진
- `RiskManager`: 위험 관리자
- `OrderManager`: 주문 관리자
- `WebSocketManager`: 실시간 데이터 연결

## 2. Data Agent (데이터 에이전트)

### 📁 파일 위치
- `project/data_agent.py` - 메인 데이터 에이전트
- `project/indicator/` - 기술지표 계산
- `project/database/` - 데이터베이스 관리

### 🎯 주요 책임
- **데이터 수집**: MongoDB에서 시장 데이터 수집
- **기술지표**: RSI, MACD, Bollinger Bands 등 계산
- **데이터 정제**: 결측치 처리 및 데이터 품질 관리
- **성능 최적화**: 대용량 데이터 효율적 처리

### 📊 관리 데이터베이스
- `NasDataBase_D`: 나스닥 일봉 데이터
- `NysDataBase_D`: NYSE 일봉 데이터
- `NasDataBase_M`: 나스닥 분봉 데이터
- `NysDataBase_M`: NYSE 분봉 데이터

## 3. Strategy Agent (전략 에이전트)

### 📁 파일 위치
- `project/strategy_agent.py` - 메인 전략 에이전트
- `project/strategy/` - 전략 구현체들
- `project/core/strategy_integration_service.py` - 전략 통합

### 🎯 주요 책임
- **전략 개발**: 매매 전략 로직 구현
- **신호 생성**: 매수/매도 신호 생성
- **백테스팅**: 전략 성능 검증
- **최적화**: 파라미터 튜닝 및 성능 개선

### 📈 제공 전략
- **Momentum Strategy**: 모멘텀 기반 전략
- **Mean Reversion**: 평균 회귀 전략
- **Relative Strength**: 상대 강도 전략
- **Custom Strategies**: 사용자 정의 전략

## 4. Service Agent (서비스 에이전트)

### 📁 파일 위치
- `project/service_agent.py` - 메인 서비스 에이전트
- `project/service/` - 서비스 구현체들

### 🎯 주요 책임
- **백테스트 엔진**: 전략 성능 검증
- **실행 서비스**: 주문 실행 및 포지션 관리
- **데이터베이스**: MongoDB 연동 및 데이터 저장
- **성능 분석**: 수익률, 샤프 비율 등 계산

### ⚙️ 핵심 서비스
- `BacktestEngine`: 백테스트 실행
- `ExecutionServices`: 주문 실행
- `PerformanceAnalyzer`: 성과 분석
- `TradeRecorder`: 거래 기록

## 5. Helper Agent (헬퍼 에이전트)

### 📁 파일 위치
- `project/helper_agent.py` - 메인 헬퍼 에이전트
- `project/Helper/` - 외부 API 연동

### 🎯 주요 책임
- **브로커 API**: KIS API, LS증권 API 연동
- **데이터 제공**: Alpha Vantage, Yahoo Finance API
- **메신저**: 텔레그램 알림 서비스
- **인증 관리**: API 키 및 토큰 관리

### 🔌 외부 연동
- `KisApiHelperUS`: 한국투자증권 미국주식 API
- `BrokerApiConnector`: 브로커 API 통합
- `YfinanceHelper`: Yahoo Finance 데이터
- `TelegramMessenger`: 텔레그램 알림

## 에이전트 간 인터페이스

### 표준 통신 프로토콜
```python
# 표준 메시지 형식
{
    "agent_id": "data_agent",
    "request_id": "req_001",
    "method": "get_technical_indicators",
    "params": {
        "symbols": ["AAPL", "MSFT"],
        "indicators": ["RSI", "MACD"]
    },
    "timestamp": "2025-09-26T10:30:00Z"
}

# 표준 응답 형식
{
    "agent_id": "data_agent",
    "request_id": "req_001",
    "status": "success",
    "data": { ... },
    "error": null,
    "timestamp": "2025-09-26T10:30:05Z"
}
```

### 인터페이스 정의 파일
- `project/interfaces/service_interfaces.py`: 서비스 인터페이스 정의
- `config/agent_interfaces.yaml`: 에이전트간 함수 호출 규약
- `config/mcp_integration.yaml`: MCP 통신 프로토콜

## 데이터 흐름

```
1. Data Agent → 시장 데이터 수집 → 기술지표 계산
                     ↓
2. Strategy Agent → 신호 생성 → 매매 전략 실행
                     ↓
3. Service Agent → 백테스트 → 성과 분석
                     ↓
4. Helper Agent → 주문 실행 → 브로커 API 호출
                     ↓
5. Orchestrator → 결과 취합 → 실시간 모니터링
```

## 파일 접근 권한 매트릭스

| Agent | 읽기 권한 | 쓰기 권한 | 공유 권한 |
|-------|----------|----------|----------|
| **Orchestrator** | `project/core/*` | `project/core/*` | 모든 에이전트 |
| **Data Agent** | `project/indicator/*`, `project/database/*` | `project/indicator/*`, `project/database/*` | Service Agent |
| **Strategy Agent** | `project/strategy/*` | `project/strategy/*` | 독점 |
| **Service Agent** | `project/service/*` | `project/service/*` | Data Agent |
| **Helper Agent** | `project/Helper/*`, `myStockInfo.yaml` | `project/Helper/*`, `myStockInfo.yaml` | 독점 |

## 설정 파일 관리

### 계층적 설정 구조
```
config/
├── api_credentials.yaml     # API 자격증명
├── broker_config.yaml       # 브로커 설정
├── risk_management.yaml     # 리스크 관리
├── agent_model.yaml         # LLM 모델 할당
└── mcp_integration.yaml     # MCP 통합 설정
```

### 설정 소유권
- **Orchestrator**: 모든 설정 파일 읽기
- **Data Agent**: `broker_config.yaml` 읽기
- **Strategy Agent**: `risk_management.yaml` 읽기
- **Service Agent**: `broker_config.yaml`, `risk_management.yaml` 읽기
- **Helper Agent**: `api_credentials.yaml` 읽기/쓰기

## 보안 및 격리

### 에이전트 격리
- 각 에이전트는 할당된 디렉토리만 접근
- 크로스 에이전트 접근은 표준 인터페이스를 통해서만 허용
- API 키는 암호화 저장

### 오류 격리
- 개별 에이전트 오류가 전체 시스템에 영향을 주지 않음
- 자동 복구 메커니즘 구현
- 상세 로깅 및 알림 시스템

## 모니터링 및 로깅

### 시스템 모니터링
- 에이전트별 성능 지표 추적
- API 사용량 및 비용 모니터링
- 실시간 건강성 체크

### 로깅 구조
```
logs/
├── orchestrator.log         # 오케스트레이터 로그
├── data_agent.log          # 데이터 에이전트 로그
├── strategy_agent.log      # 전략 에이전트 로그
├── service_agent.log       # 서비스 에이전트 로그
└── helper_agent.log        # 헬퍼 에이전트 로그
```

## 확장성

### 새로운 에이전트 추가
1. `project/new_agent.py` 생성
2. `project/router/new_agent_router.py` 라우터 추가
3. 인터페이스 정의 업데이트
4. 권한 매트릭스 수정

### 새로운 전략 추가
1. `project/strategy/new_strategy.py` 구현
2. Strategy Agent에서 등록
3. 백테스트 검증
4. 프로덕션 배포

---

**문서 관리**: 이 문서는 시스템 변경사항에 따라 지속적으로 업데이트됩니다.
**버전 관리**: 모든 변경사항은 Git을 통해 추적됩니다.
**접근 권한**: Orchestrator Agent가 이 문서를 관리하고 업데이트합니다.