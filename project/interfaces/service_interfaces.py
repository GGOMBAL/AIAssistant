"""
Service Interfaces for Auto Trade System

서비스 간 통신을 위한 표준 인터페이스 정의
모든 서비스는 이 인터페이스를 구현해야 함
"""

from typing import Protocol, Dict, List, Any, Optional, Callable
from abc import abstractmethod
import asyncio

class ILivePriceService(Protocol):
    """실시간 가격 서비스 인터페이스"""

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""
        pass

    @abstractmethod
    async def subscribe_price_updates(self, symbol: str, callback: Callable) -> bool:
        """가격 업데이트 구독"""
        pass

    @abstractmethod
    async def unsubscribe_price_updates(self, symbol: str) -> bool:
        """가격 업데이트 구독 해제"""
        pass

    @abstractmethod
    async def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 심볼 목록"""
        pass

    @abstractmethod
    async def start_service(self) -> bool:
        """서비스 시작"""
        pass

    @abstractmethod
    async def stop_service(self) -> bool:
        """서비스 중지"""
        pass

class IAccountAnalysisService(Protocol):
    """계좌 분석 서비스 인터페이스"""

    @abstractmethod
    async def get_holdings(self) -> Dict[str, Dict]:
        """보유 종목 조회

        Returns:
            Dict[symbol, {
                'quantity': int,
                'avg_price': float,
                'current_price': float,
                'market_value': float,
                'unrealized_pnl': float,
                'unrealized_pnl_pct': float
            }]
        """
        pass

    @abstractmethod
    async def get_portfolio_value(self) -> Dict[str, float]:
        """포트폴리오 총 가치

        Returns:
            {
                'total_value': float,
                'cash': float,
                'stock_value': float,
                'daily_pnl': float,
                'total_pnl': float
            }
        """
        pass

    @abstractmethod
    async def get_available_cash(self) -> float:
        """매수 가능 현금"""
        pass

    @abstractmethod
    async def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """포트폴리오 지표 계산"""
        pass

    @abstractmethod
    async def refresh_account_data(self) -> bool:
        """계좌 데이터 새로고침"""
        pass

class IPositionSizingService(Protocol):
    """포지션 사이징 서비스 인터페이스"""

    @abstractmethod
    async def calculate_buy_quantity(self, symbol: str, price: float,
                                   strategy: str = "default") -> int:
        """매수 수량 계산"""
        pass

    @abstractmethod
    async def get_candidates(self, strategy: str = "all") -> List[str]:
        """매수 후보 종목"""
        pass

    @abstractmethod
    async def update_candidates(self, candidates: List[str]) -> bool:
        """매수 후보 종목 업데이트"""
        pass

    @abstractmethod
    async def check_position_limits(self, symbol: str, quantity: int,
                                  price: float) -> Dict[str, Any]:
        """포지션 제한 확인"""
        pass

    @abstractmethod
    async def apply_risk_constraints(self, orders: List[Dict]) -> List[Dict]:
        """리스크 제약 조건 적용"""
        pass

class IAPIOrderService(Protocol):
    """API 주문 서비스 인터페이스"""

    @abstractmethod
    async def place_order(self, order: Dict) -> Optional[str]:
        """주문 제출

        Args:
            order: {
                'symbol': str,
                'order_type': 'BUY' | 'SELL',
                'quantity': int,
                'price': float,
                'strategy_source': str
            }

        Returns:
            order_id: str or None if failed
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """주문 상태 조회"""
        pass

    @abstractmethod
    async def get_pending_orders(self) -> List[Dict]:
        """대기 중인 주문 목록"""
        pass

    @abstractmethod
    async def get_order_history(self, limit: int = 100) -> List[Dict]:
        """주문 이력 조회"""
        pass

class IAutoTradeService(Protocol):
    """자동매매 서비스 메인 인터페이스"""

    @abstractmethod
    async def start_trading(self) -> bool:
        """자동매매 시작"""
        pass

    @abstractmethod
    async def stop_trading(self) -> bool:
        """자동매매 중지"""
        pass

    @abstractmethod
    async def pause_trading(self) -> bool:
        """자동매매 일시 정지"""
        pass

    @abstractmethod
    async def resume_trading(self) -> bool:
        """자동매매 재개"""
        pass

    @abstractmethod
    async def emergency_stop(self) -> bool:
        """긴급 정지"""
        pass

    @abstractmethod
    async def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        pass

    @abstractmethod
    async def process_market_data(self, data: Dict) -> None:
        """실시간 시장 데이터 처리"""
        pass

class IRealtimeDisplayService(Protocol):
    """실시간 표시 서비스 인터페이스"""

    @abstractmethod
    async def update_price_display(self, price_data: Dict) -> None:
        """가격 정보 표시 업데이트"""
        pass

    @abstractmethod
    async def update_portfolio_display(self, portfolio: Dict) -> None:
        """포트폴리오 표시 업데이트"""
        pass

    @abstractmethod
    async def update_signal_display(self, signal: Dict) -> None:
        """매매 신호 표시 업데이트"""
        pass

    @abstractmethod
    async def update_order_display(self, order: Dict, status: str) -> None:
        """주문 상태 표시 업데이트"""
        pass

    @abstractmethod
    async def display_dashboard(self) -> None:
        """전체 대시보드 표시"""
        pass

    @abstractmethod
    async def show_alert(self, message: str, level: str = "INFO") -> None:
        """알림 표시"""
        pass

# Base Service Class
class BaseService:
    """모든 서비스의 기본 클래스"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        self.error_count = 0
        self.last_error = None

    async def initialize(self) -> bool:
        """서비스 초기화"""
        try:
            self.is_running = True
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    async def cleanup(self) -> bool:
        """서비스 정리"""
        try:
            self.is_running = False
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """서비스 건강 상태"""
        return {
            'is_running': self.is_running,
            'error_count': self.error_count,
            'last_error': self.last_error
        }

    def log_error(self, error: str) -> None:
        """에러 로깅"""
        self.error_count += 1
        self.last_error = error
        print(f"[ERROR] {self.__class__.__name__}: {error}")