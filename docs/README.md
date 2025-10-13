# AI Assistant Documentation System

**Version**: 2.1
**Last Updated**: 2025-10-06
**Managed by**: Orchestrator Agent

---

## 📚 Documentation Index

This directory contains all technical documentation for the AI Assistant Multi-Agent Trading System.

### 🔗 Key Documents

#### **Interface Documentation** (핵심 인터페이스 문서)
1. **[INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md)** - 레이어 간 데이터 인터페이스
   - Indicator Layer → Strategy Layer 데이터 형식
   - Strategy Layer 출력 형식 (df_dump, Universe)
   - 표준 데이터 타입 및 검증 규칙

2. **[DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md)** - 데이터 레이어 간 컬럼 표준
   - Market DB → Indicator Layer 컬럼 스펙 (before_TRD.json)
   - Indicator Layer → Strategy Layer 컬럼 스펙 (after_TRD.json)
   - df_D, df_W, df_RS, df_E, df_F 각 데이터의 컬럼 명세
   - Indicator Layer에서 추가되는 계산 컬럼 정의

3. **[AGENT_INTERFACES.md](AGENT_INTERFACES.md)** - 에이전트 간 통신 프로토콜
   - 메시지 구조 (Request/Response)
   - RPC 및 이벤트 기반 통신
   - 오류 처리 및 재시도 로직

4. **[REQUEST_TYPE_SYSTEM.md](REQUEST_TYPE_SYSTEM.md)** - Request Type 분류 시스템
   - EXECUTION vs CODE_MODIFICATION 요청 구분
   - Layer Architecture 기반 코드 수정
   - Agent별 프롬프트 생성 전략

5. **[SIGNAL_TIMELINE_FEATURE.md](SIGNAL_TIMELINE_FEATURE.md)** - Signal Timeline 기능 (신규)
   - 개별 티커 W/D/RS/E/F 시그널 타임라인 표시
   - 사용자 인터랙티브 종목/기간 선택
   - Staged Pipeline 통합 및 데이터 구조 변환
   - 타임라인 시각화 출력

**연계 관계**:
```
AGENT_INTERFACES.md     ←→  INTERFACE_SPECIFICATION.md  ←→  DATA_LAYER_INTERFACES.md
(통신 프로토콜)              (데이터 구조)                   (컬럼 스펙)
     ↓                           ↓                              ↓
에이전트 간 메시지         레이어 간 데이터 교환           Market DB → Indicator → Strategy
RPC 스타일 호출          DataFrame/Dict 형식            컬럼명 및 타입 정의
```

#### **Architecture & System** (아키텍처 & 시스템)
5. **[architecture/ARCHITECTURE_OVERVIEW.md](architecture/ARCHITECTURE_OVERVIEW.md)** - 시스템 아키텍처
6. **[architecture/DATABASE_ARCHITECTURE.md](architecture/DATABASE_ARCHITECTURE.md)** - MongoDB 구조
7. **[HELPER_FUNCTIONS_MANUAL.md](HELPER_FUNCTIONS_MANUAL.md)** - Helper 유틸리티

**전체 아키텍처 문서**: [architecture/](architecture/) 폴더 참조

---

## 🎯 빠른 네비게이션

### 작업별 참조 문서

| 하고 싶은 작업 | 참조 문서 |
|-------------|---------|
| 시스템 이해 | [architecture/ARCHITECTURE_OVERVIEW.md](architecture/ARCHITECTURE_OVERVIEW.md) → [CLAUDE.md](../CLAUDE.md) |
| 새 에이전트 구현 | [AGENT_INTERFACES.md](AGENT_INTERFACES.md) → [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md) |
| 데이터 작업 | [DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md) → [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md) → [architecture/DATABASE_ARCHITECTURE.md](architecture/DATABASE_ARCHITECTURE.md) |
| Indicator Layer 개발 | [DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md) → `refer/debug_json/*_before_TRD.json` |
| Strategy Layer 개발 | [DATA_LAYER_INTERFACES.md](DATA_LAYER_INTERFACES.md) → `refer/debug_json/*_after_TRD.json` |
| 코드 수정 요청 이해 | [REQUEST_TYPE_SYSTEM.md](REQUEST_TYPE_SYSTEM.md) → [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md) |
| 시스템 디버깅 | [AGENT_INTERFACES.md](AGENT_INTERFACES.md) → [architecture/ARCHITECTURE_OVERVIEW.md](architecture/ARCHITECTURE_OVERVIEW.md) |
| 시그널 타임라인 사용 | [SIGNAL_TIMELINE_FEATURE.md](SIGNAL_TIMELINE_FEATURE.md) → [AGENT_INTERFACES.md](AGENT_INTERFACES.md) |

---

## 📋 문서 계층 구조

본 문서 시스템은 계층적으로 구성되어 있으며, 각 에이전트가 담당하는 영역의 문서를 관리합니다.

```
docs/
├── README.md                         # 문서 시스템 개요 (이 파일)
├── AGENT_INTERFACES.md               # 에이전트 간 통신 프로토콜
├── INTERFACE_SPECIFICATION.md        # 레이어 간 데이터 인터페이스
├── DATA_LAYER_INTERFACES.md          # 데이터 레이어 간 컬럼 표준 (신규)
├── FILE_PERMISSIONS.md               # 파일 접근 권한 매트릭스
├── HELPER_FUNCTIONS_MANUAL.md        # Helper 유틸리티 함수
│
├── architecture/                     # 시스템 아키텍처 문서
│   ├── ARCHITECTURE_OVERVIEW.md      # 시스템 아키텍처 개요
│   ├── ARCHITECTURE.md               # 전체 시스템 아키텍처
│   ├── ARCHITECTURE_GUIDE.md         # 아키텍처 가이드
│   ├── DATABASE_ARCHITECTURE.md      # MongoDB 구조
│   ├── MULTI_AGENT_SYSTEM_ARCHITECTURE.md    # 멀티 에이전트 시스템
│   ├── UNIFIED_SYSTEM_ARCHITECTURE.md        # 통합 시스템 아키텍처
│   ├── DATA_AGENT_ARCHITECTURE.md            # Data Agent 아키텍처
│   ├── STRATEGY_AGENT_ARCHITECTURE.md        # Strategy Agent 아키텍처
│   ├── HELPER_AGENT_ARCHITECTURE.md          # Helper Agent 아키텍처
│   └── SERVICE_LAYER_BACKTEST_ARCHITECTURE.md # 백테스트 아키텍처
│
├── orchestrator/                     # Orchestrator Agent 문서
│   ├── README.md                     # 오케스트레이터 개요
│   ├── CORE_COMPONENTS.md            # 핵심 컴포넌트 문서
│   ├── REAL_TIME_TRADING.md          # 실시간 거래 시스템
│   └── SYSTEM_MONITORING.md          # 시스템 모니터링
│
├── data_agent/                       # Data Agent 문서
│   ├── README.md                     # 데이터 에이전트 개요
│   ├── DATA_SOURCES.md               # 데이터 소스 관리
│   ├── TECHNICAL_INDICATORS.md       # 기술지표 계산
│   └── DATABASE_SCHEMA.md            # 데이터베이스 스키마
│
├── strategy_agent/                   # Strategy Agent 문서
│   ├── README.md                     # 전략 에이전트 개요
│   ├── TRADING_STRATEGIES.md         # 매매 전략 목록
│   ├── SIGNAL_GENERATION.md          # 신호 생성 로직
│   └── BACKTESTING.md                # 백테스트 프레임워크
│
├── service_agent/                    # Service Agent 문서
│   ├── README.md                     # 서비스 에이전트 개요
│   ├── EXECUTION_SERVICES.md         # 실행 서비스
│   ├── PERFORMANCE_ANALYSIS.md       # 성과 분석
│   └── DATABASE_OPERATIONS.md        # 데이터베이스 운영
│
├── helper_agent/                     # Helper Agent 문서
│   ├── README.md                     # 헬퍼 에이전트 개요
│   ├── BROKER_APIS.md                # 브로커 API 연동
│   ├── EXTERNAL_APIS.md              # 외부 API 연동
│   └── NOTIFICATION_SYSTEM.md        # 알림 시스템
│
└── deployment/                       # 배포 및 운영 문서
    ├── SETUP_GUIDE.md                # 초기 설정 가이드
    ├── CONFIGURATION.md              # 설정 파일 가이드
    ├── TROUBLESHOOTING.md            # 문제 해결 가이드
    └── MAINTENANCE.md                # 유지보수 가이드
```

## 문서 관리 규칙

### 1. 문서 소유권

각 문서는 해당 에이전트가 관리하며, 다음 규칙을 따릅니다:

| 문서 디렉토리 | 관리 에이전트 | 접근 권한 |
|--------------|--------------|-----------|
| `docs/` | Orchestrator | RW (전체 관리) |
| `docs/orchestrator/` | Orchestrator | RWX-E |
| `docs/data_agent/` | Data Agent | RWX-E |
| `docs/strategy_agent/` | Strategy Agent | RWX-E |
| `docs/service_agent/` | Service Agent | RWX-E |
| `docs/helper_agent/` | Helper Agent | RWX-E |
| `docs/deployment/` | Orchestrator | RW-S (모든 에이전트 읽기) |

### 2. 문서 작성 표준

모든 문서는 다음 형식을 따라야 합니다:

```markdown
# 문서 제목

**Version**: X.Y
**Last Updated**: YYYY-MM-DD
**Managed by**: [Agent Name]

## 개요
[문서 목적 및 범위]

## 내용
[실제 내용]

---
**업데이트 정책**: [업데이트 주기 및 조건]
**관련 문서**: [연관된 다른 문서들]
```

### 3. 문서 상호 참조

문서 간 참조는 상대 경로를 사용합니다:

```markdown
# 올바른 참조 방법
[아키텍처 개요](../ARCHITECTURE.md)
[데이터 소스](../data_agent/DATA_SOURCES.md)

# 잘못된 참조 방법 (절대 경로 사용 금지)
[아키텍처](/docs/ARCHITECTURE.md)
```

## 에이전트별 문서 영역

### Orchestrator Agent 문서 영역

**관리 범위**: 시스템 전체 관리 및 조정
- 핵심 시스템 컴포넌트 (`project/core/`)
- 실시간 거래 시스템
- 시스템 모니터링 및 건강성 체크
- 전체 시스템 아키텍처

**핵심 문서**:
- `CORE_COMPONENTS.md`: SignalEngine, RiskManager, OrderManager 등
- `REAL_TIME_TRADING.md`: 실시간 거래 실행 로직
- `SYSTEM_MONITORING.md`: 건강성 체크 및 모니터링

### Data Agent 문서 영역

**관리 범위**: 데이터 수집, 처리, 기술지표
- MongoDB 데이터베이스 관리
- 기술지표 계산 알고리즘
- 데이터 품질 관리
- 외부 데이터 소스 연동

**핵심 문서**:
- `DATA_SOURCES.md`: MongoDB, 외부 API 데이터 소스
- `TECHNICAL_INDICATORS.md`: RSI, MACD, 볼린저 밴드 등
- `DATABASE_SCHEMA.md`: 데이터베이스 구조 및 스키마

### Strategy Agent 문서 영역

**관리 범위**: 전략 개발 및 신호 생성
- 매매 전략 알고리즘
- 신호 생성 로직
- 백테스트 프레임워크
- 전략 성과 평가

**핵심 문서**:
- `TRADING_STRATEGIES.md`: 모든 매매 전략 목록 및 설명
- `SIGNAL_GENERATION.md`: 매매 신호 생성 알고리즘
- `BACKTESTING.md`: 백테스트 실행 및 검증 방법

### Service Agent 문서 영역

**관리 범위**: 백테스트, 실행, 데이터베이스 관리
- 백테스트 엔진
- 실행 서비스
- 성과 분석 도구
- 데이터베이스 운영

**핵심 문서**:
- `EXECUTION_SERVICES.md`: 주문 실행 및 포지션 관리
- `PERFORMANCE_ANALYSIS.md`: 수익률, 위험도 분석
- `DATABASE_OPERATIONS.md`: DB 쿼리, 인덱싱, 백업

### Helper Agent 문서 영역

**관리 범위**: 외부 API 및 브로커 연결
- 브로커 API 연동 (KIS, LS증권)
- 외부 데이터 API (Alpha Vantage, Yahoo Finance)
- 알림 시스템 (텔레그램)
- API 키 관리

**핵심 문서**:
- `BROKER_APIS.md`: KIS, LS증권 API 연동 방법
- `EXTERNAL_APIS.md`: 외부 데이터 소스 API
- `NOTIFICATION_SYSTEM.md`: 텔레그램 알림 설정

## 자동 문서 생성

### 코드 문서화
```python
def generate_api_docs():
    """
    코드에서 자동으로 API 문서 생성
    - 함수 시그니처 추출
    - docstring 파싱
    - 타입 힌트 정보 수집
    """
    pass
```

### 설정 문서화
```python
def generate_config_docs():
    """
    설정 파일에서 자동으로 설정 문서 생성
    - YAML 파일 파싱
    - 설정 옵션 설명 추출
    - 기본값 및 예제 생성
    """
    pass
```

## 문서 품질 관리

### 문서 검토 체크리스트
- [ ] 문서 헤더 정보 완성 (버전, 날짜, 관리자)
- [ ] 개요 섹션 명확성
- [ ] 코드 예제 동작 확인
- [ ] 상호 참조 링크 유효성
- [ ] 마크다운 문법 준수
- [ ] 스크린샷 및 다이어그램 최신성

### 자동 문서 검증
```bash
# 문서 링크 확인
./scripts/check_docs_links.sh

# 문서 형식 검증
./scripts/validate_docs_format.sh

# 코드 예제 테스트
./scripts/test_docs_examples.sh
```

## 문서 업데이트 정책

### 자동 업데이트 트리거
- 코드 변경 시 관련 문서 자동 업데이트 제안
- 새로운 함수/클래스 추가 시 문서 템플릿 생성
- 설정 파일 변경 시 설정 문서 업데이트

### 수동 업데이트 주기
| 문서 유형 | 업데이트 주기 | 책임자 |
|----------|--------------|--------|
| **아키텍처 문서** | 분기별 | Orchestrator |
| **인터페이스 문서** | 월별 | 모든 에이전트 |
| **API 문서** | 주간 | 해당 에이전트 |
| **설정 가이드** | 설정 변경 시 즉시 | Helper Agent |
| **문제해결 가이드** | 새로운 이슈 발생 시 | 관련 에이전트 |

## 문서 액세스 방법

### Orchestrator Agent에서 문서 로드
```python
class DocumentationManager:
    def __init__(self):
        self.docs_path = "docs/"
        self.agent_docs = {
            "orchestrator": "orchestrator/",
            "data_agent": "data_agent/",
            "strategy_agent": "strategy_agent/",
            "service_agent": "service_agent/",
            "helper_agent": "helper_agent/"
        }

    def load_agent_docs(self, agent_name: str) -> Dict[str, str]:
        """특정 에이전트의 모든 문서 로드"""
        pass

    def search_docs(self, query: str) -> List[Dict[str, str]]:
        """문서 내용 검색"""
        pass

    def validate_doc_links(self) -> Dict[str, Any]:
        """문서 간 링크 유효성 검사"""
        pass
```

### CLI를 통한 문서 접근
```bash
# 전체 문서 구조 보기
python -m docs.viewer --structure

# 특정 에이전트 문서 보기
python -m docs.viewer --agent data_agent

# 문서 검색
python -m docs.viewer --search "WebSocket"

# 문서 유효성 검사
python -m docs.validator --check-all
```

---

**문서 시스템 목적**: 시스템의 모든 지식을 체계적으로 관리하고 에이전트가 언제든 참조할 수 있도록 합니다.
**유지보수**: 각 에이전트는 자신이 관리하는 영역의 문서를 최신 상태로 유지할 책임이 있습니다.
**확장성**: 새로운 에이전트나 기능 추가 시 해당 문서도 함께 생성하여 시스템 문서의 완전성을 보장합니다.