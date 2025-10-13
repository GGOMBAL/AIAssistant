# Request Type Classification System

**버전**: 1.0
**작성일**: 2025-10-11
**목적**: 실행(EXECUTION)과 코드 수정(CODE_MODIFICATION) 요청을 구분하여 처리

---

## 1. 개요

Interactive Orchestrator는 사용자 요청을 두 가지 타입으로 분류합니다:

1. **EXECUTION**: 기존 코드를 실행하는 요청 (백테스트, 데이터 조회, 시그널 생성 등)
2. **CODE_MODIFICATION**: 코드를 수정하거나 추가하는 요청 (함수 추가, 로직 개선, 버그 수정 등)

---

## 2. Request Type 분류

### 2.1 EXECUTION 키워드

다음 키워드가 포함되면 EXECUTION으로 분류됩니다:

```
backtest, 백테스트, run, 실행, execute,
test, 테스트, check, 확인, query, 조회,
search, 검색, generate, 생성,
show, 보여, display, 표시, get, 가져
```

**예시**:
- "NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘"
- "AAPL 데이터 조회해줘"
- "최근 시그널 생성해줘"

### 2.2 CODE_MODIFICATION 키워드

다음 키워드가 포함되면 CODE_MODIFICATION으로 분류됩니다:

```
modify, 수정, change, 변경, update, 업데이트,
add, 추가, create, 만들, implement, 구현,
fix, 고치, improve, 개선, refactor, 리팩토링,
optimize, 최적화, function, 함수, method, 메서드,
class, 클래스, code, 코드
```

**예시**:
- "Strategy Layer에 새로운 필터 함수 추가해줘"
- "백테스트 로직 개선해줘"
- "MongoDB 연결 코드 수정해줘"

---

## 3. EXECUTION 요청 처리

### 3.1 프롬프트 생성

`_generate_execution_prompt()` 메서드가 다음을 수행합니다:

1. Agent별 템플릿 선택
2. 작업 설명 생성 (`_generate_task_description`)
3. 파라미터 포맷팅
4. 의존성 정보 추가

### 3.2 실행 흐름

```
사용자 입력
    ↓
Request Type 분류 (EXECUTION)
    ↓
적절한 Agent 선택 (run_agent, database_agent, etc.)
    ↓
실행 프롬프트 생성
    ↓
Agent 실행
    ↓
결과 반환
```

---

## 4. CODE_MODIFICATION 요청 처리

### 4.1 3단계 워크플로우 (Plan-Review-Implementation)

CODE_MODIFICATION 요청은 다음 3단계로 처리됩니다:

#### Phase 1: PLANNING
- **담당**: Sub-Agent (database_agent, strategy_agent, etc.)
- **작업**: 상세한 구현 Plan 생성
- **출력**: JSON 형식의 Plan 문서
- **내용**:
  - 현재 코드 구조 분석
  - 함수/메서드 명세
  - 구현 단계 (step-by-step)
  - 인터페이스 영향 분석
  - 테스트 요구사항
  - 예상 작업 시간

#### Phase 2: REVIEW
- **담당**: Orchestrator Agent
- **작업**: Plan 품질 검증 및 승인 여부 결정
- **검증 기준**:
  - `has_function_spec`: 함수 명세 존재
  - `has_implementation_plan`: 구현 단계 존재
  - `has_test_requirements`: 테스트 요구사항 존재
  - `has_interface_impact`: 인터페이스 영향 분석 존재
  - `has_estimated_effort`: 예상 작업 시간 존재
- **승인 기준**: 품질 점수 80% 이상
- **결과**: 승인 (Implementation 진행) 또는 거부 (재작성 요청)

#### Phase 3: IMPLEMENTATION
- **담당**: Sub-Agent (Plan 작성한 동일 Agent)
- **작업**: 승인된 Plan 기반으로 코드 작성
- **출력**: JSON 형식의 구현 결과
- **내용**:
  - 구현된 코드 변경사항
  - 테스트 코드
  - 문서 업데이트
  - 검증 결과

### 4.2 프롬프트 생성

`_generate_code_modification_prompt()` 메서드가 단계별로 다른 프롬프트를 생성합니다:

**PLANNING 단계 프롬프트**:
1. **Layer Architecture Context**: 프로젝트의 레이어 구조 설명
2. **Modification Target**: 수정 대상 레이어, 파일, 컴포넌트
3. **Specifications**: 수정 사양 및 요구사항
4. **Agent Responsibilities**: Agent별 코드 수정 책임
5. **Output Requirements**: Plan JSON 형식

**IMPLEMENTATION 단계 프롬프트**:
1. **Approved Plan**: Orchestrator가 승인한 Plan 전체
2. **Implementation Guidelines**: 코딩 표준, 에러 처리, 호환성 유지
3. **Output Requirements**: 구현 결과 JSON 형식

### 4.3 Layer Architecture Context

프롬프트에 포함되는 레이어 정보:

```
1. Helper Layer (project/Helper/)
   - External API integration
   - System configuration
   - MongoDB connection

2. Data/Indicator Layer (project/indicator/)
   - MongoDB data loading
   - Technical indicator calculation
   - Data transformation

3. Strategy Layer (project/strategy/)
   - Trading signal generation
   - Universe selection
   - Market-specific strategies

4. Service Layer (project/service/)
   - Backtest execution
   - Portfolio management
   - Performance analysis
```

### 4.4 Modification Target 분석

사용자 요청에서 자동으로 수정 대상을 분석합니다:

| 키워드 | Layer | File Path |
|--------|-------|-----------|
| api, helper, kis | Helper Layer | project/Helper/ |
| indicator, data, mongodb | Data/Indicator Layer | project/indicator/ |
| strategy, signal, universe | Strategy Layer | project/strategy/ |
| backtest, service, portfolio | Service Layer | project/service/ |

### 4.5 Agent 출력 형식

#### PLANNING 단계 출력 (Sub-Agent → Orchestrator)

Sub-Agent는 다음 JSON 형식으로 Plan을 생성합니다:

```json
{
    "phase": "planning",
    "analysis": {
        "current_code_structure": "Detailed analysis",
        "identified_issues": ["Issue 1", "Issue 2"],
        "modification_scope": "Scope of changes"
    },
    "function_specification": {
        "name": "function_name",
        "parameters": [
            {"name": "param1", "type": "type1", "description": "Purpose"}
        ],
        "return_type": "return_type",
        "purpose": "Clear description",
        "algorithm": "High-level algorithm"
    },
    "implementation_plan": {
        "steps": [
            {
                "step_number": 1,
                "description": "Step description",
                "files_to_modify": ["file1.py"],
                "estimated_complexity": "low/medium/high"
            }
        ],
        "dependencies": ["Dependency 1"],
        "risks": ["Risk 1"]
    },
    "interface_impact": {
        "affected_layers": ["layer1", "layer2"],
        "interface_changes": [
            {
                "type": "new_function/modify_signature",
                "description": "Description",
                "backward_compatible": true/false
            }
        ]
    },
    "test_requirements": {
        "unit_tests": ["Test 1"],
        "integration_tests": ["Integration test 1"]
    },
    "estimated_effort": {
        "hours": 2.5,
        "complexity": "low/medium/high",
        "confidence": 0.85
    }
}
```

#### IMPLEMENTATION 단계 출력 (Sub-Agent → Orchestrator)

Plan이 승인된 후, Sub-Agent는 다음 JSON 형식으로 구현 결과를 반환합니다:

```json
{
    "phase": "implementation",
    "implemented_changes": [
        {
            "file_path": "path/to/file.py",
            "change_type": "new_function/modify_function/new_class",
            "code": "Complete code implementation",
            "line_number": "Insert at line N or append",
            "description": "What this change does"
        }
    ],
    "tests_implemented": [
        {
            "test_file": "path/to/test_file.py",
            "test_code": "Complete test code",
            "description": "What this test verifies"
        }
    ],
    "documentation_updates": [
        {
            "file_path": "path/to/doc.md",
            "updates": "Documentation changes needed"
        }
    ],
    "verification": {
        "all_tests_pass": true/false,
        "interface_compatible": true/false,
        "no_breaking_changes": true/false
    },
    "notes": "Implementation notes"
}
```

---

## 5. 구현 상세

### 5.1 파일 위치

**orchestrator/prompt_generator.py**:
- `RequestType` enum (line 22-25): EXECUTION vs CODE_MODIFICATION
- `CodeModificationPhase` enum (line 27-31): PLANNING, REVIEW, IMPLEMENTATION 단계
- `PromptContext` dataclass (line 33-43): code_modification_phase, plan_data 추가
- `generate_prompt()` - 메인 라우팅 (line 267-286)
- `_generate_execution_prompt()` - 실행 프롬프트 (line 288-350)
- `_generate_code_modification_prompt()` - 코드 수정 라우팅 (line 352-374)
- `_generate_planning_prompt()` - PLANNING 프롬프트 (line 376-491)
- `_generate_implementation_prompt()` - IMPLEMENTATION 프롬프트 (line 493-570)
- Helper methods:
  - `_get_layer_architecture_context()`
  - `_analyze_modification_target()`
  - `_format_modification_specifications()`
  - `_format_plan_summary()`
  - `_get_agent_modification_responsibilities()`
  - `_determine_request_type()`

**orchestrator/user_input_handler.py**:
- `process_user_input()` - Request Type 분기 처리 (line 105-158)
- `_execute_code_modification_workflow()` - 3단계 워크플로우 (line 699-788)
  - Phase 1: PLANNING 실행
  - Phase 2: REVIEW 실행
  - Phase 3: IMPLEMENTATION 실행
- `_parse_plan_from_response()` - Plan JSON 파싱 (line 790-829)
- `_review_plan()` - Orchestrator Plan 리뷰 (line 831-885)

### 5.2 주요 메서드

#### `_determine_request_type(user_input_lower: str) -> RequestType`

키워드 기반으로 요청 타입을 결정합니다.

```python
# CODE_MODIFICATION 키워드가 우선순위
if any(keyword in user_input_lower for keyword in modification_keywords):
    return RequestType.CODE_MODIFICATION

# 기본값은 EXECUTION
return RequestType.EXECUTION
```

#### `_analyze_modification_target(user_request: str, task_type: TaskType) -> Dict`

수정 대상 레이어와 파일 경로를 자동으로 분석합니다.

---

## 6. 사용 예시

### 6.1 EXECUTION 요청

```
You: NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘
```

**처리 과정**:
1. Request Type: EXECUTION
2. Task Type: BACKTEST
3. Agent: run_agent
4. Workflow: Execute main_auto_trade.py

### 6.2 CODE_MODIFICATION 요청

```
You: Strategy Layer에 RSI 필터 함수 추가해줘
```

**처리 과정**:

**Phase 1: PLANNING**
1. Request Type: CODE_MODIFICATION
2. Modification Target:
   - Layer: Strategy Layer
   - File Path: project/strategy/
   - Component Type: function
3. Agent: strategy_agent
4. strategy_agent가 Plan 생성 (JSON 형식)
   - 함수명: `filter_by_rsi`
   - 파라미터: `symbols: List[str], rsi_threshold: float`
   - 구현 단계: 5 steps
   - 예상 시간: 2시간

**Phase 2: REVIEW**
5. Orchestrator가 Plan 검증
   - 함수 명세: OK
   - 구현 단계: OK (5 steps)
   - 테스트 요구사항: OK
   - 인터페이스 영향: OK
   - 예상 작업 시간: OK
6. 품질 점수: 100% → 승인

**Phase 3: IMPLEMENTATION**
7. strategy_agent가 승인된 Plan 기반으로 코드 작성
   - 파일: `project/strategy/filters.py`
   - 함수 구현
   - 유닛 테스트 작성
   - 문서 업데이트
8. 구현 완료 및 검증 결과 반환

---

## 7. 향후 개선 사항

1. **LLM 기반 Plan Review**: 현재는 규칙 기반, LLM 활용하여 품질 향상
2. **자동 파일 탐색**: Layer 내에서 적절한 파일 자동 선택
3. **코드 분석 통합**: AST 분석으로 기존 함수/클래스 파악
4. **Interactive Confirmation**: Implementation 전 사용자 확인 옵션
5. **Plan Iteration**: Plan이 승인되지 않을 경우 자동 재생성 (최대 N회)
6. **Implementation 검증**: 코드 작성 후 자동 테스트 실행 및 검증

---

## 8. 관련 문서

- **Claude.md**: 프로젝트 핵심 규칙
- **docs/INTERFACE_SPECIFICATION.md**: 레이어 간 인터페이스 명세
- **docs/architecture/ARCHITECTURE_OVERVIEW.md**: 시스템 아키텍처

---

**버전**: 1.0
**최종 업데이트**: 2025-10-11
