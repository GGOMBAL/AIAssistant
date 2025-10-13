# File Access Permissions Matrix

**Version**: 2.0
**Last Updated**: 2025-09-26
**Managed by**: Orchestrator Agent

## 개요

본 문서는 각 에이전트의 파일 시스템 접근 권한을 정의합니다. 모든 에이전트는 할당된 권한 내에서만 파일을 읽고 쓸 수 있으며, 보안과 시스템 안정성을 위해 엄격히 관리됩니다.

## 권한 유형 정의

| 권한 유형 | 기호 | 설명 |
|----------|------|------|
| **READ** | R | 파일 읽기 전용 |
| **WRITE** | W | 파일 쓰기 가능 |
| **EXECUTE** | X | 파일 실행 가능 |
| **EXCLUSIVE** | E | 독점적 접근 (다른 에이전트 접근 불가) |
| **SHARED** | S | 공유 접근 (지정된 에이전트들과 공유) |
| **NONE** | - | 접근 불가 |

## Agent별 파일 접근 권한

### 1. Orchestrator Agent (오케스트레이터)

**역할**: 시스템 전체 관리 및 조정

| 경로 | 권한 | 공유 대상 | 비고 |
|------|------|-----------|------|
| `project/core/` | RWX-E | 없음 | 핵심 시스템 관리 |
| `project/orchestrator_agent.py` | RWX-E | 없음 | 메인 오케스트레이터 |
| `project/multi_agent_trading_system.py` | RWX-E | 없음 | 시스템 통합 |
| `main_auto_trade.py` | RWX-E | 없음 | 메인 실행 파일 |
| `config/*.yaml` | R-S | All Agents | 모든 설정 읽기 |
| `docs/*.md` | RW-S | All Agents | 문서 관리 |
| `logs/orchestrator.log` | RW-E | 없음 | 오케스트레이터 로그 |
| `project/ui/` | RW-S | Service Agent | 실시간 디스플레이 |

### 2. Data Agent (데이터 에이전트)

**역할**: 데이터 수집, 처리, 기술지표 계산

| 경로 | 권한 | 공유 대상 | 비고 |
|------|------|-----------|------|
| `project/data_agent.py` | RWX-E | 없음 | 메인 데이터 에이전트 |
| `project/indicator/` | RWX-E | 없음 | 기술지표 계산 모듈 |
| `project/database/` | RWX-S | Service Agent | 데이터베이스 관리 |
| `project/router/data_agent_router.py` | RWX-E | 없음 | 데이터 에이전트 라우터 |
| `logs/data_agent.log` | RW-E | 없음 | 데이터 에이전트 로그 |
| `config/broker_config.yaml` | R-S | Service Agent | 시장 데이터 설정 |
| `project/models/trading_models.py` | R-S | All Agents | 데이터 모델 정의 |

#### MongoDB 데이터베이스 접근 권한

| 데이터베이스 | 권한 | 공유 대상 | 용도 |
|-------------|------|-----------|------|
| `NasDataBase_D` | RW-S | Service Agent | 나스닥 일봉 데이터 |
| `NysDataBase_D` | RW-S | Service Agent | NYSE 일봉 데이터 |
| `NasDataBase_M` | RW-S | Service Agent | 나스닥 분봉 데이터 |
| `NysDataBase_M` | RW-S | Service Agent | NYSE 분봉 데이터 |

### 3. Strategy Agent (전략 에이전트)

**역할**: 전략 개발 및 신호 생성

| 경로 | 권한 | 공유 대상 | 비고 |
|------|------|-----------|------|
| `project/strategy_agent.py` | RWX-E | 없음 | 메인 전략 에이전트 |
| `project/strategy/` | RWX-E | 없음 | 전략 구현체들 |
| `project/core/strategy_integration_service.py` | RW-S | Orchestrator | 전략 통합 서비스 |
| `project/router/strategy_agent_router.py` | RWX-E | 없음 | 전략 에이전트 라우터 |
| `logs/strategy_agent.log` | RW-E | 없음 | 전략 에이전트 로그 |
| `config/risk_management.yaml` | R-S | Service Agent | 리스크 관리 설정 |
| `project/models/trading_models.py` | R-S | All Agents | 신호 모델 정의 |

#### 전략별 세부 권한

| 전략 파일 | 권한 | 설명 |
|----------|------|------|
| `project/strategy/signal_generation_service.py` | RWX-E | 신호 생성 서비스 |
| `project/strategy/position_sizing_service.py` | RW-S | 포지션 사이징 (Service Agent 공유) |
| `project/strategy/account_analysis_service.py` | RW-S | 계좌 분석 (Service Agent 공유) |

### 4. Service Agent (서비스 에이전트)

**역할**: 백테스트, 실행, 데이터베이스 관리

| 경로 | 권한 | 공유 대상 | 비고 |
|------|------|-----------|------|
| `project/service_agent.py` | RWX-E | 없음 | 메인 서비스 에이전트 |
| `project/service/` | RWX-E | 없음 | 서비스 구현체들 |
| `project/database/` | RW-S | Data Agent | 데이터베이스 관리 공유 |
| `project/router/service_agent_router.py` | RWX-E | 없음 | 서비스 에이전트 라우터 |
| `logs/service_agent.log` | RW-E | 없음 | 서비스 에이전트 로그 |
| `config/broker_config.yaml` | R-S | Data Agent | 브로커 설정 읽기 |
| `config/risk_management.yaml` | R-S | Strategy Agent | 리스크 관리 읽기 |
| `project/ui/` | R-S | Orchestrator | 실시간 디스플레이 읽기 |

#### 서비스별 세부 권한

| 서비스 파일 | 권한 | 공유 대상 | 설명 |
|------------|------|-----------|------|
| `project/service/backtest_engine.py` | RWX-E | 없음 | 백테스트 엔진 |
| `project/service/execution_services.py` | RWX-E | 없음 | 실행 서비스 |
| `project/service/performance_analyzer.py` | RWX-E | 없음 | 성과 분석 |
| `project/service/live_price_service.py` | RW-S | Orchestrator | 실시간 가격 서비스 |
| `project/service/api_order_service.py` | RW-S | Orchestrator | API 주문 서비스 |
| `project/service/account_analysis_service.py` | RW-S | Orchestrator | 계좌 분석 서비스 |

### 5. Helper Agent (헬퍼 에이전트)

**역할**: 외부 API 연동 및 브로커 접속

| 경로 | 권한 | 공유 대상 | 비고 |
|------|------|-----------|------|
| `project/helper_agent.py` | RWX-E | 없음 | 메인 헬퍼 에이전트 |
| `project/Helper/` | RWX-E | 없음 | 외부 API 연동 모듈 |
| `project/router/helper_agent_router.py` | RWX-E | 없음 | 헬퍼 에이전트 라우터 |
| `myStockInfo.yaml` | RWX-E | 없음 | API 키 및 계좌 정보 |
| `logs/helper_agent.log` | RW-E | 없음 | 헬퍼 에이전트 로그 |
| `config/api_credentials.yaml` | RWX-E | 없음 | API 자격증명 |

#### API 연동별 세부 권한

| API 파일 | 권한 | 설명 |
|----------|------|------|
| `project/Helper/kis_api_helper_us.py` | RWX-E | 한국투자증권 US API |
| `project/Helper/broker_api_connector.py` | RWX-E | 브로커 API 통합 |
| `project/Helper/yfinance_helper.py` | RWX-E | Yahoo Finance API |
| `project/Helper/telegram_messenger.py` | RWX-E | 텔레그램 메신저 |
| `project/Helper/data_provider_api.py` | RWX-E | 데이터 제공 API |

## 공유 인터페이스 파일

### 모든 에이전트가 읽기 가능한 파일

| 파일 경로 | 권한 | 목적 |
|----------|------|------|
| `project/interfaces/service_interfaces.py` | R | 서비스 인터페이스 정의 |
| `project/models/trading_models.py` | R | 데이터 모델 정의 |
| `project/models/__init__.py` | R | 모델 패키지 초기화 |
| `CLAUDE.md` | R | 프로젝트 규칙 및 가이드라인 |
| `README.md` | R | 프로젝트 개요 |

### 설정 파일 접근 권한

| 설정 파일 | Orchestrator | Data | Strategy | Service | Helper |
|-----------|-------------|------|----------|---------|--------|
| `config/api_credentials.yaml` | R | - | - | - | RW |
| `config/broker_config.yaml` | R | R | - | R | - |
| `config/risk_management.yaml` | R | - | R | R | - |
| `config/agent_model.yaml` | RW | R | R | R | R |
| `config/mcp_integration.yaml` | RW | R | R | R | R |
| `myStockInfo.yaml` | R | - | - | - | RW |

## 임시 파일 및 캐시

### 에이전트별 임시 디렉토리

| 에이전트 | 임시 디렉토리 | 권한 | 자동 정리 |
|----------|--------------|------|-----------|
| **Orchestrator** | `temp/orchestrator/` | RWX-E | 24시간 |
| **Data Agent** | `temp/data/` | RWX-E | 1시간 |
| **Strategy Agent** | `temp/strategy/` | RWX-E | 24시간 |
| **Service Agent** | `temp/service/` | RWX-E | 1주일 |
| **Helper Agent** | `temp/helper/` | RWX-E | 1시간 |

## 권한 위반 처리

### 보안 위반 감지
1. **무단 접근 시도**: 즉시 로그 기록 및 알림
2. **권한 초과 행위**: 해당 작업 차단 및 에러 반환
3. **중요 파일 변경**: 백업에서 자동 복원

### 복구 절차
1. 권한 위반 감지 시 해당 에이전트 일시 중단
2. 시스템 상태 점검 및 무결성 검증
3. 필요시 백업에서 파일 복원
4. 에이전트 재시작 및 정상 동작 확인

## 백업 및 버전 관리

### 자동 백업 대상
- 모든 설정 파일 (`config/*.yaml`, `myStockInfo.yaml`)
- 전략 파일 (`project/strategy/`)
- 로그 파일 (최근 30일)
- 데이터베이스 스키마 정보

### 버전 관리 규칙
- 모든 코드 변경사항은 Git으로 관리
- 설정 파일 변경 시 백업 생성
- 중요 변경사항은 태그로 마킹

## 모니터링 및 감사

### 파일 접근 로깅
```
[2025-09-26 10:30:15] [DATA_AGENT] READ project/database/mongodb_operations.py SUCCESS
[2025-09-26 10:30:16] [STRATEGY_AGENT] WRITE project/strategy/custom_strategy.py SUCCESS
[2025-09-26 10:30:17] [HELPER_AGENT] READ config/api_credentials.yaml SUCCESS
```

### 권한 감사 리포트
- 일간 파일 접근 통계
- 권한 위반 시도 횟수
- 비정상적인 파일 접근 패턴
- 미사용 권한 목록

---

**보안 정책**: 이 권한 매트릭스는 시스템 보안의 핵심입니다. 무단 수정을 엄격히 금지합니다.
**업데이트 주기**: 새로운 에이전트나 파일 추가 시 즉시 업데이트
**책임자**: Orchestrator Agent가 이 문서를 관리하고 권한을 감시합니다.