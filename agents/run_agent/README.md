# RUN AGENT

**Version**: 1.0.0
**Created**: 2025-10-09
**Role**: Multi-Agent System Main Controller

---

## 📋 Overview

RUN AGENT는 Multi-Agent Trading System의 **최상위 실행 관리자**입니다.

모든 Agent들의 라이프사이클을 관리하고, Orchestrator와 협업하여 전체 시스템을 조율합니다.

### 아키텍처 위치

```
RUN AGENT (최상위 실행 관리자)
    ↓
Orchestrator (작업 분배 및 조정)
    ↓
├── HELPER_AGENT
├── DATABASE_AGENT
├── STRATEGY_AGENT
└── SERVICE_AGENT
```

---

## 🎯 주요 역할

### 1. Agent 라이프사이클 관리
- 모든 Agent 초기화
- Agent 상태 추적 및 모니터링
- Agent 종료 및 리소스 정리

### 2. 작업 조율
- Orchestrator와 협업하여 작업 분배
- Agent 간 데이터 흐름 제어
- 작업 의존성 관리

### 3. 에러 처리
- Agent 에러 감지 및 복구
- Failover 메커니즘
- 재시도 로직

### 4. 시스템 모니터링
- 실시간 상태 모니터링
- 성능 메트릭 수집
- Health check

---

## 🚀 사용 방법

### 기본 실행

```python
# run_agent.py 직접 실행
python run_agent.py
```

### 프로그래밍 방식

```python
import asyncio
from agents.run_agent import RunAgent

async def main():
    # RUN AGENT 생성
    run_agent = RunAgent(config_path="myStockInfo.yaml")

    # Agent 초기화
    await run_agent.initialize_agents()

    # 백테스트 실행
    result = await run_agent.run_backtest(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        start_date='2023-01-01',
        end_date='2024-01-01',
        initial_cash=100000.0
    )

    # Agent 종료
    await run_agent.shutdown()

    return result

asyncio.run(main())
```

---

## 📊 실행 모드

### 1. Backtest Mode (백테스트)
```python
result = await run_agent.run_backtest(
    symbols=symbols,
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_cash=100000.0
)
```

**Flow**:
1. Database Agent → 데이터 로드
2. Strategy Agent → 시그널 생성
3. Service Agent → 백테스트 실행
4. RUN AGENT → 결과 수집

### 2. Live Trading Mode (실시간 거래)
```python
await run_agent.run_live_trading()
```

**Status**: 🚧 구현 예정

### 3. Analysis Mode (분석)
```python
await run_agent.run_analysis(
    symbols=symbols,
    analysis_type='performance'
)
```

**Status**: 🚧 구현 예정

---

## 🔧 설정

### config.yaml

```yaml
agent:
  name: "RUN_AGENT"
  version: "1.0.0"

  managed_agents:
    - name: "HELPER_AGENT"
      type: "helper"
    - name: "DATABASE_AGENT"
      type: "database"
    - name: "STRATEGY_AGENT"
      type: "strategy"
    - name: "SERVICE_AGENT"
      type: "service"

execution_modes:
  backtest:
    enabled: true
    default_period_days: 365
    max_symbols: 500

logging:
  level: "INFO"
  file: "run_agent.log"
```

---

## 📈 Agent 상태 관리

### AgentStatus 구조

```python
@dataclass
class AgentStatus:
    name: str           # Agent 이름
    type: AgentType     # Agent 타입
    status: str         # 'ready', 'running', 'completed', 'error'
    last_update: datetime
    message: str
```

### 상태 출력 예시

```
============================================================
Agent 상태 현황
============================================================
✅ HELPER: ready - Helper Agent 준비 완료
✅ DATABASE: ready - Database Agent 준비 완료
✅ STRATEGY: ready - Strategy Agent 준비 완료
✅ SERVICE: ready - Service Agent 준비 완료
============================================================
```

---

## 🔄 실행 Flow

### Backtest Flow

```
1. RUN AGENT 초기화
   ↓
2. 모든 Agent 초기화 (Helper, Database, Strategy, Service)
   ↓
3. Database Agent를 통한 데이터 로드
   ↓
4. Strategy Agent를 통한 시그널 생성
   ↓
5. Service Agent를 통한 백테스트 실행
   ↓
6. 결과 수집 및 반환
   ↓
7. Agent 종료
```

---

## 📝 로그 예시

```
2025-10-09 21:00:00 - [RUN_AGENT] INFO - 🚀 RUN AGENT 초기화 완료
2025-10-09 21:00:01 - [RUN_AGENT] INFO - ============================================================
2025-10-09 21:00:01 - [RUN_AGENT] INFO - Agent 초기화 시작
2025-10-09 21:00:01 - [RUN_AGENT] INFO - 1. Helper Agent 초기화 중...
2025-10-09 21:00:02 - [RUN_AGENT] INFO - 2. Database Agent 초기화 중...
2025-10-09 21:00:03 - [RUN_AGENT] INFO - ✅ 모든 Agent 초기화 완료
2025-10-09 21:00:04 - [RUN_AGENT] INFO - [Step 1] Database Agent - 데이터 로드
2025-10-09 21:00:05 - [RUN_AGENT] INFO - ✅ 데이터 로드 완료: 100 종목
2025-10-09 21:00:06 - [RUN_AGENT] INFO - [Step 2] Strategy Agent - 시그널 생성
2025-10-09 21:00:07 - [RUN_AGENT] INFO - ✅ 시그널 생성 완료: 20 시그널
2025-10-09 21:00:08 - [RUN_AGENT] INFO - [Step 3] Service Agent - 백테스트 실행
2025-10-09 21:00:09 - [RUN_AGENT] INFO - ✅ 백테스트 실행 완료
```

---

## 🛠️ API Reference

### RunAgent Class

#### `__init__(config_path: str)`
RUN AGENT 초기화

**Parameters**:
- `config_path`: 설정 파일 경로 (default: "myStockInfo.yaml")

#### `async initialize_agents()`
모든 Agent 초기화

**Returns**: None

#### `async run_backtest(...)`
백테스트 실행

**Parameters**:
- `symbols`: 종목 리스트
- `start_date`: 시작일 (YYYY-MM-DD)
- `end_date`: 종료일 (YYYY-MM-DD)
- `initial_cash`: 초기 자금

**Returns**: `Dict[str, Any]` - 백테스트 결과

#### `async shutdown()`
모든 Agent 종료

**Returns**: None

---

## 🔗 관련 파일

### Core Files
- `agents/run_agent/agent.py` - RUN AGENT 메인 로직
- `agents/run_agent/config.yaml` - 설정 파일
- `run_agent.py` - 독립 실행 파일 (wrapper)

### Dependencies
- `project/router/helper_agent_router.py`
- `project/router/data_agent_router.py`
- `project/router/strategy_agent_router.py`
- `project/router/service_agent_router.py`
- `orchestrator/main_orchestrator.py`

---

## 📚 참고 문서

- **CLAUDE.md**: 프로젝트 핵심 규칙
- **docs/architecture/**: 아키텍처 문서
- **Draw/Architecture Design.png**: 아키텍처 다이어그램

---

**Last Updated**: 2025-10-09
**Status**: ✅ Active Development
**Maintainer**: Orchestrator Team
