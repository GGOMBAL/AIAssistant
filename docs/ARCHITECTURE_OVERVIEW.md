# AI Assistant 전체 아키텍처 개요

**프로젝트**: AI Assistant Multi-Agent Trading System
**버전**: 1.0
**작성일**: 2025-09-15
**관리**: 모든 에이전트 공통 참조

---

## 🏗️ 시스템 전체 아키텍처

### 멀티 에이전트 계층 구조
```
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                        │
│                   (메인 관리자)                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐    ┌────▼────┐
│ Data  │    │Strategy│    │Service│    │ Helper  │
│Agent  │    │ Agent │    │ Agent │    │ Agent   │
└───────┘    └───────┘    └───────┘    └─────────┘
```

### 레이어별 책임
- **Orchestrator**: 전체 워크플로우 조정, 에이전트간 통신
- **Data Agent**: 데이터 수집, 기술지표 계산, 데이터베이스 관리
- **Strategy Agent**: 전략 개발, 신호 생성, 포트폴리오 최적화
- **Service Agent**: 백테스팅, 주문 실행, 리스크 관리
- **Helper Agent**: 외부 API, 브로커 연결, 알림 서비스

---

## 📊 데이터 플로우

### 1. 데이터 수집 플로우
```
External APIs → Helper Agent → Data Agent → Database
     ↓              ↓             ↓           ↓
(Market Data)  (API Management) (Processing) (Storage)
```

### 2. 전략 실행 플로우
```
Database → Data Agent → Strategy Agent → Service Agent → Broker
    ↓          ↓             ↓              ↓            ↓
(Historical) (Indicators) (Signals)    (Orders)    (Execution)
```

### 3. 모니터링 플로우
```
All Agents → Orchestrator → Helper Agent → Notifications
     ↓            ↓              ↓             ↓
  (Status)    (Coordination)  (Telegram)   (Alerts)
```

---

## 🔧 기술 스택

### Core Technologies
- **LLM Models**: Claude-3 (Opus/Sonnet), Gemini-Pro
- **Database**: MongoDB (market data, trading history)
- **APIs**: KIS, Alpha Vantage, Yahoo Finance
- **Messaging**: Telegram Bot API
- **Configuration**: YAML-based config management

### LLM 라우터 시스템
```
Agent Request → LLM Router → Model Selection → Response
      ↓             ↓             ↓              ↓
  (Task Type)  (Load Balance)  (Optimization)  (Result)
```

---

## 📁 프로젝트 구조

```
AIAssistant/
├── Claude.md                    # 프로젝트 핵심 규칙
├── README.md                    # 프로젝트 메인 문서
├── docs/                        # 문서 아카이브
│   ├── ARCHITECTURE_OVERVIEW.md # 이 문서
│   ├── DATABASE_ARCHITECTURE.md # 데이터베이스 상세
│   └── HELPER_FUNCTIONS_MANUAL.md # Helper 함수 매뉴얼
├── plan/                        # 계획 문서
│   └── project_reorganization_plan.md
├── Report/                      # 테스트 리포트
├── config/                      # 설정 파일
│   ├── agent_interfaces.yaml    # 에이전트 인터페이스
│   ├── agent_model.yaml         # LLM 모델 할당
│   ├── api_credentials.yaml     # API 자격증명
│   ├── broker_config.yaml       # 브로커 설정
│   ├── risk_management.yaml     # 리스크 관리
│   └── file_ownership.yaml      # 파일 접근 권한
└── Project/                     # 구현 파일
    ├── Helper/                  # Helper Agent 전용
    ├── indicator/               # Data Agent 관리
    ├── strategy/                # Strategy Agent 관리
    ├── service/                 # Service Agent 관리
    └── database/                # Data Agent 관리
```

---

## 🤖 에이전트별 상세 역할

### Data Agent (Indicator Layer)
**주요 책임**:
- 시장 데이터 수집 및 검증
- 기술지표 계산 (RSI, MACD, Bollinger Bands 등)
- 데이터베이스 운영 및 관리
- 데이터 품질 보증

**관리 파일**:
- `Project/indicator/technical_indicators.py`
- `Project/database/database_manager.py`
- `Project/service/data_gathering_service.py`

**사용 모델**: Claude-3-Sonnet (데이터 처리 최적화)

### Strategy Agent (Strategy Layer)
**주요 책임**:
- 트레이딩 전략 개발 및 최적화
- 매매 신호 생성
- 포지션 사이징 계산
- 리스크 관리 전략

**관리 파일**:
- `Project/strategy/signal_generator.py`
- `Project/strategy/position_sizing.py`
- `Project/strategy/risk_management.py`

**사용 모델**: Claude-3-Opus (복잡한 전략 로직)

### Service Agent (Service Layer)
**주요 책임**:
- 백테스팅 엔진 운영
- 실시간 주문 실행
- 포트폴리오 관리
- 성과 분석

**관리 파일**:
- `Project/service/backtester.py`
- `Project/service/trade_executor.py`
- `Project/service/position_manager.py`

**사용 모델**: Claude-3-Sonnet (안정적인 서비스 운영)

### Helper Agent (Service Layer)
**주요 책임**:
- 외부 API 연동 및 관리
- 브로커 계정 관리
- 알림 및 보고서 전송
- API 키 및 자격증명 관리

**관리 파일** (독점):
- `Project/Helper/**/*.py`
- `myStockInfo.yaml`
- `config/api_credentials.yaml`

**사용 모델**: Claude-3-Sonnet (API 통합 최적화)

---

## 🔐 보안 및 권한 관리

### 파일 접근 매트릭스
| 에이전트 | Helper Files | Indicator Files | Strategy Files | Service Files | Database Files |
|---------|--------------|----------------|----------------|---------------|----------------|
| Data Agent | READ-ONLY | FULL ACCESS | READ-ONLY | LIMITED | FULL ACCESS |
| Strategy Agent | READ-ONLY | READ-ONLY | FULL ACCESS | READ-ONLY | READ-ONLY |
| Service Agent | READ-ONLY | READ-ONLY | READ-ONLY | FULL ACCESS | LIMITED |
| Helper Agent | FULL ACCESS | NO ACCESS | NO ACCESS | NO ACCESS | NO ACCESS |

### API 보안
- 모든 API 키는 암호화 저장
- 실제 계좌 접근 시 2단계 인증
- API 호출 로깅 및 모니터링
- 비정상 활동 자동 감지

---

## 📈 성능 최적화

### LLM 모델 최적화
- **작업별 모델 선택**: 복잡도에 따른 Opus/Sonnet 선택
- **Gemini 모델 활용**: 대용량 데이터 처리용
- **Load Balancing**: claude-code-router 활용
- **캐싱 전략**: 반복 작업 결과 캐시

### 데이터베이스 최적화
- **MongoDB 인덱싱**: 날짜, 심볼별 최적화
- **쿼리 최적화**: 필요한 필드만 조회
- **배치 처리**: 대용량 데이터 청크 단위 처리
- **연결 풀링**: 커넥션 재사용

---

## 🔄 운영 워크플로우

### 일일 운영 사이클
```
08:30 - 사전 시장 준비
├── API 인증 및 연결 테스트
├── 시장 휴일 확인
├── 워치리스트 업데이트
└── 전략 매개변수 검증

09:00-15:30 - 실시간 트레이딩
├── 시장 데이터 모니터링
├── 신호 생성 및 검증
├── 주문 실행 및 관리
└── 리스크 모니터링

16:00-18:00 - 사후 분석
├── 거래 성과 분석
├── 포트폴리오 재조정
├── 다음 날 전략 준비
└── 일일 보고서 생성
```

### 주간 운영 사이클
- **월요일**: 주간 전략 계획 수립
- **수요일**: 중간 성과 리뷰
- **금요일**: 주간 성과 분석 및 다음 주 준비

---

## 📊 모니터링 및 알림

### 시스템 모니터링
- **에이전트 상태**: 각 에이전트별 응답 시간 및 성공률
- **API 사용량**: 호출 횟수, 비용, 한도 모니터링
- **데이터베이스**: 연결 상태, 쿼리 성능, 저장 용량
- **거래 성과**: 실시간 P&L, 리스크 지표

### 알림 시스템
- **긴급 알림**: 시스템 오류, 대규모 손실
- **일반 알림**: 거래 체결, 신호 생성
- **일일 보고**: 성과 요약, 다음 날 계획
- **주간 보고**: 상세 분석, 전략 조정 제안

---

## 🎯 확장 계획

### 단기 확장 (1-3개월)
- 추가 거래소 지원 (업비트, 바이낸스)
- 더 많은 기술지표 구현
- 고급 리스크 관리 기능
- 실시간 뉴스 분석 통합

### 중기 확장 (3-6개월)
- 머신러닝 모델 통합
- 멀티 자산 포트폴리오 지원
- 소셜 트레이딩 기능
- 모바일 앱 개발

### 장기 비전 (6개월+)
- AI 기반 자동 전략 생성
- 글로벌 마켓 완전 지원
- 기관 투자자 급 기능
- 오픈소스 커뮤니티 구축

---

## 📞 지원 및 문의

### 기술 지원
- **아키텍처 문의**: 이 문서 참조
- **에이전트 이슈**: `agent_interfaces.yaml` 확인
- **권한 문제**: `file_ownership.yaml` 검토
- **성능 이슈**: 모니터링 대시보드 확인

### 문서 관리
- 모든 아키텍처 변경사항은 이 문서에 반영
- 에이전트별 세부 문서는 각 docs 하위 파일 참조
- 설정 변경은 해당 YAML 파일 및 관련 문서 동시 업데이트

---

**🔥 핵심**: 이 아키텍처는 모든 에이전트가 공통으로 이해하고 준수해야 하는 기본 구조입니다.

*문서 버전: 1.0 | 최종 업데이트: 2025-09-15*