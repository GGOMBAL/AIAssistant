# Unified Backtest & Trading System Architecture

**Version**: 3.0
**Date**: 2025-09-26
**Managed by**: Orchestrator Agent

## 🎯 개요

백테스트와 실시간 트레이딩 시스템이 **동일한 신호 생성 로직**을 사용하는 통합 아키텍처입니다.
**유일한 차이점은 데이터 시점**입니다:
- **백테스트**: 하루 전(t-1) 데이터 사용
- **트레이딩**: 실시간(t) 데이터 사용

## 🏗️ 통합 시스템 아키텍처

```
                    Unified Multi-Agent Trading System
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Main Orchestrator Agent                      │
    │  ┌─────────────────────────────────────────────────────────┐    │
    │  │              Core Engine Manager                        │    │
    │  │  • Mode Selection (BACKTEST | TRADING)                 │    │
    │  │  • Data Timeline Control (t-1 | t)                     │    │
    │  │  • Signal Engine (Common Logic)                        │    │
    │  │  • Risk Manager (Common Logic)                         │    │
    │  │  • Execution Engine (Mock | Real)                      │    │
    │  └─────────────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────────┘
                │           │           │           │
                ▼           ▼           ▼           ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │Data Agent   │ │Strategy     │ │Service      │ │Helper       │
      │(Common Data)│ │Agent        │ │Agent        │ │Agent        │
      │Provider     │ │(Time Control│ │(Execution)  │ │(API/Broker) │
      │             │ │+ Signal Gen)│ │             │ │             │
      └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

## 📋 핵심 설계 원칙

### 1. **신호 생성 통합 원칙**
```python
class UnifiedSignalEngine:
    """백테스트와 트레이딩에서 동일한 신호 생성 로직"""

    def generate_signals(self, market_data: MarketData, mode: str):
        """
        공통 신호 생성 로직

        Args:
            market_data: 시장 데이터 (시점은 mode에 따라 결정)
            mode: "BACKTEST" | "TRADING"
        """
        # 동일한 알고리즘 사용
        rsi_signals = self._calculate_rsi_signals(market_data)
        macd_signals = self._calculate_macd_signals(market_data)
        volume_signals = self._calculate_volume_signals(market_data)

        # 통합 신호 생성
        return self._combine_signals([rsi_signals, macd_signals, volume_signals])
```

### 2. **신호 생성 시점 제어 원칙 (Strategy Agent에서 제어)**
```python
class UnifiedStrategyAgent:
    """전략 에이전트에서 데이터 시점 제어"""

    def generate_signals(self, market_data: MarketData, mode: str):
        """
        신호 생성 시 데이터 시점 선택

        Args:
            market_data: 전체 시계열 데이터 (Data Agent에서 동일하게 제공)
            mode: "BACKTEST" | "TRADING"
        """
        if mode == "BACKTEST":
            # 백테스트: t-1 (하루 전) 데이터로 신호 생성
            signal_data = market_data.shift(1)  # 하루 전 데이터 사용
        elif mode == "TRADING":
            # 트레이딩: t (마지막/최신) 데이터로 신호 생성
            signal_data = market_data  # 최신 데이터 사용

        # 동일한 신호 생성 알고리즘 적용 (시점만 다름)
        rsi_signals = self._calculate_rsi_signals(signal_data)
        macd_signals = self._calculate_macd_signals(signal_data)
        return self._combine_signals([rsi_signals, macd_signals])
```

### 3. **실행 엔진 분리 원칙**
```python
class UnifiedExecutionEngine:
    """백테스트/실거래 실행 엔진"""

    def execute_signal(self, signal: TradingSignal, mode: str):
        if mode == "BACKTEST":
            # 모의 실행 (수수료, 슬리피지 시뮬레이션)
            return self._mock_execution(signal)
        elif mode == "TRADING":
            # 실제 브로커 API 호출
            return self._real_execution(signal)
```

## 🔄 모드별 동작 차이

### 백테스트 모드 (BACKTEST)
```python
config = {
    "mode": "BACKTEST",
    "data_timeline": {
        "offset_days": 1,           # t-1 데이터 사용
        "start_date": "2023-01-01",
        "end_date": "2024-01-01"
    },
    "execution": {
        "type": "SIMULATION",
        "commission": 0.002,        # 수수료 시뮬레이션
        "slippage": 0.001          # 슬리피지 시뮬레이션
    }
}
```

### 트레이딩 모드 (TRADING)
```python
config = {
    "mode": "TRADING",
    "data_timeline": {
        "offset_days": 0,           # t (실시간) 데이터 사용
        "realtime": True,
        "websocket": True
    },
    "execution": {
        "type": "REAL",
        "broker_api": "KIS",        # 실제 브로커 연결
        "safety_checks": True
    }
}
```

## 🧩 에이전트별 역할 재정의

### 1. **Main Orchestrator Agent**
```python
class MainOrchestrator:
    """통합 오케스트레이터 - 모드에 따른 동작 제어"""

    def __init__(self, mode: str = "TRADING"):
        self.mode = mode  # "BACKTEST" | "TRADING"
        self.signal_engine = UnifiedSignalEngine()
        self.execution_engine = UnifiedExecutionEngine()
        self.timeline_manager = TimelineDataManager()

    async def run_system(self):
        """모드에 관계없이 동일한 워크플로우"""
        # 1. 데이터 수집 (시점만 다름)
        market_data = await self.timeline_manager.get_market_data(
            symbols=self.config['symbols'],
            mode=self.mode
        )

        # 2. 신호 생성 (동일한 로직)
        signals = await self.signal_engine.generate_signals(
            market_data, self.mode
        )

        # 3. 실행 (방식만 다름)
        for signal in signals:
            await self.execution_engine.execute_signal(signal, self.mode)
```

### 2. **Data Agent (데이터 에이전트)**
**역할**: 공통 데이터 제공 (모드 무관)
```python
class DataAgent:
    """통합 데이터 에이전트 - 동일한 데이터를 제공"""

    async def get_market_data(self, symbols: List[str]):
        """모든 시계열 데이터 제공 (모드 무관)"""
        # MongoDB에서 전체 시계열 데이터 조회 (백테스트/트레이딩 공통)
        # Strategy Agent가 필요한 시점의 데이터를 선택
        return await self.get_full_timeseries_data(symbols)

    async def calculate_technical_indicators(self, data):
        """기술지표 계산 (공통 로직)"""
        # RSI, MACD, Bollinger Bands 등
        # 백테스트/트레이딩 모드 관계없이 동일한 계산
        indicators = {}
        indicators['RSI'] = self._calculate_rsi(data)
        indicators['MACD'] = self._calculate_macd(data)
        indicators['BB'] = self._calculate_bollinger_bands(data)
        return indicators
```

### 3. **Strategy Agent (전략 에이전트)**
**역할**: 시점 제어 + 신호 생성 로직 (핵심!)
```python
class StrategyAgent:
    """통합 전략 에이전트 - 시점 제어 담당"""

    async def generate_trading_signals(self, market_data, mode: str):
        """데이터 시점 제어 + 동일한 신호 생성 로직"""

        # 🎯 핵심: 모드에 따른 데이터 시점 선택
        if mode == "BACKTEST":
            # 백테스트: t-1 (하루 전) 데이터로 신호 생성
            signal_data = market_data.shift(1)  # 하루 전 데이터
        elif mode == "TRADING":
            # 트레이딩: t (마지막/최신) 데이터로 신호 생성
            signal_data = market_data  # 최신 데이터

        # Data Agent에서 기술지표 계산 (시점 적용된 데이터로)
        indicators = await self.data_agent.calculate_technical_indicators(signal_data)

        # 🔄 동일한 신호 생성 알고리즘 (모드 무관)
        signals = []

        # 공통 신호 로직 1: RSI 기반 신호
        rsi_signals = self._generate_rsi_signals(indicators['RSI'])

        # 공통 신호 로직 2: MACD 기반 신호
        macd_signals = self._generate_macd_signals(indicators['MACD'])

        # 공통 신호 로직 3: 볼밴 기반 신호
        bb_signals = self._generate_bollinger_signals(indicators['BB'])

        # 통합 신고 필터링 (동일 로직)
        final_signals = self._filter_and_combine_signals([
            rsi_signals, macd_signals, bb_signals
        ])

        return final_signals

    def _generate_rsi_signals(self, rsi_data):
        """RSI 신호 - 백테스트/트레이딩 완전 동일"""
        # 과매도/과매수 구간 동일 로직
        buy_signals = rsi_data < 30
        sell_signals = rsi_data > 70
        return {'buy': buy_signals, 'sell': sell_signals}
```

### 4. **Service Agent (서비스 에이전트)**
**역할**: 모드별 실행 및 성과 분석
```python
class ServiceAgent:
    """통합 서비스 에이전트"""

    async def execute_signals(self, signals: List[TradingSignal], mode: str):
        """모드별 실행"""
        if mode == "BACKTEST":
            return await self._backtest_execution(signals)
        else:
            return await self._live_execution(signals)

    async def _backtest_execution(self, signals):
        """백테스트 실행 - 시뮬레이션"""
        results = []
        for signal in signals:
            # 수수료, 슬리피지 고려한 모의 체결
            execution_price = signal.price * (1 + self.slippage)
            commission = execution_price * signal.quantity * self.commission_rate

            result = {
                'signal': signal,
                'executed_price': execution_price,
                'commission': commission,
                'timestamp': signal.timestamp,
                'mode': 'BACKTEST'
            }
            results.append(result)
        return results

    async def _live_execution(self, signals):
        """실시간 실행 - 실제 주문"""
        results = []
        for signal in signals:
            # 실제 브로커 API 호출
            order_result = await self.broker_api.place_order(
                symbol=signal.symbol,
                side=signal.side,
                quantity=signal.quantity,
                price=signal.price
            )

            result = {
                'signal': signal,
                'order_result': order_result,
                'timestamp': datetime.now(),
                'mode': 'TRADING'
            }
            results.append(result)
        return results
```

### 5. **Helper Agent (헬퍼 에이전트)**
**역할**: 모드별 외부 연동
```python
class HelperAgent:
    """통합 헬퍼 에이전트"""

    async def get_broker_connection(self, mode: str):
        """모드별 브로커 연결"""
        if mode == "BACKTEST":
            # 모의 브로커 (로컬 시뮬레이션)
            return MockBrokerAPI()
        else:
            # 실제 브로커 API
            return KISBrokerAPI()

    async def send_notification(self, message: str, mode: str):
        """모드별 알림"""
        if mode == "BACKTEST":
            # 백테스트 결과만 로그에 기록
            self.logger.info(f"[BACKTEST] {message}")
        else:
            # 실거래는 텔레그램 알림
            await self.telegram.send_message(message)
```

## 🚀 통합 시스템 실행 방법

### 1. **백테스트 모드 실행**
```bash
python main_auto_trade.py --mode BACKTEST \
    --start-date 2023-01-01 \
    --end-date 2024-01-01 \
    --symbols AAPL,MSFT,GOOGL
```

### 2. **실시간 트레이딩 모드 실행**
```bash
python main_auto_trade.py --mode TRADING \
    --realtime True \
    --symbols AAPL,MSFT,GOOGL
```

### 3. **통합 시스템 설정**
```python
# main_auto_trade.py 수정
async def main():
    """통합 메인 함수"""
    # 명령행 인자로 모드 결정
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['BACKTEST', 'TRADING'],
                       default='TRADING')
    parser.add_argument('--start-date', default='2023-01-01')
    parser.add_argument('--end-date', default='2024-01-01')
    parser.add_argument('--symbols', default='AAPL,MSFT,GOOGL')

    args = parser.parse_args()

    # 통합 오케스트레이터 초기화
    orchestrator = UnifiedOrchestrator(
        mode=args.mode,
        symbols=args.symbols.split(','),
        start_date=args.start_date,
        end_date=args.end_date
    )

    # 모드에 관계없이 동일한 실행
    await orchestrator.run()
```

## 📊 신호 검증 시스템

### 신호 일관성 검증
```python
class SignalConsistencyValidator:
    """백테스트와 실거래 신호 일관성 검증"""

    async def validate_signal_consistency(self):
        """동일한 데이터에서 동일한 신호 생성 확인"""

        # 동일한 과거 데이터로 테스트
        test_date = "2024-01-01"
        test_data = await self.data_agent.get_historical_data(
            date=test_date, symbols=['AAPL']
        )

        # 백테스트 모드로 신호 생성
        backtest_signals = await self.strategy_agent.generate_signals(
            test_data, mode="BACKTEST"
        )

        # 동일 데이터로 트레이딩 모드 신호 생성
        trading_signals = await self.strategy_agent.generate_signals(
            test_data, mode="TRADING"
        )

        # 신호 일치성 검증
        assert backtest_signals == trading_signals, "신호 불일치 발생!"

        print("✅ 신호 일관성 검증 통과")
```

## 🎯 성능 지표 통합

### 백테스트 vs 실거래 성과 비교
```python
class PerformanceComparator:
    """백테스트와 실거래 성과 비교"""

    def compare_performance(self, backtest_results, trading_results):
        """성과 비교 분석"""

        comparison = {
            'backtest': {
                'total_return': self._calculate_return(backtest_results),
                'sharpe_ratio': self._calculate_sharpe(backtest_results),
                'max_drawdown': self._calculate_drawdown(backtest_results),
                'win_rate': self._calculate_win_rate(backtest_results)
            },
            'trading': {
                'total_return': self._calculate_return(trading_results),
                'sharpe_ratio': self._calculate_sharpe(trading_results),
                'max_drawdown': self._calculate_drawdown(trading_results),
                'win_rate': self._calculate_win_rate(trading_results)
            }
        }

        # 성과 차이 분석
        performance_gap = {
            'return_gap': comparison['trading']['total_return'] -
                         comparison['backtest']['total_return'],
            'sharpe_gap': comparison['trading']['sharpe_ratio'] -
                         comparison['backtest']['sharpe_ratio']
        }

        return comparison, performance_gap
```

## 📋 구현 우선순위

### Phase 1: 핵심 통합 (2주)
1. **UnifiedSignalEngine** 구현
2. **TimelineDataManager** 구현
3. **모드별 실행 엔진** 분리
4. **기본 백테스트 기능** 통합

### Phase 2: 고급 기능 (2주)
1. **신호 일관성 검증** 시스템
2. **성과 비교 분석** 도구
3. **실시간 모니터링** 통합
4. **리스크 관리** 공통화

### Phase 3: 최적화 (1주)
1. **성능 최적화**
2. **UI/UX 개선**
3. **문서 정리**
4. **테스트 케이스** 완성

## 🔧 기술 스택

### 공통 컴포넌트
- **Signal Engine**: 동일한 알고리즘 로직
- **Risk Manager**: 공통 리스크 규칙
- **Data Models**: 통합 데이터 구조
- **Performance Analytics**: 통합 성과 분석

### 모드별 컴포넌트
- **Data Source**: MongoDB(백테스트) vs WebSocket(실거래)
- **Execution**: Mock(백테스트) vs Real API(실거래)
- **Monitoring**: Log(백테스트) vs Real-time UI(실거래)

---

**결과**: 하나의 통합 시스템에서 백테스트와 실시간 거래가 **동일한 신호 로직**을 사용하며, **데이터 시점만** 다르게 동작하는 완전한 아키텍처를 설계했습니다!