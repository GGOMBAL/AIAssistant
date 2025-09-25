# 🏗️ Multi-Agent Trading System 아키텍처 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처 설계 원칙](#아키텍처-설계-원칙)
3. [에이전트 상세 분석](#에이전트-상세-분석)
4. [데이터 플로우](#데이터-플로우)
5. [통신 프로토콜](#통신-프로토콜)
6. [확장성 설계](#확장성-설계)
7. [성능 최적화](#성능-최적화)

---

## 🎯 시스템 개요

### 핵심 아키텍처 개념

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│                  (Business Logic)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Agent Coordination Layer                     │
│            (Inter-Agent Communication)                     │
└─┬─────────┬─────────┬─────────┬─────────────────────────────┘
  │         │         │         │
  ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌─────────┐
│ Data  │ │Strategy│ │Service│ │ Helper  │    ← Agent Layer
│ Agent │ │ Agent │ │ Agent │ │ Agent   │      (Specialized)
└─┬─────┘ └─┬─────┘ └─┬─────┘ └─┬───────┘
  │         │         │         │
  ▼         ▼         ▼         ▼
┌─────────────────────────────────────────┐
│            Infrastructure Layer         │    ← Data Layer
│         (MongoDB, Config, Logs)         │      (Persistence)
└─────────────────────────────────────────┘
```

### 설계 철학

#### 1. **Single Responsibility Principle**
각 에이전트는 하나의 명확한 책임을 가집니다.
- **Data Agent**: 데이터 수집 및 전처리만 담당
- **Strategy Agent**: 매매 신호 생성만 담당
- **Service Agent**: 백테스트 실행만 담당
- **Helper Agent**: 시스템 리소스 관리만 담당

#### 2. **Loose Coupling**
에이전트 간 느슨한 결합으로 독립적 개발/테스트가 가능합니다.
```python
# 에이전트 간 직접 의존성 없음
class DataAgent:
    def __init__(self):
        # MongoDB 연결만 관리
        pass

class StrategyAgent:
    def __init__(self):
        # 전략 로직만 관리 (DataAgent 의존하지 않음)
        pass
```

#### 3. **High Cohesion**
각 에이전트 내부 기능들은 높은 응집도를 가집니다.
```python
class DataAgent:
    def load_market_data(self):     # 데이터 로딩
    def calculate_indicators(self):  # 기술지표 계산
    def validate_data_quality(self): # 데이터 품질 검증
    # 모든 메서드가 데이터 처리와 관련됨
```

---

## 🏛️ 아키텍처 설계 원칙

### 1. **Multi-Agent Pattern**

#### 전통적 모놀리식 구조의 문제점
```python
# 문제가 있는 모놀리식 구조
class TradingSystem:
    def run_backtest(self):
        # 데이터 로딩
        data = self.load_data()      # 300줄
        # 신호 생성
        signals = self.generate_signals(data)  # 500줄
        # 백테스트 실행
        results = self.execute_backtest(signals)  # 800줄
        # 결과 분석
        analysis = self.analyze_results(results)  # 200줄

        return analysis  # 총 1800줄의 거대한 클래스
```

#### Multi-Agent 구조의 장점
```python
# 개선된 Multi-Agent 구조
class OrchestratorAgent:
    def run_backtest(self):
        # 각 에이전트에게 작업 위임
        data = self.data_agent.load_data()           # 300줄 → DataAgent
        signals = self.strategy_agent.generate(data)  # 500줄 → StrategyAgent
        results = self.service_agent.execute(signals) # 800줄 → ServiceAgent
        analysis = self._analyze_results(results)     # 200줄 → 50줄로 축소

        return analysis  # 총 50줄의 간결한 조정자
```

### 2. **Event-Driven Architecture**

#### 에이전트 간 이벤트 기반 통신
```python
class AgentEvent:
    def __init__(self, event_type, data, source_agent):
        self.event_type = event_type
        self.data = data
        self.source_agent = source_agent
        self.timestamp = datetime.now()

class EventBus:
    def __init__(self):
        self.subscribers = {}

    def publish(self, event):
        for subscriber in self.subscribers.get(event.event_type, []):
            subscriber.handle_event(event)

    def subscribe(self, event_type, handler):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

# 사용 예시
event_bus.publish(AgentEvent(
    event_type="data_loaded",
    data=market_data,
    source_agent="data_agent"
))
```

### 3. **Dependency Injection**

#### 설정 기반 의존성 주입
```python
class AgentFactory:
    def __init__(self, config):
        self.config = config

    def create_agent(self, agent_type):
        if agent_type == "data":
            return DataAgent(
                mongodb_config=self.config['mongodb'],
                indicators_config=self.config['indicators']
            )
        elif agent_type == "strategy":
            return StrategyAgent(
                nasdaq_params=self.config['strategies']['nasdaq'],
                nyse_params=self.config['strategies']['nyse']
            )
        # ...

# Orchestrator에서 사용
class OrchestratorAgent:
    def __init__(self, config):
        factory = AgentFactory(config)
        self.data_agent = factory.create_agent("data")
        self.strategy_agent = factory.create_agent("strategy")
        # 설정 기반으로 에이전트 생성
```

---

## 🤖 에이전트 상세 분석

### 1. **Orchestrator Agent** (orchestrator_agent.py)

#### 역할 및 책임
```python
class OrchestratorAgent:
    """
    시스템의 두뇌 역할을 하는 마스터 에이전트

    주요 책임:
    1. 워크플로우 관리 - 작업 순서 결정
    2. 에이전트 조정 - 작업 분배 및 결과 수집
    3. 에러 처리 - 시스템 레벨 예외 관리
    4. 결과 통합 - 최종 리포트 생성
    """
```

#### 내부 구조
```python
class OrchestratorAgent:
    def __init__(self):
        self.execution_log = []      # 실행 로그
        self.agents = {}            # 관리되는 에이전트들
        self.config = {}            # 시스템 설정
        self.workflow_state = {}     # 워크플로우 상태

    # Phase별 실행 관리
    def execute_integrated_backtest(self):
        try:
            # Phase 1: Data Loading
            data = self._delegate_to_data_agent()

            # Phase 2: Signal Generation
            signals = self._delegate_to_strategy_agent(data)

            # Phase 3: Backtest Execution
            results = self._delegate_to_service_agent(data, signals)

            # Phase 4: Result Consolidation
            return self._consolidate_results(results)

        except Exception as e:
            return self._handle_system_error(e)
```

#### 에이전트 위임 패턴
```python
def _delegate_to_data_agent(self, symbols, start_date, end_date):
    """
    Data Agent에게 작업 위임하는 표준 패턴
    """
    # 1. 작업 지시 생성
    prompt = self._generate_data_prompt(symbols, start_date, end_date)

    # 2. 에이전트 실행
    if 'data' in self.agents:
        result = self.agents['data'].load_market_data(
            nas_symbols=symbols['nas'],
            nys_symbols=symbols['nys'],
            start_date=start_date,
            end_date=end_date,
            prompt=prompt
        )
    else:
        # Fallback: 직접 실행
        result = self._fallback_data_loading()

    # 3. 결과 검증
    self._validate_data_result(result)

    # 4. 로깅
    self._log(f"Data Agent 작업 완료: {len(result)} 종목")

    return result
```

### 2. **Data Agent** (data_agent.py)

#### 데이터 파이프라인 아키텍처
```python
class DataAgent:
    """
    데이터 수집 및 전처리 전문 에이전트

    Pipeline:
    Raw MongoDB Data → Validation → Indicators → Quality Check → Output
    """

    def __init__(self):
        self.pipeline = DataPipeline([
            MongoDataLoader(),
            DataValidator(),
            IndicatorCalculator(),
            QualityChecker()
        ])
```

#### 기술지표 계산 엔진
```python
class SimpleTechnicalIndicators:
    """
    외부 라이브러리 의존성 없는 독립적 지표 계산
    """

    @staticmethod
    def calculate_ma(prices, period):
        """이동평균 계산"""
        return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """볼린저 밴드 계산"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev)
        }
```

#### 데이터 품질 관리
```python
class DataQualityManager:
    def __init__(self):
        self.quality_rules = [
            PriceRangeRule(),      # 가격 범위 검증
            VolumeConsistencyRule(), # 거래량 일관성
            DateContinuityRule(),   # 날짜 연속성
            OutlierDetectionRule()  # 이상치 감지
        ]

    def validate_data(self, data):
        results = {}
        for rule in self.quality_rules:
            results[rule.name] = rule.validate(data)

        # 품질 점수 계산
        quality_score = self._calculate_quality_score(results)

        return {
            'quality_score': quality_score,
            'validation_results': results,
            'recommendation': self._get_recommendation(quality_score)
        }
```

### 3. **Strategy Agent** (strategy_agent.py)

#### 전략 팩토리 패턴
```python
class StrategyFactory:
    """
    시장별 전략을 동적으로 생성하는 팩토리
    """

    def __init__(self):
        self.strategies = {
            'NASDAQ': NasdaqGrowthStrategy,
            'NYSE': NyseValueStrategy,
            'CUSTOM': CustomStrategy
        }

    def create_strategy(self, market_type, params):
        strategy_class = self.strategies.get(market_type)
        if strategy_class:
            return strategy_class(params)
        else:
            raise ValueError(f"Unknown market type: {market_type}")

class NasdaqGrowthStrategy:
    """
    NASDAQ 성장주 특화 전략
    """

    def __init__(self, params):
        self.params = {
            'ma_fast': params.get('ma_fast', 5),
            'ma_slow': params.get('ma_slow', 20),
            'rsi_oversold': params.get('rsi_oversold', 25),
            'volume_threshold': params.get('volume_threshold', 1.5),
            'momentum_period': params.get('momentum_period', 10)
        }

    def generate_signals(self, data):
        buy_signals = []
        sell_signals = []

        for i in range(1, len(data)):
            # 골든크로스 + RSI 과매도 + 거래량 급증
            if (self._is_golden_cross(data, i) and
                self._is_rsi_oversold(data, i) and
                self._is_volume_surge(data, i)):
                buy_signals.append(i)

            # 데드크로스 + RSI 과매수
            elif (self._is_dead_cross(data, i) and
                  self._is_rsi_overbought(data, i)):
                sell_signals.append(i)

        return buy_signals, sell_signals
```

#### 신호 품질 평가
```python
class SignalQualityEvaluator:
    """
    생성된 신호의 품질을 평가하는 클래스
    """

    def evaluate_signals(self, signals, market_data):
        return {
            'signal_count': len(signals),
            'signal_density': self._calculate_density(signals),
            'market_alignment': self._check_market_alignment(signals, market_data),
            'volatility_adjusted_score': self._adjust_for_volatility(signals),
            'confidence_level': self._calculate_confidence(signals)
        }

    def _calculate_density(self, signals):
        """신호 밀도 계산 - 너무 많거나 적으면 품질 저하"""
        total_periods = len(signals['buy_signals']) + len(signals['sell_signals'])
        if total_periods == 0:
            return 0

        # 적정 신호 밀도: 전체 기간의 5-15%
        density = total_periods / 250  # 1년 기준
        if 0.05 <= density <= 0.15:
            return 1.0
        elif density < 0.05:
            return density / 0.05  # 신호 부족
        else:
            return 0.15 / density  # 신호 과다
```

### 4. **Service Agent** (service_agent.py)

#### 백테스트 엔진 아키텍처
```python
class BacktestEngine:
    """
    고성능 백테스트 실행 엔진
    """

    def __init__(self, config):
        self.portfolio_manager = PortfolioManager(config)
        self.risk_manager = RiskManager(config)
        self.execution_engine = ExecutionEngine(config)
        self.performance_analyzer = PerformanceAnalyzer()

    def run_backtest(self, market_data, signals, start_date, end_date):
        # 초기화
        self.portfolio_manager.initialize(start_date)

        # 일별 시뮬레이션
        for date in pd.date_range(start_date, end_date):
            daily_data = self._get_daily_data(market_data, date)
            daily_signals = self._get_daily_signals(signals, date)

            # 신호 처리
            orders = self._process_signals(daily_signals, daily_data)

            # 리스크 검증
            validated_orders = self.risk_manager.validate_orders(orders)

            # 주문 실행
            executions = self.execution_engine.execute_orders(validated_orders)

            # 포트폴리오 업데이트
            self.portfolio_manager.update(executions, daily_data)

        # 성과 분석
        return self.performance_analyzer.analyze(
            self.portfolio_manager.get_history()
        )
```

#### 리스크 관리 시스템
```python
class RiskManager:
    """
    실시간 리스크 모니터링 및 제어
    """

    def __init__(self, config):
        self.position_limits = config['position_limits']
        self.risk_limits = config['risk_limits']
        self.stop_loss_rules = config['stop_loss']

    def validate_orders(self, orders):
        validated_orders = []

        for order in orders:
            # 포지션 크기 제한
            if self._check_position_limit(order):
                # 집중도 위험 검사
                if self._check_concentration_risk(order):
                    # 일일 손실 한도 검사
                    if self._check_daily_loss_limit(order):
                        validated_orders.append(order)
                    else:
                        self._log_risk_rejection(order, "daily_loss_limit")
                else:
                    self._log_risk_rejection(order, "concentration_risk")
            else:
                self._log_risk_rejection(order, "position_limit")

        return validated_orders

    def _check_position_limit(self, order):
        """포지션 크기 제한 검사"""
        current_position = self.portfolio.get_position(order.symbol)
        new_position_size = abs(current_position + order.quantity)

        max_position = self.portfolio.total_value * self.position_limits['max_position_size']

        return new_position_size * order.price <= max_position
```

### 5. **Helper Agent** (helper_agent.py)

#### 설정 관리 시스템
```python
class ConfigurationManager:
    """
    계층적 설정 관리 시스템
    """

    def __init__(self):
        self.config_hierarchy = [
            'user_config.yaml',      # 사용자 커스텀 설정 (최우선)
            'environment_config.yaml', # 환경별 설정
            'default_config.yaml'    # 기본 설정 (최하위)
        ]
        self.merged_config = {}

    def load_configuration(self):
        """계층적 설정 병합"""
        for config_file in reversed(self.config_hierarchy):
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    self.merged_config = self._deep_merge(
                        self.merged_config, config
                    )

        return self.merged_config

    def _deep_merge(self, dict1, dict2):
        """딕셔너리 깊은 병합"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
```

#### 시스템 모니터링
```python
class SystemMonitor:
    """
    실시간 시스템 상태 모니터링
    """

    def __init__(self):
        self.metrics = {
            'cpu_usage': CPUMonitor(),
            'memory_usage': MemoryMonitor(),
            'disk_io': DiskIOMonitor(),
            'network_io': NetworkIOMonitor(),
            'mongodb_status': MongoDBMonitor()
        }

    def get_system_health(self):
        health_report = {}
        overall_status = "healthy"

        for metric_name, monitor in self.metrics.items():
            try:
                status = monitor.get_status()
                health_report[metric_name] = status

                if status['status'] == 'critical':
                    overall_status = "critical"
                elif status['status'] == 'warning' and overall_status == "healthy":
                    overall_status = "warning"

            except Exception as e:
                health_report[metric_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                overall_status = "critical"

        return {
            'overall_status': overall_status,
            'metrics': health_report,
            'timestamp': datetime.now().isoformat()
        }
```

---

## 🌊 데이터 플로우

### 1. **전체 데이터 플로우 맵**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   MongoDB   │    │    Data     │    │  Strategy   │    │   Service   │
│  Database   │───▶│   Agent     │───▶│   Agent     │───▶│   Agent     │
│             │    │             │    │             │    │             │
│NasDataBase_D│    │• Data Load  │    │• Signal Gen │    │• Backtest   │
│NysDataBase_D│    │• Indicators │    │• Quality    │    │• Portfolio  │
│   15,113    │    │• Quality    │    │• Filter     │    │• Risk Mgmt  │
│   symbols   │    │  Check      │    │• Optimize   │    │• Analysis   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Raw Market   │    │Processed    │    │Trading      │    │Backtest     │
│Data         │    │Data +       │    │Signals      │    │Results      │
│             │    │Technical    │    │             │    │             │
│• OHLCV      │    │Indicators   │    │• Buy/Sell  │    │• Returns    │
│• Timestamps │    │             │    │• Confidence │    │• Trades     │
│• Volume     │    │• MA, RSI    │    │• Timing     │    │• Risk Stats │
│             │    │• Bollinger  │    │• Position   │    │• Drawdown   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 2. **데이터 변환 단계**

#### Stage 1: Raw Data Loading
```python
# MongoDB Collection → Python DataFrame
{
    'AAPL': {
        'Date': ['2023-01-01', '2023-01-02', ...],
        'Open': [150.0, 151.2, ...],
        'High': [152.1, 153.4, ...],
        'Low': [149.8, 150.9, ...],
        'Close': [151.0, 152.8, ...],
        'Volume': [1000000, 1200000, ...]
    }
}
```

#### Stage 2: Technical Indicators
```python
# Enhanced DataFrame with Indicators
{
    'AAPL_NASDAQ': {
        # Original OHLCV data
        'Date': [...], 'Open': [...], 'High': [...], 'Low': [...],
        'Close': [...], 'Volume': [...],

        # Moving Averages
        'MA5': [...], 'MA10': [...], 'MA20': [...], 'MA50': [...],

        # Momentum Indicators
        'RSI14': [...], 'MACD': [...], 'MACD_Signal': [...],
        'Stochastic_K': [...], 'Stochastic_D': [...],

        # Volatility Indicators
        'BB_Upper': [...], 'BB_Middle': [...], 'BB_Lower': [...],
        'ATR': [...], 'Volatility': [...]
    }
}
```

#### Stage 3: Trading Signals
```python
# Signal Generation Output
{
    'AAPL_NASDAQ': {
        'buy_signals': [
            {'date': '2023-03-15', 'price': 155.2, 'confidence': 0.85,
             'reasons': ['golden_cross', 'rsi_oversold', 'volume_surge']},
            {'date': '2023-07-22', 'price': 189.1, 'confidence': 0.72,
             'reasons': ['bollinger_bounce', 'momentum_up']}
        ],
        'sell_signals': [
            {'date': '2023-05-10', 'price': 175.8, 'confidence': 0.90,
             'reasons': ['dead_cross', 'rsi_overbought']},
            {'date': '2023-11-03', 'price': 182.4, 'confidence': 0.78,
             'reasons': ['resistance_level', 'volume_decline']}
        ]
    }
}
```

#### Stage 4: Backtest Results
```python
# Final Performance Analysis
{
    'performance_metrics': {
        'total_return': 0.0036,        # 0.36%
        'annualized_return': 0.0053,   # 0.53%
        'sharpe_ratio': 0.603,
        'max_drawdown': 0.0089,        # 0.89%
        'volatility': 0.0061           # 0.61%
    },
    'trade_statistics': {
        'total_trades': 61,
        'win_rate': 0.4643,            # 46.43%
        'avg_profit': 15234,
        'avg_loss': -12890,
        'profit_factor': 1.18
    },
    'portfolio_history': [
        {'date': '2023-01-01', 'value': 100000000, 'cash': 100000000, 'positions': {}},
        {'date': '2023-01-02', 'value': 100000000, 'cash': 98750000, 'positions': {'KO_NYSE': 19292}},
        # ... daily portfolio snapshots
    ]
}
```

### 3. **데이터 검증 파이프라인**

```python
class DataValidationPipeline:
    """
    다층 데이터 검증 시스템
    """

    def __init__(self):
        self.validators = [
            SchemaValidator(),      # 스키마 검증
            RangeValidator(),       # 값 범위 검증
            ConsistencyValidator(), # 일관성 검증
            CompletenessValidator() # 완전성 검증
        ]

    def validate(self, data):
        validation_results = {}

        for validator in self.validators:
            result = validator.validate(data)
            validation_results[validator.name] = result

            # 치명적 오류 시 즉시 중단
            if result['severity'] == 'critical':
                raise DataValidationError(
                    f"Critical validation error: {result['message']}"
                )

        return validation_results

class SchemaValidator:
    """DataFrame 스키마 검증"""

    def validate(self, data):
        required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = []

        for symbol_data in data.values():
            missing = [col for col in required_columns if col not in symbol_data.columns]
            missing_columns.extend(missing)

        if missing_columns:
            return {
                'severity': 'critical',
                'message': f"Missing required columns: {missing_columns}"
            }

        return {'severity': 'info', 'message': 'Schema validation passed'}
```

---

## 🔗 통신 프로토콜

### 1. **에이전트 간 통신 인터페이스**

#### Orchestrator → Agent 통신
```python
class AgentCommunicationProtocol:
    """
    표준화된 에이전트 통신 프로토콜
    """

    def __init__(self):
        self.message_format = {
            'header': {
                'sender': str,      # 발신자 에이전트
                'receiver': str,    # 수신자 에이전트
                'message_type': str, # 메시지 타입
                'timestamp': datetime,
                'correlation_id': str # 추적용 ID
            },
            'payload': {
                'action': str,      # 실행할 액션
                'parameters': dict, # 액션 파라미터
                'context': dict     # 추가 컨텍스트
            },
            'metadata': {
                'priority': int,    # 우선순위 (1-10)
                'timeout': int,     # 타임아웃 (초)
                'retry_count': int  # 재시도 횟수
            }
        }

    def create_message(self, sender, receiver, action, parameters, **kwargs):
        return {
            'header': {
                'sender': sender,
                'receiver': receiver,
                'message_type': 'command',
                'timestamp': datetime.now(),
                'correlation_id': str(uuid.uuid4())
            },
            'payload': {
                'action': action,
                'parameters': parameters,
                'context': kwargs.get('context', {})
            },
            'metadata': {
                'priority': kwargs.get('priority', 5),
                'timeout': kwargs.get('timeout', 300),
                'retry_count': kwargs.get('retry_count', 3)
            }
        }
```

#### 비동기 통신 지원
```python
import asyncio
from typing import Callable, Awaitable

class AsyncAgentCommunicator:
    """
    비동기 에이전트 통신 관리자
    """

    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.response_handlers = {}
        self.running = False

    async def send_message_async(self, message):
        """비동기 메시지 전송"""
        await self.message_queue.put(message)

        # 응답 대기를 위한 Future 생성
        correlation_id = message['header']['correlation_id']
        future = asyncio.Future()
        self.response_handlers[correlation_id] = future

        # 타임아웃 설정
        timeout = message['metadata']['timeout']
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            del self.response_handlers[correlation_id]
            raise TimeoutError(f"Message {correlation_id} timed out")

    async def process_messages(self):
        """메시지 처리 루프"""
        while self.running:
            try:
                message = await self.message_queue.get()
                await self._route_message(message)
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _route_message(self, message):
        """메시지 라우팅"""
        receiver = message['header']['receiver']
        action = message['payload']['action']

        # 에이전트별 핸들러 호출
        if receiver == 'data_agent':
            response = await self._handle_data_agent_message(message)
        elif receiver == 'strategy_agent':
            response = await self._handle_strategy_agent_message(message)
        # ...

        # 응답 전달
        correlation_id = message['header']['correlation_id']
        if correlation_id in self.response_handlers:
            self.response_handlers[correlation_id].set_result(response)
            del self.response_handlers[correlation_id]
```

### 2. **에러 처리 및 복구 메커니즘**

```python
class AgentErrorHandler:
    """
    에이전트 레벨 에러 처리
    """

    def __init__(self):
        self.retry_policies = {
            'network_error': RetryPolicy(max_attempts=3, backoff='exponential'),
            'data_error': RetryPolicy(max_attempts=2, backoff='linear'),
            'calculation_error': RetryPolicy(max_attempts=1, backoff='none')
        }

        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,    # 5회 연속 실패 시 차단
            recovery_timeout=60,    # 60초 후 복구 시도
            expected_exception=Exception
        )

    def handle_agent_error(self, error, context):
        """에이전트 에러 처리"""
        error_type = self._classify_error(error)

        if error_type in self.retry_policies:
            policy = self.retry_policies[error_type]

            for attempt in range(policy.max_attempts):
                try:
                    # 재시도 로직
                    if policy.backoff == 'exponential':
                        delay = 2 ** attempt
                    elif policy.backoff == 'linear':
                        delay = attempt + 1
                    else:
                        delay = 0

                    time.sleep(delay)

                    # 원본 작업 재실행
                    return context['retry_function']()

                except Exception as retry_error:
                    if attempt == policy.max_attempts - 1:
                        # 최종 재시도 실패
                        self._escalate_error(retry_error, context)
                    continue
        else:
            # 재시도 불가능한 에러
            self._escalate_error(error, context)

    def _classify_error(self, error):
        """에러 분류"""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return 'network_error'
        elif isinstance(error, (ValueError, KeyError)):
            return 'data_error'
        elif isinstance(error, (ArithmeticError, OverflowError)):
            return 'calculation_error'
        else:
            return 'unknown_error'
```

---

## 🚀 확장성 설계

### 1. **플러그인 아키텍처**

```python
class PluginManager:
    """
    동적 플러그인 로딩 및 관리
    """

    def __init__(self):
        self.plugins = {}
        self.plugin_registry = {}

    def register_plugin(self, plugin_type, plugin_class):
        """플러그인 등록"""
        if plugin_type not in self.plugin_registry:
            self.plugin_registry[plugin_type] = []
        self.plugin_registry[plugin_type].append(plugin_class)

    def load_plugin(self, plugin_type, plugin_name, config):
        """플러그인 동적 로딩"""
        if plugin_type in self.plugin_registry:
            for plugin_class in self.plugin_registry[plugin_type]:
                if plugin_class.__name__ == plugin_name:
                    instance = plugin_class(config)
                    self.plugins[f"{plugin_type}_{plugin_name}"] = instance
                    return instance

        raise PluginNotFoundError(f"Plugin {plugin_name} of type {plugin_type} not found")

# 사용 예시: 새로운 전략 플러그인
@register_plugin('strategy', 'MLStrategy')
class MachineLearningStrategy:
    """
    머신러닝 기반 전략 플러그인
    """

    def __init__(self, config):
        self.model = self._load_model(config['model_path'])
        self.features = config['features']

    def generate_signals(self, data):
        # ML 모델 기반 신호 생성
        features = self._extract_features(data)
        predictions = self.model.predict(features)
        return self._convert_to_signals(predictions)
```

### 2. **마이크로서비스 지원**

```python
class MicroserviceAdapter:
    """
    마이크로서비스 환경 지원을 위한 어댑터
    """

    def __init__(self, service_config):
        self.service_registry = ServiceRegistry(service_config['registry_url'])
        self.load_balancer = LoadBalancer(service_config['lb_strategy'])
        self.circuit_breaker = CircuitBreaker()

    async def call_external_service(self, service_name, method, data):
        """외부 서비스 호출"""
        # 서비스 디스커버리
        service_instances = await self.service_registry.discover(service_name)

        # 로드 밸런싱
        selected_instance = self.load_balancer.select(service_instances)

        # 서킷 브레이커 적용
        with self.circuit_breaker:
            try:
                response = await self._make_http_request(
                    selected_instance, method, data
                )
                return response
            except Exception as e:
                # 실패한 인스턴스 마킹
                self.load_balancer.mark_unhealthy(selected_instance)
                raise

# REST API 엔드포인트 정의
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/v1/backtest")
async def run_backtest(request: BacktestRequest):
    """RESTful 백테스트 실행 엔드포인트"""
    orchestrator = OrchestratorAgent()

    try:
        results = await orchestrator.execute_integrated_backtest_async(
            start_date=request.start_date,
            end_date=request.end_date,
            symbols=request.symbols
        )

        return BacktestResponse(
            status="success",
            results=results,
            execution_time=results['execution_time']
        )

    except Exception as e:
        return BacktestResponse(
            status="error",
            error=str(e),
            execution_time=0
        )
```

### 3. **스케일링 전략**

#### 수평 확장 (Horizontal Scaling)
```python
class AgentCluster:
    """
    에이전트 클러스터 관리
    """

    def __init__(self, cluster_config):
        self.nodes = []
        self.work_distributor = WorkDistributor(cluster_config['strategy'])
        self.result_aggregator = ResultAggregator()

    def add_node(self, node_config):
        """새 노드 추가"""
        node = AgentNode(node_config)
        self.nodes.append(node)

        # 기존 워크로드 재분배
        self.work_distributor.rebalance(self.nodes)

    def process_large_dataset(self, symbols, start_date, end_date):
        """대용량 데이터셋 분산 처리"""
        # 심볼별로 작업 분할
        work_chunks = self.work_distributor.split_work(symbols)

        # 각 노드에 작업 할당
        futures = []
        for i, chunk in enumerate(work_chunks):
            node = self.nodes[i % len(self.nodes)]
            future = node.process_symbols_async(chunk, start_date, end_date)
            futures.append(future)

        # 결과 수집 및 병합
        results = await asyncio.gather(*futures)
        return self.result_aggregator.merge_results(results)

class WorkDistributor:
    """
    작업 분산 전략
    """

    def __init__(self, strategy='round_robin'):
        self.strategy = strategy
        self.strategies = {
            'round_robin': self._round_robin_distribution,
            'least_loaded': self._least_loaded_distribution,
            'hash_based': self._hash_based_distribution
        }

    def split_work(self, symbols):
        """심볼 목록을 청크로 분할"""
        return self.strategies[self.strategy](symbols)

    def _round_robin_distribution(self, symbols):
        """라운드 로빈 방식 분배"""
        chunk_size = len(symbols) // len(self.nodes)
        return [symbols[i:i+chunk_size] for i in range(0, len(symbols), chunk_size)]
```

---

## ⚡ 성능 최적화

### 1. **메모리 최적화**

```python
class MemoryOptimizer:
    """
    메모리 사용량 최적화
    """

    @staticmethod
    def optimize_dataframe_dtypes(df):
        """DataFrame 데이터 타입 최적화"""
        optimized_df = df.copy()

        # 정수 컬럼 최적화
        for col in optimized_df.select_dtypes(include=['int64']).columns:
            col_min = optimized_df[col].min()
            col_max = optimized_df[col].max()

            if col_min >= 0:  # unsigned 가능
                if col_max < 255:
                    optimized_df[col] = optimized_df[col].astype('uint8')
                elif col_max < 65535:
                    optimized_df[col] = optimized_df[col].astype('uint16')
                elif col_max < 4294967295:
                    optimized_df[col] = optimized_df[col].astype('uint32')
            else:  # signed 필요
                if col_min >= -128 and col_max <= 127:
                    optimized_df[col] = optimized_df[col].astype('int8')
                elif col_min >= -32768 and col_max <= 32767:
                    optimized_df[col] = optimized_df[col].astype('int16')

        # 실수 컬럼 최적화
        for col in optimized_df.select_dtypes(include=['float64']).columns:
            optimized_df[col] = optimized_df[col].astype('float32')

        return optimized_df

    @staticmethod
    def use_categorical_data(df, threshold=0.5):
        """카테고리 데이터 활용"""
        for col in df.columns:
            if df[col].dtype == 'object':
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < threshold:
                    df[col] = df[col].astype('category')

        return df
```

### 2. **연산 최적화**

```python
import numba
import numpy as np

class ComputationOptimizer:
    """
    연산 최적화 클래스
    """

    @staticmethod
    @numba.jit(nopython=True)
    def fast_moving_average(prices, window):
        """JIT 컴파일된 이동평균 계산"""
        n = len(prices)
        ma = np.empty(n)
        ma[:window-1] = np.nan

        for i in range(window-1, n):
            ma[i] = np.mean(prices[i-window+1:i+1])

        return ma

    @staticmethod
    @numba.jit(nopython=True)
    def fast_rsi(prices, period=14):
        """JIT 컴파일된 RSI 계산"""
        n = len(prices)
        rsi = np.empty(n)
        rsi[:period] = np.nan

        # 초기 평균 계산
        gains = np.zeros(n)
        losses = np.zeros(n)

        for i in range(1, n):
            change = prices[i] - prices[i-1]
            gains[i] = max(0, change)
            losses[i] = max(0, -change)

        avg_gain = np.mean(gains[1:period+1])
        avg_loss = np.mean(losses[1:period+1])

        # EMA 방식으로 RSI 계산
        alpha = 1.0 / period
        for i in range(period, n):
            avg_gain = (1 - alpha) * avg_gain + alpha * gains[i]
            avg_loss = (1 - alpha) * avg_loss + alpha * losses[i]

            if avg_loss == 0:
                rsi[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))

        return rsi
```

### 3. **캐싱 전략**

```python
class DataCache:
    """
    지능형 데이터 캐싱 시스템
    """

    def __init__(self, max_memory_mb=1024):
        self.cache = {}
        self.access_times = {}
        self.max_memory = max_memory_mb * 1024 * 1024  # MB to bytes
        self.current_memory = 0

    def get(self, key):
        """캐시에서 데이터 조회"""
        if key in self.cache:
            self.access_times[key] = time.time()  # LRU 업데이트
            return self.cache[key]
        return None

    def put(self, key, data):
        """캐시에 데이터 저장"""
        data_size = self._get_size(data)

        # 메모리 제한 확인
        while self.current_memory + data_size > self.max_memory:
            self._evict_lru()

        self.cache[key] = data
        self.access_times[key] = time.time()
        self.current_memory += data_size

    def _get_size(self, data):
        """데이터 크기 계산"""
        if hasattr(data, 'memory_usage'):
            return data.memory_usage(deep=True).sum()
        else:
            return sys.getsizeof(data)

    def _evict_lru(self):
        """LRU 방식으로 캐시 제거"""
        if not self.cache:
            return

        # 가장 오래된 항목 찾기
        oldest_key = min(self.access_times.keys(), key=self.access_times.get)

        # 제거
        data_size = self._get_size(self.cache[oldest_key])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        self.current_memory -= data_size

# 사용 예시
cache = DataCache(max_memory_mb=512)

def cached_indicator_calculation(symbol, indicator_type, params):
    """캐시된 지표 계산"""
    cache_key = f"{symbol}_{indicator_type}_{hash(str(params))}"

    # 캐시 확인
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # 계산 실행
    result = calculate_indicator(symbol, indicator_type, params)

    # 캐시 저장
    cache.put(cache_key, result)

    return result
```

---

## 📝 요약

이 Multi-Agent Trading System은 다음과 같은 아키텍처 특징을 가집니다:

### 🎯 **핵심 설계 원칙**
1. **Single Responsibility**: 각 에이전트는 명확한 단일 책임
2. **Loose Coupling**: 에이전트 간 독립적 개발/배포 가능
3. **High Cohesion**: 에이전트 내부 기능들의 높은 응집도
4. **Extensibility**: 플러그인 방식으로 확장 가능

### 🔧 **기술적 장점**
1. **모듈화**: 각 기능별 독립적 개발 및 테스트
2. **확장성**: 수평/수직 확장 지원
3. **유지보수성**: 명확한 책임 분리로 쉬운 유지보수
4. **성능**: JIT 컴파일, 캐싱, 메모리 최적화

### 🚀 **운영상 이점**
1. **장애 격리**: 한 에이전트 장애가 전체 시스템에 영향 최소화
2. **배포 유연성**: 에이전트별 독립 배포 가능
3. **모니터링**: 에이전트별 상세 모니터링 및 로깅
4. **테스트**: 단위/통합 테스트 용이성

이러한 아키텍처를 통해 **신뢰성**, **확장성**, **유지보수성**을 모두 갖춘 엔터프라이즈급 트레이딩 시스템을 구현했습니다.