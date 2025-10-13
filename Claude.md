# Claude AI Assistant 프로젝트 핵심 규칙

**프로젝트명**: AI Assistant Multi-Agent Trading System
**버전**: 2.5
**작성일**: 2025-09-15
**최종 업데이트**: 2025-10-11
**업데이트**: 모든 작업 시 필수 로드 및 적용

⚠️ **필수**: 이 문서의 모든 규칙, 특히 **섹션 15-17의 표준 인터페이스 규약**과 **섹션 12의 MongoDB 서버 규칙**을 반드시 기억하고 준수해야 합니다.
모든 코드 작성 및 수정 시 인터페이스 규약 확인은 필수입니다.

🔴 **코드 품질 규칙**:
- **신규 파일은 1000줄 이내를 목표로 작성**
- **최대 1500줄까지 허용** (1500줄 초과 시 반드시 모듈 분리)
- 파일 생성/수정 시 라인 수 자동 체크
- 기존 파일은 점진적으로 1000줄 이하로 리팩토링

🔴 **코드 작성 시 이모지 사용 금지**:
- **Python 코드, 로그 메시지, 주석에 이모지(✅, ❌, 🚀 등) 사용 절대 금지**
- **Windows cp949 인코딩 환경에서 UnicodeEncodeError 발생 방지**
- 대신 텍스트 표현 사용: [OK], [FAIL], [INFO], [WARNING], [ERROR]
- 문서 파일(.md, .txt)에서는 이모지 사용 가능

🔴 **모듈 인터페이스 관리 규칙**:
- **모든 Layer는 인터페이스 문서(MD)를 반드시 작성**
- **모듈 간 통신은 문서화된 인터페이스를 통해서만 수행**
- 각 Layer의 담당 Agent가 문서를 기억하고 관리

---

## 🔥 핵심 프로젝트 규칙 (필수 준수)

### 1. 멀티 에이전트 협업 시스템
이 프로젝트는 **여러개의 SubAgent를 연결하여 협업하는 시스템**입니다.

```
RUN AGENT (최상위 실행 관리자) - run_agent.py
    ↓
Orchestrator Agent (작업 분배 및 조정) - orchestrator/main_orchestrator.py
    ↓
├── Helper Agent (외부 API 데이터 수집) - project/router/helper_agent_router.py
├── Database Agent (MongoDB 데이터 관리) - project/router/data_agent_router.py
├── Strategy Agent (시장별 매매신호 생성) - project/router/strategy_agent_router.py
└── Service Agent (백테스트 실행, 포트폴리오 관리) - project/router/service_agent_router.py
```

### 2. RUN AGENT 역할 (2025-10-09 신규 추가)
**RUN AGENT가 최상위 실행 관리자로 전체 시스템을 관리**합니다.
- 모든 Agent의 라이프사이클 관리 (초기화, 실행, 종료)
- Orchestrator와 협업하여 작업 조율
- Agent 간 통신 및 데이터 흐름 제어
- 시스템 상태 모니터링 및 에러 처리
- 실행 모드 관리 (Backtest, Trading, Analysis)

**실행 파일**: `run_agent.py` 또는 `agents/run_agent/agent.py`

### 3. Orchestrator Agent 역할
**Orchestrator Agent가 작업 분배 및 조정을 담당**합니다.
- RUN AGENT로부터 작업 요청 수신
- 각 Agent에게 작업 할당
- Agent 간 통신 중재
- 결과 취합 및 RUN AGENT에 전달

### 4. 프롬프트 관리 체계
**오케스트레이터 에이전트가 각 서브 에이전트가 해야할 프롬프트를 작성하여 전달**합니다.
- 작업별 명확한 프롬프트 정의
- 에이전트 역할에 맞는 지시사항
- 결과 포맷 및 품질 기준 명시
- 에러 처리 및 fallback 절차

### 5. 파일 접근 권한 체계 (2025-10-09 업데이트)
**각각의 에이전트는 할당된 Layer만 수정 권한이 있으며, 인터페이스는 Orchestrator 승인 하에만 수정 가능합니다**.

#### 🔐 Layer별 수정 권한 규칙

**핵심 원칙**:
1. ✅ **각 Sub-Agent는 자신이 담당하는 Layer 파일만 수정 가능**
2. 🚫 **인터페이스(Interface)는 Sub-Agent가 직접 수정 불가** (금지)
3. 🔐 **인터페이스 수정은 Orchestrator가 승인한 경우에만 가능** (승인 필요)
4. ✅ **모든 Sub-Agent는 모든 Layer를 읽기(Read)는 가능**

#### 접근 권한 매트릭스:

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
| **Orchestrator Agent** | `orchestrator/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |
| | 모든 인터페이스 | ✅ 수정 승인 권한 | ✅ 가능 |
| **RUN AGENT** | `run_agent.py`, `agents/run_agent/` | ✅ 전체 수정 가능 | ✅ 모든 Layer |

#### Layer별 상세 구조:

**Helper Layer** (Helper Agent 전담):
```
project/Helper/
├── kis_api_helper_us.py          # KIS API 통합
├── broker_api_connector.py       # 브로커 API 커넥터
├── data_provider_api.py          # 외부 데이터 제공자
├── yfinance_helper.py            # Yahoo Finance 헬퍼
├── telegram_messenger.py         # 텔레그램 메신저
└── kis_common.py                 # KIS 공통 함수
```

**Database & Indicator Layer** (Database Agent 전담):
```
project/database/
├── mongodb_operations.py         # MongoDB 기본 연산
├── us_market_manager.py          # 미국 시장 DB 관리
├── historical_data_manager.py    # 히스토리컬 데이터 관리
├── database_manager.py           # DB 매니저
└── database_name_calculator.py   # DB 이름 계산

project/indicator/
├── technical_indicators.py       # 기술지표 생성
└── data_frame_generator.py       # 데이터프레임 생성
```

**Strategy Layer** (Strategy Agent 전담):
```
project/strategy/
├── signal_generation_service.py  # 시그널 생성 서비스
├── position_sizing_service.py    # 포지션 사이징
└── account_analysis_service.py   # 계좌 분석
```

**Service Layer** (Service Agent 전담):
```
project/service/
├── daily_backtest_service.py     # 일간 백테스트
├── backtest_engine.py            # 백테스트 엔진
├── performance_analyzer.py       # 성과 분석
├── trade_recorder.py             # 거래 기록
├── execution_services.py         # 실행 서비스
├── api_order_service.py          # API 주문 서비스
├── live_price_service.py         # 실시간 가격 서비스
└── position_sizing_service.py    # 포지션 사이징
```

#### 인터페이스 수정 프로세스:

**인터페이스 변경이 필요한 경우**:
1. Sub-Agent가 Orchestrator에게 인터페이스 변경 요청
2. Orchestrator가 변경 사항 검토
3. 영향 받는 모든 Agent와 협의
4. Orchestrator 승인 후 변경 실행
5. 모든 관련 문서 업데이트

**예시**:
```
Strategy Agent: "Orchestrator님, Strategy Layer 인터페이스에
                 새로운 신호 타입 추가가 필요합니다."

Orchestrator: [검토] → Service Agent에게 영향도 확인
              → 승인 → Strategy Agent 인터페이스 수정 허용
              → 문서 업데이트 지시
```

### 6. 파일 조직 및 배치 규칙 (신규)
**프로젝트 파일들은 명확한 규칙에 따라 조직되어야 합니다**.

#### 파일 배치 규칙:
- **테스트 파일**: 모든 `test_*.py` 파일은 `Test/` 폴더에 배치
- **데모 파일**: 모든 `*demo*.py` 파일은 `Test/Demo/` 폴더에 배치
- **프로덕션 파일**: 실제 운영 파일들은 루트 또는 적절한 프로젝트 폴더에 배치
- **설정 파일**: 모든 YAML 설정 파일은 `config/` 폴더에 배치

#### 폴더 구조 (2025-10-09 업데이트):
```
# 최상위 실행
run_agent.py                   # 🚀 RUN AGENT 메인 실행 파일
main_auto_trade.py             # 🔄 레거시 실행 파일

# Agent 구조
agents/
├── run_agent/                 # 🚀 RUN AGENT
│   ├── agent.py
│   ├── config.yaml
│   └── README.md
├── helper_agent/              # 🔧 Helper Agent
├── database_agent/            # 📊 Database Agent (구조 예정)
├── strategy_agent/            # 🧠 Strategy Agent
└── service_agent/             # ⚡ Service Agent

# Orchestrator
orchestrator/
├── main_orchestrator.py       # 🎭 메인 오케스트레이터
├── multi_agent_orchestrator.py
└── agent_scheduler.py

# Project Layers
project/
├── indicator/                 # Indicator Layer
│   ├── data_frame_generator.py
│   └── technical_indicators.py
├── strategy/                  # Strategy Layer
│   └── signal_generation_service.py
├── service/                   # Service Layer
│   └── daily_backtest_service.py
├── database/                  # Database Layer
│   ├── mongodb_operations.py
│   └── database_manager.py
├── Helper/                    # Helper Layer
│   └── kis_api_helper_us.py
└── router/                    # Agent Routers
    ├── helper_agent_router.py
    ├── data_agent_router.py
    ├── strategy_agent_router.py
    └── service_agent_router.py

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

docs/                          # 문서화 (2025-10-09 완료)
├── interfaces/                # Layer 인터페이스 명세 ✅
│   ├── STRATEGY_LAYER_INTERFACE.md
│   ├── SERVICE_LAYER_INTERFACE.md
│   ├── HELPER_LAYER_INTERFACE.md
│   ├── INDICATOR_LAYER_INTERFACE.md
│   └── DATABASE_LAYER_INTERFACE.md
├── modules/                   # Layer 모듈 설명 ✅
│   ├── STRATEGY_MODULES.md
│   ├── SERVICE_MODULES.md
│   ├── HELPER_MODULES.md
│   ├── INDICATOR_MODULES.md
│   └── DATABASE_MODULES.md
├── specs/                     # 알고리즘 상세 ✅
│   ├── SIGNAL_GENERATION_SPEC.md
│   ├── BACKTEST_SERVICE_SPEC.md
│   ├── API_INTEGRATION_SPEC.md
│   ├── TECHNICAL_INDICATORS_SPEC.md
│   └── DATABASE_SCHEMA.md
└── architecture/              # 아키텍처 문서들

storage/                       # 데이터 저장소
├── agent_interactions/        # 에이전트 상호작용 로그
└── outputs/                   # 결과 파일들
```

#### 파일 생성 규칙:
- **새로운 데모 파일**: 반드시 `Test/Demo/` 폴더에 생성
- **새로운 테스트 파일**: 반드시 `Test/` 폴더에 생성
- **임시 실험 파일**: `Test/` 폴더 하위에 적절한 위치에 생성
- **프로덕션 코드**: 에이전트별 지정된 폴더에 생성

---

## 🤖 Agent 및 문서 관리 규칙 (2025-10-09 신규)

### 5-1. Agent 파일 관리 규칙
**모든 Agent 관련 파일은 `agents/` 폴더 하위에서 관리합니다**.

#### 폴더 구조:
```
agents/
├── helper_agent/          # Helper Agent 전용
│   ├── agent.py           # Agent 메인 로직
│   ├── config.yaml        # Agent 설정
│   └── prompts/           # Agent 프롬프트
├── database_agent/        # Database Agent 전용
│   ├── agent.py
│   ├── config.yaml
│   └── prompts/
├── indicator_agent/       # Indicator Agent 전용
│   ├── agent.py
│   ├── config.yaml
│   └── prompts/
├── strategy_agent/        # Strategy Agent 전용
│   ├── agent.py
│   ├── config.yaml
│   └── prompts/
└── service_agent/         # Service Agent 전용
    ├── agent.py
    ├── config.yaml
    └── prompts/
```

#### Agent 파일 참조 규칙:
- **프로젝트에서 Agent 참조**: `from agents.helper_agent.agent import HelperAgent`
- **Agent 설정 로드**: `agents/{agent_name}/config.yaml`
- **Agent 프롬프트**: `agents/{agent_name}/prompts/{task_name}.md`

### 5-2. 문서 관리 규칙
**모든 인터페이스 및 모듈 문서는 `docs/` 폴더에서 관리합니다**.

#### 문서 구조:
```
docs/
├── interfaces/                  # 레이어 간 인터페이스
│   ├── HELPER_LAYER_INTERFACE.md
│   ├── DATABASE_LAYER_INTERFACE.md
│   ├── INDICATOR_LAYER_INTERFACE.md
│   ├── STRATEGY_LAYER_INTERFACE.md
│   └── SERVICE_LAYER_INTERFACE.md
├── modules/                     # 모듈 설명
│   ├── HELPER_MODULES.md
│   ├── DATABASE_MODULES.md
│   ├── INDICATOR_MODULES.md
│   ├── STRATEGY_MODULES.md
│   └── SERVICE_MODULES.md
├── specs/                       # 상세 스펙
│   ├── API_INTEGRATION_SPEC.md
│   ├── MONGODB_SCHEMA.md
│   ├── TECHNICAL_INDICATORS_SPEC.md
│   ├── SIGNAL_GENERATION_SPEC.md
│   └── BACKTEST_SERVICE_SPEC.md
└── architecture/                # 아키텍처 문서
    └── ...
```

#### 문서 참조 규칙:
- **프로젝트에서 문서 참조**: 코드 주석에 `# Ref: docs/interfaces/STRATEGY_LAYER_INTERFACE.md` 형식으로 명시
- **문서 업데이트**: Layer 코드 변경 시 **반드시** 해당 문서 동시 업데이트
- **문서 검증**: 월 1회 정기 검증 및 프로젝트 코드와 일치 여부 확인

### 5-3. Orchestrator 역할 및 프롬프트 관리
**Orchestrator는 `orchestrator/` 폴더에서 관리되며, 사용자 입력을 분석하여 각 Agent에게 프롬프트를 전달합니다**.

#### Orchestrator 구조:
```
orchestrator/
├── orchestrator.py            # 메인 Orchestrator 로직
├── prompt_generator.py        # 프롬프트 생성기
├── task_analyzer.py           # 사용자 입력 분석
├── agent_router.py            # Agent 라우팅
├── validator.py               # 결과 검증
├── config/
│   ├── orchestrator_config.yaml  # Orchestrator 설정
│   └── feedback_config.yaml      # Feedback iteration 설정
└── templates/                 # 프롬프트 템플릿
    ├── helper_agent_template.md
    ├── database_agent_template.md
    ├── indicator_agent_template.md
    ├── strategy_agent_template.md
    └── service_agent_template.md
```

#### Orchestrator 역할:
1. **사용자 입력 분석** (`task_analyzer.py`):
   - 사용자 요청 파싱 및 의도 파악
   - 필요한 Agent 식별
   - 작업 우선순위 결정

2. **프롬프트 생성** (`prompt_generator.py`):
   - 각 Agent에게 전달할 프롬프트 생성
   - 템플릿 기반 프롬프트 커스터마이징
   - Context 및 의존성 정보 포함

3. **Agent 라우팅** (`agent_router.py`):
   - 적절한 Agent에게 작업 분배
   - 병렬/순차 실행 결정
   - Agent 간 데이터 전달 관리

4. **결과 검증** (`validator.py`):
   - Sub-Agent 작업 결과 검증
   - 품질 기준 충족 여부 확인
   - Feedback 필요 여부 판단

### 5-4. 작업 워크플로우 (Orchestrator-driven)

#### 표준 작업 흐름:
```
[1] User Input
      ↓
[2] Orchestrator: Analyze Task (task_analyzer.py)
      ↓
[3] Orchestrator: Generate Prompts (prompt_generator.py)
      ↓
[4] Sub-Agents: Execute Work (parallel/sequential)
      ↓
[5] Orchestrator: Validate Results (validator.py)
      ↓
[6a] Pass → Complete
[6b] Fail → Re-generate Prompts + Feedback → [4]
```

#### Feedback Iteration 설정:
`orchestrator/config/feedback_config.yaml`:
```yaml
feedback_iteration:
  max_iterations: 3          # 최대 재시도 횟수
  auto_feedback: true        # 자동 피드백 활성화
  validation_strict: false   # 엄격한 검증 모드

validation_criteria:
  code_quality:
    max_line_length: 1500    # 파일 최대 줄 수
    min_test_coverage: 0.8   # 최소 테스트 커버리지

  documentation:
    require_interface: true  # 인터페이스 문서 필수
    require_examples: true   # 예제 코드 필수
```

#### Feedback 예시:
```
Iteration 1:
- Orchestrator → Strategy Agent: "Generate trading signals for AAPL"
- Strategy Agent → Output: [Signal with incomplete fundamental check]
- Orchestrator Validation: ❌ Fundamental signal missing

Iteration 2:
- Orchestrator → Strategy Agent: "Re-generate with fundamental analysis"
- Strategy Agent → Output: [Signal with all components]
- Orchestrator Validation: ✅ Pass
```

### 5-5. 작업 계획 관리 (Plan-driven Workflow)

**모든 작업은 `plan/` 폴더에 계획 문서를 생성하여 관리합니다**.

#### Plan 폴더 구조:
```
plan/
├── plan.md                    # 현재 작업 계획 (필수)
├── completed/                 # 완료된 계획 아카이브
│   ├── plan_20251009_001.md
│   ├── plan_20251009_002.md
│   └── ...
└── templates/
    └── plan_template.md       # 계획 문서 템플릿
```

#### Plan.md 구조:
```markdown
# Work Plan: [Task Name]

**Created**: 2025-10-09 14:30
**Status**: In Progress / Completed
**Assigned Agents**: Helper, Database, Indicator, Strategy
**Estimated Time**: 2 hours

---

## 1. Objective
[작업 목표 및 배경]

## 2. Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## 3. Sub-Tasks
### Task 1: [Description]
- **Agent**: Helper Agent
- **Status**: Pending / In Progress / Completed
- **Output**: [Expected output]
- **Validation**: [Validation criteria]

### Task 2: [Description]
- **Agent**: Database Agent
- **Status**: Pending / In Progress / Completed
- **Output**: [Expected output]
- **Validation**: [Validation criteria]

## 4. Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2

## 5. Success Criteria
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Code review completed

## 6. Notes
[추가 참고사항]

---

**Last Updated**: 2025-10-09 15:45
**Completion Date**: 2025-10-09 16:00
```

#### Plan 관리 규칙:
1. **작업 시작 시**:
   - Orchestrator가 자동으로 `plan/plan.md` 생성
   - 사용자 요청 분석 → Sub-task 분해 → Agent 할당

2. **작업 진행 중**:
   - 각 Sub-task 상태 실시간 업데이트
   - Agent 작업 결과를 plan.md에 기록

3. **작업 완료 시**:
   - plan.md를 `plan/completed/plan_YYYYMMDD_NNN.md`로 이동
   - 자동으로 Git commit & push

### 5-6. Git 자동 커밋 규칙

**작업 완료 시 자동으로 Git에 commit 및 push합니다**.

#### 자동 커밋 조건:
1. `plan/plan.md`의 모든 Sub-task가 Completed 상태
2. Orchestrator validation 통과
3. 모든 문서 업데이트 완료

#### 커밋 메시지 형식:
```
feat: [Task Name]

- Sub-task 1: Description
- Sub-task 2: Description
- Sub-task 3: Description

Agents: Helper, Database, Indicator, Strategy
Plan: plan/completed/plan_20251009_001.md

🤖 Generated with Claude Code
Orchestrator: Data Orchestrator Agent
```

#### 자동 커밋 워크플로우:
```python
# orchestrator/git_manager.py

def auto_commit_and_push():
    """
    작업 완료 시 자동 Git commit & push
    """
    # 1. plan.md 완료 여부 확인
    if not is_plan_completed():
        return False

    # 2. 변경 파일 스테이징
    changed_files = get_changed_files()
    git_add(changed_files)

    # 3. 커밋 메시지 생성
    commit_msg = generate_commit_message(plan_file='plan/plan.md')

    # 4. 커밋 실행
    git_commit(commit_msg)

    # 5. plan.md 아카이브
    archive_plan()

    # 6. Push to remote
    git_push()

    return True
```

#### 자동 커밋 설정:
`orchestrator/config/orchestrator_config.yaml`:
```yaml
git_auto_commit:
  enabled: true                # 자동 커밋 활성화
  require_validation: true     # 검증 통과 필수
  push_to_remote: true         # 자동 푸시 활성화
  branch: main                 # 대상 브랜치

commit_message:
  prefix: "feat"               # 기본 prefix (feat/fix/docs/refactor)
  include_plan: true           # plan 파일 경로 포함
  include_agents: true         # 참여 Agent 목록 포함
```

---

## 📋 설정 파일 관리 규칙

### 6. 인터페이스 정의
**인터페이스는 `agent_interfaces.yaml` 파일에 정의되어 있습니다**.
- 에이전트간 함수 호출 규약
- 데이터 전달 포맷 정의
- 에러 처리 프로토콜
- 버전 호환성 관리

### 7. API 자격증명 관리
**계좌 정보와 API 키 정보들은 `api_credentials.yaml` 파일에 정의합니다**.
```yaml
# api_credentials.yaml 구조
brokers:
  kis:
    real_account: "encrypted_credentials"
    virtual_account: "encrypted_credentials"
  ls_securities:
    credentials: "encrypted_data"

external_apis:
  alpha_vantage: "api_key"
  telegram: "bot_token"
```

### 8. 브로커 설정 관리
**실제 마켓 오픈시간과 모의 계좌 실제 구분 등의 정보는 `broker_config.yaml` 파일에 정의합니다**.
- 마켓 오픈/클로즈 시간
- 거래 가능 상품 정의
- 주문 타입 및 제한사항
- 계좌 타입별 설정

### 9. 파일 소유권 관리
**각각의 파일에 대한 접근 권한 정보는 `file_ownership.yaml`에 정의합니다**.
- READ/WRITE/EXECUTE 권한 매트릭스
- 에이전트별 파일 접근 범위
- 크로스 에이전트 접근 규칙
- 보안 및 격리 정책

### 10. LLM 모델 할당 (신규)
**각각의 에이전트의 사용 LLM 모델은 `agent_model.yaml`에 기록합니다**.
```yaml
# agent_model.yaml 구조 예시
agents:
  orchestrator:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "claude-3-sonnet-20240229"
  data_agent:
    primary_model: "claude-3-sonnet-20240229"
    fallback_model: "gemini-pro"
  strategy_agent:
    primary_model: "claude-3-opus-20240229"
    fallback_model: "gemini-pro"
```

### 11. 리스크 관리 분리 (신규)
**계좌의 리스크 매니지먼트 정보는 `risk_management.yaml`에 정의합니다**.
**기존 `broker_config.yaml`에 있던 내용을 분리합니다**.

분리 대상:
- `max_position_size`, `max_daily_loss`
- `max_orders_per_minute`, `max_concentration`
- `min_order_amount`, `max_order_amount`
- `default_stop_loss`, `max_stop_loss`

### 12. MongoDB 서버 규칙 (2025-10-11 추가)
**백테스트 및 오토트레이딩은 MONGODB_LOCAL 서버를 사용합니다**.

#### MongoDB 서버 구분:
- **MONGODB_LOCAL**: localhost (127.0.0.1 또는 localhost:27017)
  - **용도**: 백테스트 실행, 오토트레이딩 시스템, 개발 및 테스트
  - **데이터베이스**: NasDataBase_D, NysDataBase_D, HkDataBase_D 등
  - **특징**: 빠른 응답 속도, 로컬 데이터 접근

- **MONGODB_NAS**: 192.168.55.14 (NAS 서버)
  - **용도**: 데이터 백업, 아카이브
  - **특징**: 네트워크 의존, 백업 전용

- **MONGODB_MAIN**: 192.168.55.85 (메인 서버)
  - **용도**: 프로덕션 데이터베이스 (미래 확장용)

#### 코드 설정:
모든 Database Layer 및 Indicator Layer에서는 다음과 같이 설정:
```python
# project/database/mongodb_operations.py
db = MongoDBOperations(db_address="MONGODB_LOCAL")

# project/indicator/data_frame_generator.py
db = MongoDBOperations(db_address="MONGODB_LOCAL")
```

#### myStockInfo.yaml 설정:
```yaml
MONGODB_LOCAL: localhost
MONGODB_NAS: 192.168.55.14
MONGODB_MAIN: 192.168.55.85
MONGODB_PORT: 27017
MONGODB_ID: admin
MONGODB_PW: wlsaud07
```

---

## 🤖 LLM 모델 관리 규칙

### 13. 구독 모델 체계 (신규)
**각각의 에이전트의 모델은 구독 모델을 사용하며, Gemini 모델을 Claude Code에서 사용하기 위해 라우터를 사용합니다**.

#### 모델 선택 기준:
- **Claude-3-Opus**: 복잡한 전략 개발, 중요한 의사결정
- **Claude-3-Sonnet**: 일반적인 데이터 처리, 서비스 운영
- **Gemini-Pro**: 대용량 데이터 분석, 빠른 응답 필요시

### 14. LLM 라우터 구현 (신규)
**LLM 모델 라우터는 `https://github.com/musistudio/claude-code-router`를 활용하여 구현합니다**.

#### 라우터 기능:
- 에이전트별 모델 자동 할당
- 모델 간 load balancing
- API 사용량 최적화
- Fallback 모델 자동 전환

---

## 📊 레이어간 표준 인터페이스 (2025-10-06 추가)

### 15. Indicator Layer → Strategy Layer 인터페이스
**기술지표 레이어에서 전략 레이어로 전달되는 표준 데이터 형식입니다**.

#### 데이터 구조:
모든 데이터는 Dictionary 형태로 전달되며, 티커를 key로 사용합니다.

```python
# 일간 데이터 (df_D)
{
    "TICKER": {
        "columns": ["Dvolume", "Dopen", "Dhigh", "Dlow", "Dclose", "ADR", "SMA20", "SMA50", "SMA200", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # ISO 8601 datetime
        "data": [[value1, value2, ...], ...]
    }
}

# 주간 데이터 (df_W)
{
    "TICKER": {
        "columns": ["Wopen", "Whigh", "Wlow", "Wclose", "52_H", "52_L", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # 주간 금요일
        "data": [[value1, value2, ...], ...]
    }
}

# 상대강도 데이터 (df_RS)
{
    "TICKER": {
        "columns": ["RS_4W", "RS_12W", "Sector", "Industry", "Sector_RS_4W", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    }
}

# 실적 데이터 (df_E)
{
    "TICKER": {
        "columns": ["EarningDate", "eps", "eps_yoy", "revenue", "rev_yoy", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],  # 분기별
        "data": [[value1, value2, ...], ...]
    }
}

# 펀더멘털 데이터 (df_F)
{
    "TICKER": {
        "columns": ["EPS", "EPS_YOY", "REV_YOY", "PBR", "PSR", "ROE", ...],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    }
}
```

### 16. Strategy Layer 출력 인터페이스
**전략 레이어에서 생성되는 매매 후보 종목의 표준 형식입니다**.

#### Trading Candidates (df_dump):
```python
{
    "TICKER": {
        "columns": [
            "open", "high", "low", "close", "ADR",
            "LossCutPrice",    # 손절가
            "TargetPrice",     # 목표가
            "BuySig",          # 매수 신호 (1/0)
            "SellSig",         # 매도 신호 (1/0)
            "signal",          # 신호 강도
            "Type",            # 신호 타입
            "RS_4W",           # 4주 상대강도
            "Rev_Yoy_Growth",  # 매출 성장률
            "Eps_Yoy_Growth",  # EPS 성장률
            "Sector",          # 섹터
            "Industry"         # 산업
        ],
        "index": ["YYYY-MM-DDTHH:MM:SS.mmm", ...],
        "data": [[value1, value2, ...], ...]
    }
}
```

#### Universe 출력:
```python
{
    "Universe": ["TICKER1", "TICKER2", "TICKER3", ...],
    "count": 58  # 선정된 종목 수
}
```

### 17. 인터페이스 준수 사항
- **데이터 타입**: Datetime은 ISO 8601 형식, 가격은 float (2-4자리), 신호는 integer (0/1)
- **Missing Data**: 숫자는 null/NaN, 문자열은 빈 문자열 "" 사용
- **성능 최적화**: Dictionary 구조로 O(1) 티커 검색 보장
- **에러 처리**: 필수 컬럼 누락 시 명확한 에러 메시지 제공

자세한 인터페이스 명세는 `docs/INTERFACE_SPECIFICATION.md` 파일을 참조하세요.

### 17.1 데이터 레이어 간 컬럼 표준 (2025-10-06 추가)
**Market DB → Indicator Layer → Strategy Layer의 컬럼 스펙은 JSON 파일로 표준화됩니다**.

#### 표준 컬럼 정의 파일 위치:
- **Market DB → Indicator Layer**: `refer/debug_json/df_*_columns_before_TRD.json`
- **Indicator Layer → Strategy Layer**: `refer/debug_json/df_*_columns_after_TRD.json`

#### 데이터 타입별 JSON 파일:
1. **df_D** (Daily Data):
   - `df_D_columns_before_TRD.json`: Market DB 출력 컬럼 (volume, ad_open, ad_high, ad_low, ad_close 등)
   - `df_D_columns_after_TRD.json`: Indicator Layer 출력 컬럼 (Dopen, Dhigh, Dlow, Dclose + SMA, Highest, ADR 등)

2. **df_W** (Weekly Data):
   - `df_W_columns_before_TRD.json`: Market DB 출력 컬럼 (open, high, low, close, volume 등)
   - `df_W_columns_after_TRD.json`: Indicator Layer 출력 컬럼 (Wopen, Whigh + 52_H, 52_L, 1Year_H 등)

3. **df_RS** (Relative Strength):
   - `df_RS_columns_before_TRD.json`: Market DB 출력 컬럼
   - `df_RS_columns_after_TRD.json`: Indicator Layer 출력 컬럼 (+ RS_SMA5, RS_SMA20)

4. **df_E** (Earnings):
   - `df_E_columns_before_TRD.json`: Market DB 출력 컬럼
   - `df_E_columns_after_TRD.json`: Indicator Layer 출력 컬럼 (변화 없음)

5. **df_F** (Fundamental):
   - `df_F_columns_before_TRD.json`: Market DB 출력 컬럼 (raw fundamental data)
   - `df_F_columns_after_TRD.json`: Indicator Layer 출력 컬럼 (+ PBR, PSR, ROE, ROA, EBITDA 등)

#### Indicator Layer의 역할:
- Market DB에서 가져온 raw 데이터 컬럼명 변환 (예: `ad_open` → `Dopen`)
- 기술지표 및 계산 컬럼 추가 (예: SMA20, SMA50, SMA200, ADR 등)
- Helper Layer API 호출하여 추가 데이터 수집 (fundamental ratios 등)

#### 프로젝트 작업 시 필수 준수 사항:
1. **컬럼 추가/삭제** 시 반드시 해당 JSON 파일 업데이트
2. **코드 작성** 시 JSON 파일 스키마 기준으로 validation 수행
3. **테스트** 시 실제 데이터 컬럼이 JSON 스키마와 일치하는지 확인

상세한 컬럼 명세는 `docs/DATA_LAYER_INTERFACES.md` 파일을 참조하세요.

### 18. 문서 체계 및 Layer별 책임 (2025-10-09 업데이트)
**프로젝트 문서는 `docs/` 폴더에 체계적으로 관리되며, 각 Layer는 자신의 인터페이스와 모듈 설명을 문서화합니다**.

#### 주요 문서:
- **CLAUDE.md**: 프로젝트 핵심 규칙 (루트 폴더)
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 데이터 인터페이스 명세
- **docs/DATA_LAYER_INTERFACES.md**: 데이터 레이어 간 컬럼 표준
- **docs/AGENT_INTERFACES.md**: 에이전트 간 통신 프로토콜
- **docs/HELPER_FUNCTIONS_MANUAL.md**: Helper 함수 매뉴얼

#### Layer별 필수 문서 (2025-10-09 신규):
각 Layer는 다음 문서들을 **반드시 작성하고 유지**해야 합니다:

**1. Indicator Layer (Data Agent 관리)**
- 위치: `project/indicator/`
- 필수 문서:
  - `INDICATOR_LAYER_INTERFACE.md`: 입출력 인터페이스 정의
  - `INDICATOR_MODULES.md`: 모듈 설명 및 사용법
  - `TECHNICAL_INDICATORS_SPEC.md`: 기술지표 상세 스펙
- 책임 Agent: **Data Agent**

**2. Strategy Layer (Strategy Agent 관리)**
- 위치: `project/strategy/`
- 필수 문서:
  - `STRATEGY_LAYER_INTERFACE.md`: 입출력 인터페이스 정의
  - `STRATEGY_MODULES.md`: 전략 모듈 설명
  - `SIGNAL_GENERATION_SPEC.md`: 시그널 생성 로직 명세
- 책임 Agent: **Strategy Agent**

**3. Service Layer (Service Agent 관리)**
- 위치: `project/service/`
- 필수 문서:
  - `SERVICE_LAYER_INTERFACE.md`: 입출력 인터페이스 정의
  - `SERVICE_MODULES.md`: 서비스 모듈 설명
  - `BACKTEST_SERVICE_SPEC.md`: 백테스트 서비스 상세 스펙
  - `ORDER_EXECUTION_SPEC.md`: 주문 실행 로직 명세
- 책임 Agent: **Service Agent**

**4. Helper Layer (Helper Agent 관리)**
- 위치: `project/Helper/`
- 필수 문서:
  - `HELPER_LAYER_INTERFACE.md`: 입출력 인터페이스 정의
  - `HELPER_MODULES.md`: Helper 모듈 설명
  - `API_INTEGRATION_SPEC.md`: 외부 API 연동 명세
- 책임 Agent: **Helper Agent**

**5. Database Layer (Data Agent 관리)**
- 위치: `project/database/`
- 필수 문서:
  - `DATABASE_LAYER_INTERFACE.md`: MongoDB 접근 인터페이스
  - `DATABASE_MODULES.md`: 데이터베이스 모듈 설명
  - `MONGODB_SCHEMA.md`: MongoDB 스키마 정의
- 책임 Agent: **Data Agent**

#### 아키텍처 문서 (docs/architecture/):
- **ARCHITECTURE_OVERVIEW.md**: 시스템 아키텍처 개요
- **DATABASE_ARCHITECTURE.md**: MongoDB 데이터베이스 구조
- **MULTI_AGENT_SYSTEM_ARCHITECTURE.md**: 멀티 에이전트 시스템
- **DATA_AGENT_ARCHITECTURE.md**: Data Agent 아키텍처
- **STRATEGY_AGENT_ARCHITECTURE.md**: Strategy Agent 아키텍처
- **HELPER_AGENT_ARCHITECTURE.md**: Helper Agent 아키텍처
- **SERVICE_LAYER_BACKTEST_ARCHITECTURE.md**: 백테스트 아키텍처

#### 문서 간 연계:
```
CLAUDE.md (프로젝트 규칙)
    ↓
docs/
  ├── README.md (문서 인덱스)
  ├── INTERFACE_SPECIFICATION.md  ←→  AGENT_INTERFACES.md
  │   (데이터 구조)                    (통신 프로토콜)
  ├── HELPER_FUNCTIONS_MANUAL.md
  └── architecture/                    (아키텍처 문서)
      ├── README.md
      ├── ARCHITECTURE_OVERVIEW.md
      ├── DATABASE_ARCHITECTURE.md
      └── [에이전트별 아키텍처 문서들]

project/
  ├── indicator/
  │   ├── INDICATOR_LAYER_INTERFACE.md  (필수)
  │   ├── INDICATOR_MODULES.md          (필수)
  │   └── TECHNICAL_INDICATORS_SPEC.md  (필수)
  ├── strategy/
  │   ├── STRATEGY_LAYER_INTERFACE.md   (필수)
  │   ├── STRATEGY_MODULES.md           (필수)
  │   └── SIGNAL_GENERATION_SPEC.md     (필수)
  ├── service/
  │   ├── SERVICE_LAYER_INTERFACE.md    (필수)
  │   ├── SERVICE_MODULES.md            (필수)
  │   ├── BACKTEST_SERVICE_SPEC.md      (필수)
  │   └── ORDER_EXECUTION_SPEC.md       (필수)
  ├── Helper/
  │   ├── HELPER_LAYER_INTERFACE.md     (필수)
  │   ├── HELPER_MODULES.md             (필수)
  │   └── API_INTEGRATION_SPEC.md       (필수)
  └── database/
      ├── DATABASE_LAYER_INTERFACE.md   (필수)
      ├── DATABASE_MODULES.md           (필수)
      └── MONGODB_SCHEMA.md             (필수)
```

### 18. 문서 관리 규칙 (2025-10-09 신규)

#### Agent의 문서 관리 책임:
1. **Layer 담당 Agent는 해당 Layer의 모든 문서를 관리**
   - 코드 변경 시 문서를 **즉시** 업데이트
   - 인터페이스 변경 시 **반드시** 문서에 반영
   - 새 모듈 추가 시 MODULES.md에 설명 추가

2. **문서 작성 규칙**:
   - **INTERFACE.md**: 입출력 파라미터, 반환 값, 예외 처리
   - **MODULES.md**: 각 모듈의 목적, 사용법, 예제 코드
   - **SPEC.md**: 상세 로직, 알고리즘, 성능 특성

3. **문서 검증**:
   - 매 작업 시작 시 해당 Layer 문서 확인
   - 인터페이스 변경 시 의존 Layer에 통보
   - 월 1회 문서 정합성 검증

4. **문서 우선순위**:
   - **High**: *_INTERFACE.md (반드시 최신 상태 유지)
   - **Medium**: *_MODULES.md (주요 변경 시 업데이트)
   - **Low**: *_SPEC.md (필요시 업데이트)

#### 인터페이스 문서 필수 항목:
```markdown
# [Layer Name] Interface Specification

## 1. Overview
- Layer 목적 및 역할
- 주요 기능 요약

## 2. Input Interface
- 입력 파라미터 타입 및 설명
- 필수/선택 파라미터
- 데이터 포맷 (DataFrame, Dict 등)

## 3. Output Interface
- 반환 값 타입 및 설명
- 데이터 구조 (컬럼 명세 등)
- 성공/실패 응답 포맷

## 4. Error Handling
- 예외 타입 및 발생 조건
- 에러 코드 정의
- 복구 방법

## 5. Examples
- 기본 사용 예제
- 엣지 케이스 처리 예제

## 6. Dependencies
- 의존하는 다른 Layer
- 필수 라이브러리

## 7. Version History
- 변경 이력 및 버전 정보
```

---

## 🔒 보안 및 운영 규칙

### 데이터 보안
- API 키는 암호화하여 저장
- 실제 계좌 정보 접근 시 추가 인증
- 로그에 민감 정보 포함 금지
- 에이전트간 권한 격리 유지

### 에러 처리
- 각 에이전트별 독립적 에러 처리
- 시스템 전체 장애 방지를 위한 격리
- 자동 복구 메커니즘 구현
- 상세한 에러 로깅 및 알림

### 모니터링
- 에이전트별 성능 지표 추적
- API 사용량 및 비용 모니터링
- 시스템 리소스 사용량 추적
- 실시간 알림 시스템 운영

---

## ⚡ 필수 작업 흐름

### 모든 작업 시 확인사항:
1. [ ] 해당 에이전트의 파일 접근 권한 확인
2. [ ] 필요한 설정 파일들 로드 확인
3. [ ] 인터페이스 규약 준수 확인
4. [ ] 에러 처리 로직 구현
5. [ ] 로깅 및 모니터링 적용

### 설정 변경 시:
1. [ ] 관련 YAML 파일 업데이트
2. [ ] 영향 받는 에이전트들에게 변경사항 전파
3. [ ] 테스트 환경에서 검증
4. [ ] 프로덕션 배포 및 모니터링

### 새로운 기능 추가 시:
1. [ ] 에이전트 역할 분담 검토
2. [ ] 인터페이스 정의 업데이트
3. [ ] 파일 소유권 할당
4. [ ] 테스트 케이스 작성

---

## 🎯 성공 지표

### 시스템 안정성
- 에이전트간 협업 성공률 > 99%
- API 호출 실패율 < 1%
- 시스템 가용시간 > 99.9%

### 성능 최적화
- 응답 시간 < 5초 (일반 작업)
- 메모리 사용률 < 80%
- CPU 사용률 < 70%

### 보안 준수
- 권한 위반 사건 = 0
- 데이터 유출 사건 = 0
- 보안 감사 통과율 = 100%

---

## 📞 지원 및 문의

### 문제 발생 시:
1. **에이전트 협업 이슈**: `agent_interfaces.yaml` 확인
2. **권한 문제**: `file_ownership.yaml` 검토
3. **설정 오류**: 해당 YAML 파일 검증
4. **LLM 모델 이슈**: `agent_model.yaml` 및 라우터 상태 확인

### 문서 업데이트:
- 이 규칙은 프로젝트 진행에 따라 지속 업데이트됩니다
- 모든 변경사항은 버전 관리되며 이력을 추적합니다
- 새로운 규칙 추가 시 모든 에이전트에게 즉시 반영됩니다

---

## ✅ 체크리스트

### 프로젝트 시작 전:
- [ ] 모든 YAML 설정 파일 확인
- [ ] 에이전트별 권한 매트릭스 검토
- [ ] LLM 라우터 연결 테스트
- [ ] API 자격증명 검증

### 작업 진행 중:
- [ ] 이 규칙 문서 참조
- [ ] 에이전트간 인터페이스 준수
- [ ] 파일 접근 권한 확인
- [ ] 에러 처리 구현

### 작업 완료 후:
- [ ] 테스트 케이스 실행
- [ ] 문서 업데이트
- [ ] 성능 지표 확인
- [ ] 보안 검토 완료

---

## 🎯 최신 업데이트 (2025-09-22)

### 완성된 Multi-Agent Trading System

#### ✅ 구현 완료 사항:
1. **완전한 5-Agent 시스템 구현**
   - Orchestrator Agent (orchestrator_agent.py): 시스템 총괄 관리
   - Data Agent (data_agent.py): MongoDB 데이터 로딩 및 기술지표 계산
   - Strategy Agent (strategy_agent.py): 시장별 매매신호 생성
   - Service Agent (service_agent.py): 백테스트 실행 및 포트폴리오 관리
   - Helper Agent (helper_agent.py): 시스템 설정 및 MongoDB 연결 관리

2. **통합 실행 파일**
   - multi_agent_trading_system.py: 메인 실행 인터페이스
   - 자동 모드 및 대화형 모드 지원
   - 완전한 에이전트 협업 구현

3. **데이터베이스 통합**
   - NasDataBase_D (8,878 NASDAQ 종목) 완전 연동
   - NysDataBase_D (6,235 NYSE 종목) 완전 연동
   - MongoDB 실시간 데이터 로딩 최적화

4. **성능 최적화**
   - 전체 실행 시간: 1.93초
   - 15,113 종목 데이터 처리: 1.38초
   - 194개 매매신호 생성: 0.30초
   - 백테스트 실행: 0.05초

5. **포괄적 문서화**
   - USER_MANUAL.md (50+ 페이지 완전 가이드)
   - QUICK_START_GUIDE.md (5분 빠른 시작)
   - ARCHITECTURE_GUIDE.md (시스템 아키텍처)
   - README.md (프로젝트 개요)

#### 🚀 실행 방법:
```bash
# 자동 모드 (추천)
cd Project && python multi_agent_trading_system.py --auto

# 대화형 모드
cd Project && python multi_agent_trading_system.py

# 개별 에이전트 테스트
python data_agent.py
python strategy_agent.py
python service_agent.py
python helper_agent.py
```

#### 📊 실제 성과 (2023년 데이터):
- 총 수익률: 0.36%
- 샤프 비율: 0.603
- 최대 드로우다운: 0.89%
- 승률: 46.43%
- 총 거래 수: 61회

### 시스템 아키텍처 완성도:
```
✅ Multi-Agent 협업 패턴 구현 완료
✅ 시장별 차별화 전략 (NASDAQ vs NYSE) 구현 완료
✅ 실시간 리스크 관리 시스템 구현 완료
✅ MongoDB Big Data 처리 최적화 완료
✅ 포괄적 에러 처리 및 복구 메커니즘 완료
✅ 사용자 친화적 인터페이스 구현 완료
✅ Production-Ready 상태 달성
```

---

**🚨 중요: 이 규칙은 모든 Claude 작업 세션에서 반드시 로드하고 적용해야 합니다.**

*규칙 버전: 2.4 | 최종 업데이트: 2025-10-09*

---

## 📐 새로운 아키텍처 (2025-10-09 업데이트)

### 🔄 데이터 파이프라인 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Orchestrator Agent                       │
│                   (데이터 파이프라인 조정)                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Helper Agent │ │Database Agent│ │Indicator Agt │
│ (외부 API)   │ │ (MongoDB)    │ │ (기술지표)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ↓
                ┌──────────────┐
                │Strategy Agent│
                │ (매매 신호)  │
                └──────┬───────┘
                       │
                       ↓
                ┌──────────────┐
                │Service Agent │
                │(백테스트/주문)│
                └──────────────┘
```

### 🎯 Agent별 책임 및 역할

#### 1. Helper Agent
**위치**: `project/Helper/`
**책임**: 외부 API 데이터 수집
- KIS API 연동 (한국투자증권)
- LS Securities API 연동 (LS증권)
- Alpha Vantage API 연동
- 실시간 시세 데이터 수집
- 펀더멘털 데이터 수집

**주요 파일**:
- `kis_api_helper_us.py`: 미국 시장 API
- `kis_api_helper_kr.py`: 한국 시장 API
- `ls_api_helper.py`: LS 증권 API

**출력**: Raw 시장 데이터 (JSON/Dict 형식)

---

#### 2. Database Agent
**위치**: `project/database/`
**책임**: MongoDB 데이터 CRUD 작업
- 시장 데이터 저장 (Daily, Weekly, RS, Fundamental, Earnings)
- 데이터 조회 및 필터링
- 스키마 검증
- 데이터 품질 관리

**주요 파일**:
- `mongodb_operations.py`: CRUD 연산
- `schema_validator.py`: 데이터 검증

**컬렉션**:
- `NasDataBase_D`, `NysDataBase_D`: 일간 데이터
- `NasDataBase_W`, `NysDataBase_W`: 주간 데이터
- `NasDataBase_RS`, `NysDataBase_RS`: 상대강도 데이터
- `NasDataBase_F`, `NysDataBase_F`: 펀더멘털 데이터
- `NasDataBase_E`, `NysDataBase_E`: 어닝스 데이터

**출력**: DataFrame (pandas) - Raw 시장 데이터

---

#### 3. Indicator Agent
**위치**: `project/indicator/`
**책임**: 기술지표 계산 및 데이터 전처리
- SMA (20, 50, 200일)
- ADR (Average Daily Range)
- Highest (1M, 3M, 6M, 1Y, 2Y)
- RSI, MACD 등 기술지표
- 데이터 정규화

**주요 파일**:
- `data_frame_generator.py`: 데이터 로드 및 지표 계산
- `technical_indicators.py`: 기술지표 모듈

**문서**:
- ✅ `INDICATOR_LAYER_INTERFACE.md` (완료)
- ⏳ `INDICATOR_MODULES.md` (TODO)
- ⏳ `TECHNICAL_INDICATORS_SPEC.md` (TODO)

**출력**: DataFrame with indicators (df_D, df_W, df_RS, df_F, df_E)

---

#### 4. Strategy Agent
**위치**: `project/strategy/`
**책임**: 매매 신호 생성 및 포지션 크기 계산
- 주봉 신호 생성
- RS 신호 생성
- 펀더멘털 신호 생성
- 어닝스 신호 생성
- 최종 BUY/SELL/HOLD 결정
- 포지션 크기 계산
- 계좌 분석

**주요 파일**:
- `signal_generation_service.py`: 신호 생성
- `position_sizing_service.py`: 포지션 크기
- `account_analysis_service.py`: 계좌 분석

**문서**:
- ✅ `STRATEGY_LAYER_INTERFACE.md` (완료)
- ✅ `STRATEGY_MODULES.md` (완료)
- ✅ `SIGNAL_GENERATION_SPEC.md` (완료)

**출력**:
```python
{
    'final_signal': SignalType.BUY,
    'signal_strength': 0.85,
    'target_price': 180.0,
    'losscut_price': 174.6,
    'signal_type': 'Breakout_1Y',
    'confidence': 0.7
}
```

---

#### 5. Service Agent
**위치**: `project/service/`
**책임**: 백테스트 실행 및 주문 관리
- 백테스트 시뮬레이션
- 포트폴리오 관리
- 주문 생성 및 실행
- 성과 분석 및 리포팅

**주요 파일**:
- `daily_backtest_service.py`: 백테스트 실행
- `order_manager.py`: 주문 관리
- `portfolio_manager.py`: 포트폴리오 관리

**문서**:
- ⏳ `SERVICE_LAYER_INTERFACE.md` (TODO)
- ⏳ `SERVICE_MODULES.md` (TODO)
- ⏳ `BACKTEST_SERVICE_SPEC.md` (TODO)

**출력**: 백테스트 결과, 거래 내역, 성과 지표

---

#### 6. Data Orchestrator Agent
**위치**: `project/data_orchestrator.py`
**책임**: 데이터 파이프라인 전체 조정
- Helper → Database → Indicator → Strategy 순서 제어
- 에이전트 간 데이터 전달
- 에러 처리 및 복구
- 병렬 처리 최적화

**데이터 흐름**:
```
1. Helper Agent가 외부 API에서 데이터 수집
2. Database Agent가 MongoDB에 저장
3. Indicator Agent가 기술지표 계산
4. Strategy Agent가 매매 신호 생성
5. Service Agent가 백테스트/주문 실행
```

---

### 🔗 레이어 간 인터페이스

#### Helper → Database
```python
# Helper Agent 출력
{
    "ticker": "AAPL",
    "date": "2025-10-09",
    "open": 150.0,
    "high": 152.0,
    "low": 149.0,
    "close": 151.5,
    "volume": 1000000
}

# Database Agent 입력
db.save_market_data(data)
```

#### Database → Indicator
```python
# Database Agent 출력
df = pd.DataFrame({
    "ad_open": [150.0],
    "ad_high": [152.0],
    "ad_low": [149.0],
    "ad_close": [151.5],
    "volume": [1000000]
})

# Indicator Agent 입력
df_with_indicators = indicator_agent.calculate_indicators(df)
```

#### Indicator → Strategy
```python
# Indicator Agent 출력
{
    "AAPL": pd.DataFrame({
        "Dopen": [150.0],
        "Dhigh": [152.0],
        "Dlow": [149.0],
        "Dclose": [151.5],
        "SMA20": [150.0],
        "SMA50": [148.5],
        "SMA200": [145.0]
    })
}

# Strategy Agent 입력
signal = strategy_agent.generate_comprehensive_signals(
    df_daily=df_D["AAPL"],
    df_weekly=df_W["AAPL"],
    df_rs=df_RS["AAPL"]
)
```

#### Strategy → Service
```python
# Strategy Agent 출력
{
    "final_signal": SignalType.BUY,
    "signal_strength": 0.85,
    "target_price": 180.0,
    "losscut_price": 174.6
}

# Service Agent 입력
backtest_service.execute_signal(
    ticker="AAPL",
    signal=signal_result
)
```

---

### 📊 문서화 상태 (2025-10-09)

#### ✅ 완료된 문서:
1. **Indicator Layer**:
   - ✅ INDICATOR_LAYER_INTERFACE.md

2. **Strategy Layer**:
   - ✅ STRATEGY_LAYER_INTERFACE.md
   - ✅ STRATEGY_MODULES.md
   - ✅ SIGNAL_GENERATION_SPEC.md

#### ⏳ 진행 중:
3. **Service Layer**:
   - ⏳ SERVICE_LAYER_INTERFACE.md
   - ⏳ SERVICE_MODULES.md
   - ⏳ BACKTEST_SERVICE_SPEC.md

#### 📝 TODO:
4. **Helper Layer**:
   - ⏳ HELPER_LAYER_INTERFACE.md
   - ⏳ HELPER_MODULES.md
   - ⏳ API_INTEGRATION_SPEC.md

5. **Database Layer**:
   - ⏳ DATABASE_LAYER_INTERFACE.md
   - ⏳ DATABASE_MODULES.md
   - ⏳ MONGODB_SCHEMA.md

6. **Indicator Layer (나머지)**:
   - ⏳ INDICATOR_MODULES.md
   - ⏳ TECHNICAL_INDICATORS_SPEC.md

## 📝 버전 히스토리
- v2.4 (2025-10-09): Orchestrator-driven Workflow 추가 (agents/, docs/, orchestrator/, plan/ 폴더 구조 및 자동 Git 커밋)
- v2.3 (2025-10-09): 새로운 아키텍처 업데이트 (Helper, Database, Indicator, Strategy Agent 분리)
- v2.2 (2025-10-09): 코드 품질 규칙 및 모듈 인터페이스 관리 규칙 추가
- v2.1 (2025-10-06): 레이어간 표준 인터페이스 추가 (Indicator→Strategy, Strategy Output)
- v2.0 (2025-09-22): Multi-Agent Trading System 완성
- v1.0 (2025-09-15): 초기 프로젝트 규칙 정립