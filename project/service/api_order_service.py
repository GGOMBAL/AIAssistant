"""
API Order Service

KIS API를 통한 실제 주문 실행 및 관리 서비스
포지션 사이징 서비스로부터 받은 주문 요청을 실제 거래소에 전송
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid

from ..interfaces.service_interfaces import IAPIOrderService, BaseService
from ..models.trading_models import (
    OrderRequest, OrderResponse, OrderType, OrderStatus,
    CandidateStock, PriceData
)


class APIOrderService(BaseService, IAPIOrderService):
    """API 주문 서비스 구현"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # KIS API 설정
        self.kis_config = config.get('kis_api', {})
        self.app_key = self.kis_config.get('app_key', '')
        self.app_secret = self.kis_config.get('app_secret', '')
        self.account_no = self.kis_config.get('account_no', '')
        self.is_virtual = self.kis_config.get('is_virtual', True)

        # 주문 관리
        self.active_orders: Dict[str, OrderRequest] = {}
        self.order_history: List[OrderResponse] = []
        self.pending_orders: List[OrderRequest] = []

        # API 연결 상태
        self.is_connected = False
        self.access_token = None
        self.token_expires_at = None

        # 주문 제한 설정
        self.max_orders_per_minute = config.get('order_limits', {}).get('max_per_minute', 10)
        self.max_order_amount = config.get('order_limits', {}).get('max_amount', 100000)
        self.min_order_amount = config.get('order_limits', {}).get('min_amount', 100)

        # 통계
        self.orders_submitted_today = 0
        self.orders_filled_today = 0
        self.orders_failed_today = 0
        self.total_trade_volume = 0.0

        # 가격 데이터 캐시
        self.price_data_cache: Dict[str, PriceData] = {}

        # 주문 실행 큐
        self.order_queue = asyncio.Queue()
        self.order_processor_task = None

    async def start_service(self) -> bool:
        """서비스 시작"""
        try:
            self.logger.info("[APIOrderService] 서비스 시작")

            # KIS API 연결
            if not await self._initialize_kis_api():
                raise Exception("KIS API 초기화 실패")

            # 주문 처리 태스크 시작
            self.order_processor_task = asyncio.create_task(self._order_processing_loop())

            await self.initialize()
            self.logger.info("[APIOrderService] 서비스 시작 완료")
            return True

        except Exception as e:
            self.log_error(f"서비스 시작 실패: {e}")
            return False

    async def stop_service(self) -> bool:
        """서비스 중지"""
        try:
            self.logger.info("[APIOrderService] 서비스 중지")

            # 주문 처리 태스크 중지
            if self.order_processor_task and not self.order_processor_task.done():
                self.order_processor_task.cancel()

            # 활성 주문들 처리
            await self._handle_shutdown_orders()

            await self.cleanup()
            return True

        except Exception as e:
            self.log_error(f"서비스 중지 실패: {e}")
            return False

    async def submit_buy_order(self, candidate: CandidateStock, quantity: int, price: float) -> OrderResponse:
        """매수 주문 제출"""
        try:
            # 주문 요청 생성
            order_id = str(uuid.uuid4())

            order_request = OrderRequest(
                symbol=candidate.symbol,
                order_type=OrderType.BUY,
                quantity=quantity,
                price=price,
                order_id=order_id,
                strategy_source=candidate.strategy,
                notes=f"Score: {candidate.score:.3f}, Reasons: {'; '.join(candidate.reasons[:2])}"
            )

            # 주문 검증
            validation_result = await self._validate_order(order_request)
            if not validation_result['valid']:
                return OrderResponse(
                    order_id=order_id,
                    symbol=candidate.symbol,
                    status=OrderStatus.REJECTED,
                    error_message=validation_result['reason']
                )

            # 주문 큐에 추가
            await self.order_queue.put(order_request)
            self.active_orders[order_id] = order_request

            self.logger.info(f"[APIOrderService] 매수 주문 큐에 추가: {candidate.symbol} "
                           f"{quantity}주 @ ${price:.2f}")

            # 대기 상태 응답
            return OrderResponse(
                order_id=order_id,
                symbol=candidate.symbol,
                status=OrderStatus.PENDING,
                remaining_quantity=quantity
            )

        except Exception as e:
            self.log_error(f"매수 주문 제출 실패 ({candidate.symbol}): {e}")
            return OrderResponse(
                order_id=str(uuid.uuid4()),
                symbol=candidate.symbol,
                status=OrderStatus.FAILED,
                error_message=str(e)
            )

    async def submit_sell_order(self, symbol: str, quantity: int, price: float) -> OrderResponse:
        """매도 주문 제출"""
        try:
            order_id = str(uuid.uuid4())

            order_request = OrderRequest(
                symbol=symbol,
                order_type=OrderType.SELL,
                quantity=quantity,
                price=price,
                order_id=order_id,
                strategy_source="AutoSell",
                notes="Automated sell order"
            )

            # 주문 검증
            validation_result = await self._validate_order(order_request)
            if not validation_result['valid']:
                return OrderResponse(
                    order_id=order_id,
                    symbol=symbol,
                    status=OrderStatus.REJECTED,
                    error_message=validation_result['reason']
                )

            # 주문 큐에 추가
            await self.order_queue.put(order_request)
            self.active_orders[order_id] = order_request

            self.logger.info(f"[APIOrderService] 매도 주문 큐에 추가: {symbol} "
                           f"{quantity}주 @ ${price:.2f}")

            return OrderResponse(
                order_id=order_id,
                symbol=symbol,
                status=OrderStatus.PENDING,
                remaining_quantity=quantity
            )

        except Exception as e:
            self.log_error(f"매도 주문 제출 실패 ({symbol}): {e}")
            return OrderResponse(
                order_id=str(uuid.uuid4()),
                symbol=symbol,
                status=OrderStatus.FAILED,
                error_message=str(e)
            )

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            if order_id not in self.active_orders:
                self.logger.warning(f"[APIOrderService] 취소할 주문 없음: {order_id}")
                return False

            order = self.active_orders[order_id]

            # KIS API 취소 요청 (시뮬레이션)
            cancel_success = await self._cancel_order_via_api(order_id)

            if cancel_success:
                # 주문 상태 업데이트
                cancel_response = OrderResponse(
                    order_id=order_id,
                    symbol=order.symbol,
                    status=OrderStatus.CANCELLED,
                    timestamp=datetime.now()
                )

                self.order_history.append(cancel_response)
                del self.active_orders[order_id]

                self.logger.info(f"[APIOrderService] 주문 취소 성공: {order_id}")
                return True

            return False

        except Exception as e:
            self.log_error(f"주문 취소 실패 ({order_id}): {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[OrderResponse]:
        """주문 상태 조회"""
        try:
            # 히스토리에서 최신 상태 조회
            for response in reversed(self.order_history):
                if response.order_id == order_id:
                    return response

            # 활성 주문에서 확인
            if order_id in self.active_orders:
                order = self.active_orders[order_id]

                # API에서 최신 상태 조회 (시뮬레이션)
                api_status = await self._query_order_status_via_api(order_id)

                return OrderResponse(
                    order_id=order_id,
                    symbol=order.symbol,
                    status=api_status.get('status', OrderStatus.PENDING),
                    filled_quantity=api_status.get('filled_quantity', 0),
                    remaining_quantity=api_status.get('remaining_quantity', order.quantity),
                    avg_fill_price=api_status.get('avg_fill_price')
                )

            return None

        except Exception as e:
            self.log_error(f"주문 상태 조회 실패 ({order_id}): {e}")
            return None

    async def get_active_orders(self) -> List[OrderRequest]:
        """활성 주문 목록"""
        return list(self.active_orders.values())

    async def get_order_history(self, days: int = 30) -> List[OrderResponse]:
        """주문 히스토리"""
        cutoff_date = datetime.now() - timedelta(days=days)

        return [
            order for order in self.order_history
            if order.timestamp >= cutoff_date
        ]

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """가격 데이터 업데이트"""
        self.price_data_cache[symbol] = price_data

    async def _initialize_kis_api(self) -> bool:
        """KIS API 초기화"""
        try:
            # OAuth 토큰 획득 (시뮬레이션)
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션

            self.access_token = "simulated_token_" + str(uuid.uuid4())[:8]
            self.token_expires_at = datetime.now() + timedelta(hours=12)
            self.is_connected = True

            self.logger.info(f"[APIOrderService] KIS API 연결 성공 (계좌: {self.account_no})")
            return True

        except Exception as e:
            self.log_error(f"KIS API 초기화 실패: {e}")
            return False

    async def _order_processing_loop(self):
        """주문 처리 루프"""
        while self.is_running:
            try:
                # 큐에서 주문 요청 대기 (타임아웃 1초)
                order_request = await asyncio.wait_for(
                    self.order_queue.get(), timeout=1.0
                )

                # 주문 실행
                await self._execute_order(order_request)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.log_error(f"주문 처리 루프 오류: {e}")
                await asyncio.sleep(1)

    async def _execute_order(self, order_request: OrderRequest) -> None:
        """주문 실행"""
        try:
            self.logger.info(f"[APIOrderService] 주문 실행 시작: {order_request.order_id}")

            # 토큰 유효성 확인
            if not await self._ensure_valid_token():
                raise Exception("Invalid or expired token")

            # KIS API 주문 제출 (시뮬레이션)
            api_response = await self._submit_order_to_kis(order_request)

            # 응답 처리
            if api_response['success']:
                # 성공 응답
                response = OrderResponse(
                    order_id=order_request.order_id,
                    symbol=order_request.symbol,
                    status=OrderStatus.SUBMITTED,
                    remaining_quantity=order_request.quantity,
                    timestamp=datetime.now()
                )

                # 체결 시뮬레이션 (90% 확률로 즉시 체결)
                import random
                if random.random() < 0.9:
                    # 즉시 체결 시뮬레이션
                    await asyncio.sleep(0.1)

                    fill_price = self._get_simulated_fill_price(
                        order_request.symbol, order_request.price
                    )

                    response.status = OrderStatus.FILLED
                    response.filled_quantity = order_request.quantity
                    response.remaining_quantity = 0
                    response.avg_fill_price = fill_price
                    response.commission = order_request.quantity * fill_price * 0.0001  # 0.01% 수수료

                    self.orders_filled_today += 1
                    self.total_trade_volume += order_request.quantity * fill_price

                    self.logger.info(f"[APIOrderService] 주문 체결: {order_request.symbol} "
                                   f"{order_request.quantity}주 @ ${fill_price:.2f}")

                else:
                    # 부분 체결 또는 대기
                    self.logger.info(f"[APIOrderService] 주문 대기: {order_request.order_id}")

                self.orders_submitted_today += 1

            else:
                # 실패 응답
                response = OrderResponse(
                    order_id=order_request.order_id,
                    symbol=order_request.symbol,
                    status=OrderStatus.REJECTED,
                    error_message=api_response.get('error', 'Unknown error'),
                    timestamp=datetime.now()
                )

                self.orders_failed_today += 1
                self.logger.error(f"[APIOrderService] 주문 실패: {order_request.order_id} - "
                                f"{response.error_message}")

            # 결과 저장
            self.order_history.append(response)

            # 활성 주문에서 제거 (체결 완료 또는 실패 시)
            if response.status in [OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.FAILED]:
                if order_request.order_id in self.active_orders:
                    del self.active_orders[order_request.order_id]

            # 히스토리 크기 제한
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]

        except Exception as e:
            self.log_error(f"주문 실행 실패 ({order_request.order_id}): {e}")

            # 실패 응답 기록
            error_response = OrderResponse(
                order_id=order_request.order_id,
                symbol=order_request.symbol,
                status=OrderStatus.FAILED,
                error_message=str(e),
                timestamp=datetime.now()
            )

            self.order_history.append(error_response)
            self.orders_failed_today += 1

            # 활성 주문에서 제거
            if order_request.order_id in self.active_orders:
                del self.active_orders[order_request.order_id]

    async def _validate_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """주문 유효성 검증"""
        try:
            # 1. 기본 필드 확인
            if not order_request.symbol or order_request.quantity <= 0 or order_request.price <= 0:
                return {'valid': False, 'reason': 'Invalid order parameters'}

            # 2. 주문 금액 한도 확인
            order_amount = order_request.quantity * order_request.price
            if order_amount < self.min_order_amount:
                return {'valid': False, 'reason': f'Order amount below minimum (${self.min_order_amount:,})'}

            if order_amount > self.max_order_amount:
                return {'valid': False, 'reason': f'Order amount exceeds maximum (${self.max_order_amount:,})'}

            # 3. API 연결 상태 확인
            if not self.is_connected:
                return {'valid': False, 'reason': 'API not connected'}

            # 4. 주문 빈도 제한 확인
            recent_orders = await self._count_recent_orders(minutes=1)
            if recent_orders >= self.max_orders_per_minute:
                return {'valid': False, 'reason': 'Order frequency limit exceeded'}

            # 5. 심볼 유효성 확인 (간단한 검증)
            if len(order_request.symbol) < 1 or len(order_request.symbol) > 10:
                return {'valid': False, 'reason': 'Invalid symbol format'}

            return {'valid': True, 'reason': 'Valid order'}

        except Exception as e:
            self.log_error(f"주문 검증 실패: {e}")
            return {'valid': False, 'reason': f'Validation error: {e}'}

    async def _submit_order_to_kis(self, order_request: OrderRequest) -> Dict[str, Any]:
        """KIS API에 주문 제출 (시뮬레이션)"""
        try:
            # 실제로는 KIS API 호출
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션

            # 시뮬레이션 응답 (95% 성공률)
            import random
            success_rate = 0.95

            if random.random() < success_rate:
                return {
                    'success': True,
                    'kis_order_id': f"KIS_{str(uuid.uuid4())[:8]}",
                    'message': 'Order submitted successfully'
                }
            else:
                error_messages = [
                    'Insufficient buying power',
                    'Invalid symbol',
                    'Market closed',
                    'Price limit exceeded',
                    'System maintenance'
                ]

                return {
                    'success': False,
                    'error': random.choice(error_messages)
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'API communication error: {e}'
            }

    async def _cancel_order_via_api(self, order_id: str) -> bool:
        """KIS API를 통한 주문 취소 (시뮬레이션)"""
        try:
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션

            # 80% 확률로 취소 성공
            import random
            return random.random() < 0.8

        except Exception as e:
            self.log_error(f"API 주문 취소 실패: {e}")
            return False

    async def _query_order_status_via_api(self, order_id: str) -> Dict[str, Any]:
        """KIS API를 통한 주문 상태 조회 (시뮬레이션)"""
        try:
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션

            # 시뮬레이션 상태 반환
            import random
            statuses = [OrderStatus.PENDING, OrderStatus.FILLED, OrderStatus.CANCELLED]
            status = random.choice(statuses)

            if order_id in self.active_orders:
                order = self.active_orders[order_id]

                return {
                    'status': status,
                    'filled_quantity': order.quantity if status == OrderStatus.FILLED else 0,
                    'remaining_quantity': 0 if status == OrderStatus.FILLED else order.quantity,
                    'avg_fill_price': order.price * random.uniform(0.995, 1.005) if status == OrderStatus.FILLED else None
                }

            return {'status': OrderStatus.PENDING}

        except Exception as e:
            self.log_error(f"API 상태 조회 실패: {e}")
            return {'status': OrderStatus.PENDING}

    async def _ensure_valid_token(self) -> bool:
        """토큰 유효성 확인 및 갱신"""
        try:
            if not self.access_token or not self.token_expires_at:
                return await self._refresh_token()

            # 토큰 만료 10분 전에 갱신
            if datetime.now() >= (self.token_expires_at - timedelta(minutes=10)):
                return await self._refresh_token()

            return True

        except Exception as e:
            self.log_error(f"토큰 확인 실패: {e}")
            return False

    async def _refresh_token(self) -> bool:
        """토큰 갱신"""
        try:
            # 토큰 갱신 API 호출 (시뮬레이션)
            await asyncio.sleep(0.1)

            self.access_token = "refreshed_token_" + str(uuid.uuid4())[:8]
            self.token_expires_at = datetime.now() + timedelta(hours=12)

            self.logger.info("[APIOrderService] 토큰 갱신 완료")
            return True

        except Exception as e:
            self.log_error(f"토큰 갱신 실패: {e}")
            self.is_connected = False
            return False

    async def _count_recent_orders(self, minutes: int = 1) -> int:
        """최근 주문 수 카운트"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        return sum(
            1 for order in self.order_history
            if order.timestamp >= cutoff_time
        )

    def _get_simulated_fill_price(self, symbol: str, order_price: float) -> float:
        """시뮬레이션 체결가 계산"""
        try:
            # 실시간 가격이 있으면 사용
            if symbol in self.price_data_cache:
                market_price = self.price_data_cache[symbol].price
                # 시장가와 주문가 사이의 가격으로 체결 시뮬레이션
                import random
                return market_price + random.uniform(-0.01, 0.01)

            # 주문가 기준 약간의 슬리피지 적용
            import random
            return order_price * random.uniform(0.999, 1.001)

        except Exception:
            return order_price

    async def _handle_shutdown_orders(self) -> None:
        """서비스 종료 시 활성 주문 처리"""
        try:
            if not self.active_orders:
                return

            self.logger.info(f"[APIOrderService] 서비스 종료 - 활성 주문 {len(self.active_orders)}개 처리")

            # 모든 활성 주문 취소
            for order_id in list(self.active_orders.keys()):
                try:
                    await self.cancel_order(order_id)
                except Exception as e:
                    self.log_error(f"종료 시 주문 취소 실패 ({order_id}): {e}")

        except Exception as e:
            self.log_error(f"종료 시 주문 처리 실패: {e}")

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계"""
        success_rate = 0
        if self.orders_submitted_today > 0:
            success_rate = (self.orders_filled_today / self.orders_submitted_today) * 100

        return {
            'is_connected': self.is_connected,
            'account_no': self.account_no,
            'is_virtual': self.is_virtual,
            'active_orders': len(self.active_orders),
            'orders_today': {
                'submitted': self.orders_submitted_today,
                'filled': self.orders_filled_today,
                'failed': self.orders_failed_today,
                'success_rate': success_rate
            },
            'total_trade_volume': self.total_trade_volume,
            'order_history_count': len(self.order_history),
            'token_expires': self.token_expires_at.isoformat() if self.token_expires_at else None,
            **self.get_health_status()
        }

    # IAPIOrderService 인터페이스 구현
    async def place_order(self, order: Dict) -> Optional[str]:
        """주문 제출"""
        try:
            symbol = order.get('symbol', '')
            order_type = order.get('order_type', '')
            quantity = order.get('quantity', 0)
            price = order.get('price', 0.0)
            strategy_source = order.get('strategy_source', 'manual')

            if not all([symbol, order_type in ['BUY', 'SELL'], quantity > 0, price > 0]):
                self.logger.error(f"주문 파라미터 오류: {order}")
                return None

            # 주문 ID 생성
            order_id = str(uuid.uuid4())

            # OrderRequest 생성
            order_request = OrderRequest(
                order_id=order_id,
                symbol=symbol,
                quantity=quantity,
                order_type=OrderType.BUY if order_type == 'BUY' else OrderType.SELL,
                price=price,
                timestamp=datetime.now()
            )

            # 주문 처리 (시뮬레이션)
            if await self._submit_order_to_kis(order_request):
                # 주문 추적에 추가
                self.active_orders[order_id] = order_request
                self.orders_submitted_today += 1

                # OrderResponse 생성
                response = OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.SUBMITTED,
                    filled_quantity=0,
                    remaining_quantity=quantity,
                    avg_fill_price=0.0,
                    timestamp=datetime.now()
                )

                self.order_history.append(response)
                self.logger.info(f"주문 제출 성공: {symbol} {order_type} {quantity}주 @ ${price:.2f}")
                return order_id
            else:
                self.orders_failed_today += 1
                return None

        except Exception as e:
            self.log_error(f"주문 제출 실패: {e}")
            self.orders_failed_today += 1
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            if order_id not in self.active_orders:
                self.logger.warning(f"주문 ID를 찾을 수 없음: {order_id}")
                return False

            order = self.active_orders[order_id]

            # KIS API 주문 취소 (시뮬레이션)
            if await self._cancel_order_from_kis(order_id):
                # 주문 상태 업데이트
                response = OrderResponse(
                    order_id=order_id,
                    status=OrderStatus.CANCELLED,
                    filled_quantity=0,
                    remaining_quantity=0,
                    avg_fill_price=0.0,
                    timestamp=datetime.now()
                )

                self.order_history.append(response)
                del self.active_orders[order_id]

                self.logger.info(f"주문 취소 성공: {order.symbol} ({order_id[:8]})")
                return True
            else:
                self.logger.error(f"주문 취소 실패: {order_id}")
                return False

        except Exception as e:
            self.log_error(f"주문 취소 중 오류 ({order_id}): {e}")
            return False

    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """주문 상태 조회"""
        try:
            # 활성 주문에서 찾기
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                return {
                    'order_id': order_id,
                    'symbol': order.symbol,
                    'quantity': order.quantity,
                    'order_type': order.order_type.value,
                    'price': order.price,
                    'status': 'ACTIVE',
                    'timestamp': order.timestamp.isoformat()
                }

            # 히스토리에서 찾기
            for response in reversed(self.order_history):
                if response.order_id == order_id:
                    return {
                        'order_id': order_id,
                        'status': response.status.value,
                        'filled_quantity': response.filled_quantity,
                        'remaining_quantity': response.remaining_quantity,
                        'avg_fill_price': response.avg_fill_price,
                        'timestamp': response.timestamp.isoformat()
                    }

            return None

        except Exception as e:
            self.log_error(f"주문 상태 조회 실패 ({order_id}): {e}")
            return None

    async def get_pending_orders(self) -> List[Dict]:
        """대기 중인 주문 목록"""
        try:
            pending = []
            for order_id, order in self.active_orders.items():
                pending.append({
                    'order_id': order_id,
                    'symbol': order.symbol,
                    'quantity': order.quantity,
                    'order_type': order.order_type.value,
                    'price': order.price,
                    'timestamp': order.timestamp.isoformat()
                })
            return pending

        except Exception as e:
            self.log_error(f"대기 주문 조회 실패: {e}")
            return []

    async def get_order_history(self, limit: int = 100) -> List[Dict]:
        """주문 이력 조회"""
        try:
            history = []
            for response in self.order_history[-limit:]:
                history.append({
                    'order_id': response.order_id,
                    'status': response.status.value,
                    'filled_quantity': response.filled_quantity,
                    'remaining_quantity': response.remaining_quantity,
                    'avg_fill_price': response.avg_fill_price,
                    'timestamp': response.timestamp.isoformat()
                })
            return history

        except Exception as e:
            self.log_error(f"주문 이력 조회 실패: {e}")
            return []


# 테스트 함수
async def test_api_order_service():
    """APIOrderService 테스트"""
    print("\n=== APIOrderService 테스트 시작 ===")

    config = {
        'kis_api': {
            'app_key': 'test_key',
            'app_secret': 'test_secret',
            'account_no': '12345678-01',
            'is_virtual': True
        },
        'order_limits': {
            'max_per_minute': 10,
            'max_amount': 100000,
            'min_amount': 100
        }
    }

    service = APIOrderService(config)

    try:
        # 서비스 시작
        success = await service.start_service()
        print(f"서비스 시작: {'성공' if success else '실패'}")

        # 가격 데이터 설정
        from ..models.trading_models import PriceData, CandidateStock

        symbols = ['AAPL', 'MSFT', 'GOOGL']
        prices = [174.25, 338.92, 125.87]

        for symbol, price in zip(symbols, prices):
            price_data = PriceData(
                symbol=symbol,
                price=price,
                volume=100000,
                timestamp=datetime.now()
            )
            service.set_price_data(symbol, price_data)

        # 매수 주문 테스트
        print("\n매수 주문 테스트...")

        for i, (symbol, price) in enumerate(zip(symbols, prices)):
            candidate = CandidateStock(
                symbol=symbol,
                score=0.75 + (i * 0.05),
                strategy=f"TestStrategy_{i+1}",
                reasons=[f"Technical signal", f"High confidence"],
                target_price=price * 1.1,
                expected_return=0.08,
                risk_level="MEDIUM"
            )

            quantity = 10 + (i * 5)
            order_price = price * 0.999  # 약간 낮은 가격으로 주문

            response = await service.submit_buy_order(candidate, quantity, order_price)

            print(f"주문 제출: {symbol} {quantity}주 @ ${order_price:.2f}")
            print(f"  주문 ID: {response.order_id}")
            print(f"  상태: {response.status.value}")

            if response.error_message:
                print(f"  오류: {response.error_message}")

        # 주문 처리 대기
        print("\n주문 처리 대기 (3초)...")
        await asyncio.sleep(3)

        # 활성 주문 조회
        active_orders = await service.get_active_orders()
        print(f"\n활성 주문 ({len(active_orders)}개):")
        for order in active_orders:
            print(f"  {order.symbol}: {order.quantity}주 @ ${order.price:.2f} ({order.order_id[:8]})")

        # 주문 히스토리 조회
        history = await service.get_order_history(1)
        print(f"\n주문 히스토리 ({len(history)}개):")
        for response in history:
            status_info = f"{response.status.value}"
            if response.status == OrderStatus.FILLED:
                status_info += f" - {response.filled_quantity}주 @ ${response.avg_fill_price:.2f}"

            print(f"  {response.symbol}: {status_info} ({response.order_id[:8]})")

        # 매도 주문 테스트
        print("\n매도 주문 테스트...")

        sell_response = await service.submit_sell_order("AAPL", 5, 175.0)
        print(f"매도 주문: AAPL 5주 @ $175.00")
        print(f"  주문 ID: {sell_response.order_id}")
        print(f"  상태: {sell_response.status.value}")

        # 주문 상태 조회 테스트
        if history:
            test_order_id = history[0].order_id
            status = await service.get_order_status(test_order_id)
            if status:
                print(f"\n주문 상태 조회 ({test_order_id[:8]}):")
                print(f"  상태: {status.status.value}")
                print(f"  체결: {status.filled_quantity}주")
                print(f"  잔량: {status.remaining_quantity}주")

        # 서비스 통계
        stats = service.get_service_stats()
        print(f"\n서비스 통계:")
        print(f"  연결 상태: {stats['is_connected']}")
        print(f"  오늘 주문: {stats['orders_today']}")
        print(f"  거래량: ${stats['total_trade_volume']:,.0f}")
        print(f"  주문 히스토리: {stats['order_history_count']}개")

        # 서비스 중지
        await service.stop_service()
        print("\n서비스 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_order_service())