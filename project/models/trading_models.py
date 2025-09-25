"""
Trading Data Models

자동매매 시스템에서 사용되는 모든 데이터 모델 정의
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import datetime
from decimal import Decimal

class OrderType(Enum):
    """주문 유형"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "PENDING"      # 대기 중
    SUBMITTED = "SUBMITTED"  # 제출됨
    FILLED = "FILLED"       # 체결됨
    CANCELLED = "CANCELLED"  # 취소됨
    REJECTED = "REJECTED"   # 거부됨
    FAILED = "FAILED"       # 실패

class SignalType(Enum):
    """신호 유형"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class MarketType(Enum):
    """시장 유형"""
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    KRX = "KRX"

@dataclass
class PriceData:
    """실시간 가격 데이터"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime.datetime
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_volume: Optional[int] = None
    ask_volume: Optional[int] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    market: Optional[MarketType] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'bid_price': self.bid_price,
            'ask_price': self.ask_price,
            'bid_volume': self.bid_volume,
            'ask_volume': self.ask_volume,
            'change': self.change,
            'change_pct': self.change_pct,
            'market': self.market.value if self.market else None
        }

@dataclass
class TradingSignal:
    """매매 신호"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 0.0 ~ 1.0
    price: float
    timestamp: datetime.datetime
    strategy_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 추가 정보
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    expected_return: Optional[float] = None
    risk_score: Optional[float] = None

    def is_buy_signal(self) -> bool:
        """매수 신호인지 확인"""
        return self.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]

    def is_sell_signal(self) -> bool:
        """매도 신호인지 확인"""
        return self.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'strategy_name': self.strategy_name,
            'metadata': self.metadata,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'expected_return': self.expected_return,
            'risk_score': self.risk_score
        }

@dataclass
class OrderRequest:
    """주문 요청"""
    symbol: str
    order_type: OrderType
    quantity: int
    price: float
    order_id: Optional[str] = None
    strategy_source: Optional[str] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    # 주문 옵션
    time_in_force: str = "DAY"  # DAY, GTC, IOC, FOK
    order_class: str = "LIMIT"  # MARKET, LIMIT, STOP, STOP_LIMIT

    # 추가 정보
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'order_id': self.order_id,
            'strategy_source': self.strategy_source,
            'timestamp': self.timestamp.isoformat(),
            'time_in_force': self.time_in_force,
            'order_class': self.order_class,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'notes': self.notes
        }

@dataclass
class OrderResponse:
    """주문 응답"""
    order_id: str
    symbol: str
    status: OrderStatus
    filled_quantity: int = 0
    remaining_quantity: int = 0
    avg_fill_price: Optional[float] = None
    commission: Optional[float] = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'avg_fill_price': self.avg_fill_price,
            'commission': self.commission,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message
        }

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
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None

    # 추가 정보
    market: Optional[MarketType] = None
    sector: Optional[str] = None
    last_update: datetime.datetime = field(default_factory=datetime.datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct,
            'day_change': self.day_change,
            'day_change_pct': self.day_change_pct,
            'market': self.market.value if self.market else None,
            'sector': self.sector,
            'last_update': self.last_update.isoformat()
        }

@dataclass
class Portfolio:
    """포트폴리오 전체 정보"""
    total_value: float
    cash: float
    stock_value: float
    day_pnl: float
    total_pnl: float
    day_pnl_pct: float
    total_pnl_pct: float
    positions: Dict[str, PortfolioPosition] = field(default_factory=dict)
    last_update: datetime.datetime = field(default_factory=datetime.datetime.now)

    def add_position(self, position: PortfolioPosition) -> None:
        """포지션 추가"""
        self.positions[position.symbol] = position

    def remove_position(self, symbol: str) -> None:
        """포지션 제거"""
        if symbol in self.positions:
            del self.positions[symbol]

    def get_position_count(self) -> int:
        """보유 종목 수"""
        return len(self.positions)

    def get_market_allocation(self) -> Dict[str, float]:
        """시장별 할당 비율"""
        market_values = {}
        for position in self.positions.values():
            if position.market:
                market = position.market.value
                if market not in market_values:
                    market_values[market] = 0
                market_values[market] += position.market_value

        # 비율 계산
        total_stock_value = self.stock_value
        if total_stock_value > 0:
            return {market: value / total_stock_value
                   for market, value in market_values.items()}
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_value': self.total_value,
            'cash': self.cash,
            'stock_value': self.stock_value,
            'day_pnl': self.day_pnl,
            'total_pnl': self.total_pnl,
            'day_pnl_pct': self.day_pnl_pct,
            'total_pnl_pct': self.total_pnl_pct,
            'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
            'position_count': self.get_position_count(),
            'market_allocation': self.get_market_allocation(),
            'last_update': self.last_update.isoformat()
        }

@dataclass
class SystemStatus:
    """시스템 상태"""
    is_trading_active: bool = False
    is_market_open: bool = False
    websocket_connected: bool = False
    last_price_update: Optional[datetime.datetime] = None
    last_portfolio_update: Optional[datetime.datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    uptime: Optional[float] = None  # seconds

    # 성능 지표
    orders_today: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    avg_response_time: Optional[float] = None

    def get_success_rate(self) -> float:
        """주문 성공률"""
        if self.orders_today == 0:
            return 0.0
        return self.successful_orders / self.orders_today

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'is_trading_active': self.is_trading_active,
            'is_market_open': self.is_market_open,
            'websocket_connected': self.websocket_connected,
            'last_price_update': self.last_price_update.isoformat() if self.last_price_update else None,
            'last_portfolio_update': self.last_portfolio_update.isoformat() if self.last_portfolio_update else None,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'uptime': self.uptime,
            'orders_today': self.orders_today,
            'successful_orders': self.successful_orders,
            'failed_orders': self.failed_orders,
            'success_rate': self.get_success_rate(),
            'avg_response_time': self.avg_response_time
        }

@dataclass
class CandidateStock:
    """매수 후보 종목"""
    symbol: str
    score: float  # 0.0 ~ 1.0
    strategy: str
    reasons: List[str] = field(default_factory=list)
    target_price: Optional[float] = None
    expected_return: Optional[float] = None
    risk_level: Optional[str] = None  # LOW, MEDIUM, HIGH
    market: Optional[MarketType] = None
    last_analysis: datetime.datetime = field(default_factory=datetime.datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'score': self.score,
            'strategy': self.strategy,
            'reasons': self.reasons,
            'target_price': self.target_price,
            'expected_return': self.expected_return,
            'risk_level': self.risk_level,
            'market': self.market.value if self.market else None,
            'last_analysis': self.last_analysis.isoformat()
        }