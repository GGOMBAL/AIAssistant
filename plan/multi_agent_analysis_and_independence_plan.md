# 🤖 Multi-Agent 시스템 동작 방식 및 독립성 분석

**작성일**: 2025-09-23
**버전**: 1.0
**목적**: 현재 Multi-Agent Trading System의 동작 방식 분석 및 독립성 개선 방안 제시

---

## 📋 현재 에이전트 동작 방식

### 1. 🎭 Orchestrator Agent (오케스트레이터)
- **역할**: 전체 시스템의 총괄 관리자
- **주요 기능**:
  - 모든 서브 에이전트 초기화 및 조정
  - 작업 위임 및 프롬프트 생성
  - 결과 통합 및 최종 분석
  - Fallback 메커니즘 제공
- **워크플로우**:
  ```
  Phase 1: Data Agent → 데이터 수집
  Phase 2: Strategy Agent → 신호 생성
  Phase 3: Service Agent → 백테스트 실행
  Phase 4: 결과 통합 및 분석
  ```
- **파일**: `orchestrator_agent.py`
- **의존성**: 모든 서브 에이전트, myStockInfo.yaml

### 2. 📊 Data Agent (데이터)
- **역할**: 데이터 수집, 처리, 기술지표 계산
- **주요 기능**:
  - MongoDB 연결 및 NAS/NYS 데이터 로드
  - 기술지표 계산 (MA, RSI, Bollinger Bands, MACD 등)
  - 데이터 품질 검증 및 표준화
  - 시장별 특화 지표 추가 (NASDAQ: Price_Momentum, NYSE: Price_Stability)
- **파일**: `data_agent.py`
- **의존성**: MongoDB, simple_technical_indicators.py
- **독립성**: MongoDB 의존, 기술지표 모듈 필요

### 3. 🧠 Strategy Agent (전략)
- **역할**: 시장별 차별화된 매매 전략 수립
- **주요 기능**:
  - NASDAQ (성장주) vs NYSE (가치주) 전략 분리
  - 골든크로스/데드크로스, RSI, 볼린저밴드 신호
  - 포트폴리오 레벨 최적화 및 상관관계 분석
  - 신호 확신도 계산 (0.0 ~ 1.0)
- **전략 파라미터**:
  - **NASDAQ**: MA(5,20), RSI(25-75), 높은 변동성 대응
  - **NYSE**: MA(10,50), RSI(35-65), 안정적 접근
- **파일**: `strategy_agent.py`
- **의존성**: Data Agent 결과물
- **독립성**: 데이터에 의존하지만 전략 로직은 독립적

### 4. ⚡ Service Agent (서비스)
- **역할**: 백테스트 실행, 포트폴리오 관리, 성과 분석
- **주요 기능**:
  - 시장별 분리된 포트폴리오 관리 (NASDAQ 50%, NYSE 50%)
  - 리스크 관리 및 포지션 조절
  - 성과 및 거래 통계 계산
  - 일일 거래 실행 시뮬레이션
- **리스크 설정**:
  - 종목당 최대 15%, 시장당 최대 60%
  - 손절 8%, 익절 25%
  - 상관관계 위험 제한
- **파일**: `service_agent.py`
- **의존성**: Strategy Agent 신호, Data Agent 데이터
- **독립성**: 신호와 데이터에 의존, 백테스트 엔진은 독립적

### 5. 🔧 Helper Agent (헬퍼)
- **역할**: MongoDB 연결, 설정 관리, 시스템 리소스 모니터링
- **주요 기능**:
  - MongoDB 클라이언트 관리
  - 설정 파일 로드 (api_credentials.yaml, broker_config.yaml 등)
  - 시스템 상태 검증 및 헬스체크
  - 전체 주식 심볼 조회 (15,000+ 종목)
- **파일**: `helper_agent.py`
- **의존성**: MongoDB, YAML 설정 파일
- **독립성**: 완전히 독립적, 다른 에이전트들에게 서비스 제공

---

## ⚠️ 현재 독립성 문제점

### 1. 강한 결합도 (Tight Coupling)
```python
# orchestrator_agent.py에서 직접 import
from data_agent import DataAgent
from strategy_agent import StrategyAgent
from service_agent import ServiceAgent
from helper_agent import HelperAgent
```
**문제**: 모든 에이전트가 같은 프로세스에서 실행되어 하나의 에이전트 오류가 전체 시스템에 영향

### 2. 프로젝트 폴더 의존성
```python
# 모든 에이전트에서 공통 패턴
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
```
**문제**: 프로젝트 폴더 구조에 강하게 의존, 배포 시 유연성 부족

### 3. 공유 설정 파일 의존성
- `myStockInfo.yaml`: MongoDB 연결 정보
- `simple_technical_indicators.py`: 기술지표 모듈
- `mongodb_integrated_backtest.py`: Fallback 시스템

**문제**: 설정 파일 변경 시 모든 에이전트 재시작 필요

### 4. 동기식 처리
**문제**: 순차적 실행으로 인한 성능 제약, 병렬 처리 불가

---

## 🚀 에이전트 독립성 개선 방안

### 1. 마이크로서비스 아키텍처 도입

```python
# 에이전트별 독립 실행 가능한 구조
class AgentInterface:
    def __init__(self, config_path: str, host: str = "localhost", port: int = 8000):
        self.config = self._load_config(config_path)
        self.api_server = self._start_api_server(host, port)

    def process_request(self, request_data: Dict) -> Dict:
        # 에이전트별 처리 로직
        pass

    def health_check(self) -> Dict:
        return {"status": "healthy", "timestamp": datetime.now()}
```

### 2. 메시지 큐 시스템 도입

```yaml
# docker-compose.yml
version: '3.8'
services:
  orchestrator:
    build: ./agents/orchestrator
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_HOST=mongodb
    depends_on:
      - redis
      - mongodb

  data-agent:
    build: ./agents/data
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_HOST=mongodb
    depends_on:
      - redis
      - mongodb

  strategy-agent:
    build: ./agents/strategy
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  service-agent:
    build: ./agents/service
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  helper-agent:
    build: ./agents/helper
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_HOST=mongodb
    depends_on:
      - redis
      - mongodb

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=wlsaud07
```

### 3. API 기반 통신 구조

```python
# FastAPI 기반 각 에이전트 서버
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Data Agent API", version="1.0")

class DataLoadRequest(BaseModel):
    start_date: str
    end_date: str
    nas_symbols: Optional[List[str]] = None
    nys_symbols: Optional[List[str]] = None
    prompt: str = ""

@app.post("/data/load")
async def load_data(request: DataLoadRequest):
    try:
        agent = DataAgent()
        result = await agent.execute_data_loading(**request.dict())
        return {"status": "success", "data": result, "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategy/generate")
async def generate_signals(request: StrategyRequest):
    try:
        agent = StrategyAgent()
        result = await agent.generate_trading_signals(**request.dict())
        return {"status": "success", "signals": result, "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "data", "timestamp": datetime.now()}
```

### 4. 컨테이너화된 배포

```dockerfile
# Dockerfile (각 에이전트별)
FROM python:3.9-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 에이전트 코드 복사
COPY agent/ .
COPY config/ ./config/

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV AGENT_PORT=8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 에이전트 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔧 즉시 적용 가능한 개선사항

### 1. 설정 외부화
```python
# config/agent_config.py
import os
from typing import Dict, Optional

class AgentConfig:
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_from_env_or_file(config_file)

    def get_mongodb_config(self) -> Dict:
        return {
            'host': os.getenv('MONGODB_HOST', 'localhost'),
            'port': int(os.getenv('MONGODB_PORT', 27017)),
            'username': os.getenv('MONGODB_USER', 'admin'),
            'password': os.getenv('MONGODB_PASS', 'wlsaud07'),
            'auth_database': os.getenv('MONGODB_AUTH_DB', 'admin')
        }

    def get_redis_config(self) -> Dict:
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0))
        }

    def get_backtest_config(self) -> Dict:
        return {
            'initial_cash': int(os.getenv('INITIAL_CASH', 100000000)),
            'commission_rate': float(os.getenv('COMMISSION_RATE', 0.002)),
            'slippage': float(os.getenv('SLIPPAGE', 0.001))
        }
```

### 2. 인터페이스 표준화
```python
# interfaces/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime

class BaseAgent(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.start_time = datetime.now()
        self.status = "initializing"

    @abstractmethod
    async def initialize(self) -> bool:
        """에이전트 초기화"""
        pass

    @abstractmethod
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """메인 작업 실행"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """헬스체크"""
        pass

    async def shutdown(self) -> bool:
        """안전한 종료"""
        self.status = "shutdown"
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "start_time": self.start_time,
            "uptime": (datetime.now() - self.start_time).total_seconds()
        }
```

### 3. 의존성 주입
```python
# dependency_injection.py
from typing import Dict, Type, Any
import importlib

class AgentContainer:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._configs: Dict[str, Any] = {}
        self._factories: Dict[str, Type] = {}

    def register_agent_factory(self, name: str, agent_class: Type, config: Dict):
        """에이전트 팩토리 등록"""
        self._factories[name] = agent_class
        self._configs[name] = config

    async def get_agent(self, name: str):
        """에이전트 인스턴스 반환 (지연 초기화)"""
        if name not in self._agents:
            if name in self._factories:
                agent_class = self._factories[name]
                config = self._configs[name]
                self._agents[name] = agent_class(config)
                await self._agents[name].initialize()
            else:
                raise ValueError(f"Agent {name} not registered")
        return self._agents[name]

    async def shutdown_all(self):
        """모든 에이전트 안전 종료"""
        for agent in self._agents.values():
            await agent.shutdown()
```

### 4. 비동기 메시지 큐
```python
# messaging/queue_manager.py
import asyncio
import json
from typing import Dict, Callable, Any
import aioredis

class MessageQueue:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url)

    async def publish(self, channel: str, message: Dict[str, Any]):
        """메시지 발행"""
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, handler: Callable):
        """채널 구독"""
        self.handlers[channel] = handler
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)

        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await handler(data)

    async def request_response(self, request_channel: str, response_channel: str,
                              message: Dict[str, Any], timeout: int = 30):
        """요청-응답 패턴"""
        correlation_id = str(uuid.uuid4())
        message['correlation_id'] = correlation_id

        # 응답 대기 설정
        response_future = asyncio.Future()

        async def response_handler(data):
            if data.get('correlation_id') == correlation_id:
                response_future.set_result(data)

        await self.subscribe(response_channel, response_handler)
        await self.publish(request_channel, message)

        return await asyncio.wait_for(response_future, timeout)
```

---

## 📈 권장 구현 단계

### Phase 1: 설정 외부화 (즉시 구현 가능)
**목표**: 에이전트별 설정 독립성 확보
- ✅ 환경변수 기반 설정 관리
- ✅ Docker Compose 환경 구축
- ✅ 설정 파일 표준화
- ✅ 헬스체크 엔드포인트 추가

**예상 소요시간**: 1-2일
**우선순위**: 높음

### Phase 2: API 인터페이스 도입 (단기)
**목표**: HTTP 기반 에이전트 간 통신
- 🔄 FastAPI 기반 에이전트 서버 구축
- 🔄 HTTP 기반 에이전트 간 통신
- 🔄 로드 밸런싱 및 헬스체크
- 🔄 API 문서화 (Swagger)

**예상 소요시간**: 1주일
**우선순위**: 높음

### Phase 3: 메시지 큐 통합 (중기)
**목표**: 비동기 메시지 기반 아키텍처
- ⏳ Redis/RabbitMQ 도입
- ⏳ 비동기 작업 처리
- ⏳ 이벤트 기반 아키텍처
- ⏳ 실시간 모니터링

**예상 소요시간**: 2-3주
**우선순위**: 중간

### Phase 4: 완전 독립성 (장기)
**목표**: 완전히 독립적인 마이크로서비스
- 📋 각 에이전트별 독립 배포
- 📋 서비스 디스커버리 (Consul, etcd)
- 📋 중앙집중 로깅 (ELK Stack)
- 📋 분산 추적 (Jaeger, Zipkin)
- 📋 자동 스케일링 (Kubernetes)

**예상 소요시간**: 1-2개월
**우선순위**: 낮음

---

## 🎯 기대 효과

### 1. 안정성 향상
- **장애 격리**: 하나의 에이전트 오류가 전체 시스템에 영향 없음
- **무중단 서비스**: 에이전트별 독립 재시작 가능
- **복구 시간 단축**: 문제 에이전트만 선택적 복구

### 2. 확장성 개선
- **수평 확장**: 부하가 높은 에이전트만 스케일 아웃
- **자원 최적화**: 에이전트별 리소스 요구사항에 맞는 배포
- **성능 향상**: 병렬 처리로 전체 실행 시간 단축

### 3. 개발 생산성 향상
- **독립 개발**: 에이전트별 팀 분할 개발 가능
- **빠른 배포**: 변경된 에이전트만 선택적 배포
- **테스트 용이성**: 에이전트별 단위 테스트 및 통합 테스트

### 4. 운영 편의성
- **모니터링**: 에이전트별 상세 메트릭 수집
- **로그 관리**: 중앙집중식 로그 수집 및 분석
- **설정 관리**: 실시간 설정 변경 및 적용

---

## 📊 성능 예측

### 현재 시스템 vs 개선된 시스템

| 항목 | 현재 시스템 | 개선된 시스템 | 개선율 |
|------|-------------|---------------|--------|
| 전체 실행 시간 | 1.93초 | 0.8-1.2초 | 37-58% 향상 |
| 메모리 사용량 | 500MB | 300-400MB | 20-40% 절약 |
| 장애 복구 시간 | 전체 재시작 (30초) | 부분 재시작 (5-10초) | 66-83% 단축 |
| 동시 처리 가능 요청 | 1개 | 5-10개 | 500-1000% 향상 |

### 리소스 사용량 예측
```
에이전트별 리소스 할당:
├── Orchestrator: 50MB RAM, 0.1 CPU
├── Data Agent: 200MB RAM, 0.3 CPU
├── Strategy Agent: 100MB RAM, 0.2 CPU
├── Service Agent: 150MB RAM, 0.2 CPU
└── Helper Agent: 50MB RAM, 0.1 CPU

총계: 550MB RAM, 0.9 CPU (기존 대비 10% 증가)
```

---

## 🔍 모니터링 계획

### 1. 에이전트별 메트릭
```python
# 수집할 주요 메트릭
agent_metrics = {
    "response_time": "에이전트 응답 시간",
    "throughput": "초당 처리량",
    "error_rate": "에러 발생률",
    "memory_usage": "메모리 사용량",
    "cpu_usage": "CPU 사용률",
    "active_connections": "활성 연결 수"
}
```

### 2. 대시보드 구성
- **실시간 모니터링**: Grafana + Prometheus
- **로그 분석**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **알림 시스템**: PagerDuty, Slack 연동
- **성능 분석**: APM (Application Performance Monitoring)

---

## 🚀 시작하기

### 1. 즉시 실행 가능한 개선
```bash
# 1. 환경변수 설정
export MONGODB_HOST=localhost
export MONGODB_PORT=27017
export REDIS_HOST=localhost
export REDIS_PORT=6379

# 2. Docker Compose 실행
docker-compose -f docker-compose.dev.yml up -d

# 3. 에이전트별 헬스체크
curl http://localhost:8001/health  # Data Agent
curl http://localhost:8002/health  # Strategy Agent
curl http://localhost:8003/health  # Service Agent
curl http://localhost:8004/health  # Helper Agent
```

### 2. 개발 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 설정 파일 생성
cp .env.example .env
# .env 파일 편집 후 설정값 입력
```

이러한 구조로 개선하면 **"멀티 에이전트가 항상 동작하고 프로젝트 폴더와 독립적"**인 시스템을 구축할 수 있습니다.

---

**📝 마지막 업데이트**: 2025-09-23
**📧 문의**: Multi-Agent Trading System Team
**🔗 관련 문서**: [CLAUDE.md](../CLAUDE.md), [ARCHITECTURE_GUIDE.md](../docs/ARCHITECTURE_GUIDE.md)