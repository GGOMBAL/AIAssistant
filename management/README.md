# Agent Management System

매뉴얼 관리가 가능한 멀티 에이전트 시스템의 관리 도구입니다.

## 🎯 주요 기능

### 1. 에이전트 협업 관계 관리
- 각 에이전트별 협업 파트너 정의
- 협업 목적 및 인터페이스 명세
- 데이터 요구사항 및 통신 프로토콜

### 2. 파일 소유권 관리
- 에이전트별 관리 파일 정의
- 파일 접근 권한 제어
- 공유 접근 권한 관리

### 3. 협업 매트릭스 관리
- 에이전트 간 통신 패턴
- 프로토콜 및 데이터 형식 정의
- 모니터링 및 성능 지표

## 📁 구성 파일

### `config/agent_interfaces.yaml`
각 에이전트의 관리 파일과 협업 관계를 정의합니다.

```yaml
strategy_agent:
  managed_files:
    - "Project/strategy/signal_generator.py"
    - "Project/strategy/position_sizing.py"
  collaborates_with:
    - agent: data_agent
      purpose: "Receive market data and indicators"
      interface: "data_feed"
```

### `config/file_ownership.yaml`
파일 소유권과 접근 권한을 관리합니다.

```yaml
file_ownership:
  strategy_files:
    owner: strategy_agent
    files:
      - path: "Project/strategy/signal_generator.py"
        permissions: ["read", "write", "execute"]
```

### `config/collaboration_matrix.yaml`
에이전트 간 협업 패턴과 통신 프로토콜을 정의합니다.

```yaml
collaboration_matrix:
  strategy_agent:
    primary_collaborations:
      - partner: data_agent
        communication_protocol: "request_response"
        data_format: "json"
```

## 🛠️ 사용법

### 1. CLI 인터페이스 사용

```bash
cd management
python agent_management_system.py
```

대화형 메뉴에서 다음 작업을 수행할 수 있습니다:

1. **모든 에이전트 나열**: 구성된 모든 에이전트 목록
2. **에이전트 세부정보**: 특정 에이전트의 상세 정보
3. **에이전트 설정 검증**: 구성 오류 확인
4. **파일 소유자 확인**: 특정 파일의 소유 에이전트
5. **협업 관계 확인**: 두 에이전트 간 협업 세부사항
6. **시스템 개요**: 전체 시스템 상태
7. **관리 파일 추가**: 에이전트에 새 파일 할당
8. **협업 관계 업데이트**: 협업 설정 수정

### 2. 프로그래밍 인터페이스 사용

```python
from management.agent_management_system import AgentManagementSystem

# 관리 시스템 초기화
manager = AgentManagementSystem()

# 에이전트 협업자 조회
collaborators = manager.get_agent_collaborators("strategy_agent")

# 에이전트 관리 파일 조회
managed_files = manager.get_agent_managed_files("data_agent")

# 파일 소유자 확인
owner = manager.get_file_owner("Project/strategy/signal_generator.py")

# 협업 관계 확인
collab = manager.get_collaboration_details("strategy_agent", "data_agent")
```

## 🔧 관리 작업

### 새로운 에이전트 추가

1. `agent_interfaces.yaml`에 에이전트 정의 추가
2. `file_ownership.yaml`에 파일 소유권 추가
3. `collaboration_matrix.yaml`에 협업 관계 추가

### 협업 관계 수정

```python
manager.update_agent_collaborator(
    "strategy_agent",
    "new_partner_agent",
    {
        "purpose": "New collaboration purpose",
        "interface": "new_interface",
        "required_data": ["data1", "data2"]
    }
)
```

### 관리 파일 추가

```python
manager.add_managed_file(
    "strategy_agent",
    "Project/strategy/new_module.py",
    "New strategy module"
)
```

## 📊 시스템 검증

### 에이전트 설정 검증
각 에이전트의 구성이 올바른지 자동으로 확인합니다:

- 관리 파일 존재 여부
- 협업 파트너 유효성
- 파일 소유권 일관성

```python
validation = manager.validate_agent_setup("strategy_agent")
print(validation["issues"])  # 발견된 문제점 목록
```

### 시스템 개요 생성
전체 시스템의 상태를 요약합니다:

```python
overview = manager.get_system_overview()
print(f"총 에이전트: {overview['total_agents']}")
print(f"총 관리 파일: {overview['total_managed_files']}")
```

## 🔍 모니터링 및 디버깅

### 로그 확인
시스템은 모든 작업을 로그로 기록합니다:

```python
import logging
logging.basicConfig(level=logging.INFO)

# 구성 로딩, 업데이트 등의 로그가 출력됩니다
```

### 구성 파일 백업
중요한 변경 전에 구성 파일을 백업하는 것이 좋습니다:

```bash
cp config/agent_interfaces.yaml config/agent_interfaces.yaml.backup
cp config/file_ownership.yaml config/file_ownership.yaml.backup
cp config/collaboration_matrix.yaml config/collaboration_matrix.yaml.backup
```

## 🚀 모범 사례

1. **정기적인 검증**: `validate_agent_setup()`을 정기적으로 실행
2. **구성 백업**: 변경 전 구성 파일 백업
3. **점진적 변경**: 큰 변경사항은 단계별로 적용
4. **문서화**: 변경사항과 이유를 문서화
5. **테스트**: 변경 후 시스템 동작 확인

## 🔐 보안 고려사항

- API 자격증명은 별도 파일로 관리
- 파일 권한은 최소 필요 권한으로 설정
- 민감한 구성 변경은 승인 프로세스 필요
- 모든 변경사항은 감사 로그에 기록

## 📞 문제 해결

### 일반적인 문제

1. **구성 파일 로딩 실패**
   - 파일 경로 확인
   - YAML 문법 검증

2. **에이전트 검증 실패**
   - 관리 파일 경로 확인
   - 협업 파트너 존재 확인

3. **협업 관계 오류**
   - 인터페이스 파일 존재 확인
   - 통신 프로토콜 호환성 확인