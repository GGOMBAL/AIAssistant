# 🚀 Auto Trade Service 구현 계획

**작성일**: 2025-09-23
**버전**: 1.0
**목적**: Multi-Agent Trading System의 실시간 자동매매 서비스 구현

---

## 📋 프로젝트 개요

### 목표
기존 백테스트 전략을 실제 매매에 적용하여 **실시간 자동매매 시스템** 구축

### 핵심 요구사항
1. **WebSocket 실시간 데이터** 수신 및 처리
2. **전략 엔진**과 연동하여 매매 신호 생성
3. **KIS API**를 통한 실제 주문 실행
4. **계좌 분석** 및 **포지션 사이징** 서비스 연동
5. **실시간 모니터링** 및 사용자 인터페이스

---

## 🏗️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────────────────────────────────────────────────────────┐
│                    Auto Trade Service Layer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Account   │    │  Position   │    │ Live Price  │         │
│  │  Analysis   │◄──►│   Sizing    │◄──►│   Service   │         │
│  │  Service    │    │  Service    │    │             │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         ▲                   ▲                   ▲              │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Auto Trade Service Core                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │   │
│  │  │ Signal  │  │ Risk    │  │ Order   │  │ Monitor │   │   │
│  │  │ Engine  │  │ Manager │  │ Manager │  │ Service │   │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               ▲                                │
│                               │                                │
│                               ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                API Order Service                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │   │
│  │  │ KIS Helper  │    │ Order Queue │    │ Error       │ │   │
│  │  │ Module      │    │ Manager     │    │ Handler     │ │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                   ┌─────────────────────┐
                   │   WebSocket         │
                   │   Real-time Data    │
                   │   (KIS API)         │
                   └─────────────────────┘
```

---

## 🔧 Service Layer 구조

### 1. Auto Trade Service Core
**파일**: `project/service/auto_trade_service.py`

```python
class AutoTradeService:
    """실시간 자동매매 핵심 서비스"""

    def __init__(self, config: Dict):
        self.signal_engine = SignalEngine()
        self.risk_manager = RiskManager()
        self.order_manager = OrderManager()
        self.monitor_service = MonitorService()

    async def start_trading(self):
        """자동매매 시작"""

    async def stop_trading(self):
        """자동매매 중지"""

    async def process_market_data(self, data: Dict):
        """실시간 시장 데이터 처리"""
```

### 2. Live Price Service
**파일**: `project/service/live_price_service.py`

```python
class LivePriceService:
    """실시간 가격 데이터 수신 및 관리"""

    def __init__(self, websocket_config: Dict):
        self.websocket_manager = WebSocketManager()
        self.price_cache = {}
        self.subscribers = []

    async def connect_websocket(self):
        """WebSocket 연결"""

    async def subscribe_symbol(self, symbol: str):
        """종목 구독"""

    async def on_price_update(self, symbol: str, price_data: Dict):
        """가격 업데이트 이벤트"""
```

### 3. Account Analysis Service
**파일**: `project/service/account_analysis_service.py`

```python
class AccountAnalysisService:
    """계좌 분석 서비스"""

    def __init__(self, kis_helper: KISHelper):
        self.kis_helper = kis_helper
        self.holdings_cache = {}

    async def get_current_holdings(self) -> Dict:
        """현재 보유 종목 조회"""

    async def calculate_portfolio_metrics(self) -> Dict:
        """포트폴리오 지표 계산"""

    async def get_available_cash(self) -> float:
        """매수 가능 현금 조회"""
```

### 4. Position Sizing Service
**파일**: `project/service/position_sizing_service.py`

```python
class PositionSizingService:
    """포지션 사이징 서비스"""

    def __init__(self, strategy_config: Dict):
        self.risk_config = strategy_config['risk']
        self.candidates_cache = {}

    async def get_buy_candidates(self) -> List[Dict]:
        """매수 후보 종목 조회"""

    async def calculate_position_size(self, symbol: str, price: float) -> int:
        """포지션 크기 계산"""

    async def apply_risk_constraints(self, orders: List[Dict]) -> List[Dict]:
        """리스크 제약 조건 적용"""
```

### 5. API Order Service
**파일**: `project/service/api_order_service.py`

```python
class APIOrderService:
    """API 주문 서비스"""

    def __init__(self, kis_helper: KISHelper):
        self.kis_helper = kis_helper
        self.order_queue = asyncio.Queue()
        self.pending_orders = {}

    async def submit_buy_order(self, symbol: str, quantity: int, price: float) -> str:
        """매수 주문 제출"""

    async def submit_sell_order(self, symbol: str, quantity: int, price: float) -> str:
        """매도 주문 제출"""

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
```

---

## 📡 인터페이스 정의

### 1. Service Interface Protocol
**파일**: `project/interfaces/service_interfaces.py`

```python
from typing import Protocol, Dict, List, Any, Optional
from abc import abstractmethod

class ILivePriceService(Protocol):
    """실시간 가격 서비스 인터페이스"""

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""

    @abstractmethod
    async def subscribe_price_updates(self, symbol: str, callback: callable):
        """가격 업데이트 구독"""

class IAccountAnalysisService(Protocol):
    """계좌 분석 서비스 인터페이스"""

    @abstractmethod
    async def get_holdings(self) -> Dict[str, Dict]:
        """보유 종목 조회"""

    @abstractmethod
    async def get_portfolio_value(self) -> float:
        """포트폴리오 총 가치"""

class IPositionSizingService(Protocol):
    """포지션 사이징 서비스 인터페이스"""

    @abstractmethod
    async def calculate_buy_quantity(self, symbol: str, price: float) -> int:
        """매수 수량 계산"""

    @abstractmethod
    async def get_candidates(self) -> List[str]:
        """매수 후보 종목"""

class IAPIOrderService(Protocol):
    """API 주문 서비스 인터페이스"""

    @abstractmethod
    async def place_order(self, order: Dict) -> str:
        """주문 제출"""

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict:
        """주문 상태 조회"""
```

### 2. Data Transfer Objects
**파일**: `project/models/trading_models.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import datetime

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

@dataclass
class PriceData:
    """실시간 가격 데이터"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime.datetime
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None

@dataclass
class TradingSignal:
    """매매 신호"""
    symbol: str
    signal_type: OrderType
    confidence: float
    price: float
    timestamp: datetime.datetime
    strategy_name: str
    metadata: Dict[str, Any]

@dataclass
class OrderRequest:
    """주문 요청"""
    symbol: str
    order_type: OrderType
    quantity: int
    price: float
    order_id: Optional[str] = None
    strategy_source: Optional[str] = None

@dataclass
class PortfolioPosition:
    """포트폴리오 포지션"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
```

---

## 🔄 WebSocket 통합

### 1. WebSocket Manager
**파일**: `project/core/websocket_manager.py`

```python
import asyncio
import json
import websockets
from typing import Dict, Callable, List
import logging

class WebSocketManager:
    """WebSocket 연결 관리자"""

    def __init__(self, kis_config: Dict):
        self.kis_config = kis_config
        self.ws_connection = None
        self.subscriptions = {}
        self.is_connected = False
        self.callbacks = {}

    async def connect(self):
        """KIS WebSocket 연결"""
        try:
            # KIS WebSocket 설정 로드
            ws_url = self.kis_config['ws_url']
            headers = self._prepare_headers()

            self.ws_connection = await websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self.is_connected = True
            logging.info("[WebSocket] KIS WebSocket 연결 성공")

            # 메시지 수신 루프 시작
            asyncio.create_task(self._listen_messages())

        except Exception as e:
            logging.error(f"[WebSocket] 연결 실패: {e}")
            self.is_connected = False

    async def subscribe_price(self, symbol: str, callback: Callable):
        """실시간 가격 구독"""
        if not self.is_connected:
            await self.connect()

        # KIS WebSocket 구독 메시지 생성
        subscribe_msg = {
            "header": {
                "approval_key": self.kis_config['approval_key'],
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "HDFSCNT0",  # 해외주식 실시간 체결가
                    "tr_key": symbol
                }
            }
        }

        await self.ws_connection.send(json.dumps(subscribe_msg))
        self.callbacks[symbol] = callback
        self.subscriptions[symbol] = True

        logging.info(f"[WebSocket] {symbol} 실시간 가격 구독")

    async def _listen_messages(self):
        """WebSocket 메시지 수신"""
        try:
            async for message in self.ws_connection:
                await self._process_message(message)
        except Exception as e:
            logging.error(f"[WebSocket] 메시지 수신 오류: {e}")
            self.is_connected = False

    async def _process_message(self, message: str):
        """수신 메시지 처리"""
        try:
            data = json.loads(message)

            # KIS WebSocket 데이터 파싱
            if 'body' in data and 'output' in data['body']:
                output = data['body']['output']
                symbol = output.get('SYMB')
                price = float(output.get('LAST', 0))
                volume = int(output.get('VOLM', 0))

                price_data = PriceData(
                    symbol=symbol,
                    price=price,
                    volume=volume,
                    timestamp=datetime.now()
                )

                # 콜백 함수 호출
                if symbol in self.callbacks:
                    await self.callbacks[symbol](price_data)

        except Exception as e:
            logging.error(f"[WebSocket] 메시지 처리 오류: {e}")
```

### 2. Real-time Display Manager
**파일**: `project/ui/realtime_display.py`

```python
import asyncio
from datetime import datetime
from typing import Dict, List
import pandas as pd

class RealtimeDisplayManager:
    """실시간 데이터 표시 관리자"""

    def __init__(self):
        self.price_data = {}
        self.portfolio_data = {}
        self.signals_data = []
        self.orders_data = []

    async def update_price_display(self, price_data: PriceData):
        """가격 정보 업데이트"""
        self.price_data[price_data.symbol] = {
            'symbol': price_data.symbol,
            'price': price_data.price,
            'volume': price_data.volume,
            'timestamp': price_data.timestamp.strftime('%H:%M:%S'),
            'change': self._calculate_change(price_data)
        }

        # 실시간 출력
        print(f"[{price_data.timestamp.strftime('%H:%M:%S')}] "
              f"{price_data.symbol}: ${price_data.price:.2f} "
              f"(Vol: {price_data.volume:,})")

    async def update_portfolio_display(self, portfolio: Dict):
        """포트폴리오 정보 업데이트"""
        self.portfolio_data = portfolio

        print("=" * 60)
        print(f"[포트폴리오] 총 가치: ${portfolio.get('total_value', 0):,.2f}")
        print(f"[포트폴리오] 현금: ${portfolio.get('cash', 0):,.2f}")
        print(f"[포트폴리오] 보유 종목: {len(portfolio.get('positions', {}))}")

        for symbol, position in portfolio.get('positions', {}).items():
            pnl_color = "🟢" if position['unrealized_pnl'] >= 0 else "🔴"
            print(f"  {pnl_color} {symbol}: {position['quantity']}주 "
                  f"(${position['avg_price']:.2f} → ${position['current_price']:.2f}) "
                  f"PnL: ${position['unrealized_pnl']:,.2f}")

    async def update_signal_display(self, signal: TradingSignal):
        """매매 신호 표시"""
        self.signals_data.append({
            'timestamp': signal.timestamp.strftime('%H:%M:%S'),
            'symbol': signal.symbol,
            'type': signal.signal_type.value,
            'confidence': f"{signal.confidence:.2%}",
            'price': f"${signal.price:.2f}",
            'strategy': signal.strategy_name
        })

        # 최근 10개만 유지
        if len(self.signals_data) > 10:
            self.signals_data = self.signals_data[-10:]

        signal_emoji = "🟢" if signal.signal_type == OrderType.BUY else "🔴"
        print(f"{signal_emoji} [SIGNAL] {signal.symbol} {signal.signal_type.value} "
              f"@ ${signal.price:.2f} (Confidence: {signal.confidence:.1%})")

    async def update_order_display(self, order: OrderRequest, status: OrderStatus):
        """주문 상태 표시"""
        self.orders_data.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'type': order.order_type.value,
            'quantity': order.quantity,
            'price': f"${order.price:.2f}",
            'status': status.value
        })

        # 최근 20개만 유지
        if len(self.orders_data) > 20:
            self.orders_data = self.orders_data[-20:]

        status_emoji = {"PENDING": "⏳", "FILLED": "✅", "CANCELLED": "❌", "FAILED": "⚠️"}
        print(f"{status_emoji.get(status.value, '❓')} [ORDER] {order.symbol} "
              f"{order.order_type.value} {order.quantity}주 @ ${order.price:.2f} "
              f"Status: {status.value}")

    def display_dashboard(self):
        """전체 대시보드 표시"""
        print("\n" + "=" * 80)
        print("                    AUTO TRADING DASHBOARD")
        print("=" * 80)

        # 실시간 가격 정보
        print("\n📊 실시간 가격 정보:")
        for symbol, data in list(self.price_data.items())[-5:]:  # 최근 5개
            print(f"  {data['timestamp']} | {symbol}: ${data['price']:.2f} "
                  f"(Vol: {data['volume']:,})")

        # 최근 신호
        print("\n🎯 최근 매매 신호:")
        for signal in self.signals_data[-3:]:  # 최근 3개
            print(f"  {signal['timestamp']} | {signal['symbol']} {signal['type']} "
                  f"@ {signal['price']} (신뢰도: {signal['confidence']})")

        # 최근 주문
        print("\n📝 최근 주문 내역:")
        for order in self.orders_data[-3:]:  # 최근 3개
            print(f"  {order['timestamp']} | {order['symbol']} {order['type']} "
                  f"{order['quantity']}주 @ {order['price']} ({order['status']})")

        print("=" * 80)
```

---

## 🎯 구현 단계별 계획

### Phase 1: 기본 인프라 구축 (1주)
**우선순위**: 높음

#### 1.1 Service Layer 기본 구조 (2일)
- [ ] Service 인터페이스 정의
- [ ] Data Transfer Objects 구현
- [ ] 기본 Service 클래스 뼈대 구축

#### 1.2 WebSocket 연동 (3일)
- [ ] WebSocket Manager 구현
- [ ] KIS WebSocket API 연동
- [ ] 실시간 데이터 수신 테스트

#### 1.3 실시간 Display 구현 (2일)
- [ ] Console 기반 실시간 표시
- [ ] 가격/포트폴리오/신호 표시
- [ ] 대시보드 UI 구성

### Phase 2: 핵심 서비스 구현 (2주)

#### 2.1 Account Analysis Service (4일)
- [ ] KIS API 연동하여 계좌 정보 조회
- [ ] 보유 종목 분석
- [ ] 포트폴리오 메트릭 계산
- [ ] 매수 가능 금액 계산

#### 2.2 Position Sizing Service (3일)
- [ ] 전략별 포지션 사이징 로직
- [ ] 리스크 관리 규칙 적용
- [ ] 매수 후보 종목 관리
- [ ] 동적 포지션 조정

#### 2.3 Live Price Service (4일)
- [ ] 실시간 가격 데이터 캐싱
- [ ] 가격 업데이트 이벤트 처리
- [ ] 다중 종목 구독 관리
- [ ] 연결 안정성 보장

#### 2.4 API Order Service (3일)
- [ ] KIS Helper 모듈 연동
- [ ] 주문 큐 관리
- [ ] 에러 처리 및 재시도
- [ ] 주문 상태 추적

### Phase 3: Auto Trade Core 구현 (2주)

#### 3.1 Signal Engine (5일)
- [ ] 기존 Strategy Agent 통합
- [ ] 실시간 신호 생성
- [ ] 신호 확신도 계산
- [ ] 신호 필터링 로직

#### 3.2 Risk Manager (4일)
- [ ] 실시간 리스크 모니터링
- [ ] 포지션 제한 관리
- [ ] 손절/익절 로직
- [ ] 긴급 매도 기능

#### 3.3 Order Manager (3일)
- [ ] 주문 라이프사이클 관리
- [ ] 주문 우선순위 처리
- [ ] 실행 가능성 검증
- [ ] 주문 이력 관리

#### 3.4 Monitor Service (2일)
- [ ] 시스템 상태 모니터링
- [ ] 성과 추적
- [ ] 알림 시스템
- [ ] 로그 관리

### Phase 4: 통합 및 최적화 (1주)

#### 4.1 서비스 통합 (3일)
- [ ] 모든 서비스 연동
- [ ] 인터페이스 검증
- [ ] 데이터 플로우 최적화
- [ ] 동시성 처리

#### 4.2 테스트 및 검증 (2일)
- [ ] 단위 테스트
- [ ] 통합 테스트
- [ ] 시뮬레이션 테스트
- [ ] 성능 테스트

#### 4.3 문서화 및 배포 (2일)
- [ ] API 문서 작성
- [ ] 사용자 가이드
- [ ] 설정 가이드
- [ ] 배포 스크립트

---

## 📁 파일 구조

```
project/
├── service/
│   ├── __init__.py
│   ├── auto_trade_service.py          # 메인 자동매매 서비스
│   ├── live_price_service.py          # 실시간 가격 서비스
│   ├── account_analysis_service.py    # 계좌 분석 서비스
│   ├── position_sizing_service.py     # 포지션 사이징 서비스
│   └── api_order_service.py           # API 주문 서비스
│
├── interfaces/
│   ├── __init__.py
│   └── service_interfaces.py          # 서비스 인터페이스 정의
│
├── models/
│   ├── __init__.py
│   └── trading_models.py              # 데이터 모델
│
├── core/
│   ├── __init__.py
│   ├── websocket_manager.py           # WebSocket 관리자
│   ├── signal_engine.py               # 신호 엔진
│   ├── risk_manager.py                # 리스크 관리자
│   └── order_manager.py               # 주문 관리자
│
├── ui/
│   ├── __init__.py
│   └── realtime_display.py            # 실시간 표시
│
├── config/
│   ├── __init__.py
│   ├── trading_config.yaml            # 매매 설정
│   └── websocket_config.yaml          # WebSocket 설정
│
└── tests/
    ├── __init__.py
    ├── test_services.py
    ├── test_websocket.py
    └── test_integration.py
```

---

## ⚙️ 설정 파일

### 1. Trading Configuration
**파일**: `project/config/trading_config.yaml`

```yaml
# 자동매매 설정
auto_trading:
  enabled: true
  mode: "live"  # live, simulation, paper

  # 매매 시간 설정
  trading_hours:
    start_time: "09:30"
    end_time: "16:00"
    timezone: "US/Eastern"

  # 리스크 관리
  risk_management:
    max_portfolio_risk: 0.02      # 포트폴리오 최대 리스크 2%
    max_position_size: 0.10       # 개별 종목 최대 10%
    stop_loss_pct: 0.05           # 손절 5%
    take_profit_pct: 0.20         # 익절 20%
    max_daily_loss: 0.05          # 일일 최대 손실 5%

  # 포지션 사이징
  position_sizing:
    method: "fixed_ratio"         # fixed_ratio, kelly, volatility_adjusted
    base_position_size: 0.05      # 기본 포지션 크기 5%
    min_position_value: 1000      # 최소 포지션 가치 $1,000
    max_positions: 10             # 최대 동시 보유 종목 수

  # 신호 필터링
  signal_filtering:
    min_confidence: 0.6           # 최소 신뢰도 60%
    cooldown_period: 300          # 동일 종목 재매매 대기시간 (초)
    max_orders_per_minute: 5      # 분당 최대 주문 수

# 전략 설정
strategies:
  nasdaq_growth:
    enabled: true
    allocation: 0.6               # 포트폴리오의 60% 할당
    parameters:
      ma_fast: 5
      ma_slow: 20
      rsi_oversold: 25
      rsi_overbought: 75

  nyse_value:
    enabled: true
    allocation: 0.4               # 포트폴리오의 40% 할당
    parameters:
      ma_fast: 10
      ma_slow: 50
      rsi_oversold: 35
      rsi_overbought: 65

# 모니터링 설정
monitoring:
  display_update_interval: 1      # 화면 업데이트 간격 (초)
  portfolio_update_interval: 30   # 포트폴리오 업데이트 간격 (초)
  log_level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  enable_telegram_alerts: true   # 텔레그램 알림 활성화
```

### 2. WebSocket Configuration
**파일**: `project/config/websocket_config.yaml`

```yaml
# WebSocket 연결 설정
websocket:
  # KIS WebSocket 설정
  kis:
    url: "ws://ops.koreainvestment.com:21000"  # 실서버
    url_dev: "ws://ops.koreainvestment.com:31000"  # 모의서버

    # 연결 설정
    connection:
      ping_interval: 20           # Ping 간격 (초)
      ping_timeout: 10            # Ping 타임아웃 (초)
      reconnect_interval: 5       # 재연결 간격 (초)
      max_reconnect_attempts: 10  # 최대 재연결 시도

    # 구독 설정
    subscriptions:
      price_data: true            # 실시간 가격 구독
      orderbook: false            # 호가 정보 구독
      trades: true                # 체결 정보 구독

  # 데이터 버퍼 설정
  buffering:
    max_buffer_size: 1000         # 최대 버퍼 크기
    buffer_timeout: 1             # 버퍼 플러시 간격 (초)

  # 에러 처리
  error_handling:
    max_consecutive_errors: 5     # 연속 에러 허용 한계
    error_cooldown: 10            # 에러 후 대기시간 (초)
```

---

## 🔌 KIS Helper 모듈 연동

### 1. KIS Helper Adapter
**파일**: `project/adapters/kis_helper_adapter.py`

```python
import sys
sys.path.append('../refer/Helper/KIS')

import KIS_API_Helper_US as KisUS
import KIS_API_Helper_KR as KisKR
import KIS_Common as Common
from typing import Dict, List, Optional
import asyncio

class KISHelperAdapter:
    """KIS Helper 모듈 어댑터"""

    def __init__(self, market: str = "US"):
        self.market = market
        self.api_helper = KisUS if market == "US" else KisKR

    async def get_account_balance(self) -> Dict:
        """계좌 잔고 조회"""
        try:
            if self.market == "US":
                balance_data = self.api_helper.GetBalanceInfo()
            else:
                balance_data = self.api_helper.GetBalanceInfo()

            return {
                'total_value': float(balance_data.get('total_value', 0)),
                'cash': float(balance_data.get('cash', 0)),
                'stock_value': float(balance_data.get('stock_value', 0))
            }
        except Exception as e:
            print(f"[KIS] 계좌 조회 실패: {e}")
            return {}

    async def get_holdings(self) -> Dict[str, Dict]:
        """보유 종목 조회"""
        try:
            if self.market == "US":
                holdings_data = self.api_helper.GetMyStockList()
            else:
                holdings_data = self.api_helper.GetMyStockList()

            holdings = {}
            for stock in holdings_data:
                symbol = stock.get('symbol')
                holdings[symbol] = {
                    'quantity': int(stock.get('quantity', 0)),
                    'avg_price': float(stock.get('avg_price', 0)),
                    'current_price': float(stock.get('current_price', 0)),
                    'market_value': float(stock.get('market_value', 0)),
                    'unrealized_pnl': float(stock.get('unrealized_pnl', 0))
                }

            return holdings
        except Exception as e:
            print(f"[KIS] 보유종목 조회 실패: {e}")
            return {}

    async def place_buy_order(self, symbol: str, quantity: int, price: float) -> Optional[str]:
        """매수 주문"""
        try:
            if self.market == "US":
                result = self.api_helper.MakeBuyLimitOrder(symbol, quantity, price)
            else:
                result = self.api_helper.MakeBuyLimitOrder(symbol, quantity, price)

            if result and result.get('rt_cd') == '0':
                return result.get('KRX_FWDG_ORD_ORGNO', '') + result.get('ODNO', '')
            else:
                print(f"[KIS] 매수 주문 실패: {result}")
                return None

        except Exception as e:
            print(f"[KIS] 매수 주문 오류: {e}")
            return None

    async def place_sell_order(self, symbol: str, quantity: int, price: float) -> Optional[str]:
        """매도 주문"""
        try:
            if self.market == "US":
                result = self.api_helper.MakeSellLimitOrder(symbol, quantity, price)
            else:
                result = self.api_helper.MakeSellLimitOrder(symbol, quantity, price)

            if result and result.get('rt_cd') == '0':
                return result.get('KRX_FWDG_ORD_ORGNO', '') + result.get('ODNO', '')
            else:
                print(f"[KIS] 매도 주문 실패: {result}")
                return None

        except Exception as e:
            print(f"[KIS] 매도 주문 오류: {e}")
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            # order_id를 분리 (기관번호 + 주문번호)
            org_no = order_id[:5]
            order_no = order_id[5:]

            result = self.api_helper.CancelModifyOrder(
                stockcode="",
                order_num=order_no,
                order_amt=0,
                order_price=0,
                mode="CANCEL"
            )

            return result and result.get('rt_cd') == '0'

        except Exception as e:
            print(f"[KIS] 주문 취소 오류: {e}")
            return False

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""
        try:
            if self.market == "US":
                price_data = self.api_helper.GetCurrentPrice(symbol)
            else:
                price_data = self.api_helper.GetCurrentPrice(symbol)

            return float(price_data.get('price', 0)) if price_data else None

        except Exception as e:
            print(f"[KIS] 가격 조회 오류: {e}")
            return None
```

---

## 📊 실시간 모니터링 예시

### Console 출력 예시
```
================================================================================
                            AUTO TRADING DASHBOARD
================================================================================
[09:31:25] 시스템 상태: 🟢 ACTIVE | 연결 상태: 🟢 CONNECTED | 모드: LIVE

📊 실시간 가격 정보:
  09:31:25 | AAPL: $174.25 (Vol: 125,430) ↗️ +0.45%
  09:31:25 | MSFT: $338.92 (Vol: 89,234)  ↘️ -0.12%
  09:31:25 | GOOGL: $125.87 (Vol: 67,891) ↗️ +0.89%
  09:31:25 | TSLA: $248.33 (Vol: 234,567) ↗️ +1.23%
  09:31:25 | NVDA: $421.45 (Vol: 156,789) ↘️ -0.33%

💰 포트폴리오 현황:
  총 자산: $125,847.92 | 현금: $25,847.92 | 주식: $100,000.00
  일일 손익: +$1,247.50 (+1.00%) | 총 수익률: +25.85%

  🟢 AAPL: 100주 ($172.30 → $174.25) PnL: +$195.00
  🔴 MSFT: 50주 ($340.15 → $338.92) PnL: -$61.50
  🟢 GOOGL: 75주 ($124.50 → $125.87) PnL: +$102.75

🎯 최근 매매 신호:
  09:31:15 | TSLA BUY @ $247.80 (신뢰도: 78%)
  09:30:45 | NVDA SELL @ $422.10 (신뢰도: 82%)
  09:30:22 | AAPL BUY @ $173.95 (신뢰도: 71%)

📝 최근 주문 내역:
  09:31:18 | TSLA BUY 20주 @ $247.85 (✅ FILLED)
  09:30:48 | NVDA SELL 30주 @ $422.05 (✅ FILLED)
  09:30:25 | AAPL BUY 15주 @ $174.00 (⏳ PENDING)

⚠️ 알림:
  • AAPL 매수 신호 발생 - 포지션 크기 확인 중
  • 포트폴리오 집중도 80% - 분산 투자 권장

================================================================================
다음 업데이트: 09:31:30
```

---

## 🚨 리스크 관리 및 안전장치

### 1. 자동 중단 조건
- 일일 손실 한계 도달 시 (기본: 5%)
- 연속 주문 실패 시 (기본: 5회)
- WebSocket 연결 장애 시
- API 응답 지연 시 (기본: 10초)

### 2. 긴급 정지 기능
```python
class EmergencyStop:
    """긴급 정지 기능"""

    @staticmethod
    async def emergency_stop_all():
        """모든 거래 즉시 중단"""
        # 1. 신규 주문 차단
        # 2. 대기 중인 주문 취소
        # 3. 포지션 일괄 매도 (옵션)
        # 4. 시스템 안전 모드 전환
```

### 3. 모니터링 알림
- 텔레그램 봇 연동
- 이메일 알림
- SMS 알림 (중요한 이벤트)

---

## 🎯 성공 지표 (KPI)

### 1. 시스템 안정성
- WebSocket 연결 안정성: > 99%
- 주문 실행 성공률: > 95%
- 시스템 가동 시간: > 99.5%

### 2. 거래 성능
- 신호 생성 지연: < 1초
- 주문 실행 지연: < 3초
- 포트폴리오 업데이트 지연: < 5초

### 3. 리스크 관리
- 최대 드로우다운: < 10%
- 일일 손실 제한 준수: 100%
- 포지션 크기 제한 준수: 100%

---

## 📋 체크리스트

### 개발 전 준비사항
- [ ] KIS API 계정 및 토큰 확인
- [ ] WebSocket 연결 테스트
- [ ] 기존 Strategy Agent 코드 분석
- [ ] 리스크 관리 정책 정의
- [ ] 테스트 환경 구축

### 개발 중 확인사항
- [ ] 각 서비스 단위 테스트
- [ ] 인터페이스 호환성 검증
- [ ] 실시간 성능 테스트
- [ ] 메모리 누수 검사
- [ ] 예외 처리 검증

### 배포 전 검증사항
- [ ] 전체 시스템 통합 테스트
- [ ] 모의 거래 환경 테스트
- [ ] 장애 시나리오 테스트
- [ ] 성능 벤치마크 측정
- [ ] 보안 검토

---

이 계획을 바탕으로 단계별로 구현하면 **안정적이고 확장 가능한 실시간 자동매매 시스템**을 구축할 수 있습니다.

**📝 마지막 업데이트**: 2025-09-23
**📧 문의**: Auto Trading System Team
**🔗 관련 문서**: [multi_agent_analysis_and_independence_plan.md](./multi_agent_analysis_and_independence_plan.md)