# LLM 라우터 통합 계획

**프로젝트**: AI Assistant Multi-Agent Trading System
**작성일**: 2025-09-15
**담당**: Orchestrator Agent
**라우터**: https://github.com/musistudio/claude-code-router

---

## 🎯 통합 목표

### 주요 목표
1. **Gemini 모델을 Claude Code에서 사용 가능하게 함**
2. **에이전트별 최적 모델 자동 선택**
3. **비용 효율적인 LLM 사용**
4. **로드 밸런싱 및 failover 구현**

### 예상 효과
- **비용 절감**: Gemini 모델 활용으로 30-50% 비용 절약
- **성능 향상**: 작업별 최적 모델 선택으로 응답 품질 개선
- **안정성 확보**: 다중 모델 지원으로 서비스 연속성 보장

---

## 🏗️ 아키텍처 설계

### 현재 구조
```
Claude Code → Anthropic API → Claude Models Only
```

### 목표 구조
```
Claude Code → LLM Router → Multiple LLM Providers
                        ├── Anthropic (Claude-3 Opus/Sonnet/Haiku)
                        ├── Google (Gemini-Pro/Gemini-Ultra)
                        └── OpenAI (GPT-4/GPT-3.5) [Future]
```

### 라우터 컴포넌트
```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Router System                       │
├─────────────────────────────────────────────────────────────┤
│ Request Handler │ Model Selector │ Load Balancer │ Monitor │
├─────────────────┼────────────────┼───────────────┼─────────┤
│ - Agent Auth    │ - Task Analysis│ - Round Robin │ - Metrics│
│ - Request Parse │ - Model Match  │ - Health Check│ - Logging│
│ - Response Fmt  │ - Cost Calc    │ - Failover   │ - Alerts │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 단계별 구현 계획

### Phase 1: 기반 인프라 구축 (1-2일)

#### 1.1 claude-code-router 설치 및 설정
```bash
# Router 클론 및 설치
git clone https://github.com/musistudio/claude-code-router.git
cd claude-code-router
npm install

# 기본 설정 파일 생성
cp config.example.json config.json
```

#### 1.2 기본 설정 구성
```json
{
  "server": {
    "port": 3000,
    "host": "localhost"
  },
  "providers": {
    "anthropic": {
      "enabled": true,
      "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
    },
    "google": {
      "enabled": true,
      "models": ["gemini-pro"]
    }
  },
  "routing": {
    "strategy": "agent_based",
    "load_balancing": "round_robin"
  }
}
```

#### 1.3 Claude Code 연동 테스트
```python
# 연동 테스트 스크립트
import requests

def test_router_connection():
    router_url = "http://localhost:3000/api/chat"
    test_payload = {
        "agent": "data_agent",
        "message": "Hello from Claude Code",
        "model_preference": "cost_efficient"
    }

    response = requests.post(router_url, json=test_payload)
    return response.status_code == 200
```

### Phase 2: 에이전트 통합 (2-3일)

#### 2.1 Agent-Router 인터페이스 구현
```python
# Project/shared/llm_router_client.py
class LLMRouterClient:
    def __init__(self, router_url="http://localhost:3000"):
        self.router_url = router_url
        self.agent_configs = load_agent_model_config()

    def route_request(self, agent_name, task_type, message, **kwargs):
        """에이전트 요청을 적절한 LLM으로 라우팅"""
        payload = {
            "agent": agent_name,
            "task": task_type,
            "message": message,
            "preferences": self._get_agent_preferences(agent_name),
            **kwargs
        }

        return self._send_request(payload)

    def _get_agent_preferences(self, agent_name):
        """agent_model.yaml에서 에이전트별 선호도 로드"""
        config = self.agent_configs.get(agent_name, {})
        return {
            "primary_model": config.get("primary_model"),
            "fallback_model": config.get("fallback_model"),
            "strategy": config.get("model_selection_strategy")
        }
```

#### 2.2 각 에이전트별 라우터 클라이언트 통합
```python
# Project/indicator/data_agent_main.py
from shared.llm_router_client import LLMRouterClient

class DataAgent:
    def __init__(self):
        self.router = LLMRouterClient()

    def process_data_request(self, data_type, parameters):
        # LLM 라우터를 통해 요청 처리
        response = self.router.route_request(
            agent_name="data_agent",
            task_type="data_processing",
            message=f"Process {data_type} data with {parameters}",
            context="large_dataset" if len(parameters) > 1000 else "normal"
        )

        return self._parse_response(response)
```

### Phase 3: 모델 최적화 (3-4일)

#### 3.1 작업별 모델 매핑 구현
```yaml
# config/task_model_mapping.yaml
task_mappings:
  data_processing:
    large_dataset: "gemini-pro"
    normal_dataset: "claude-3-sonnet"
    simple_calculation: "claude-3-haiku"

  strategy_development:
    complex_strategy: "claude-3-opus"
    signal_generation: "claude-3-sonnet"
    parameter_optimization: "gemini-pro"

  service_operations:
    backtesting: "claude-3-sonnet"
    order_execution: "claude-3-haiku"
    risk_monitoring: "claude-3-sonnet"
```

#### 3.2 동적 모델 선택 로직
```python
class ModelSelector:
    def select_optimal_model(self, agent, task, context):
        # 비용 고려
        if context.get("budget_constraint", False):
            return self._get_cost_efficient_model(task)

        # 성능 우선
        if context.get("quality_critical", False):
            return self._get_high_quality_model(task)

        # 속도 우선
        if context.get("time_critical", False):
            return self._get_fast_model(task)

        # 기본 선택
        return self._get_default_model(agent, task)
```

### Phase 4: 모니터링 및 최적화 (2-3일)

#### 4.1 성능 모니터링 시스템
```python
# monitoring/llm_performance_monitor.py
class LLMPerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "response_times": {},
            "success_rates": {},
            "cost_tracking": {},
            "model_usage": {}
        }

    def log_request(self, agent, model, task, start_time, end_time, cost, success):
        """요청 메트릭 로깅"""
        response_time = end_time - start_time

        self.metrics["response_times"][model] = self.metrics["response_times"].get(model, [])
        self.metrics["response_times"][model].append(response_time)

        # 비용 추적
        self.metrics["cost_tracking"][agent] = self.metrics["cost_tracking"].get(agent, 0)
        self.metrics["cost_tracking"][agent] += cost

    def generate_daily_report(self):
        """일일 성능 리포트 생성"""
        return {
            "total_requests": sum(len(times) for times in self.metrics["response_times"].values()),
            "average_response_time": self._calculate_avg_response_time(),
            "total_cost": sum(self.metrics["cost_tracking"].values()),
            "model_distribution": self._calculate_model_distribution()
        }
```

#### 4.2 자동 최적화 시스템
```python
class AutoOptimizer:
    def optimize_model_selection(self):
        """성능 데이터 기반 모델 선택 최적화"""
        monitor = LLMPerformanceMonitor()
        daily_report = monitor.generate_daily_report()

        # 비용 효율성 분석
        if daily_report["total_cost"] > self.cost_threshold:
            self._shift_to_cost_efficient_models()

        # 응답 시간 최적화
        if daily_report["average_response_time"] > self.time_threshold:
            self._shift_to_faster_models()
```

---

## 🔧 기술적 구현 세부사항

### API 인터페이스 설계
```typescript
// Router API 엔드포인트
interface RouterRequest {
  agent: string;
  task: string;
  message: string;
  preferences?: {
    model?: string;
    strategy?: "quality" | "cost" | "speed";
    max_tokens?: number;
    temperature?: number;
  };
  context?: {
    dataset_size?: "small" | "medium" | "large";
    time_critical?: boolean;
    budget_constraint?: boolean;
  };
}

interface RouterResponse {
  model_used: string;
  response: string;
  metadata: {
    cost: number;
    response_time: number;
    tokens_used: number;
    provider: string;
  };
}
```

### 로드 밸런싱 전략
```javascript
// 라운드 로빈 로드 밸런싱
class LoadBalancer {
  constructor() {
    this.modelQueues = {
      "claude-3-opus": [],
      "claude-3-sonnet": [],
      "gemini-pro": []
    };
    this.currentIndex = {};
  }

  selectModel(availableModels, strategy = "round_robin") {
    switch(strategy) {
      case "round_robin":
        return this.roundRobinSelect(availableModels);
      case "least_loaded":
        return this.leastLoadedSelect(availableModels);
      case "health_based":
        return this.healthBasedSelect(availableModels);
    }
  }
}
```

### Gemini 모델 통합
```python
# providers/gemini_provider.py
class GeminiProvider:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"

    def generate_response(self, prompt, model="gemini-pro", **kwargs):
        """Gemini API 호출"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1000)
            }
        }

        response = requests.post(
            f"{self.base_url}/{model}:generateContent",
            headers=headers,
            json=payload
        )

        return self._parse_gemini_response(response)
```

---

## 📊 모니터링 및 알림 체계

### 실시간 모니터링 대시보드
```python
# monitoring/dashboard.py
class RouterDashboard:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/dashboard")
        def dashboard():
            metrics = self.get_current_metrics()
            return render_template("dashboard.html", metrics=metrics)

        @self.app.route("/api/metrics")
        def api_metrics():
            return jsonify(self.get_current_metrics())

    def get_current_metrics(self):
        return {
            "active_models": self.get_active_models(),
            "request_rate": self.get_request_rate(),
            "average_response_time": self.get_avg_response_time(),
            "cost_per_hour": self.get_hourly_cost(),
            "error_rate": self.get_error_rate()
        }
```

### 알림 시스템
```python
# monitoring/alerts.py
class AlertManager:
    def __init__(self):
        self.thresholds = {
            "high_cost": 100,  # USD per hour
            "slow_response": 10,  # seconds
            "high_error_rate": 0.05  # 5%
        }

    def check_alerts(self, metrics):
        alerts = []

        if metrics["cost_per_hour"] > self.thresholds["high_cost"]:
            alerts.append({
                "type": "high_cost",
                "message": f"Hourly cost exceeded: ${metrics['cost_per_hour']:.2f}",
                "severity": "warning"
            })

        if metrics["error_rate"] > self.thresholds["high_error_rate"]:
            alerts.append({
                "type": "high_error_rate",
                "message": f"Error rate: {metrics['error_rate']:.1%}",
                "severity": "critical"
            })

        return alerts
```

---

## 🚀 배포 및 운영 계획

### 개발 환경 구성
```bash
# 개발 환경 설정
mkdir llm-router-dev
cd llm-router-dev

# Docker Compose로 개발 환경 구성
docker-compose up -d

# 환경별 설정
cp config/development.json config/config.json
```

### 프로덕션 배포
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  llm-router:
    image: musistudio/claude-code-router:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./config:/app/config
    restart: unless-stopped

  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data
    restart: unless-stopped

  monitoring:
    image: prometheus/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### 백업 및 복구 계획
```bash
# 설정 백업
tar -czf router-config-backup-$(date +%Y%m%d).tar.gz config/

# 로그 아카이브
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;

# 메트릭 데이터 백업
pg_dump metrics_db > metrics-backup-$(date +%Y%m%d).sql
```

---

## 📈 성공 지표 및 KPI

### 기술적 지표
- **응답 시간**: 평균 < 3초
- **가용성**: > 99.9%
- **에러율**: < 1%
- **모델 다양성**: 최소 3개 모델 활용

### 비즈니스 지표
- **비용 절감**: 30% 이상
- **처리량 증가**: 50% 이상
- **사용자 만족도**: 9/10 이상

### 모니터링 대상
```python
# KPI 추적
kpis = {
    "technical": {
        "avg_response_time": "< 3000ms",
        "uptime": "> 99.9%",
        "error_rate": "< 1%",
        "throughput": "> 1000 requests/hour"
    },
    "business": {
        "cost_reduction": "> 30%",
        "model_utilization": {
            "claude": "< 70%",
            "gemini": "> 30%"
        }
    }
}
```

---

## 🔮 향후 확장 계획

### 단기 확장 (1-3개월)
- **OpenAI GPT 모델 추가**
- **Cohere 모델 통합**
- **더 정교한 작업별 모델 매핑**

### 중기 확장 (3-6개월)
- **머신러닝 기반 모델 선택**
- **A/B 테스팅 프레임워크**
- **실시간 성능 최적화**

### 장기 비전 (6개월+)
- **자체 LLM 모델 통합**
- **엣지 컴퓨팅 지원**
- **멀티 리전 배포**

---

## 🎯 실행 일정

| 주차 | 주요 작업 | 담당 | 완료 기준 |
|------|----------|------|-----------|
| 1주차 | 라우터 설치 및 기본 설정 | 전체팀 | 기본 연동 테스트 완료 |
| 2주차 | 에이전트 통합 | 각 에이전트팀 | 모든 에이전트 라우터 연동 |
| 3주차 | 모델 최적화 구현 | 전략팀 | 동적 모델 선택 작동 |
| 4주차 | 모니터링 시스템 구축 | 인프라팀 | 대시보드 및 알림 시스템 |
| 5주차 | 테스트 및 최적화 | 전체팀 | 성능 목표 달성 |
| 6주차 | 프로덕션 배포 | DevOps팀 | 실서비스 적용 완료 |

---

**🚨 중요**: 이 계획은 claude-code-router의 성숙도와 안정성에 따라 조정될 수 있습니다.

*계획 버전: 1.0 | 최종 업데이트: 2025-09-15*