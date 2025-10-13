# Interactive Orchestrator 사용 가이드

**Version**: 1.0
**Created**: 2025-10-09
**목적**: 클로드 창에서 자연어 입력을 통해 Multi-Agent 시스템 제어

---

## 📋 목차

1. [개요](#개요)
2. [시작하기](#시작하기)
3. [사용 방법](#사용-방법)
4. [예시](#예시)
5. [시스템 아키텍처](#시스템-아키텍처)
6. [API 레퍼런스](#api-레퍼런스)

---

## 1. 개요

Interactive Orchestrator는 사용자의 자연어 입력을 받아서 자동으로:

1. ✅ **입력 분석**: 어떤 작업이 필요한지 파악
2. ✅ **Agent 선택**: 적절한 Sub-Agent 식별
3. ✅ **프롬프트 생성**: Agent별 맞춤 프롬프트 자동 생성
4. ✅ **작업 할당**: Sub-Agent에게 작업 분배
5. ✅ **결과 통합**: 모든 결과를 취합하여 반환

### 지원하는 작업 타입

| 작업 타입 | 설명 | 사용되는 Agent |
|----------|------|---------------|
| 백테스트 | 전략 백테스트 실행 | Database → Strategy → Service |
| 시그널 생성 | 매매 시그널 생성 | Database → Strategy |
| 데이터 수집 | 외부 API 데이터 수집 | Helper → Database |
| 성과 분석 | 포트폴리오 분석 | Database → Service |

---

## 2. 시작하기

### 2.1 설치 및 실행

```bash
# 1. 프로젝트 디렉토리로 이동
cd C:\WorkSpace\AIAgentProject\AIAssistant

# 2. Interactive Orchestrator 실행
python interactive_orchestrator.py
```

### 2.2 테스트 모드

```bash
# 자동 테스트 실행
python test_interactive.py
```

---

## 3. 사용 방법

### 3.1 대화형 모드

```
🤖 Interactive Orchestrator
Multi-Agent System with Dynamic Prompts

사용 가능한 명령어:
  - 자연어 입력: 원하는 작업을 자연어로 입력하세요
  - 'exit' 또는 'quit': 종료
  - 'history': 대화 히스토리 보기
  - 'help': 도움말

👤 You: _
```

### 3.2 자연어 입력 형식

**백테스트:**
```
NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘
```

**시그널 생성:**
```
AAPL, MSFT, GOOGL에 대한 매매 시그널 생성해줘
```

**데이터 수집:**
```
MongoDB에서 최근 데이터 가져와줘
```

**성과 분석:**
```
포트폴리오 성과 분석해줘
```

---

## 4. 예시

### 예시 1: 백테스트 실행

**입력:**
```
👤 You: NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘
```

**시스템 응답:**
```
================================================================================
🤖 Orchestrator가 요청을 분석하고 Sub-Agent에게 작업을 할당합니다...
================================================================================

[분석 결과]
작업 타입: TaskType.BACKTEST
필요한 Agent: ['database_agent', 'strategy_agent', 'service_agent']
파라미터: {'market': 'NASDAQ', 'start_date': '2024-01-01', 'end_date': '2024-06-30'}

[Workflow 계획]
1. database_agent: Load historical data
2. strategy_agent: Generate signals
3. service_agent: Run backtest

[실행] database_agent
✅ database_agent 완료

[실행] strategy_agent
✅ strategy_agent 완료

[실행] service_agent
✅ service_agent 완료

================================================================================
📊 실행 결과
================================================================================

✅ 성공한 Agent: database_agent, strategy_agent, service_agent

📝 요약:
백테스트 완료:
- 총 수익률: 15.00%
- 샤프 비율: 1.23
- 최대 낙폭: 8.00%
- 승률: 58.0%
- 총 거래: 45회

📋 상세 결과:

✅ database_agent:
  - 종목 수: 15113

✅ strategy_agent:
  - AAPL: BUY (신뢰도: 85%)
  - MSFT: BUY (신뢰도: 78%)
  - GOOGL: HOLD (신뢰도: 62%)

✅ service_agent:
  - 수익률: 15.00%
  - 샤프 비율: 1.23
  - 승률: 58.0%

================================================================================
```

### 예시 2: 시그널 생성

**입력:**
```
👤 You: AAPL, MSFT에 대한 매매 시그널 생성해줘
```

**시스템 응답:**
```
[분석 결과]
작업 타입: TaskType.SIGNAL_GENERATION
필요한 Agent: ['database_agent', 'strategy_agent']

[실행] database_agent
✅ database_agent 완료

[실행] strategy_agent
✅ strategy_agent 완료

📊 실행 결과
✅ 성공한 Agent: database_agent, strategy_agent

📝 요약:
매매 시그널 생성 완료:
- 총 시그널: 1개
- BUY 시그널: 1개
- SELL 시그널: 0개

📋 상세 결과:
✅ strategy_agent:
  - AAPL: BUY (신뢰도: 85%)
```

### 예시 3: 대화 히스토리

**명령:**
```
👤 You: history
```

**시스템 응답:**
```
================================================================================
📋 대화 히스토리
================================================================================

1. [2025-10-09T21:30:00.000000]
   입력: NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘
   실행: database_agent, strategy_agent, service_agent
   결과: 백테스트 완료: 총 수익률: 15.00%...

2. [2025-10-09T21:32:15.000000]
   입력: AAPL, MSFT에 대한 매매 시그널 생성해줘
   실행: database_agent, strategy_agent
   결과: 매매 시그널 생성 완료: 총 시그널: 1개...
```

---

## 5. 시스템 아키텍처

### 5.1 전체 흐름

```
사용자 입력 (자연어)
    ↓
Interactive Orchestrator
    ↓
User Input Handler
    ├── 입력 분석 (Prompt Generator)
    ├── Agent 선택
    ├── 프롬프트 생성
    └── 작업 할당
    ↓
Orchestrator
    ↓
Sub-Agents (병렬/순차 실행)
    ├── Helper Agent
    ├── Database Agent
    ├── Strategy Agent
    └── Service Agent
    ↓
결과 통합 및 반환
```

### 5.2 핵심 컴포넌트

#### 1. **PromptGenerator** (`orchestrator/prompt_generator.py`)
- 사용자 입력 분석
- Agent별 맞춤 프롬프트 자동 생성
- 작업 타입 식별

```python
from orchestrator.prompt_generator import PromptGenerator, PromptContext, TaskType

generator = PromptGenerator()

# 입력 분석
analysis = generator.parse_user_request("백테스트 실행해줘")

# 프롬프트 생성
context = PromptContext(
    task_type=TaskType.BACKTEST,
    user_request="백테스트 실행해줘",
    parameters={"market": "NASDAQ"}
)
prompt = generator.generate_prompt("strategy_agent", context)
```

#### 2. **UserInputHandler** (`orchestrator/user_input_handler.py`)
- 전체 Workflow 관리
- Agent 실행 조율
- 결과 취합

```python
from orchestrator.user_input_handler import UserInputHandler

handler = UserInputHandler()

# 요청 처리
result = await handler.process_user_input("백테스트 실행해줘")
```

#### 3. **InteractiveOrchestrator** (`interactive_orchestrator.py`)
- 대화형 인터페이스
- 사용자 입력 처리
- 결과 출력

```python
from interactive_orchestrator import InteractiveOrchestrator

orchestrator = InteractiveOrchestrator()

# 대화형 모드
await orchestrator.interactive_mode()

# 또는 직접 처리
result = await orchestrator.process_request("백테스트 실행해줘")
```

---

## 6. API 레퍼런스

### 6.1 PromptGenerator

#### `parse_user_request(user_input: str) -> Dict`
사용자 입력 분석

**Parameters:**
- `user_input`: 사용자의 자연어 입력

**Returns:**
```python
{
    "agents_needed": ["database_agent", "strategy_agent"],
    "task_type": TaskType.SIGNAL_GENERATION,
    "parameters": {"market": "NASDAQ"},
    "workflow": [
        {"agent": "database_agent", "task": "Load data"},
        {"agent": "strategy_agent", "task": "Generate signals"}
    ]
}
```

#### `generate_prompt(agent_name: str, context: PromptContext) -> str`
Agent별 프롬프트 생성

**Parameters:**
- `agent_name`: Agent 이름
- `context`: 프롬프트 컨텍스트

**Returns:** 생성된 프롬프트 문자열

### 6.2 UserInputHandler

#### `async process_user_input(user_input: str) -> Dict`
사용자 입력 처리

**Parameters:**
- `user_input`: 사용자 요청

**Returns:**
```python
{
    "user_request": "...",
    "task_type": "...",
    "agents_executed": [...],
    "successful_agents": [...],
    "failed_agents": [...],
    "results": {...},
    "summary": "...",
    "timestamp": "..."
}
```

#### `get_conversation_history() -> List[Dict]`
대화 히스토리 반환

**Returns:** 대화 히스토리 리스트

### 6.3 InteractiveOrchestrator

#### `async process_request(user_input: str) -> dict`
요청 처리

#### `async interactive_mode()`
대화형 모드 실행

---

## 7. 키워드 매칭

시스템은 다음 키워드를 인식하여 자동으로 적절한 Agent를 선택합니다:

| 키워드 | 작업 타입 | Agent 할당 |
|--------|----------|-----------|
| backtest, 백테스트 | BACKTEST | Database → Strategy → Service |
| signal, 시그널, buy, sell | SIGNAL_GENERATION | Database → Strategy |
| data, 데이터, collect, fetch | DATA_COLLECTION | Helper → Database |
| analyze, 분석, report, performance | REPORTING | Database → Service |
| nasdaq, nyse | (파라미터 추출) | market = "NASDAQ" or "NYSE" |
| YYYY-MM-DD 형식 | (파라미터 추출) | start_date, end_date |

---

## 8. 트러블슈팅

### 문제 1: Agent 실행 실패
**증상**: Agent가 오류를 반환

**해결**:
1. 로그 확인: `interactive_orchestrator.log`
2. Agent별 설정 확인
3. API 키 및 권한 확인

### 문제 2: 잘못된 Agent 선택
**증상**: 의도와 다른 Agent가 실행됨

**해결**:
1. 키워드를 명확하게 입력
2. "백테스트", "시그널", "데이터" 등 명확한 작업 타입 언급
3. 파라미터를 명시적으로 제공 (날짜, 종목 등)

### 문제 3: 시뮬레이션 모드
**현재 상태**: 실제 Orchestrator 없이 시뮬레이션

**실제 모드 활성화**:
```python
# interactive_orchestrator.py 수정
from orchestrator.main_orchestrator import MainOrchestrator

# API 키 설정
api_key = "your-anthropic-api-key"
self.orchestrator = MainOrchestrator(api_key)
```

---

## 9. 확장 가능성

### 새로운 Agent 추가

1. **프롬프트 템플릿 추가** (`prompt_generator.py`):
```python
self.agent_templates["new_agent"] = """
You are a New Agent...
"""
```

2. **키워드 매칭 추가** (`parse_user_request`):
```python
if any(keyword in user_input_lower for keyword in ['new', 'keyword']):
    result["agents_needed"].append("new_agent")
```

3. **시뮬레이션 응답 추가** (`user_input_handler.py`):
```python
simulated_responses["new_agent"] = {
    "status": "success",
    ...
}
```

---

## 10. 참고 문서

- **[CLAUDE.md](../CLAUDE.md)**: 프로젝트 핵심 규칙
- **[README.md](../README.md)**: 프로젝트 개요
- **[Architecture Design.png](../Draw/Architecture Design.png)**: 아키텍처 다이어그램

---

**Last Updated**: 2025-10-09
**Author**: Orchestrator Team
**Status**: ✅ Active Development
