># Hybrid Model 가이드
**Claude 구독 + Gemini API 통합 사용**

**Version**: 1.0
**Created**: 2025-10-09

---

## 📋 개요

본 시스템은 **Claude 구독 모델**과 **Gemini API**를 하이브리드로 사용합니다:

- **Orchestrator**: Claude 구독 모델 (현재 Claude Code 세션)
- **Sub-Agents**: Gemini API (helper, database, strategy, service)

### 장점

1. **비용 효율**: Orchestrator만 Claude 구독, 나머지는 저렴한 Gemini API
2. **성능**: Claude의 추론 능력 + Gemini의 빠른 응답
3. **확장성**: Agent별 모델 선택 가능

---

## 🔧 설정

### 1. API 키 설정

```bash
# 환경 변수로 Gemini API 키 설정
export GOOGLE_API_KEY="your-gemini-api-key"

# Windows
set GOOGLE_API_KEY=your-gemini-api-key
```

### 2. YAML 설정 파일

**파일 위치**: `config/agent_model.yaml`

```yaml
# Agent별 모델 할당
agents:
  orchestrator:
    primary_model: "claude_opus"      # Claude 구독
    fallback_model: "claude_sonnet"

  data_agent:
    primary_model: "gemini_flash"     # Gemini API
    fallback_model: "gemini_pro"

  strategy_agent:
    primary_model: "gemini_flash"     # Gemini API
    fallback_model: "claude_sonnet"

  service_agent:
    primary_model: "gemini_flash"     # Gemini API
    fallback_model: "claude_haiku"

  helper_agent:
    primary_model: "gemini_flash"     # Gemini API
    fallback_model: "gemini_pro"

# 모델 정의
models:
  gemini_flash:
    model_id: "gemini-2.5-flash"
    provider: "google"
    api_key_env: "GOOGLE_API_KEY"
    max_tokens: 1048576
```

---

## 🚀 사용 방법

### 1. 기본 사용

```python
from orchestrator.hybrid_model_manager import HybridModelManager

# Manager 생성
manager = HybridModelManager()

# Agent 작업 실행
response = await manager.execute_agent_task(
    agent_name="strategy_agent",
    prompt="Generate trading signals for AAPL",
    system_prompt="You are a strategy agent."
)
```

### 2. Interactive Orchestrator와 통합

```bash
# Hybrid Model 활성화 상태로 실행
python interactive_orchestrator.py
```

**내부 동작**:
```python
# UserInputHandler에서 자동으로 Hybrid Model 사용
handler = UserInputHandler(use_hybrid_models=True)

# 사용자 입력 처리
result = await handler.process_user_input(
    "NASDAQ 종목으로 백테스트 실행해줘"
)
```

### 3. 테스트

```bash
# Hybrid Model 테스트
python test_hybrid_model.py
```

---

## 📊 Agent별 모델 매핑

| Agent | Provider | Model | 비용 |
|-------|----------|-------|------|
| Orchestrator | Claude 구독 | claude-code-session | 무료 (구독 포함) |
| Database Agent | Gemini API | gemini-2.5-flash | 매우 저렴 |
| Strategy Agent | Gemini API | gemini-2.5-flash | 매우 저렴 |
| Service Agent | Gemini API | gemini-2.5-flash | 매우 저렴 |
| Helper Agent | Gemini API | gemini-2.5-flash | 매우 저렴 |

---

## 💰 비용 비교

### Before (모두 Claude 사용)

```
Orchestrator: Claude Opus ($15/M tokens)
Database Agent: Claude Sonnet ($3/M tokens)
Strategy Agent: Claude Opus ($15/M tokens)
Service Agent: Claude Sonnet ($3/M tokens)
Helper Agent: Claude Haiku ($0.25/M tokens)

월간 예상 비용: ~$500
```

### After (Hybrid 모델)

```
Orchestrator: Claude 구독 (무료)
Database Agent: Gemini Flash ($0.15/M tokens)
Strategy Agent: Gemini Flash ($0.15/M tokens)
Service Agent: Gemini Flash ($0.15/M tokens)
Helper Agent: Gemini Flash ($0.15/M tokens)

월간 예상 비용: ~$50 (90% 절감!)
```

---

## 🔄 동작 방식

### 1. 사용자 입력
```
👤 You: NASDAQ 종목으로 백테스트 실행해줘
```

### 2. Orchestrator (Claude 구독)
```
[입력 분석]
- 작업 타입: 백테스트
- 필요한 Agent: database → strategy → service
- 프롬프트 생성
```

### 3. Sub-Agents (Gemini API)
```
Database Agent (Gemini)
  ↓ 데이터 로드
Strategy Agent (Gemini)
  ↓ 시그널 생성
Service Agent (Gemini)
  ↓ 백테스트 실행
```

### 4. 결과 통합 (Claude 구독)
```
Orchestrator가 모든 결과 취합 및 사용자에게 반환
```

---

## 🛠️ API 문서

### HybridModelManager

#### `execute_agent_task(agent_name, prompt, system_prompt)`
Agent 작업 실행

**Parameters:**
- `agent_name`: Agent 이름 ("orchestrator", "data_agent", etc.)
- `prompt`: 작업 프롬프트
- `system_prompt`: 시스템 프롬프트 (선택)

**Returns:** Agent 응답 문자열

**Example:**
```python
response = await manager.execute_agent_task(
    agent_name="strategy_agent",
    prompt="Generate signals for AAPL, MSFT",
    system_prompt="You are a trading strategy specialist."
)
```

#### `get_agent_model_info(agent_name)`
Agent 모델 정보 반환

**Returns:**
```python
{
    'provider': ModelProvider.GEMINI_API,
    'model_id': 'gemini-2.5-flash',
    'primary_model': 'gemini_flash',
    'fallback_model': 'gemini_pro',
    'use_cases': [...]
}
```

#### `test_connectivity()`
모델 연결 테스트

**Returns:**
```python
{
    'claude_subscription': True,
    'gemini_api': True/False
}
```

---

## ⚙️ 고급 설정

### 1. 모델 변경

**config/agent_model.yaml** 수정:

```yaml
agents:
  strategy_agent:
    primary_model: "claude_opus"  # Claude로 변경
    fallback_model: "gemini_flash"
```

### 2. Fallback 설정

```yaml
error_handling:
  fallback_chain:
    - "primary_model"
    - "fallback_model"
    - "emergency_model"  # claude_haiku
```

### 3. 비용 제한

```yaml
usage_limits:
  daily_budget: 100.00  # USD
  alert_threshold: 80   # percentage

  agent_quotas:
    orchestrator: 30%
    data_agent: 25%
    strategy_agent: 30%
    service_agent: 10%
    helper_agent: 5%
```

---

## 🔍 트러블슈팅

### 문제 1: Gemini API 연결 실패

**증상**: `gemini_api: False`

**해결:**
```bash
# API 키 확인
echo $GOOGLE_API_KEY

# API 키 재설정
export GOOGLE_API_KEY="your-api-key"

# 연결 테스트
python test_hybrid_model.py
```

### 문제 2: Claude 구독 모델 실행 안됨

**증상**: Orchestrator가 시뮬레이션 모드로 실행

**해결:**
- 현재는 Claude Code 세션에서 실행 중이므로 자동으로 작동
- 별도 Claude API 연결이 필요한 경우 추가 구현 필요

### 문제 3: Agent가 잘못된 모델 사용

**증상**: 의도와 다른 모델로 실행

**해결:**
```yaml
# config/agent_model.yaml 확인
agents:
  [agent_name]:
    primary_model: "gemini_flash"  # 올바른 모델 설정
```

---

## 📈 성능 모니터링

### 1. 사용량 확인

```python
# Agent별 모델 정보 출력
for agent, info in manager.get_all_agent_models().items():
    print(f"{agent}: {info['model_id']}")
```

### 2. 비용 추적

```yaml
# config/agent_model.yaml
monitoring:
  enabled: true
  metrics:
    - "response_time"
    - "success_rate"
    - "cost_tracking"
```

### 3. 로그 확인

```bash
# 로그 파일
tail -f orchestrator.log
tail -f interactive_orchestrator.log
```

---

## 🔗 관련 문서

- **[Interactive Orchestrator 가이드](INTERACTIVE_ORCHESTRATOR_GUIDE.md)**: 사용자 입력 처리
- **[Agent Model 설정](../config/agent_model.yaml)**: 모델 설정 파일
- **[Gemini Client](../gemini_client.py)**: Gemini API 클라이언트

---

## 📝 요약

✅ **Orchestrator는 Claude 구독 모델 사용** (현재 세션)
✅ **Sub-Agents는 Gemini API 사용** (helper, database, strategy, service)
✅ **모든 설정은 YAML 파일로 관리**
✅ **90% 비용 절감** 효과
✅ **쉬운 모델 전환** (YAML 수정만으로 가능)

---

**Last Updated**: 2025-10-09
**Author**: Orchestrator Team
**Status**: ✅ Production Ready
