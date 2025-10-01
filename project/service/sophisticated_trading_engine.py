"""
Sophisticated Trading Engine

정교한 백테스트 엔진의 매매로직을 실제 트레이딩 시스템에 적용
손절매, 매도신호, 포지션 관리 등 모든 로직을 실시간으로 처리
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..models.trading_models import (
    TradingSignal, Portfolio, PortfolioPosition, PriceData, SignalType
)


class SellReason(Enum):
    """매도 이유"""
    LOSSCUT = "LOSSCUT"
    SIGNAL_SELL = "SIGNAL_SELL"
    HALF_SELL = "HALF_SELL"
    TAKE_PROFIT = "TAKE_PROFIT"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"


@dataclass
class TradingPosition:
    """거래 포지션 (DailyBacktestService.Position과 동일)"""
    symbol: str
    quantity: int
    avg_price: float
    entry_date: datetime
    losscut_price: float
    target_price: Optional[float] = None
    again: float = 1.0  # 수익률 배수
    risk: float = 0.03  # 리스크 수준

    @property
    def market_value(self) -> float:
        """현재 시장가치"""
        return self.quantity * self.avg_price * self.again

    @property
    def unrealized_pnl(self) -> float:
        """미실현 손익"""
        return self.market_value - (self.quantity * self.avg_price)


@dataclass
class SellOrder:
    """매도 주문"""
    symbol: str
    quantity: int
    price: float
    reason: SellReason
    timestamp: datetime
    expected_pnl: float


class SophisticatedTradingEngine:
    """정교한 트레이딩 엔진"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 트레이딩 설정
        self.init_risk = config.get('init_risk', 0.03)  # 3% 손절선
        self.half_sell_threshold = config.get('half_sell_threshold', 0.1)  # 10% 수익시 절반 매도
        self.enable_half_sell = config.get('enable_half_sell', True)
        self.enable_whipsaw = config.get('enable_whipsaw', True)

        # 활성 포지션 관리
        self.active_positions: Dict[str, TradingPosition] = {}
        self.price_cache: Dict[str, PriceData] = {}
        self.half_sell_executed: set = set()

        # 통계
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    async def start_engine(self) -> bool:
        """엔진 시작"""
        try:
            self.logger.info("[SophisticatedTradingEngine] 정교한 트레이딩 엔진 시작")
            return True
        except Exception as e:
            self.logger.error(f"엔진 시작 실패: {e}")
            return False

    async def stop_engine(self) -> None:
        """엔진 중지"""
        try:
            self.logger.info("[SophisticatedTradingEngine] 엔진 중지")
            self.active_positions.clear()
            self.price_cache.clear()
        except Exception as e:
            self.logger.error(f"엔진 중지 실패: {e}")

    def update_price(self, symbol: str, price_data: PriceData) -> None:
        """가격 데이터 업데이트"""
        self.price_cache[symbol] = price_data

        # 활성 포지션의 수익률 업데이트
        if symbol in self.active_positions:
            position = self.active_positions[symbol]
            if position.avg_price > 0:
                position.again = price_data.price / position.avg_price

    async def add_position(self, symbol: str, quantity: int, entry_price: float,
                          entry_date: datetime) -> bool:
        """새 포지션 추가"""
        try:
            # 손절가 계산
            losscut_price = entry_price * (1 - self.init_risk)

            position = TradingPosition(
                symbol=symbol,
                quantity=quantity,
                avg_price=entry_price,
                entry_date=entry_date,
                losscut_price=losscut_price,
                risk=self.init_risk
            )

            self.active_positions[symbol] = position
            self.logger.info(f"[포지션 추가] {symbol}: {quantity}주 @${entry_price:.2f}, "
                           f"손절가: ${losscut_price:.2f}")

            return True

        except Exception as e:
            self.logger.error(f"포지션 추가 실패 ({symbol}): {e}")
            return False

    async def check_sell_conditions(self) -> List[SellOrder]:
        """매도 조건 확인"""
        sell_orders = []

        try:
            for symbol, position in self.active_positions.items():
                if symbol not in self.price_cache:
                    continue

                price_data = self.price_cache[symbol]
                current_price = price_data.price
                low_price = getattr(price_data, 'low', current_price)
                open_price = getattr(price_data, 'open', current_price)

                # 1. 손절매 확인 (최우선)
                if low_price < position.losscut_price:
                    sell_price = min(open_price, position.losscut_price) if open_price < position.losscut_price else position.losscut_price
                    expected_pnl = (sell_price - position.avg_price) * position.quantity

                    sell_orders.append(SellOrder(
                        symbol=symbol,
                        quantity=position.quantity,
                        price=sell_price,
                        reason=SellReason.LOSSCUT,
                        timestamp=datetime.now(),
                        expected_pnl=expected_pnl
                    ))

                    self.logger.warning(f"[손절매] {symbol}: ${position.avg_price:.2f} -> ${sell_price:.2f} "
                                       f"(손실: ${expected_pnl:.2f})")

                # 2. 매도 신호 확인
                elif hasattr(price_data, 'sell_signal') and price_data.sell_signal == 1:
                    sell_price = open_price
                    expected_pnl = (sell_price - position.avg_price) * position.quantity

                    sell_orders.append(SellOrder(
                        symbol=symbol,
                        quantity=position.quantity,
                        price=sell_price,
                        reason=SellReason.SIGNAL_SELL,
                        timestamp=datetime.now(),
                        expected_pnl=expected_pnl
                    ))

                    self.logger.info(f"[매도신호] {symbol}: ${position.avg_price:.2f} -> ${sell_price:.2f} "
                                    f"(손익: ${expected_pnl:.2f})")

                # 3. 절반 매도 확인
                elif (self.enable_half_sell and
                      symbol not in self.half_sell_executed and
                      position.again >= (1 + self.half_sell_threshold)):

                    sell_price = current_price
                    half_quantity = position.quantity // 2
                    expected_pnl = (sell_price - position.avg_price) * half_quantity

                    sell_orders.append(SellOrder(
                        symbol=symbol,
                        quantity=half_quantity,
                        price=sell_price,
                        reason=SellReason.HALF_SELL,
                        timestamp=datetime.now(),
                        expected_pnl=expected_pnl
                    ))

                    self.logger.info(f"[절반매도] {symbol}: {half_quantity}주 @${sell_price:.2f} "
                                    f"(수익: ${expected_pnl:.2f})")

        except Exception as e:
            self.logger.error(f"매도 조건 확인 실패: {e}")

        return sell_orders

    async def execute_sell_order(self, sell_order: SellOrder) -> bool:
        """매도 주문 실행"""
        try:
            symbol = sell_order.symbol

            if symbol not in self.active_positions:
                self.logger.warning(f"포지션이 없는 종목 매도 시도: {symbol}")
                return False

            position = self.active_positions[symbol]

            # 절반 매도 처리
            if sell_order.reason == SellReason.HALF_SELL:
                position.quantity -= sell_order.quantity
                self.half_sell_executed.add(symbol)

                self.logger.info(f"[절반매도 완료] {symbol}: 잔여 {position.quantity}주")

            else:
                # 전량 매도 - 포지션 제거
                del self.active_positions[symbol]
                if symbol in self.half_sell_executed:
                    self.half_sell_executed.remove(symbol)

                self.logger.info(f"[전량매도 완료] {symbol}: 포지션 종료")

            # 통계 업데이트
            self.total_trades += 1
            if sell_order.expected_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

            return True

        except Exception as e:
            self.logger.error(f"매도 주문 실행 실패 ({sell_order.symbol}): {e}")
            return False

    async def remove_position(self, symbol: str) -> bool:
        """포지션 제거 (외부 매도 후)"""
        try:
            if symbol in self.active_positions:
                del self.active_positions[symbol]
                if symbol in self.half_sell_executed:
                    self.half_sell_executed.remove(symbol)

                self.logger.info(f"[포지션 제거] {symbol}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"포지션 제거 실패 ({symbol}): {e}")
            return False

    def get_active_positions(self) -> Dict[str, TradingPosition]:
        """활성 포지션 조회"""
        return self.active_positions.copy()

    def get_position_summary(self) -> Dict[str, Any]:
        """포지션 요약 정보"""
        total_value = sum(pos.market_value for pos in self.active_positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.active_positions.values())

        return {
            'position_count': len(self.active_positions),
            'total_market_value': total_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'active_symbols': list(self.active_positions.keys())
        }

    async def process_market_close(self) -> None:
        """장 마감 처리"""
        try:
            summary = self.get_position_summary()
            self.logger.info(f"[장마감] 활성포지션: {summary['position_count']}개, "
                           f"미실현손익: ${summary['total_unrealized_pnl']:,.2f}, "
                           f"승률: {summary['win_rate']:.1f}%")

        except Exception as e:
            self.logger.error(f"장 마감 처리 실패: {e}")


# 트레이딩 엔진 통합 함수들
async def integrate_sophisticated_engine_to_orchestrator(orchestrator, config: Dict[str, Any]) -> bool:
    """오케스트레이터에 정교한 트레이딩 엔진 통합"""
    try:
        # 정교한 트레이딩 엔진 생성
        trading_engine = SophisticatedTradingEngine(config)

        # 오케스트레이터에 엔진 연결
        orchestrator.sophisticated_engine = trading_engine

        # 엔진 시작
        await trading_engine.start_engine()

        logging.getLogger(__name__).info("[통합] 정교한 트레이딩 엔진이 오케스트레이터에 통합되었습니다")
        return True

    except Exception as e:
        logging.getLogger(__name__).error(f"정교한 엔진 통합 실패: {e}")
        return False


async def setup_sophisticated_monitoring(orchestrator) -> bool:
    """정교한 모니터링 설정"""
    try:
        if not hasattr(orchestrator, 'sophisticated_engine'):
            return False

        engine = orchestrator.sophisticated_engine

        # 주기적 매도 조건 확인 (30초마다)
        async def periodic_sell_check():
            while True:
                try:
                    sell_orders = await engine.check_sell_conditions()

                    for sell_order in sell_orders:
                        # 오케스트레이터를 통해 실제 매도 주문 실행
                        success = await orchestrator.execute_sell_order(
                            sell_order.symbol,
                            sell_order.quantity,
                            sell_order.reason.value
                        )

                        if success:
                            await engine.execute_sell_order(sell_order)

                    await asyncio.sleep(30)  # 30초 대기

                except Exception as e:
                    logging.getLogger(__name__).error(f"매도 조건 확인 실패: {e}")
                    await asyncio.sleep(60)  # 에러시 1분 대기

        # 백그라운드 태스크 시작
        asyncio.create_task(periodic_sell_check())

        logging.getLogger(__name__).info("[모니터링] 정교한 매도 조건 모니터링 시작")
        return True

    except Exception as e:
        logging.getLogger(__name__).error(f"정교한 모니터링 설정 실패: {e}")
        return False