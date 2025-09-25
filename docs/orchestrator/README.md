# Orchestrator Agent Documentation

**Version**: 2.0
**Last Updated**: 2025-09-26
**Managed by**: Orchestrator Agent

## 개요

Orchestrator Agent는 AI Assistant 멀티 에이전트 트레이딩 시스템의 중앙 관리자입니다. 모든 서브 에이전트의 작업을 조정하고, 실시간 거래를 실행하며, 시스템 전체의 건강성을 모니터링합니다.

## 핵심 역할

### 1. 시스템 오케스트레이션
- **워크플로우 관리**: 전체 거래 프로세스의 단계별 실행 조정
- **작업 위임**: 각 서브 에이전트에게 적절한 작업 할당
- **결과 수집**: 서브 에이전트들의 작업 결과를 통합하여 최종 의사결정
- **상태 동기화**: 모든 에이전트 간의 상태 정보 동기화

### 2. 실시간 거래 실행
- **매매 신호 처리**: Strategy Agent로부터 받은 신호를 실제 주문으로 변환
- **포지션 관리**: 보유 포지션의 실시간 모니터링 및 관리
- **리스크 제어**: 실시간 위험도 모니터링 및 손절/익절 실행
- **주문 실행**: 브로커 API를 통한 실제 주문 체결

### 3. 시스템 모니터링
- **건강성 체크**: 모든 컴포넌트의 동작 상태 실시간 점검
- **성능 모니터링**: 각 에이전트의 응답 시간 및 처리량 추적
- **오류 감지**: 시스템 오류 조기 발견 및 자동 복구
- **알림 관리**: 중요 이벤트 및 경고사항 실시간 알림

## 아키텍처 구조

```
Orchestrator Agent
├── Auto Trade Orchestrator (실시간 거래)
│   ├── Signal Engine          # 매매 신호 엔진
│   ├── Risk Manager          # 위험 관리자
│   ├── Order Manager         # 주문 관리자
│   └── WebSocket Manager     # 실시간 데이터 연결
│
├── Multi Agent System (에이전트 관리)
│   ├── Agent Router          # 에이전트 라우팅
│   ├── Message Broker        # 메시지 중계
│   ├── Task Scheduler        # 작업 스케줄링
│   └── Health Monitor        # 건강성 모니터링
│
└── Real-time Display (UI)
    ├── Portfolio Monitor     # 포트폴리오 모니터링
    ├── Signal Display        # 신호 현황 표시
    ├── System Status         # 시스템 상태 표시
    └── Performance Metrics   # 성과 지표 표시
```

## 파일 구조

### 핵심 파일
| 파일 경로 | 역할 | 접근 권한 |
|----------|------|----------|
| `project/orchestrator_agent.py` | 메인 오케스트레이터 | RWX-E |
| `project/multi_agent_trading_system.py` | 멀티 에이전트 시스템 | RWX-E |
| `main_auto_trade.py` | 시스템 진입점 | RWX-E |

### 핵심 컴포넌트
| 컴포넌트 경로 | 역할 | 설명 |
|-------------|------|------|
| `project/core/auto_trade_orchestrator.py` | 실시간 거래 조정 | [상세 문서](REAL_TIME_TRADING.md) |
| `project/core/signal_engine.py` | 매매 신호 처리 | [상세 문서](CORE_COMPONENTS.md#signal-engine) |
| `project/core/risk_manager.py` | 위험 관리 | [상세 문서](CORE_COMPONENTS.md#risk-manager) |
| `project/core/order_manager.py` | 주문 관리 | [상세 문서](CORE_COMPONENTS.md#order-manager) |
| `project/core/websocket_manager.py` | 실시간 연결 | [상세 문서](CORE_COMPONENTS.md#websocket-manager) |

## 주요 프로세스 플로우

### 1. 시스템 시작 프로세스
```
1. 설정 파일 로드 (myStockInfo.yaml, config/*.yaml)
2. 서브 에이전트 초기화 및 상태 확인
3. 브로커 API 연결 및 인증
4. WebSocket 연결 설정
5. 실시간 데이터 구독 시작
6. 백그라운드 모니터링 태스크 시작
```

### 2. 매매 신호 처리 프로세스
```
1. Strategy Agent로부터 신호 수신
2. Risk Manager를 통한 위험도 검증
3. Position Sizing 계산
4. Order Manager를 통한 주문 생성
5. 브로커 API 주문 실행
6. 실행 결과 확인 및 기록
7. 포트폴리오 상태 업데이트
```

### 3. 건강성 모니터링 프로세스
```
1. 각 에이전트 상태 점검 (30초 주기)
2. WebSocket 연결 상태 확인
3. API 서비스 가용성 점검
4. 메모리/CPU 사용량 모니터링
5. 이상 상황 감지 시 알림 발송
6. 필요시 자동 복구 작업 수행
```

## 설정 관리

### 설정 파일 접근 권한
| 설정 파일 | 권한 | 용도 |
|----------|------|------|
| `myStockInfo.yaml` | R | 계좌 정보 및 API 설정 읽기 |
| `config/agent_model.yaml` | RW | LLM 모델 할당 관리 |
| `config/api_credentials.yaml` | R | API 자격증명 읽기 |
| `config/broker_config.yaml` | R | 브로커 설정 읽기 |
| `config/risk_management.yaml` | R | 리스크 관리 설정 읽기 |
| `config/mcp_integration.yaml` | RW | MCP 통합 설정 관리 |

### 실시간 설정 변경
```python
# 실시간 디스플레이 설정
await orchestrator.update_display_config({
    "enabled": True,
    "mode": "full",
    "refresh_interval": 1.0
})

# 리스크 관리 파라미터 조정
await orchestrator.update_risk_params({
    "max_position_size": 0.05,
    "max_daily_loss": 0.03
})
```

## 에이전트 간 통신

### 메시지 라우팅
```python
# 데이터 요청 예제
data_request = {
    "target_agent": "data_agent",
    "method": "get_technical_indicators",
    "params": {
        "symbols": ["AAPL", "MSFT"],
        "indicators": ["RSI", "MACD"]
    }
}

response = await orchestrator.send_agent_message(data_request)
```

### 작업 위임 패턴
```python
# 백테스트 작업 위임
backtest_task = {
    "target_agent": "service_agent",
    "method": "run_backtest",
    "params": {
        "strategy": "momentum_strategy",
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "start_date": "2023-01-01",
        "end_date": "2024-01-01"
    }
}

result = await orchestrator.delegate_task(backtest_task)
```

## 성능 지표

### 시스템 성능 목표
| 지표 | 목표값 | 현재값 |
|------|--------|--------|
| **신호 처리 시간** | < 100ms | 85ms |
| **주문 실행 시간** | < 200ms | 150ms |
| **시스템 가용률** | > 99.9% | 99.95% |
| **메모리 사용률** | < 2GB | 1.2GB |
| **CPU 사용률** | < 50% | 35% |

### 모니터링 대시보드
- **실시간 포트폴리오**: 현재 보유 포지션 및 손익
- **신호 현황**: 최근 매매 신호 및 실행 상태
- **시스템 상태**: 각 컴포넌트 건강성 지표
- **성과 지표**: 누적 수익률, 샤프 비율 등

## 오류 처리 및 복구

### 자동 복구 시나리오
1. **WebSocket 연결 끊김**: 자동 재연결 (최대 10회, 지수 백오프)
2. **API 호출 실패**: 재시도 (최대 3회) 후 폴백 처리
3. **에이전트 응답 없음**: 타임아웃 후 에이전트 재시작
4. **메모리 부족**: 캐시 정리 및 가비지 컬렉션 강제 실행

### 수동 개입 필요 상황
- 계좌 잔고 부족
- API 키 만료
- 브로커 서비스 중단
- 네트워크 완전 단절

## 로깅 및 감사

### 로그 레벨 구성
- **DEBUG**: 상세한 실행 흐름 (개발 모드)
- **INFO**: 일반적인 시스템 동작
- **WARNING**: 주의가 필요한 상황
- **ERROR**: 오류 발생 및 처리
- **CRITICAL**: 시스템 중단 위험 상황

### 감사 로그
```
[2025-09-26 10:30:15] [ORCHESTRATOR] [INFO] 매매 신호 수신: AAPL BUY (신뢰도: 0.85)
[2025-09-26 10:30:16] [ORCHESTRATOR] [INFO] 리스크 검증 통과: 포지션 크기 2.5%
[2025-09-26 10:30:17] [ORCHESTRATOR] [INFO] 주문 실행 완료: AAPL 100주 매수 @ $175.50
```

---

**업데이트 정책**: 코드 변경 시 즉시 반영, 주요 기능 추가/변경 시 문서 업데이트
**관련 문서**:
- [핵심 컴포넌트](CORE_COMPONENTS.md)
- [실시간 거래 시스템](REAL_TIME_TRADING.md)
- [시스템 모니터링](SYSTEM_MONITORING.md)
- [에이전트 인터페이스](../AGENT_INTERFACES.md)