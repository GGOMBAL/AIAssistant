# Multi-Agent 협업 시스템 규칙

**최종 업데이트**: 2025-10-21
**적용 대상**: 모든 Agent

---

## 시스템 아키텍처

이 프로젝트는 **여러개의 SubAgent를 연결하여 협업하는 시스템**입니다.

```
RUN AGENT (최상위 실행 관리자) - run_agent.py
    ↓
Orchestrator Agent (작업 분배 및 조정) - orchestrator/main_orchestrator.py
    ↓
├── Helper Agent (외부 API 데이터 수집) - project/router/helper_agent_router.py
├── Database Agent (MongoDB 데이터 관리) - project/router/data_agent_router.py
├── Strategy Agent (시장별 매매신호 생성) - project/router/strategy_agent_router.py
├── Service Agent (백테스트 실행, 포트폴리오 관리) - project/router/service_agent_router.py
└── Report Agent (거래 분석 및 리포팅) - project/router/report_agent_router.py
```

---

## 1. RUN AGENT 역할

**RUN AGENT가 최상위 실행 관리자로 전체 시스템을 관리**합니다.

### 주요 책임:
- 모든 Agent의 라이프사이클 관리 (초기화, 실행, 종료)
- Orchestrator와 협업하여 작업 조율
- Agent 간 통신 및 데이터 흐름 제어
- 시스템 상태 모니터링 및 에러 처리
- 실행 모드 관리 (Backtest, Trading, Analysis)

### 실행 파일:
- `run_agent.py` (메인)
- `agents/run_agent/agent.py` (Agent 클래스)

---

## 2. Orchestrator Agent 역할

**Orchestrator Agent가 작업 분배 및 조정을 담당**합니다.

### 주요 책임:
- RUN AGENT로부터 작업 요청 수신
- 각 Agent에게 작업 할당
- Agent 간 통신 중재
- 결과 취합 및 RUN AGENT에 전달

### Orchestrator 구조:
```
orchestrator/
├── orchestrator.py            # 메인 Orchestrator 로직
├── prompt_generator.py        # 프롬프트 생성기
├── task_analyzer.py           # 사용자 입력 분석
├── agent_router.py            # Agent 라우팅
├── validator.py               # 결과 검증
├── config/
│   ├── orchestrator_config.yaml
│   └── feedback_config.yaml
└── templates/                 # 프롬프트 템플릿
    ├── helper_agent_template.md
    ├── database_agent_template.md
    ├── indicator_agent_template.md
    ├── strategy_agent_template.md
    └── service_agent_template.md
```

---

## 3. 프롬프트 관리 체계

**오케스트레이터 에이전트가 각 서브 에이전트가 해야할 프롬프트를 작성하여 전달**합니다.

### 프롬프트 구성 요소:
- 작업별 명확한 프롬프트 정의
- 에이전트 역할에 맞는 지시사항
- 결과 포맷 및 품질 기준 명시
- 에러 처리 및 fallback 절차

### Orchestrator 역할:

#### 1. 사용자 입력 분석 (`task_analyzer.py`)
- 사용자 요청 파싱 및 의도 파악
- 필요한 Agent 식별
- 작업 우선순위 결정

#### 2. 프롬프트 생성 (`prompt_generator.py`)
- 각 Agent에게 전달할 프롬프트 생성
- 템플릿 기반 프롬프트 커스터마이징
- Context 및 의존성 정보 포함

#### 3. Agent 라우팅 (`agent_router.py`)
- 적절한 Agent에게 작업 분배
- 병렬/순차 실행 결정
- Agent 간 데이터 전달 관리

#### 4. 결과 검증 (`validator.py`)
- Sub-Agent 작업 결과 검증
- 품질 기준 충족 여부 확인
- Feedback 필요 여부 판단

---

## 4. 작업 워크플로우 (Orchestrator-driven)

### 표준 작업 흐름:
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

### Feedback Iteration 설정:
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

### Feedback 예시:
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

---

## 5. 작업 계획 관리 (Plan-driven Workflow)

**모든 작업은 `plan/` 폴더에 계획 문서를 생성하여 관리합니다**.

### Plan 폴더 구조:
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

### Plan 관리 규칙:

#### 1. 작업 시작 시:
- Orchestrator가 자동으로 `plan/plan.md` 생성
- 사용자 요청 분석 → Sub-task 분해 → Agent 할당

#### 2. 작업 진행 중:
- 각 Sub-task 상태 실시간 업데이트
- Agent 작업 결과를 plan.md에 기록

#### 3. 작업 완료 시:
- plan.md를 `plan/completed/plan_YYYYMMDD_NNN.md`로 이동
- 자동으로 Git commit & push

---

## 6. Git 자동 커밋 규칙

**작업 완료 시 자동으로 Git에 commit 및 push합니다**.

### 자동 커밋 조건:
1. `plan/plan.md`의 모든 Sub-task가 Completed 상태
2. Orchestrator validation 통과
3. 모든 문서 업데이트 완료

### 커밋 메시지 형식:
```
feat: [Task Name]

- Sub-task 1: Description
- Sub-task 2: Description
- Sub-task 3: Description

Agents: Helper, Database, Indicator, Strategy
Plan: plan/completed/plan_20251009_001.md

Generated with Claude Code
Orchestrator: Data Orchestrator Agent
```

### 자동 커밋 설정:
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

## 7. Agent 간 협업 원칙

### 원칙 1: 명확한 책임 분리
- 각 Agent는 자신의 Layer만 책임
- Cross-layer 작업은 Orchestrator를 통해 조율

### 원칙 2: 인터페이스 기반 통신
- 모든 데이터 전달은 정의된 인터페이스 사용
- 직접 파일 접근 금지

### 원칙 3: 비동기 처리
- 독립적인 작업은 병렬 실행
- 의존성 있는 작업은 순차 실행

### 원칙 4: 에러 격리
- 한 Agent의 에러가 다른 Agent에 영향 최소화
- 각 Agent는 독립적인 에러 처리

### 원칙 5: 문서화 우선
- 모든 변경사항은 문서화
- 인터페이스 변경 시 즉시 문서 업데이트

---

## 참조 문서

- **파일 접근 권한**: `docs/rules/FILE_PERMISSIONS.md`
- **인터페이스 규약**: `docs/interfaces/`
- **문서 관리**: `docs/rules/DOCUMENTATION.md` (예정)
