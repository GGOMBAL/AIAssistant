# 파일 접근 권한 체계

**최종 업데이트**: 2025-10-21
**적용 대상**: 모든 Agent

---

## 핵심 원칙

**각각의 에이전트는 할당된 Layer만 수정 권한이 있으며, 인터페이스는 Orchestrator 승인 하에만 수정 가능합니다**.

### Layer별 수정 권한 규칙:

1. ✅ **각 Sub-Agent는 자신이 담당하는 Layer 파일만 수정 가능**
2. 🚫 **인터페이스(Interface)는 Sub-Agent가 직접 수정 불가** (금지)
3. 🔐 **인터페이스 수정은 Orchestrator가 승인한 경우에만 가능** (승인 필요)
4. ✅ **모든 Sub-Agent는 모든 Layer를 읽기(Read)는 가능**

---

## 접근 권한 매트릭스

| Agent | 담당 Layer | 수정 권한 (WRITE) | 읽기 권한 (READ) |
|-------|-----------|------------------|-----------------|
| **Helper Agent** | `project/Helper/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | `project/router/helper_agent_router.py` | ✅ 수정 가능 | |
| | Helper Layer 인터페이스 | ❌ Orchestrator 승인 필요 | ✅ 가능 |
| **Database Agent** | `project/database/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | `project/indicator/` | ✅ 전체 수정 가능 | |
| | `project/router/data_agent_router.py` | ✅ 수정 가능 | |
| | Database/Indicator 인터페이스 | ❌ Orchestrator 승인 필요 | ✅ 가능 |
| **Strategy Agent** | `project/strategy/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | `project/router/strategy_agent_router.py` | ✅ 수정 가능 | |
| | Strategy Layer 인터페이스 | ❌ Orchestrator 승인 필요 | ✅ 가능 |
| **Service Agent** | `project/service/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | `project/router/service_agent_router.py` | ✅ 수정 가능 | |
| | Service Layer 인터페이스 | ❌ Orchestrator 승인 필요 | ✅ 가능 |
| **Report Agent** | `project/reporting/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | `project/router/report_agent_router.py` | ✅ 수정 가능 | |
| | Report Layer 인터페이스 | ❌ Orchestrator 승인 필요 | ✅ 가능 |
| **Orchestrator Agent** | `orchestrator/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | 모든 인터페이스 | ✅ 수정 승인 권한 | ✅ 가능 |
| **RUN AGENT** | `run_agent.py`, `agents/run_agent/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |

---

## Layer별 상세 구조

### Helper Layer (Helper Agent 전담)

```
project/Helper/
├── kis_api_helper_us.py          # KIS API 통합
├── broker_api_connector.py       # 브로커 API 커넥터
├── data_provider_api.py          # 외부 데이터 제공자
├── yfinance_helper.py            # Yahoo Finance 헬퍼
├── telegram_messenger.py         # 텔레그램 메신저
└── kis_common.py                 # KIS 공통 함수
```

### Database & Indicator Layer (Database Agent 전담)

```
project/database/
├── mongodb_operations.py         # MongoDB 기본 연산
├── us_market_manager.py          # 미국 시장 DB 관리
├── historical_data_manager.py    # 히스토리컬 데이터 관리
├── database_manager.py           # DB 매니저
└── database_name_calculator.py   # DB 이름 계산

project/indicator/
├── technical_indicators.py       # 기술지표 생성
├── data_frame_generator.py       # 데이터프레임 생성
└── staged_data_loader.py         # Staged 데이터 로더
```

### Strategy Layer (Strategy Agent 전담)

```
project/strategy/
├── signal_generation_service.py  # 시그널 생성 서비스
├── staged_signal_service.py      # Staged 시그널 서비스
├── position_sizing_service.py    # 포지션 사이징
├── account_analysis_service.py   # 계좌 분석
├── strategy_manager_cli.py       # 전략 관리 CLI
└── strategy_signal_config_loader.py  # 전략 설정 로더
```

### Service Layer (Service Agent 전담)

```
project/service/
├── daily_backtest_service.py     # 일간 백테스트
├── staged_pipeline_service.py    # Staged 파이프라인
├── backtest_engine.py            # 백테스트 엔진
├── performance_analyzer.py       # 성과 분석
├── trade_recorder.py             # 거래 기록
├── execution_services.py         # 실행 서비스
├── api_order_service.py          # API 주문 서비스
├── live_price_service.py         # 실시간 가격 서비스
└── position_sizing_service.py    # 포지션 사이징
```

### Report Layer (Report Agent 전담)

```
project/reporting/
├── report_agent.py               # Report Agent 메인
├── pl_analyzer.py                # P/L 분석
├── balance_analyzer.py           # 잔고 분석
└── gap_analyzer.py               # GAP 분석 (향후 구현)
```

---

## 인터페이스 수정 프로세스

### 인터페이스 변경이 필요한 경우:

1. **Sub-Agent가 Orchestrator에게 인터페이스 변경 요청**
2. **Orchestrator가 변경 사항 검토**
3. **영향 받는 모든 Agent와 협의**
4. **Orchestrator 승인 후 변경 실행**
5. **모든 관련 문서 업데이트**

### 예시:

```
Strategy Agent: "Orchestrator님, Strategy Layer 인터페이스에
                 새로운 신호 타입 추가가 필요합니다."

Orchestrator: [검토] → Service Agent에게 영향도 확인
              → 승인 → Strategy Agent 인터페이스 수정 허용
              → 문서 업데이트 지시
```

---

## 파일 조직 및 배치 규칙

### 파일 배치 규칙:
- **테스트 파일**: 모든 `test_*.py` 파일은 `Test/` 폴더에 배치
- **데모 파일**: 모든 `*demo*.py` 파일은 `Test/Demo/` 폴더에 배치
- **프로덕션 파일**: 실제 운영 파일들은 루트 또는 적절한 프로젝트 폴더에 배치
- **설정 파일**: 모든 YAML 설정 파일은 `config/` 폴더에 배치

### 폴더 구조:

```
# 최상위 실행
run_agent.py                   # RUN AGENT 메인 실행 파일
main_auto_trade.py             # 통합 메인 실행 파일

# Agent 구조
agents/
├── run_agent/                 # RUN AGENT
├── helper_agent/              # Helper Agent
├── database_agent/            # Database Agent (구조 예정)
├── strategy_agent/            # Strategy Agent
├── service_agent/             # Service Agent
└── report_agent/              # Report Agent

# Orchestrator
orchestrator/
├── main_orchestrator.py       # 메인 오케스트레이터
├── multi_agent_orchestrator.py
└── agent_scheduler.py

# Project Layers
project/
├── indicator/                 # Indicator Layer
├── strategy/                  # Strategy Layer
├── service/                   # Service Layer
├── database/                  # Database Layer
├── Helper/                    # Helper Layer
├── reporting/                 # Reporting Layer
└── router/                    # Agent Routers

Test/                          # 모든 테스트 파일
├── Demo/                      # 데모 및 예제 파일
├── test_*.py                  # 각종 테스트 파일
└── *.py                       # 기타 테스트 관련 파일

config/                        # 설정 파일들
├── agent_model.yaml           # 에이전트 모델 설정
├── api_credentials.yaml       # API 자격증명
├── broker_config.yaml         # 브로커 설정
├── risk_management.yaml       # 리스크 관리
└── *.yaml                     # 기타 설정 파일

docs/                          # 문서화
├── rules/                     # 프로젝트 규칙 ⭐ NEW
│   ├── AGENT_COLLABORATION.md
│   ├── FILE_PERMISSIONS.md
│   ├── CODE_QUALITY.md
│   ├── MONGODB_RULES.md
│   └── BACKTEST_VS_TRADING.md
├── config/                    # 설정 가이드 ⭐ NEW
│   └── CONFIG_FILES_GUIDE.md
├── interfaces/                # Layer 인터페이스 명세
├── modules/                   # Layer 모듈 설명
├── specs/                     # 알고리즘 상세
└── architecture/              # 아키텍처 문서들

storage/                       # 데이터 저장소
├── agent_interactions/        # 에이전트 상호작용 로그
└── outputs/                   # 결과 파일들
```

### 파일 생성 규칙:
- **새로운 데모 파일**: 반드시 `Test/Demo/` 폴더에 생성
- **새로운 테스트 파일**: 반드시 `Test/` 폴더에 생성
- **임시 실험 파일**: `Test/` 폴더 하위에 적절한 위치에 생성
- **프로덕션 코드**: 에이전트별 지정된 폴더에 생성

---

## 위반 시 조치

### 권한 위반 사례:
- Sub-Agent가 다른 Layer 파일 수정
- 인터페이스를 Orchestrator 승인 없이 수정
- 테스트 파일을 프로덕션 폴더에 생성

### 조치 방법:
1. **즉시 롤백**: 권한 위반 변경사항 되돌리기
2. **Orchestrator 통보**: 위반 사항 보고
3. **올바른 절차 안내**: 적절한 Agent에게 작업 재할당

---

## 참조 문서

- **Agent 협업**: `docs/rules/AGENT_COLLABORATION.md`
- **코드 품질**: `docs/rules/CODE_QUALITY.md`
- **인터페이스 규약**: `docs/interfaces/`
