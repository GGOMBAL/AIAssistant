# Migration Guide: Project Structure Reorganization

**Version**: 2.1
**Date**: 2025-09-26
**Managed by**: Orchestrator Agent

## 개요

프로젝트 구조가 대폭 정리되고 개선되었습니다. 이 문서는 변경사항과 새로운 구조를 설명합니다.

## 🔄 주요 변경사항

### 1. Agent 파일 재구성

**변경 전**:
```
project/
├── orchestrator_agent.py
├── data_agent.py
├── strategy_agent.py
├── service_agent.py
├── helper_agent.py
└── multi_agent_trading_system.py
```

**변경 후**:
```
agents/
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator_agent.py
├── data_agent/
│   ├── __init__.py
│   └── data_agent.py
├── strategy_agent/
│   ├── __init__.py
│   └── strategy_agent.py
├── service_agent/
│   ├── __init__.py
│   └── service_agent.py
└── helper_agent/
    ├── __init__.py
    └── helper_agent.py
```

### 2. 시스템 통합

**DEPRECATED 파일**: `project/multi_agent_trading_system.py`
- 더 이상 사용되지 않음
- 실시간 거래 시스템으로 통합됨

**메인 시스템**: `main_auto_trade.py`
- 실시간 자동매매 시스템
- AutoTradeOrchestrator 기반
- WebSocket 실시간 데이터
- 통합 리스크 관리

### 3. 불필요한 파일 제거

**제거된 파일들**:
- `project/integrated_backtest_runner.py`
- `project/mongodb_integrated_backtest.py`
- `project/simple_integrated_backtest.py`
- `project/simple_technical_indicators.py`
- `project/test_phase1_integration.py`
- `project/test_phase1_simple.py`
- `project/test_phase2_integration.py`
- `project/service/backtest_service_20250920_234946.py`
- `project/service/integration_test.py`

**제거 이유**: 중복 기능, 테스트 전용, 또는 더 나은 구현체로 대체

## 🚀 새로운 실행 방법

### 실시간 자동매매 시스템 실행
```bash
python main_auto_trade.py
```

**시스템 특징**:
- ✅ 실시간 거래 실행
- ✅ WebSocket 기반 실시간 데이터 스트리밍
- ✅ 통합된 리스크 관리
- ✅ 실시간 포트폴리오 모니터링
- ✅ 체계화된 멀티 에이전트 아키텍처

### 구 시스템 실행 시도 시
```bash
python project/multi_agent_trading_system.py
```
**결과**: DEPRECATED 메시지 출력 후 종료

## 📊 아키텍처 비교

### 구 시스템 (DEPRECATED)
```
OrchestratorAgent
├── 백테스트 중심
├── 과거 데이터만 처리
├── 콘솔 기반 UI
└── 수동 에이전트 관리
```

### 신 시스템 (현재)
```
AutoTradeOrchestrator
├── 실시간 거래 중심
├── WebSocket + MongoDB
├── 실시간 디스플레이 UI
└── 자동화된 에이전트 협업
```

## 🔧 개발자 가이드

### Import 경로 변경

**변경 전**:
```python
from orchestrator_agent import OrchestratorAgent
from data_agent import DataAgent
```

**변경 후**:
```python
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
from agents.data_agent.data_agent import DataAgent
```

### 시스템 초기화 변경

**변경 전**:
```python
orchestrator = OrchestratorAgent()
```

**변경 후**:
```python
from project.core.auto_trade_orchestrator import AutoTradeOrchestrator
orchestrator = AutoTradeOrchestrator(config)
```

## 📁 새로운 디렉토리 구조

```
AIAssistant/
├── main_auto_trade.py                    # 메인 실행 파일
├── agents/                               # 에이전트 모듈들
│   ├── orchestrator/
│   ├── data_agent/
│   ├── strategy_agent/
│   ├── service_agent/
│   └── helper_agent/
├── project/
│   ├── core/                            # 핵심 시스템 컴포넌트
│   │   ├── auto_trade_orchestrator.py
│   │   ├── signal_engine.py
│   │   ├── risk_manager.py
│   │   ├── order_manager.py
│   │   └── websocket_manager.py
│   ├── service/                         # 서비스 레이어
│   ├── database/                        # 데이터베이스 관리
│   ├── ui/                             # 사용자 인터페이스
│   └── models/                         # 데이터 모델
├── docs/                               # 문서
├── config/                             # 설정 파일
└── logs/                              # 로그 파일
```

## ⚠️ 주의사항

### 1. Deprecated 파일 사용 금지
- `project/multi_agent_trading_system.py` 사용 중단
- 관련 import 제거 필요

### 2. 새로운 Import 경로 적용
- 에이전트 파일들이 `agents/` 디렉토리로 이동
- 각 에이전트는 개별 패키지로 구성

### 3. 설정 파일 확인
- `myStockInfo.yaml` 설정 검증
- `config/` 디렉토리 설정 파일들 확인

## 🔄 Migration 체크리스트

- [ ] 기존 코드에서 deprecated import 제거
- [ ] 새로운 agent 경로로 import 수정
- [ ] `main_auto_trade.py` 실행 테스트
- [ ] 설정 파일 검증
- [ ] 실시간 거래 시스템 동작 확인
- [ ] 문서 업데이트
- [ ] 팀원들에게 변경사항 공지

## 🆘 문제 해결

### Import 오류 시
```python
# 잘못된 경우
from orchestrator_agent import OrchestratorAgent  # 파일 없음

# 올바른 경우
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
```

### 실행 오류 시
```bash
# 구 시스템 실행 시도 (작동 안 함)
python project/multi_agent_trading_system.py

# 신 시스템 실행 (정상 작동)
python main_auto_trade.py
```

### 설정 오류 시
- `myStockInfo.yaml` 파일 존재 확인
- API 키 설정 검증
- MongoDB 연결 정보 확인

---

**마이그레이션 완료 후**: 더 안정적이고 강력한 실시간 자동매매 시스템을 사용할 수 있습니다!

**지원**: 문제 발생 시 `docs/` 디렉토리의 관련 문서를 참조하거나 이슈를 보고하세요.