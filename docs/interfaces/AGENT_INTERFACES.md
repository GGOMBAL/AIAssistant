# Agent Interface Standardization

**Version**: 2.1
**Last Updated**: 2025-10-06
**Managed by**: Orchestrator Agent

**Related Documentation**:
- [Interface Specification](INTERFACE_SPECIFICATION.md) - Data structure interfaces between layers
- [Data Layer Interfaces](DATA_LAYER_INTERFACES.md) - Column specifications for data layers
- [CLAUDE.md](../CLAUDE.md) - Project rules and standards
- [Database Architecture](architecture/DATABASE_ARCHITECTURE.md) - MongoDB data structures

## 개요

본 문서는 멀티 에이전트 시스템 내에서 에이전트 간 표준화된 **통신 프로토콜**을 정의합니다. 모든 에이전트는 이 인터페이스를 통해서만 상호작용하며, 시스템의 일관성과 확장성을 보장합니다.

### 관련 문서와의 연계

이 문서는 **에이전트 간 통신(RPC, 메시지 전달)**을 정의하며, [INTERFACE_SPECIFICATION.md](INTERFACE_SPECIFICATION.md)는 **데이터 구조(DataFrame, Dict 형식)**를 정의합니다.

```
[Data Agent] ──(AGENT_INTERFACES.md)──→ [Strategy Agent]
      ↓                                        ↓
  df_D, df_W, df_RS              BuySig, SellSig, TargetPrice
  (INTERFACE_SPECIFICATION.md)   (INTERFACE_SPECIFICATION.md)
```

## 표준 통신 프로토콜

### 1. 메시지 구조

#### 요청 메시지 (Request Message)
```python
{
    "message_id": str,          # 고유 메시지 ID (UUID)
    "sender_agent": str,        # 발신자 에이전트 ID
    "receiver_agent": str,      # 수신자 에이전트 ID
    "method": str,              # 호출할 메서드명
    "params": dict,             # 메서드 파라미터
    "timestamp": str,           # ISO 8601 형식
    "priority": int,            # 우선순위 (1: 높음, 3: 낮음)
    "timeout": int,             # 타임아웃 (초)
    "retry_count": int          # 재시도 횟수
}
```

#### 응답 메시지 (Response Message)
```python
{
    "message_id": str,          # 요청 메시지와 동일한 ID
    "sender_agent": str,        # 응답하는 에이전트 ID
    "receiver_agent": str,      # 원래 요청자 에이전트 ID
    "status": str,              # "success", "error", "timeout"
    "data": Any,                # 응답 데이터 (성공시)
    "error": dict,              # 오류 정보 (실패시)
    "timestamp": str,           # 응답 시각
    "execution_time": float     # 실행 시간 (초)
}
```

#### 오류 응답 구조
```python
{
    "error": {
        "code": str,            # 오류 코드 (예: "INVALID_PARAMS")
        "message": str,         # 사용자 친화적 오류 메시지
        "details": dict,        # 상세 오류 정보
        "traceback": str        # 스택 트레이스 (개발 모드)
    }
}
```

## Agent별 제공 인터페이스

### 2. Orchestrator Agent 인터페이스

#### 시스템 관리 메서드
```python
class OrchestratorInterface:

    async def start_trading_session(
        market: str = "US",
        mode: str = "live"  # "live", "simulation", "backtest"
    ) -> Dict[str, Any]:
        """거래 세션 시작"""
        pass

    async def stop_trading_session() -> Dict[str, Any]:
        """거래 세션 중지"""
        pass

    async def get_system_status() -> Dict[str, Any]:
        """시스템 전체 상태 조회"""
        pass

    async def execute_trading_signal(
        signal: TradingSignal
    ) -> Dict[str, Any]:
        """매매 신호 실행"""
        pass

    async def get_real_time_portfolio() -> Dict[str, Any]:
        """실시간 포트폴리오 조회"""
        pass

    async def show_ticker_signal_timeline(
        config: dict
    ) -> None:
        """개별 티커 시그널 타임라인 표시

        사용자 입력을 받아 특정 종목들의 W/D/RS/E/F 시그널을
        타임라인 형태로 표시합니다.

        Args:
            config: 시스템 설정 딕셔너리

        User Input:
            - symbols: 종목 코드 (쉼표로 구분, 예: AAPL,MSFT,GOOGL)
            - period: 분석 기간 (1=3개월, 2=6개월, 3=1년, 4=2년)

        Process:
            1. 사용자로부터 종목 코드 및 분석 기간 입력
            2. StagedPipelineService를 통해 데이터 로딩 및 시그널 생성
            3. 최근 100개 거래일의 시그널 타임라인 출력

        Output:
            각 종목별로 날짜/종가/W/D/RS/E/F 시그널을 테이블 형태로 표시
        """
        pass
```

#### 에이전트 관리 메서드
```python
    async def delegate_task(
        target_agent: str,
        task_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """서브 에이전트에게 작업 위임"""
        pass

    async def monitor_agent_health(
        agent_id: str
    ) -> Dict[str, Any]:
        """에이전트 건강상태 모니터링"""
        pass
```

### 3. Data Agent 인터페이스

#### 데이터 수집 메서드
```python
class DataAgentInterface:

    async def get_market_data(
        symbols: List[str],
        timeframe: str = "1D",  # "1M", "1H", "1D"
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, pd.DataFrame]:
        """시장 데이터 조회"""
        pass

    async def get_technical_indicators(
        symbols: List[str],
        indicators: List[str],  # ["RSI", "MACD", "BB"]
        params: Dict[str, Any] = None
    ) -> Dict[str, pd.DataFrame]:
        """기술지표 계산"""
        pass

    async def get_real_time_prices(
        symbols: List[str]
    ) -> Dict[str, PriceData]:
        """실시간 가격 조회"""
        pass
```

#### 데이터 품질 관리 메서드
```python
    async def validate_data_quality(
        symbol: str,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """데이터 품질 검증"""
        pass

    async def clean_data(
        data: pd.DataFrame,
        method: str = "forward_fill"
    ) -> pd.DataFrame:
        """데이터 정제"""
        pass
```

### 4. Strategy Agent 인터페이스

#### 전략 관리 메서드
```python
class StrategyAgentInterface:

    async def generate_signals(
        strategy_name: str,
        symbols: List[str],
        market_data: Dict[str, pd.DataFrame]
    ) -> List[TradingSignal]:
        """매매 신호 생성"""
        pass

    async def backtest_strategy(
        strategy_name: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """전략 백테스트"""
        pass

    async def optimize_parameters(
        strategy_name: str,
        symbols: List[str],
        optimization_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """파라미터 최적화"""
        pass
```

#### 전략 평가 메서드
```python
    async def evaluate_strategy_performance(
        strategy_name: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """전략 성과 평가"""
        pass

    async def get_available_strategies() -> List[str]:
        """사용 가능한 전략 목록"""
        pass
```

### 5. Service Agent 인터페이스

#### 실행 서비스 메서드
```python
class ServiceAgentInterface:

    async def execute_order(
        symbol: str,
        side: str,      # "buy", "sell"
        quantity: float,
        order_type: str = "market",  # "market", "limit"
        price: float = None
    ) -> Dict[str, Any]:
        """주문 실행"""
        pass

    async def get_account_balance() -> Dict[str, Any]:
        """계좌 잔고 조회"""
        pass

    async def get_positions() -> List[Dict[str, Any]]:
        """포지션 조회"""
        pass
```

#### 백테스트 서비스 메서드
```python
    async def run_backtest(
        strategy_config: Dict[str, Any],
        data_config: Dict[str, Any],
        period_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """백테스트 실행"""
        pass

    async def analyze_performance(
        trades: List[Dict[str, Any]],
        benchmark: str = "SPY"
    ) -> Dict[str, Any]:
        """성과 분석"""
        pass
```

### 6. Helper Agent 인터페이스

#### 외부 API 연동 메서드
```python
class HelperAgentInterface:

    async def authenticate_broker_api(
        broker: str,        # "KIS", "LS"
        account_type: str   # "real", "virtual"
    ) -> Dict[str, Any]:
        """브로커 API 인증"""
        pass

    async def get_external_data(
        provider: str,      # "alpha_vantage", "yfinance"
        symbols: List[str],
        data_type: str      # "price", "fundamental", "news"
    ) -> Dict[str, Any]:
        """외부 데이터 조회"""
        pass

    async def send_notification(
        channel: str,       # "telegram", "email"
        message: str,
        priority: str = "normal"  # "high", "normal", "low"
    ) -> Dict[str, Any]:
        """알림 전송"""
        pass
```

#### API 관리 메서드
```python
    async def check_api_status(
        service: str
    ) -> Dict[str, Any]:
        """API 서비스 상태 확인"""
        pass

    async def rotate_api_keys(
        service: str
    ) -> Dict[str, Any]:
        """API 키 교체"""
        pass
```

## 인터페이스 버전 관리

### 버전 호환성 규칙
```python
# 인터페이스 버전 헤더
{
    "interface_version": "2.0",
    "backward_compatible": ["1.9", "1.8"],
    "deprecated_methods": ["old_method_name"],
    "new_methods": ["new_method_name"]
}
```

### 호환성 확인 메서드
```python
async def check_interface_compatibility(
    sender_agent: str,
    receiver_agent: str,
    method: str
) -> Dict[str, Any]:
    """인터페이스 호환성 확인"""
    pass
```

## 오류 처리 표준

### 표준 오류 코드
| 오류 코드 | 설명 | HTTP 등가 |
|----------|------|-----------|
| `SUCCESS` | 성공 | 200 |
| `INVALID_PARAMS` | 잘못된 파라미터 | 400 |
| `UNAUTHORIZED` | 인증 실패 | 401 |
| `FORBIDDEN` | 권한 없음 | 403 |
| `NOT_FOUND` | 리소스 없음 | 404 |
| `TIMEOUT` | 타임아웃 | 408 |
| `INTERNAL_ERROR` | 내부 오류 | 500 |
| `SERVICE_UNAVAILABLE` | 서비스 불가 | 503 |

### 재시도 정책
```python
{
    "retry_policy": {
        "max_retries": 3,
        "retry_delay": 1.0,     # 초
        "backoff_factor": 2.0,  # 지수적 백오프
        "retryable_errors": [
            "TIMEOUT",
            "SERVICE_UNAVAILABLE",
            "INTERNAL_ERROR"
        ]
    }
}
```

## 성능 모니터링

### 메트릭 수집
```python
{
    "performance_metrics": {
        "response_time_ms": float,
        "throughput_rps": float,    # Requests Per Second
        "error_rate": float,        # 0.0 ~ 1.0
        "queue_depth": int,
        "memory_usage_mb": float,
        "cpu_usage_percent": float
    }
}
```

### SLA (Service Level Agreement)
| 에이전트 | 응답시간 (P95) | 가용성 | 처리량 |
|----------|---------------|--------|--------|
| **Orchestrator** | < 100ms | 99.9% | 1000 RPS |
| **Data Agent** | < 500ms | 99.5% | 100 RPS |
| **Strategy Agent** | < 1000ms | 99.5% | 50 RPS |
| **Service Agent** | < 200ms | 99.9% | 200 RPS |
| **Helper Agent** | < 2000ms | 99.0% | 20 RPS |

## 보안 및 인증

### 메시지 서명
```python
{
    "security": {
        "signature": str,           # HMAC-SHA256 서명
        "timestamp": str,          # 재생 공격 방지
        "nonce": str,              # 한 번만 사용되는 값
        "api_key": str             # API 키 (해시값)
    }
}
```

### 권한 검증
```python
async def verify_agent_permission(
    sender_agent: str,
    method: str,
    target_resource: str
) -> bool:
    """에이전트 권한 검증"""
    pass
```

## 실제 구현 예제

### Python 구현 예제
```python
import asyncio
from typing import Dict, Any
from datetime import datetime
import json

class BaseAgentInterface:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.message_handlers = {}

    async def send_message(
        self,
        receiver_agent: str,
        method: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """메시지 발송"""
        message = {
            "message_id": self._generate_message_id(),
            "sender_agent": self.agent_id,
            "receiver_agent": receiver_agent,
            "method": method,
            "params": params or {},
            "timestamp": datetime.utcnow().isoformat(),
            "priority": 2,
            "timeout": 30,
            "retry_count": 0
        }

        # 실제 메시지 전송 로직
        response = await self._transmit_message(message)
        return response

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """메시지 처리"""
        method = message.get("method")
        params = message.get("params", {})

        if method not in self.message_handlers:
            return self._create_error_response(
                message, "NOT_FOUND", f"Method {method} not found"
            )

        try:
            handler = self.message_handlers[method]
            result = await handler(**params)

            return {
                "message_id": message["message_id"],
                "sender_agent": self.agent_id,
                "receiver_agent": message["sender_agent"],
                "status": "success",
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": 0.1  # 실제 실행 시간 계산
            }

        except Exception as e:
            return self._create_error_response(
                message, "INTERNAL_ERROR", str(e)
            )
```

## 테스트 및 검증

### 인터페이스 테스트 케이스
```python
class InterfaceTestSuite:
    async def test_message_format(self):
        """메시지 형식 검증"""
        pass

    async def test_error_handling(self):
        """오류 처리 검증"""
        pass

    async def test_timeout_handling(self):
        """타임아웃 처리 검증"""
        pass

    async def test_retry_mechanism(self):
        """재시도 메커니즘 검증"""
        pass
```

---

**인터페이스 규약**: 모든 에이전트는 이 인터페이스 표준을 준수해야 합니다.
**변경 관리**: 인터페이스 변경 시 하위 호환성을 보장하고 deprecated 메서드는 점진적으로 제거합니다.
**문서 동기화**: 코드 변경 시 이 문서도 함께 업데이트해야 합니다.