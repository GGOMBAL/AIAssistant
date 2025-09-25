"""
Order Manager

고도화된 주문 관리 시스템
복합 주문, 조건부 주문, 스마트 라우팅 등의 고급 주문 기능 제공
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import statistics

from ..models.trading_models import (
    OrderRequest, OrderResponse, OrderType, OrderStatus,
    TradingSignal, CandidateStock, PriceData, Portfolio
)


class OrderStrategy(Enum):
    """주문 전략"""
    MARKET = "MARKET"           # 시장가 주문
    LIMIT = "LIMIT"             # 지정가 주문
    STOP_LOSS = "STOP_LOSS"     # 손절매 주문
    TAKE_PROFIT = "TAKE_PROFIT" # 이익실현 주문
    TWAP = "TWAP"               # Time-Weighted Average Price
    VWAP = "VWAP"               # Volume-Weighted Average Price
    ICEBERG = "ICEBERG"         # 빙산 주문
    BRACKET = "BRACKET"         # 브래킷 주문 (손절매+이익실현)


class ExecutionQuality(Enum):
    """체결 품질"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


@dataclass
class SmartOrder:
    """스마트 주문"""
    order_id: str
    original_signal: TradingSignal
    candidate: CandidateStock
    strategy: OrderStrategy
    total_quantity: int
    target_price: float

    # 실행 설정
    max_slippage: float = 0.005  # 0.5%
    time_limit_minutes: int = 30
    min_fill_size: int = 1

    # 상태 추적
    executed_quantity: int = 0
    remaining_quantity: int = 0
    avg_execution_price: float = 0.0
    creation_time: datetime = None

    # 자식 주문들
    child_orders: List[OrderRequest] = None

    def __post_init__(self):
        if self.creation_time is None:
            self.creation_time = datetime.now()
        if self.remaining_quantity == 0:
            self.remaining_quantity = self.total_quantity
        if self.child_orders is None:
            self.child_orders = []


@dataclass
class ExecutionAnalysis:
    """체결 분석"""
    order_id: str
    execution_quality: ExecutionQuality
    slippage: float
    execution_time_seconds: float
    market_impact: float
    fill_ratio: float
    price_improvement: float
    timestamp: datetime


class OrderManager:
    """고급 주문 관리자"""

    def __init__(self, config: Dict[str, Any], api_order_service, position_sizing_service):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 의존성 서비스
        self.api_order_service = api_order_service
        self.position_sizing_service = position_sizing_service

        # 주문 관리 설정
        self.order_config = config.get('order_management', {})
        self.default_slippage_limit = self.order_config.get('max_slippage', 0.005)  # 0.5%
        self.default_time_limit = self.order_config.get('default_time_limit', 30)   # 30분
        self.min_order_size = self.order_config.get('min_order_size', 1)

        # 스마트 주문 관리
        self.smart_orders: Dict[str, SmartOrder] = {}
        self.completed_orders: List[SmartOrder] = []

        # 실행 분석
        self.execution_analyses: List[ExecutionAnalysis] = []

        # 가격 데이터
        self.price_data_cache: Dict[str, PriceData] = {}
        self.price_history: Dict[str, List[float]] = {}

        # 시장 상황 분석
        self.market_conditions: Dict[str, Any] = {
            'volatility': 'NORMAL',
            'liquidity': 'NORMAL',
            'trend': 'NEUTRAL'
        }

        # 콜백 및 알림
        self.execution_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []

        # 실행 상태
        self.is_running = False
        self.execution_task = None

        # 통계
        self.total_orders_managed = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_slippage = 0.0

    async def start_manager(self) -> bool:
        """주문 관리자 시작"""
        try:
            self.logger.info("[OrderManager] 주문 관리자 시작")

            # 설정 검증
            await self._validate_configuration()

            # 실행 모니터링 태스크 시작
            self.execution_task = asyncio.create_task(self._execution_monitoring_loop())

            self.is_running = True
            self.logger.info("[OrderManager] 주문 관리자 시작 완료")
            return True

        except Exception as e:
            self.logger.error(f"주문 관리자 시작 실패: {e}")
            return False

    async def stop_manager(self) -> bool:
        """주문 관리자 중지"""
        try:
            self.logger.info("[OrderManager] 주문 관리자 중지")

            self.is_running = False

            # 실행 모니터링 태스크 중지
            if self.execution_task and not self.execution_task.done():
                self.execution_task.cancel()

            # 미완료 주문들 처리
            await self._handle_pending_orders()

            return True

        except Exception as e:
            self.logger.error(f"주문 관리자 중지 실패: {e}")
            return False

    async def create_smart_order(self, signal: TradingSignal, candidate: CandidateStock,
                               strategy: OrderStrategy = OrderStrategy.LIMIT) -> str:
        """스마트 주문 생성"""
        try:
            order_id = str(uuid.uuid4())

            # 주문 수량 계산
            target_amount = await self._calculate_target_amount(candidate)
            quantity, actual_amount = await self.position_sizing_service.calculate_order_quantity(
                candidate.symbol, target_amount
            )

            if quantity <= 0:
                raise ValueError("Invalid order quantity")

            # 목표 가격 결정
            target_price = await self._determine_target_price(signal, candidate, strategy)

            # 스마트 주문 생성
            smart_order = SmartOrder(
                order_id=order_id,
                original_signal=signal,
                candidate=candidate,
                strategy=strategy,
                total_quantity=quantity,
                target_price=target_price,
                max_slippage=self.default_slippage_limit,
                time_limit_minutes=self.default_time_limit
            )

            # 주문 전략에 따른 실행 계획 생성
            await self._create_execution_plan(smart_order)

            self.smart_orders[order_id] = smart_order
            self.total_orders_managed += 1

            self.logger.info(f"[OrderManager] 스마트 주문 생성: {candidate.symbol} "
                           f"{quantity}주 @ ${target_price:.2f} ({strategy.value})")

            return order_id

        except Exception as e:
            self.logger.error(f"스마트 주문 생성 실패: {e}")
            raise

    async def execute_smart_order(self, order_id: str) -> bool:
        """스마트 주문 실행"""
        try:
            if order_id not in self.smart_orders:
                raise ValueError(f"Smart order not found: {order_id}")

            smart_order = self.smart_orders[order_id]

            # 시장 상황 분석
            await self._analyze_market_conditions(smart_order.candidate.symbol)

            # 전략별 실행
            success = False

            if smart_order.strategy == OrderStrategy.MARKET:
                success = await self._execute_market_order(smart_order)
            elif smart_order.strategy == OrderStrategy.LIMIT:
                success = await self._execute_limit_order(smart_order)
            elif smart_order.strategy == OrderStrategy.TWAP:
                success = await self._execute_twap_order(smart_order)
            elif smart_order.strategy == OrderStrategy.ICEBERG:
                success = await self._execute_iceberg_order(smart_order)
            elif smart_order.strategy == OrderStrategy.BRACKET:
                success = await self._execute_bracket_order(smart_order)
            else:
                success = await self._execute_limit_order(smart_order)  # 기본 전략

            if success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            return success

        except Exception as e:
            self.logger.error(f"스마트 주문 실행 실패 ({order_id}): {e}")
            self.failed_executions += 1
            return False

    async def cancel_smart_order(self, order_id: str) -> bool:
        """스마트 주문 취소"""
        try:
            if order_id not in self.smart_orders:
                return False

            smart_order = self.smart_orders[order_id]

            # 자식 주문들 모두 취소
            cancel_results = []
            for child_order in smart_order.child_orders:
                if child_order.order_id:
                    result = await self.api_order_service.cancel_order(child_order.order_id)
                    cancel_results.append(result)

            # 스마트 주문을 완료된 주문으로 이동
            self.completed_orders.append(smart_order)
            del self.smart_orders[order_id]

            success = all(cancel_results) if cancel_results else True

            self.logger.info(f"[OrderManager] 스마트 주문 취소: {order_id} "
                           f"({'성공' if success else '부분성공'})")

            return success

        except Exception as e:
            self.logger.error(f"스마트 주문 취소 실패 ({order_id}): {e}")
            return False

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            if order_id in self.smart_orders:
                smart_order = self.smart_orders[order_id]
                return {
                    'order_id': order_id,
                    'symbol': smart_order.candidate.symbol,
                    'strategy': smart_order.strategy.value,
                    'status': 'ACTIVE',
                    'total_quantity': smart_order.total_quantity,
                    'executed_quantity': smart_order.executed_quantity,
                    'remaining_quantity': smart_order.remaining_quantity,
                    'avg_execution_price': smart_order.avg_execution_price,
                    'target_price': smart_order.target_price,
                    'child_orders_count': len(smart_order.child_orders),
                    'creation_time': smart_order.creation_time.isoformat()
                }

            # 완료된 주문에서 찾기
            for completed_order in self.completed_orders:
                if completed_order.order_id == order_id:
                    return {
                        'order_id': order_id,
                        'symbol': completed_order.candidate.symbol,
                        'strategy': completed_order.strategy.value,
                        'status': 'COMPLETED',
                        'total_quantity': completed_order.total_quantity,
                        'executed_quantity': completed_order.executed_quantity,
                        'remaining_quantity': completed_order.remaining_quantity,
                        'avg_execution_price': completed_order.avg_execution_price,
                        'target_price': completed_order.target_price,
                        'creation_time': completed_order.creation_time.isoformat()
                    }

            return {'error': 'Order not found'}

        except Exception as e:
            self.logger.error(f"주문 상태 조회 실패 ({order_id}): {e}")
            return {'error': str(e)}

    async def get_active_smart_orders(self) -> List[Dict[str, Any]]:
        """활성 스마트 주문 목록"""
        try:
            active_orders = []

            for order_id, smart_order in self.smart_orders.items():
                status = await self.get_order_status(order_id)
                active_orders.append(status)

            return active_orders

        except Exception as e:
            self.logger.error(f"활성 주문 조회 실패: {e}")
            return []

    async def get_execution_analysis(self, order_id: str = None) -> Dict[str, Any]:
        """체결 분석 결과"""
        try:
            if order_id:
                # 특정 주문의 분석
                analyses = [a for a in self.execution_analyses if a.order_id == order_id]
                if analyses:
                    return analyses[-1].__dict__
                return {}

            # 전체 분석 통계
            if not self.execution_analyses:
                return {}

            recent_analyses = self.execution_analyses[-50:]  # 최근 50개

            slippages = [a.slippage for a in recent_analyses]
            execution_times = [a.execution_time_seconds for a in recent_analyses]
            fill_ratios = [a.fill_ratio for a in recent_analyses]

            return {
                'total_executions': len(self.execution_analyses),
                'recent_count': len(recent_analyses),
                'avg_slippage': statistics.mean(slippages) if slippages else 0,
                'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
                'avg_fill_ratio': statistics.mean(fill_ratios) if fill_ratios else 0,
                'quality_distribution': self._get_quality_distribution(recent_analyses)
            }

        except Exception as e:
            self.logger.error(f"체결 분석 조회 실패: {e}")
            return {}

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """실시간 가격 데이터 업데이트"""
        try:
            self.price_data_cache[symbol] = price_data

            # 가격 히스토리 업데이트
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            self.price_history[symbol].append(price_data.price)

            # 최대 200개 가격 히스토리 유지
            if len(self.price_history[symbol]) > 200:
                self.price_history[symbol] = self.price_history[symbol][-200:]

            # 관련 스마트 주문들에 가격 업데이트 알림
            asyncio.create_task(self._handle_price_update(symbol, price_data))

        except Exception as e:
            self.logger.error(f"가격 데이터 업데이트 실패 ({symbol}): {e}")

    def register_execution_callback(self, callback: Callable) -> None:
        """체결 콜백 등록"""
        if callback not in self.execution_callbacks:
            self.execution_callbacks.append(callback)

    def register_completion_callback(self, callback: Callable) -> None:
        """완료 콜백 등록"""
        if callback not in self.completion_callbacks:
            self.completion_callbacks.append(callback)

    async def _calculate_target_amount(self, candidate: CandidateStock) -> float:
        """목표 주문 금액 계산"""
        try:
            # 후보 점수 기반 금액 조정
            base_amount = 5000.0  # 기본 $5,000

            # 점수가 높을수록 더 많은 금액
            score_multiplier = 0.5 + (candidate.score * 1.5)  # 0.5 ~ 2.0

            target_amount = base_amount * score_multiplier

            # 최소/최대 한도 적용
            target_amount = max(1000.0, min(target_amount, 20000.0))

            return target_amount

        except Exception as e:
            self.logger.error(f"목표 금액 계산 실패: {e}")
            return 5000.0

    async def _determine_target_price(self, signal: TradingSignal, candidate: CandidateStock,
                                    strategy: OrderStrategy) -> float:
        """목표 가격 결정"""
        try:
            current_price = signal.price

            # 현재 가격이 있으면 사용
            if candidate.symbol in self.price_data_cache:
                current_price = self.price_data_cache[candidate.symbol].price

            if strategy == OrderStrategy.MARKET:
                return current_price

            elif strategy == OrderStrategy.LIMIT:
                # 매수는 현재가보다 약간 낮게
                return current_price * 0.999  # 0.1% 할인

            elif strategy in [OrderStrategy.TWAP, OrderStrategy.VWAP]:
                # 평균 가격 전략은 현재가 기준
                return current_price

            elif strategy == OrderStrategy.ICEBERG:
                # 빙산 주문은 현재가보다 약간 낮게
                return current_price * 0.998  # 0.2% 할인

            else:
                return current_price * 0.999

        except Exception as e:
            self.logger.error(f"목표 가격 결정 실패: {e}")
            return signal.price

    async def _create_execution_plan(self, smart_order: SmartOrder) -> None:
        """실행 계획 생성"""
        try:
            if smart_order.strategy == OrderStrategy.TWAP:
                # TWAP: 시간 분할 주문
                await self._create_twap_plan(smart_order)

            elif smart_order.strategy == OrderStrategy.ICEBERG:
                # 빙산 주문: 수량 분할
                await self._create_iceberg_plan(smart_order)

            elif smart_order.strategy == OrderStrategy.BRACKET:
                # 브래킷 주문: 본 주문 + 손절/이익실현
                await self._create_bracket_plan(smart_order)

            else:
                # 단순 주문: 1개 자식 주문
                child_order = OrderRequest(
                    symbol=smart_order.candidate.symbol,
                    order_type=OrderType.BUY,
                    quantity=smart_order.total_quantity,
                    price=smart_order.target_price,
                    order_id=str(uuid.uuid4()),
                    strategy_source=f"SmartOrder_{smart_order.strategy.value}"
                )

                smart_order.child_orders.append(child_order)

        except Exception as e:
            self.logger.error(f"실행 계획 생성 실패: {e}")

    async def _create_twap_plan(self, smart_order: SmartOrder) -> None:
        """TWAP 실행 계획"""
        try:
            # 30분에 걸쳐 5번 분할 실행
            time_slices = 5
            slice_quantity = smart_order.total_quantity // time_slices
            remainder = smart_order.total_quantity % time_slices

            for i in range(time_slices):
                quantity = slice_quantity
                if i == time_slices - 1:  # 마지막 주문에 나머지 수량 추가
                    quantity += remainder

                child_order = OrderRequest(
                    symbol=smart_order.candidate.symbol,
                    order_type=OrderType.BUY,
                    quantity=quantity,
                    price=smart_order.target_price,
                    order_id=str(uuid.uuid4()),
                    strategy_source=f"TWAP_Slice_{i+1}",
                    notes=f"TWAP slice {i+1}/{time_slices}"
                )

                smart_order.child_orders.append(child_order)

        except Exception as e:
            self.logger.error(f"TWAP 계획 생성 실패: {e}")

    async def _create_iceberg_plan(self, smart_order: SmartOrder) -> None:
        """빙산 주문 계획"""
        try:
            # 전체 수량을 10% 단위로 분할
            display_ratio = 0.1
            display_quantity = max(1, int(smart_order.total_quantity * display_ratio))

            remaining = smart_order.total_quantity

            while remaining > 0:
                quantity = min(display_quantity, remaining)

                child_order = OrderRequest(
                    symbol=smart_order.candidate.symbol,
                    order_type=OrderType.BUY,
                    quantity=quantity,
                    price=smart_order.target_price,
                    order_id=str(uuid.uuid4()),
                    strategy_source="Iceberg",
                    notes=f"Iceberg order {quantity}/{smart_order.total_quantity}"
                )

                smart_order.child_orders.append(child_order)
                remaining -= quantity

        except Exception as e:
            self.logger.error(f"빙산 주문 계획 생성 실패: {e}")

    async def _create_bracket_plan(self, smart_order: SmartOrder) -> None:
        """브래킷 주문 계획"""
        try:
            # 1. 메인 매수 주문
            main_order = OrderRequest(
                symbol=smart_order.candidate.symbol,
                order_type=OrderType.BUY,
                quantity=smart_order.total_quantity,
                price=smart_order.target_price,
                order_id=str(uuid.uuid4()),
                strategy_source="Bracket_Main"
            )

            smart_order.child_orders.append(main_order)

            # 2. 손절매 주문 (매수가 대비 -5%)
            stop_loss_price = smart_order.target_price * 0.95

            # 3. 이익실현 주문 (목표가 있으면 사용, 없으면 +10%)
            take_profit_price = smart_order.candidate.target_price or (smart_order.target_price * 1.10)

            # 실제로는 메인 주문 체결 후에 조건부 주문으로 등록
            # 여기서는 계획만 저장
            smart_order.candidate.metadata = smart_order.candidate.metadata or {}
            smart_order.candidate.metadata.update({
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'bracket_order': True
            })

        except Exception as e:
            self.logger.error(f"브래킷 주문 계획 생성 실패: {e}")

    async def _execute_market_order(self, smart_order: SmartOrder) -> bool:
        """시장가 주문 실행"""
        try:
            if not smart_order.child_orders:
                return False

            child_order = smart_order.child_orders[0]

            # 현재 시장가로 주문 가격 업데이트
            if smart_order.candidate.symbol in self.price_data_cache:
                current_price = self.price_data_cache[smart_order.candidate.symbol].price
                child_order.price = current_price

            # API 주문 서비스로 전송
            response = await self.api_order_service.submit_buy_order(
                smart_order.candidate,
                child_order.quantity,
                child_order.price
            )

            if response.status in [OrderStatus.SUBMITTED, OrderStatus.FILLED]:
                await self._update_smart_order_execution(smart_order, response)
                return True

            return False

        except Exception as e:
            self.logger.error(f"시장가 주문 실행 실패: {e}")
            return False

    async def _execute_limit_order(self, smart_order: SmartOrder) -> bool:
        """지정가 주문 실행"""
        try:
            if not smart_order.child_orders:
                return False

            child_order = smart_order.child_orders[0]

            # API 주문 서비스로 전송
            response = await self.api_order_service.submit_buy_order(
                smart_order.candidate,
                child_order.quantity,
                child_order.price
            )

            if response.status in [OrderStatus.SUBMITTED, OrderStatus.PENDING]:
                child_order.order_id = response.order_id
                return True

            return False

        except Exception as e:
            self.logger.error(f"지정가 주문 실행 실패: {e}")
            return False

    async def _execute_twap_order(self, smart_order: SmartOrder) -> bool:
        """TWAP 주문 실행"""
        try:
            if not smart_order.child_orders:
                return False

            # 첫 번째 슬라이스만 즉시 실행
            first_slice = smart_order.child_orders[0]

            response = await self.api_order_service.submit_buy_order(
                smart_order.candidate,
                first_slice.quantity,
                first_slice.price
            )

            if response.status in [OrderStatus.SUBMITTED, OrderStatus.FILLED]:
                first_slice.order_id = response.order_id

                # 나머지 슬라이스들은 스케줄링 (실제로는 별도 태스크에서 처리)
                asyncio.create_task(self._schedule_twap_slices(smart_order))
                return True

            return False

        except Exception as e:
            self.logger.error(f"TWAP 주문 실행 실패: {e}")
            return False

    async def _execute_iceberg_order(self, smart_order: SmartOrder) -> bool:
        """빙산 주문 실행"""
        try:
            if not smart_order.child_orders:
                return False

            # 첫 번째 부분만 즉시 실행
            first_part = smart_order.child_orders[0]

            response = await self.api_order_service.submit_buy_order(
                smart_order.candidate,
                first_part.quantity,
                first_part.price
            )

            if response.status in [OrderStatus.SUBMITTED, OrderStatus.PENDING]:
                first_part.order_id = response.order_id
                return True

            return False

        except Exception as e:
            self.logger.error(f"빙산 주문 실행 실패: {e}")
            return False

    async def _execute_bracket_order(self, smart_order: SmartOrder) -> bool:
        """브래킷 주문 실행"""
        try:
            # 메인 주문만 먼저 실행
            return await self._execute_limit_order(smart_order)

        except Exception as e:
            self.logger.error(f"브래킷 주문 실행 실패: {e}")
            return False

    async def _schedule_twap_slices(self, smart_order: SmartOrder) -> None:
        """TWAP 슬라이스 스케줄링"""
        try:
            time_interval = smart_order.time_limit_minutes * 60 / len(smart_order.child_orders)

            # 첫 번째는 이미 실행했으므로 건너뛰기
            for i, slice_order in enumerate(smart_order.child_orders[1:], 1):
                await asyncio.sleep(time_interval)

                if not self.is_running:
                    break

                response = await self.api_order_service.submit_buy_order(
                    smart_order.candidate,
                    slice_order.quantity,
                    slice_order.price
                )

                if response.order_id:
                    slice_order.order_id = response.order_id

                self.logger.info(f"[OrderManager] TWAP 슬라이스 {i+1} 실행: "
                               f"{smart_order.candidate.symbol} {slice_order.quantity}주")

        except Exception as e:
            self.logger.error(f"TWAP 슬라이스 스케줄링 실패: {e}")

    async def _update_smart_order_execution(self, smart_order: SmartOrder, response: OrderResponse) -> None:
        """스마트 주문 실행 상태 업데이트"""
        try:
            if response.status == OrderStatus.FILLED:
                smart_order.executed_quantity += response.filled_quantity
                smart_order.remaining_quantity -= response.filled_quantity

                # 평균 체결가 계산
                if smart_order.executed_quantity > 0:
                    total_value = (smart_order.avg_execution_price * (smart_order.executed_quantity - response.filled_quantity) +
                                 response.avg_fill_price * response.filled_quantity)
                    smart_order.avg_execution_price = total_value / smart_order.executed_quantity

                # 체결 분석
                await self._analyze_execution(smart_order, response)

                # 완전 체결 시
                if smart_order.remaining_quantity <= 0:
                    await self._complete_smart_order(smart_order)

        except Exception as e:
            self.logger.error(f"스마트 주문 상태 업데이트 실패: {e}")

    async def _analyze_execution(self, smart_order: SmartOrder, response: OrderResponse) -> None:
        """체결 분석"""
        try:
            if not response.avg_fill_price:
                return

            # 슬리피지 계산
            slippage = (response.avg_fill_price - smart_order.target_price) / smart_order.target_price

            # 체결 시간 계산
            execution_time = (datetime.now() - smart_order.creation_time).total_seconds()

            # 체결률
            fill_ratio = response.filled_quantity / smart_order.total_quantity

            # 시장 임팩트 (단순화된 계산)
            market_impact = abs(slippage) * 100  # 백분율

            # 체결 품질 평가
            quality = self._assess_execution_quality(slippage, execution_time, fill_ratio)

            # 분석 결과 저장
            analysis = ExecutionAnalysis(
                order_id=smart_order.order_id,
                execution_quality=quality,
                slippage=slippage,
                execution_time_seconds=execution_time,
                market_impact=market_impact,
                fill_ratio=fill_ratio,
                price_improvement=0.0,  # 간단화
                timestamp=datetime.now()
            )

            self.execution_analyses.append(analysis)

            # 통계 업데이트
            self.total_slippage += abs(slippage)

            # 최대 1000개 분석 결과 유지
            if len(self.execution_analyses) > 1000:
                self.execution_analyses = self.execution_analyses[-1000:]

        except Exception as e:
            self.logger.error(f"체결 분석 실패: {e}")

    def _assess_execution_quality(self, slippage: float, execution_time: float, fill_ratio: float) -> ExecutionQuality:
        """체결 품질 평가"""
        try:
            score = 0

            # 슬리피지 점수 (40%)
            if abs(slippage) < 0.001:  # 0.1% 미만
                score += 40
            elif abs(slippage) < 0.005:  # 0.5% 미만
                score += 30
            elif abs(slippage) < 0.01:  # 1% 미만
                score += 20
            else:
                score += 10

            # 실행 시간 점수 (30%)
            if execution_time < 60:  # 1분 미만
                score += 30
            elif execution_time < 300:  # 5분 미만
                score += 25
            elif execution_time < 900:  # 15분 미만
                score += 20
            else:
                score += 10

            # 체결률 점수 (30%)
            if fill_ratio >= 1.0:
                score += 30
            elif fill_ratio >= 0.9:
                score += 25
            elif fill_ratio >= 0.7:
                score += 20
            else:
                score += 10

            # 품질 등급 결정
            if score >= 85:
                return ExecutionQuality.EXCELLENT
            elif score >= 70:
                return ExecutionQuality.GOOD
            elif score >= 50:
                return ExecutionQuality.FAIR
            else:
                return ExecutionQuality.POOR

        except Exception as e:
            self.logger.error(f"체결 품질 평가 실패: {e}")
            return ExecutionQuality.FAIR

    async def _complete_smart_order(self, smart_order: SmartOrder) -> None:
        """스마트 주문 완료 처리"""
        try:
            # 완료된 주문 목록으로 이동
            self.completed_orders.append(smart_order)
            del self.smart_orders[smart_order.order_id]

            # 완료 콜백 호출
            await self._notify_completion_callbacks(smart_order)

            self.logger.info(f"[OrderManager] 스마트 주문 완료: {smart_order.candidate.symbol} "
                           f"{smart_order.executed_quantity}/{smart_order.total_quantity}주 "
                           f"@ ${smart_order.avg_execution_price:.2f}")

        except Exception as e:
            self.logger.error(f"스마트 주문 완료 처리 실패: {e}")

    async def _execution_monitoring_loop(self):
        """실행 모니터링 루프"""
        while self.is_running:
            try:
                # 활성 스마트 주문들 상태 체크
                for order_id in list(self.smart_orders.keys()):
                    await self._monitor_smart_order(order_id)

                # 10초마다 모니터링
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"실행 모니터링 루프 오류: {e}")
                await asyncio.sleep(5)

    async def _monitor_smart_order(self, order_id: str) -> None:
        """스마트 주문 모니터링"""
        try:
            if order_id not in self.smart_orders:
                return

            smart_order = self.smart_orders[order_id]

            # 시간 초과 확인
            elapsed = datetime.now() - smart_order.creation_time
            if elapsed.total_seconds() > smart_order.time_limit_minutes * 60:
                self.logger.warning(f"[OrderManager] 스마트 주문 시간 초과: {order_id}")
                await self.cancel_smart_order(order_id)
                return

            # 자식 주문들 상태 확인
            for child_order in smart_order.child_orders:
                if child_order.order_id:
                    status = await self.api_order_service.get_order_status(child_order.order_id)
                    if status and status.status == OrderStatus.FILLED:
                        await self._update_smart_order_execution(smart_order, status)

        except Exception as e:
            self.logger.error(f"스마트 주문 모니터링 실패 ({order_id}): {e}")

    async def _handle_price_update(self, symbol: str, price_data: PriceData) -> None:
        """가격 업데이트 처리"""
        try:
            # 관련 스마트 주문들 찾기
            for smart_order in self.smart_orders.values():
                if smart_order.candidate.symbol == symbol:
                    # 가격 변동이 큰 경우 주문 조정 고려
                    price_change = abs((price_data.price - smart_order.target_price) / smart_order.target_price)

                    if price_change > smart_order.max_slippage:
                        self.logger.warning(f"[OrderManager] 큰 가격 변동 감지: {symbol} "
                                          f"{price_change:.2%} > {smart_order.max_slippage:.2%}")

        except Exception as e:
            self.logger.error(f"가격 업데이트 처리 실패 ({symbol}): {e}")

    async def _analyze_market_conditions(self, symbol: str) -> None:
        """시장 상황 분석"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return

            prices = self.price_history[symbol][-20:]  # 최근 20개 가격

            # 변동성 계산
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0

            # 트렌드 계산 (단순 기울기)
            trend = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0

            # 시장 상황 업데이트
            if volatility > 0.02:
                self.market_conditions['volatility'] = 'HIGH'
            elif volatility < 0.005:
                self.market_conditions['volatility'] = 'LOW'
            else:
                self.market_conditions['volatility'] = 'NORMAL'

            if trend > 0.01:
                self.market_conditions['trend'] = 'UP'
            elif trend < -0.01:
                self.market_conditions['trend'] = 'DOWN'
            else:
                self.market_conditions['trend'] = 'NEUTRAL'

        except Exception as e:
            self.logger.error(f"시장 상황 분석 실패 ({symbol}): {e}")

    async def _notify_completion_callbacks(self, smart_order: SmartOrder) -> None:
        """완료 콜백 알림"""
        try:
            for callback in self.completion_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(smart_order)
                    else:
                        callback(smart_order)
                except Exception as e:
                    self.logger.error(f"완료 콜백 실행 실패: {e}")
        except Exception as e:
            self.logger.error(f"완료 콜백 알림 실패: {e}")

    async def _handle_pending_orders(self) -> None:
        """미완료 주문 처리"""
        try:
            for order_id in list(self.smart_orders.keys()):
                await self.cancel_smart_order(order_id)

        except Exception as e:
            self.logger.error(f"미완료 주문 처리 실패: {e}")

    def _get_quality_distribution(self, analyses: List[ExecutionAnalysis]) -> Dict[str, int]:
        """품질 분포 계산"""
        try:
            distribution = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 0, 'POOR': 0}

            for analysis in analyses:
                distribution[analysis.execution_quality.value] += 1

            return distribution

        except Exception as e:
            self.logger.error(f"품질 분포 계산 실패: {e}")
            return {}

    async def _validate_configuration(self) -> None:
        """설정 유효성 검증"""
        if not 0 < self.default_slippage_limit <= 0.1:
            raise ValueError("Invalid slippage limit")

        if self.default_time_limit <= 0:
            raise ValueError("Invalid time limit")

        self.logger.info(f"[OrderManager] 설정 검증 완료: "
                        f"슬리피지한도={self.default_slippage_limit:.1%}, "
                        f"시간한도={self.default_time_limit}분")

    def get_manager_stats(self) -> Dict[str, Any]:
        """매니저 통계"""
        success_rate = 0
        if self.total_orders_managed > 0:
            success_rate = (self.successful_executions / self.total_orders_managed) * 100

        avg_slippage = 0
        if self.successful_executions > 0:
            avg_slippage = self.total_slippage / self.successful_executions

        return {
            'is_running': self.is_running,
            'total_orders_managed': self.total_orders_managed,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': success_rate,
            'active_smart_orders': len(self.smart_orders),
            'completed_orders': len(self.completed_orders),
            'avg_slippage': avg_slippage,
            'execution_analyses_count': len(self.execution_analyses),
            'market_conditions': self.market_conditions.copy()
        }


# 테스트 함수
async def test_order_manager():
    """OrderManager 테스트"""
    print("\n=== OrderManager 테스트 시작 ===")

    # Mock 서비스들
    class MockAPIOrderService:
        async def submit_buy_order(self, candidate, quantity, price):
            from ..models.trading_models import OrderResponse, OrderStatus
            import random
            return OrderResponse(
                order_id=str(uuid.uuid4()),
                symbol=candidate.symbol,
                status=OrderStatus.FILLED if random.random() > 0.1 else OrderStatus.SUBMITTED,
                filled_quantity=quantity if random.random() > 0.1 else 0,
                avg_fill_price=price * random.uniform(0.999, 1.001)
            )

        async def cancel_order(self, order_id):
            return True

        async def get_order_status(self, order_id):
            from ..models.trading_models import OrderResponse, OrderStatus
            import random
            return OrderResponse(
                order_id=order_id,
                symbol="TEST",
                status=OrderStatus.FILLED if random.random() > 0.3 else OrderStatus.PENDING,
                filled_quantity=10,
                avg_fill_price=100.0
            )

    class MockPositionSizingService:
        async def calculate_order_quantity(self, symbol, amount):
            return int(amount / 100), amount  # 가정: $100 per share

    config = {
        'order_management': {
            'max_slippage': 0.01,
            'default_time_limit': 30,
            'min_order_size': 1
        }
    }

    api_service = MockAPIOrderService()
    sizing_service = MockPositionSizingService()

    manager = OrderManager(config, api_service, sizing_service)

    try:
        # 매니저 시작
        success = await manager.start_manager()
        print(f"매니저 시작: {'성공' if success else '실패'}")

        # 콜백 등록
        completed_orders = []

        async def completion_callback(smart_order):
            completed_orders.append(smart_order)
            print(f"[완료] {smart_order.candidate.symbol} {smart_order.executed_quantity}주 완료")

        manager.register_completion_callback(completion_callback)

        # 테스트 신호 및 후보
        from ..models.trading_models import TradingSignal, CandidateStock, PriceData, SignalType, MarketType

        signal = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            confidence=0.85,
            price=174.0,
            timestamp=datetime.now(),
            strategy_name='TestStrategy'
        )

        candidate = CandidateStock(
            symbol='AAPL',
            score=0.9,
            strategy='TestStrategy',
            reasons=['Strong buy signal', 'High confidence'],
            target_price=180.0,
            expected_return=0.08
        )

        # 가격 데이터 설정
        price_data = PriceData(
            symbol='AAPL',
            price=174.0,
            volume=100000,
            timestamp=datetime.now(),
            market=MarketType.NASDAQ
        )
        manager.set_price_data('AAPL', price_data)

        # 다양한 주문 전략 테스트
        strategies = [
            OrderStrategy.LIMIT,
            OrderStrategy.MARKET,
            OrderStrategy.TWAP,
            OrderStrategy.ICEBERG
        ]

        order_ids = []

        for i, strategy in enumerate(strategies):
            test_candidate = CandidateStock(
                symbol=f'TEST{i}',
                score=0.8,
                strategy='TestStrategy',
                reasons=['Test order'],
                target_price=100.0 + i
            )

            test_signal = TradingSignal(
                symbol=f'TEST{i}',
                signal_type=SignalType.BUY,
                confidence=0.8,
                price=100.0 + i,
                timestamp=datetime.now(),
                strategy_name='TestStrategy'
            )

            print(f"\n{strategy.value} 주문 생성...")
            order_id = await manager.create_smart_order(test_signal, test_candidate, strategy)
            order_ids.append(order_id)

            # 주문 실행
            execution_success = await manager.execute_smart_order(order_id)
            print(f"{strategy.value} 주문 실행: {'성공' if execution_success else '실패'}")

        # 주문 상태 확인
        print(f"\n주문 상태 확인...")
        for order_id in order_ids:
            status = await manager.get_order_status(order_id)
            print(f"주문 {order_id[:8]}: {status.get('status', 'UNKNOWN')}")

        # 활성 주문 목록
        active_orders = await manager.get_active_smart_orders()
        print(f"\n활성 주문 ({len(active_orders)}개):")
        for order in active_orders[:3]:  # 처음 3개만 표시
            print(f"  {order['symbol']}: {order['strategy']} "
                  f"({order['executed_quantity']}/{order['total_quantity']})")

        # 체결 분석
        execution_analysis = await manager.get_execution_analysis()
        print(f"\n체결 분석:")
        for key, value in execution_analysis.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")

        # 매니저 통계
        stats = manager.get_manager_stats()
        print(f"\n매니저 통계:")
        print(f"  관리된 주문: {stats['total_orders_managed']}")
        print(f"  성공 실행: {stats['successful_executions']}")
        print(f"  실패 실행: {stats['failed_executions']}")
        print(f"  성공률: {stats['success_rate']:.1f}%")
        print(f"  평균 슬리피지: {stats['avg_slippage']:.4f}")

        print(f"\n완료 콜백 수신: {len(completed_orders)}개")

        # 매니저 중지
        await manager.stop_manager()
        print("\n매니저 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_manager())