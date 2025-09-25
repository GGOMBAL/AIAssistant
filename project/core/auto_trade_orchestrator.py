"""
Auto Trade Orchestrator

전체 자동매매 시스템을 통합하고 조율하는 메인 오케스트레이터
모든 Phase의 컴포넌트들을 연결하여 완전한 자동매매 플랫폼 구현
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import uuid

# Phase 1 Components
from .websocket_manager import WebSocketManager
from ..service.live_price_service import LivePriceService
from ..ui.realtime_display import RealTimeDisplay

# Phase 2 Components
from ..service.account_analysis_service import AccountAnalysisService
from ..service.position_sizing_service import PositionSizingService
from ..service.api_order_service import APIOrderService

# Phase 3 Components
from .signal_engine import SignalEngine
from .risk_manager import RiskManager, RiskLevel, RiskAction
from .order_manager import OrderManager, OrderStrategy

# Models
from ..models.trading_models import (
    TradingSignal, Portfolio, SystemStatus,
    PriceData, CandidateStock, OrderResponse
)


class AutoTradeOrchestrator:
    """자동매매 시스템 오케스트레이터"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 시스템 상태
        self.is_running = False
        self.is_trading_active = False
        self.system_start_time = None

        # Phase 1: 기본 인프라
        self.websocket_manager = WebSocketManager(config.get('kis_websocket', {}))
        self.live_price_service = LivePriceService(config)
        self.realtime_display = RealTimeDisplay()

        # Phase 2: 핵심 서비스
        self.account_service = AccountAnalysisService(config)
        self.position_service = PositionSizingService(config)
        self.api_order_service = APIOrderService(config)

        # Phase 3: Core 엔진
        self.signal_engine = SignalEngine(config)
        self.risk_manager = RiskManager(config)
        self.order_manager = OrderManager(config, self.api_order_service, self.position_service)

        # 통합 관리
        self.active_signals: Dict[str, TradingSignal] = {}
        self.current_portfolio: Optional[Portfolio] = None
        self.system_metrics: Dict[str, Any] = {}

        # 이벤트 콜백
        self.event_callbacks: Dict[str, List[Callable]] = {
            'signal_received': [],
            'order_executed': [],
            'risk_alert': [],
            'system_error': [],
            'trading_stopped': []
        }

        # 태스크 관리
        self.orchestration_task = None
        self.monitoring_tasks = []

        # 통계
        self.total_signals_processed = 0
        self.total_orders_executed = 0
        self.system_uptime = 0.0

    async def set_real_account_data(self, account_data: Dict[str, Any]) -> None:
        """실제 계좌 데이터 설정"""
        try:
            if 'holdings' in account_data:
                # AccountAnalysisService에 실제 보유 종목 데이터 전달
                self.account_service.set_real_holdings_data(account_data['holdings'])
                # 포지션 데이터 즉시 새로고침
                await self.account_service.refresh_positions_with_real_data()
                self.logger.info(f"실제 계좌 데이터 설정 완료: {len(account_data['holdings'])}개 보유 종목")

                # 디스플레이 종목 업데이트
                await self._update_display_symbols()

            if 'balance' in account_data:
                # 계좌 잔고 정보도 설정 (필요시 구현)
                self.logger.info(f"계좌 잔고 정보: {account_data['balance']}")

        except Exception as e:
            self.logger.error(f"실제 계좌 데이터 설정 실패: {e}")

    async def start_system(self) -> bool:
        """전체 시스템 시작"""
        try:
            self.logger.info("=== Auto Trade System 시작 ===")
            self.system_start_time = datetime.now()

            # Phase 1: 기본 인프라 시작
            await self._start_phase1_components()

            # Phase 2: 핵심 서비스 시작
            await self._start_phase2_components()

            # Phase 3: Core 엔진 시작
            await self._start_phase3_components()

            # 컴포넌트 간 연결 설정
            await self._setup_component_connections()

            # 오케스트레이션 태스크 시작
            self.orchestration_task = asyncio.create_task(self._orchestration_loop())

            # 모니터링 태스크들 시작
            await self._start_monitoring_tasks()

            self.is_running = True
            self.logger.info("=== Auto Trade System 시작 완료 ===")
            return True

        except Exception as e:
            self.logger.error(f"시스템 시작 실패: {e}")
            await self.stop_system()
            return False

    async def stop_system(self) -> bool:
        """전체 시스템 중지"""
        try:
            self.logger.info("=== Auto Trade System 중지 시작 ===")

            self.is_running = False
            self.is_trading_active = False

            # 오케스트레이션 태스크 중지
            if self.orchestration_task and not self.orchestration_task.done():
                self.orchestration_task.cancel()

            # 모니터링 태스크들 중지
            await self._stop_monitoring_tasks()

            # Phase 3: Core 엔진 중지
            await self._stop_phase3_components()

            # Phase 2: 핵심 서비스 중지
            await self._stop_phase2_components()

            # Phase 1: 기본 인프라 중지
            await self._stop_phase1_components()

            self.logger.info("=== Auto Trade System 중지 완료 ===")
            return True

        except Exception as e:
            self.logger.error(f"시스템 중지 실패: {e}")
            return False

    async def enable_trading(self) -> bool:
        """거래 활성화"""
        try:
            if not self.is_running:
                self.logger.error("시스템이 실행 중이 아닙니다")
                return False

            # 리스크 상태 확인
            risk_check = await self.risk_manager.force_risk_check()
            if risk_check.get('is_trading_halted', False):
                self.logger.warning("리스크로 인해 거래를 활성화할 수 없습니다")
                return False

            self.is_trading_active = True
            self.logger.info("[Orchestrator] 자동 거래 활성화")

            # 이벤트 콜백 호출
            await self._trigger_event('trading_enabled', {'timestamp': datetime.now()})

            return True

        except Exception as e:
            self.logger.error(f"거래 활성화 실패: {e}")
            return False

    async def disable_trading(self) -> bool:
        """거래 비활성화"""
        try:
            self.is_trading_active = False
            self.logger.info("[Orchestrator] 자동 거래 비활성화")

            # 진행 중인 주문들은 유지
            # 신규 주문만 차단

            await self._trigger_event('trading_disabled', {'timestamp': datetime.now()})
            return True

        except Exception as e:
            self.logger.error(f"거래 비활성화 실패: {e}")
            return False

    async def add_trading_signal(self, signal: TradingSignal) -> bool:
        """외부에서 매매 신호 추가"""
        try:
            self.total_signals_processed += 1

            # SignalEngine에 신호 추가
            success = await self.signal_engine.add_signal(signal)

            if success:
                self.logger.info(f"[Orchestrator] 신호 수신: {signal.symbol} "
                               f"{signal.signal_type.value} (신뢰도: {signal.confidence:.3f})")

                await self._trigger_event('signal_received', {
                    'signal': signal,
                    'timestamp': datetime.now()
                })

            return success

        except Exception as e:
            self.logger.error(f"신호 추가 실패: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """전체 시스템 상태"""
        try:
            # 업타임 계산
            if self.system_start_time:
                self.system_uptime = (datetime.now() - self.system_start_time).total_seconds()

            # 각 컴포넌트 상태 수집
            component_status = {}

            # Phase 1
            component_status['websocket'] = self.websocket_manager.get_connection_status()
            component_status['live_price'] = self.live_price_service.get_service_stats()
            component_status['display'] = self.realtime_display.get_display_stats()

            # Phase 2
            component_status['account'] = self.account_service.get_service_stats()
            component_status['position_sizing'] = self.position_service.get_service_stats()
            component_status['api_orders'] = self.api_order_service.get_service_stats()

            # Phase 3
            component_status['signal_engine'] = self.signal_engine.get_engine_stats()
            component_status['risk_manager'] = self.risk_manager.get_manager_stats()
            component_status['order_manager'] = self.order_manager.get_manager_stats()

            # 전체 시스템 상태
            system_status = {
                'is_running': self.is_running,
                'is_trading_active': self.is_trading_active,
                'uptime_seconds': self.system_uptime,
                'total_signals_processed': self.total_signals_processed,
                'total_orders_executed': self.total_orders_executed,
                'current_time': datetime.now().isoformat(),
                'components': component_status
            }

            return system_status

        except Exception as e:
            self.logger.error(f"시스템 상태 조회 실패: {e}")
            return {'error': str(e)}

    async def get_trading_summary(self) -> Dict[str, Any]:
        """거래 요약 정보"""
        try:
            # 현재 신호들
            current_signals = await self.signal_engine.get_current_signals()

            # 활성 주문들
            active_orders = await self.order_manager.get_active_smart_orders()

            # 리스크 상태
            risk_metrics = await self.risk_manager.get_risk_metrics()
            risk_alerts = await self.risk_manager.get_active_alerts()

            # 포트폴리오 상태
            portfolio = await self.account_service.get_current_portfolio()

            # 체결 분석
            execution_analysis = await self.order_manager.get_execution_analysis()

            summary = {
                'timestamp': datetime.now().isoformat(),
                'signals': {
                    'current_count': len(current_signals),
                    'top_signals': [
                        {
                            'symbol': s.symbol,
                            'type': s.signal_type.value,
                            'confidence': s.confidence,
                            'strategy': s.strategy_name
                        } for s in current_signals[:5]
                    ]
                },
                'orders': {
                    'active_count': len(active_orders),
                    'recent_orders': active_orders[:3]
                },
                'risk': {
                    'level': 'NORMAL' if not risk_alerts else 'WARNING',
                    'active_alerts': len(risk_alerts),
                    'portfolio_var': risk_metrics.get('portfolio_var', 0),
                    'is_trading_halted': risk_metrics.get('is_trading_halted', False)
                },
                'portfolio': {
                    'total_value': portfolio.total_value if portfolio else 0,
                    'day_pnl': portfolio.day_pnl if portfolio else 0,
                    'day_pnl_pct': portfolio.day_pnl_pct if portfolio else 0,
                    'positions_count': portfolio.get_position_count() if portfolio else 0
                },
                'execution': {
                    'avg_slippage': execution_analysis.get('avg_slippage', 0),
                    'avg_execution_time': execution_analysis.get('avg_execution_time', 0),
                    'avg_fill_ratio': execution_analysis.get('avg_fill_ratio', 0)
                }
            }

            return summary

        except Exception as e:
            self.logger.error(f"거래 요약 조회 실패: {e}")
            return {'error': str(e)}

    def register_event_callback(self, event_type: str, callback: Callable) -> bool:
        """이벤트 콜백 등록"""
        try:
            if event_type in self.event_callbacks:
                if callback not in self.event_callbacks[event_type]:
                    self.event_callbacks[event_type].append(callback)
                    return True
            return False

        except Exception as e:
            self.logger.error(f"콜백 등록 실패: {e}")
            return False

    async def _start_phase1_components(self) -> None:
        """Phase 1 컴포넌트 시작"""
        try:
            # LivePriceService 시작
            await self.live_price_service.start_service()

            # WebSocketManager 연결
            await self.websocket_manager.connect()

            # RealTimeDisplay는 신호 추출 완료 후에 시작
            self.logger.info("RealTimeDisplay는 신호 처리 완료 후 시작됩니다")

            self.logger.info("Phase 1 컴포넌트 시작 완료")

        except Exception as e:
            self.logger.error(f"Phase 1 시작 실패: {e}")
            raise

    async def _start_phase2_components(self) -> None:
        """Phase 2 컴포넌트 시작"""
        try:
            # AccountAnalysisService 시작
            await self.account_service.start_service()

            # PositionSizingService 시작
            await self.position_service.start_service()

            # APIOrderService 시작
            await self.api_order_service.start_service()

            self.logger.info("Phase 2 컴포넌트 시작 완료")

        except Exception as e:
            self.logger.error(f"Phase 2 시작 실패: {e}")
            raise

    async def _start_phase3_components(self) -> None:
        """Phase 3 컴포넌트 시작"""
        try:
            # SignalEngine 시작
            await self.signal_engine.start_engine()

            # RiskManager 시작
            await self.risk_manager.start_monitoring()

            # OrderManager 시작
            await self.order_manager.start_manager()

            self.logger.info("Phase 3 컴포넌트 시작 완료")

        except Exception as e:
            self.logger.error(f"Phase 3 시작 실패: {e}")
            raise

    async def _setup_component_connections(self) -> None:
        """컴포넌트 간 연결 설정"""
        try:
            # 1. WebSocket → LivePriceService 연결
            self.websocket_manager.set_price_callback(self._handle_websocket_price_data)

            # 2. LivePriceService → 다른 서비스들로 가격 데이터 전파 (실제 보유/후보 종목)
            await self._setup_real_price_monitoring()

            # 3. SignalEngine → OrderManager 신호 전달
            self.signal_engine.register_signal_callback(self._handle_integrated_signal)

            # 4. RiskManager → 알림 처리
            self.risk_manager.register_risk_callback(self._handle_risk_alert)
            self.risk_manager.register_emergency_callback(self._handle_emergency_alert)

            # 5. OrderManager → 완료 알림 처리
            self.order_manager.register_completion_callback(self._handle_order_completion)

            self.logger.info("컴포넌트 연결 설정 완료")

        except Exception as e:
            self.logger.error(f"연결 설정 실패: {e}")
            raise

    async def _orchestration_loop(self):
        """메인 오케스트레이션 루프"""
        self.logger.info("오케스트레이션 루프 시작")

        while self.is_running:
            try:
                # 1. 시스템 상태 업데이트
                await self._update_system_metrics()

                # 2. 포트폴리오 동기화
                await self._sync_portfolio_data()

                # 3. 현재 신호들 처리
                if self.is_trading_active:
                    await self._process_current_signals()

                # 4. 시스템 건강성 체크
                await self._health_check()

                # 10초마다 오케스트레이션
                await asyncio.sleep(10)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"오케스트레이션 루프 오류: {e}")
                await self._trigger_event('system_error', {'error': str(e)})
                await asyncio.sleep(5)

        self.logger.info("오케스트레이션 루프 종료")

    async def _handle_websocket_price_data(self, data: Dict[str, Any]) -> None:
        """WebSocket 가격 데이터 처리"""
        try:
            # 가격 데이터를 LivePriceService로 전달
            # 실제 구현에서는 data를 PriceData 객체로 변환
            pass

        except Exception as e:
            self.logger.error(f"WebSocket 데이터 처리 실패: {e}")

    async def _setup_real_price_monitoring(self):
        """실제 보유/후보 종목 및 실시간 디스플레이 종목에 대한 실시간 가격 모니터링 설정"""
        try:
            # 실제 보유 종목 조회
            holdings_symbols = await self._get_current_holdings_symbols()

            # 실제 후보 종목 조회
            candidate_symbols = await self._get_current_candidate_symbols()

            # 실시간 디스플레이 종목 추가
            display_config = self.config.get('realtime_display', {})
            display_symbols = display_config.get('symbols', []) if display_config.get('enabled', False) else []

            # 모니터링할 전체 종목 리스트 (중복 제거)
            all_symbols = list(set(holdings_symbols + candidate_symbols + display_symbols))

            self.logger.info(f"실시간 모니터링 대상 종목: {len(all_symbols)}개")
            self.logger.info(f"  보유 종목: {holdings_symbols}")
            self.logger.info(f"  후보 종목: {candidate_symbols}")
            if display_symbols:
                self.logger.info(f"  디스플레이 종목: {display_symbols}")

            # 구독된 심볼 추적 초기화
            if not hasattr(self.live_price_service, '_subscribed_symbols'):
                self.live_price_service._subscribed_symbols = set()

            # 각 종목에 대해 가격 구독 설정
            for symbol in all_symbols:
                try:
                    await self.live_price_service.subscribe_price_updates(
                        symbol, self._broadcast_price_data
                    )
                    self.live_price_service._subscribed_symbols.add(symbol)
                    self.logger.info(f"[OK] {symbol} Real-time price subscription setup complete")
                except Exception as symbol_error:
                    self.logger.warning(f"[WARNING] {symbol} Price subscription failed: {symbol_error}")

            # 디스플레이 종목 초기 설정
            await self._update_display_symbols()

        except Exception as e:
            self.logger.error(f"실시간 가격 모니터링 설정 실패: {e}")
            # 폴백으로 기본 종목 모니터링
            await self.live_price_service.subscribe_price_updates(
                "AAPL", self._broadcast_price_data
            )

    async def _get_current_holdings_symbols(self) -> List[str]:
        """현재 보유 종목 심볼 리스트 조회"""
        try:
            # Account Analysis Service에서 현재 보유 종목 조회
            holdings = await self.account_service.get_holdings()

            symbols = []
            for holding in holdings:
                if hasattr(holding, 'ticker'):
                    symbols.append(holding.ticker)
                elif isinstance(holding, dict) and 'StockCode' in holding:
                    symbols.append(holding['StockCode'])
                elif isinstance(holding, dict) and 'symbol' in holding:
                    symbols.append(holding['symbol'])

            self.logger.info(f"현재 보유 종목: {symbols}")
            return symbols

        except Exception as e:
            self.logger.warning(f"보유 종목 조회 실패: {e}")
            return []

    async def _get_current_candidate_symbols(self) -> List[str]:
        """현재 후보 종목 심볼 리스트 조회"""
        try:
            # Position Sizing Service에서 현재 후보 종목 조회
            try:
                candidates = await self.position_service.get_candidates()
                symbols = [candidate.ticker for candidate in candidates if hasattr(candidate, 'ticker')]
                self.logger.info(f"현재 후보 종목: {symbols}")
                return symbols
            except AttributeError:
                # get_candidates 메서드가 없는 경우 최근 신호에서 추출
                return await self._get_recent_signal_symbols()

        except Exception as e:
            self.logger.warning(f"후보 종목 조회 실패: {e}")
            return []

    async def _get_recent_signal_symbols(self) -> List[str]:
        """최근 신호에서 종목 심볼 추출"""
        try:
            # Signal Engine에서 최근 신호 조회
            recent_signals = getattr(self.signal_engine, 'recent_signals', [])
            symbols = []

            for signal in recent_signals[-10:]:  # 최근 10개 신호
                if hasattr(signal, 'symbol'):
                    symbols.append(signal.symbol)
                elif isinstance(signal, dict) and 'symbol' in signal:
                    symbols.append(signal['symbol'])

            # 중복 제거
            symbols = list(set(symbols))
            self.logger.info(f"최근 신호 종목: {symbols}")
            return symbols

        except Exception as e:
            self.logger.warning(f"최근 신호 종목 조회 실패: {e}")
            return []

    async def _broadcast_price_data(self, price_data: PriceData) -> None:
        """가격 데이터를 모든 서비스로 전파"""
        try:
            symbol = price_data.symbol

            # Phase 2 서비스들에 전파
            self.account_service.set_price_data(symbol, price_data)
            self.position_service.set_price_data(symbol, price_data)
            self.api_order_service.set_price_data(symbol, price_data)

            # Phase 3 엔진들에 전파
            self.signal_engine.set_price_data(symbol, price_data)
            self.risk_manager.set_price_data(symbol, price_data)
            self.order_manager.set_price_data(symbol, price_data)

            # UI에 전파
            self.realtime_display.update_price(price_data)

        except Exception as e:
            self.logger.error(f"가격 데이터 전파 실패: {e}")

    async def _handle_integrated_signal(self, signal: TradingSignal) -> None:
        """통합된 신호 처리"""
        try:
            if not self.is_trading_active:
                return

            symbol = signal.symbol

            # 1. 리스크 검증
            risk_assessment = await self.risk_manager.check_signal_risk(signal)

            if not risk_assessment['approved']:
                self.logger.warning(f"[Orchestrator] 신호 리스크로 거부: {symbol} - "
                                  f"{risk_assessment['warnings']}")
                return

            # 2. 포지션 사이징
            candidate = await self.position_service.process_trading_signal(signal)

            if not candidate:
                self.logger.warning(f"[Orchestrator] 후보 생성 실패: {symbol}")
                return

            # 3. 스마트 주문 생성 및 실행
            order_strategy = self._select_order_strategy(signal, candidate)

            order_id = await self.order_manager.create_smart_order(
                signal, candidate, order_strategy
            )

            if order_id:
                execution_success = await self.order_manager.execute_smart_order(order_id)

                if execution_success:
                    self.logger.info(f"[Orchestrator] 자동 주문 실행: {symbol} ({order_strategy.value})")
                    # 신호 처리 후 디스플레이 업데이트
                    await self._update_display_symbols()
                    await self._trigger_event('order_executed', {
                        'signal': signal,
                        'candidate': candidate,
                        'order_id': order_id,
                        'strategy': order_strategy.value
                    })
                else:
                    self.logger.error(f"[Orchestrator] 주문 실행 실패: {symbol}")

        except Exception as e:
            self.logger.error(f"통합 신호 처리 실패: {e}")

    async def _update_display_symbols(self) -> None:
        """실제 보유종목과 신호 종목을 기반으로 디스플레이 종목 동적 업데이트"""
        try:
            display_config = self.config.get('realtime_display', {})
            if not display_config.get('enabled', False):
                return

            # 1. 실제 보유종목 가져오기
            holdings_symbols = await self._get_current_holdings_symbols()

            # 2. 최근 신호 종목 가져오기 (최근 10개)
            signal_symbols = []
            if hasattr(self.realtime_display, 'recent_signals') and self.realtime_display.recent_signals:
                signal_symbols = [signal['signal'].symbol for signal in list(self.realtime_display.recent_signals)[-10:]]

            # 3. 디스플레이할 종목 조합 (중복 제거)
            display_symbols = list(set(holdings_symbols + signal_symbols))[:10]  # 최대 10개

            # 4. 빈 배열이면 기본 종목 사용
            if not display_symbols:
                display_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA'][:5]

            # 5. RealTimeDisplay 종목 업데이트
            self.realtime_display.update_symbols(display_symbols)

            # 6. 새로운 신호 종목들에 대한 가격 모니터링 시작
            await self._ensure_price_monitoring(display_symbols)

            self.logger.info(f"Display symbols updated: Holdings {len(holdings_symbols)}, Signals {len(signal_symbols)}, Total {len(display_symbols)}")

        except Exception as e:
            self.logger.error(f"Display symbols update failed: {e}")

    async def _ensure_price_monitoring(self, symbols: List[str]) -> None:
        """지정된 종목들의 가격 모니터링 보장"""
        try:
            for symbol in symbols:
                # 이미 구독 중인지 확인하고, 없으면 추가
                if not hasattr(self.live_price_service, '_subscribed_symbols'):
                    self.live_price_service._subscribed_symbols = set()

                if symbol not in self.live_price_service._subscribed_symbols:
                    await self.live_price_service.subscribe_price_updates(
                        symbol, self._broadcast_price_data
                    )
                    self.live_price_service._subscribed_symbols.add(symbol)
                    self.logger.info(f"[OK] {symbol} New price monitoring started")

        except Exception as e:
            self.logger.error(f"가격 모니터링 보장 실패: {e}")

    async def start_realtime_display(self) -> None:
        """신호 처리 완료 후 실시간 디스플레이 시작"""
        try:
            display_config = self.config.get('realtime_display', {})
            if display_config.get('enabled', False):
                # 실제 보유종목과 신호 종목을 기반으로 디스플레이 시작
                await self._update_display_symbols()

                # 디스플레이 시작
                mode = display_config.get('mode', 'compact')
                symbols = getattr(self.realtime_display, 'selected_symbols', [])
                self.realtime_display.start_display(symbols, mode)

                self.logger.info(f"[OK] RealTimeDisplay started: {mode} mode, {len(symbols)} symbols")
            else:
                self.logger.info("RealTimeDisplay 비활성화됨 (myStockInfo.yaml 설정)")

        except Exception as e:
            self.logger.error(f"실시간 디스플레이 시작 실패: {e}")

    async def _handle_risk_alert(self, alert) -> None:
        """리스크 알림 처리"""
        try:
            self.logger.warning(f"[Orchestrator] 리스크 알림: {alert.message}")

            # 심각한 리스크는 거래 중단
            if alert.level == RiskLevel.CRITICAL:
                if alert.recommended_action == RiskAction.HALT_TRADING:
                    await self.disable_trading()
                    self.logger.critical("[Orchestrator] 리스크로 인한 자동 거래 중단")

            # UI에 알림 전달
            self.realtime_display.add_signal(TradingSignal(
                symbol="RISK",
                signal_type=alert.level.value,
                confidence=1.0,
                price=0.0,
                timestamp=datetime.now(),
                strategy_name="RiskManager",
                metadata={'alert_message': alert.message}
            ))

            await self._trigger_event('risk_alert', {'alert': alert})

        except Exception as e:
            self.logger.error(f"리스크 알림 처리 실패: {e}")

    async def _handle_emergency_alert(self, alert) -> None:
        """긴급 상황 처리"""
        try:
            self.logger.critical(f"[Orchestrator] 긴급 상황: {alert.message}")

            # 자동으로 거래 중단
            await self.disable_trading()

            await self._trigger_event('emergency_alert', {'alert': alert})

        except Exception as e:
            self.logger.error(f"긴급 상황 처리 실패: {e}")

    async def _handle_order_completion(self, smart_order) -> None:
        """주문 완료 처리"""
        try:
            self.total_orders_executed += 1

            self.logger.info(f"[Orchestrator] 주문 완료: {smart_order.candidate.symbol} "
                           f"{smart_order.executed_quantity}주")

            # 포지션 사이징에서 후보 제거
            await self.position_service.remove_candidate(smart_order.candidate.symbol)

            # UI 업데이트
            order_result = {
                'symbol': smart_order.candidate.symbol,
                'quantity': smart_order.executed_quantity,
                'price': smart_order.avg_execution_price,
                'strategy': smart_order.strategy.value,
                'status': 'COMPLETED'
            }

            self.realtime_display.add_order_result(order_result)

        except Exception as e:
            self.logger.error(f"주문 완료 처리 실패: {e}")

    def _select_order_strategy(self, signal: TradingSignal, candidate: CandidateStock) -> OrderStrategy:
        """최적 주문 전략 선택"""
        try:
            # 신호 강도 기반 선택
            if signal.signal_type.value == "STRONG_BUY":
                return OrderStrategy.MARKET  # 즉시 체결

            # 신뢰도 기반 선택
            if signal.confidence >= 0.9:
                return OrderStrategy.LIMIT   # 지정가로 좋은 가격 추구

            # 기본 전략
            return OrderStrategy.TWAP       # 안전한 분할 실행

        except Exception:
            return OrderStrategy.LIMIT

    async def _update_system_metrics(self) -> None:
        """시스템 지표 업데이트"""
        try:
            self.system_metrics = {
                'uptime': self.system_uptime,
                'signals_processed': self.total_signals_processed,
                'orders_executed': self.total_orders_executed,
                'components_health': await self._check_components_health(),
                'last_update': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"시스템 지표 업데이트 실패: {e}")

    async def _sync_portfolio_data(self) -> None:
        """포트폴리오 데이터 동기화"""
        try:
            # AccountAnalysisService에서 최신 포트폴리오 조회
            portfolio = await self.account_service.get_current_portfolio()

            if portfolio:
                self.current_portfolio = portfolio

                # 다른 서비스들에 포트폴리오 정보 전파
                await self.position_service.update_portfolio_info(portfolio)
                await self.risk_manager.update_portfolio(portfolio)

                # UI 업데이트
                self.realtime_display.update_portfolio(portfolio)

                # 후보종목 정보도 함께 업데이트 (신호 엔진에서 최근 신호 기반으로)
                try:
                    # 최근 신호들에서 후보종목 정보 추출
                    if hasattr(self.realtime_display, 'recent_signals') and self.realtime_display.recent_signals:
                        candidate_data = {}
                        for signal_info in list(self.realtime_display.recent_signals)[-5:]:  # 최근 5개
                            signal = signal_info.get('signal')
                            if signal and hasattr(signal, 'symbol'):
                                candidate_data[signal.symbol] = {
                                    'target_price': signal.price * 1.1 if hasattr(signal, 'price') else None,  # 10% 상승 목표
                                    'signal_type': signal.signal_type.value if hasattr(signal, 'signal_type') else 'BUY',
                                    'confidence': signal.confidence if hasattr(signal, 'confidence') else 0.7
                                }
                        if candidate_data:
                            self.realtime_display.update_candidate_data(candidate_data)
                except Exception as candidate_error:
                    self.logger.debug(f"후보종목 업데이트 오류: {candidate_error}")

        except Exception as e:
            self.logger.error(f"포트폴리오 동기화 실패: {e}")

    async def _process_current_signals(self) -> None:
        """현재 신호들 처리"""
        try:
            # SignalEngine에서 현재 유효한 신호들 조회
            current_signals = await self.signal_engine.get_current_signals()

            # 새로운 신호들만 처리 (이미 처리된 신호는 제외)
            for signal in current_signals:
                if signal.symbol not in self.active_signals:
                    self.active_signals[signal.symbol] = signal
                    # 신호는 이미 SignalEngine에서 콜백으로 처리됨

            # 만료된 활성 신호들 정리
            current_symbols = {s.symbol for s in current_signals}
            expired_symbols = set(self.active_signals.keys()) - current_symbols

            for symbol in expired_symbols:
                del self.active_signals[symbol]

        except Exception as e:
            self.logger.error(f"현재 신호 처리 실패: {e}")

    async def _health_check(self) -> None:
        """시스템 건강성 체크"""
        try:
            # 각 컴포넌트의 건강 상태 확인
            health_issues = []

            # WebSocket 연결 상태
            ws_status = self.websocket_manager.get_connection_status()
            if not ws_status.get('is_connected', False):
                health_issues.append("WebSocket 연결 끊김")

            # API 서비스 상태
            api_stats = self.api_order_service.get_service_stats()
            if not api_stats.get('is_connected', False):
                health_issues.append("KIS API 연결 끊김")

            # 리스크 상태
            risk_metrics = await self.risk_manager.get_risk_metrics()
            if risk_metrics.get('is_trading_halted', False):
                health_issues.append("리스크로 인한 거래 중단")

            # 문제가 있으면 로그 기록
            if health_issues:
                self.logger.warning(f"시스템 건강성 이슈: {health_issues}")

        except Exception as e:
            self.logger.error(f"건강성 체크 실패: {e}")

    async def _check_components_health(self) -> Dict[str, str]:
        """컴포넌트별 건강 상태"""
        try:
            health_status = {}

            # 각 컴포넌트 상태 체크
            health_status['websocket'] = 'OK' if self.websocket_manager.get_connection_status().get('is_connected') else 'ERROR'
            health_status['live_price'] = 'OK' if self.live_price_service.get_service_stats().get('is_running') else 'ERROR'
            health_status['account'] = 'OK' if self.account_service.get_service_stats().get('is_running') else 'ERROR'
            health_status['position_sizing'] = 'OK' if self.position_service.get_service_stats().get('is_running') else 'ERROR'
            health_status['api_orders'] = 'OK' if self.api_order_service.get_service_stats().get('is_connected') else 'ERROR'
            health_status['signal_engine'] = 'OK' if self.signal_engine.get_engine_stats().get('is_running') else 'ERROR'
            health_status['risk_manager'] = 'OK' if self.risk_manager.get_manager_stats().get('is_monitoring') else 'ERROR'
            health_status['order_manager'] = 'OK' if self.order_manager.get_manager_stats().get('is_running') else 'ERROR'

            return health_status

        except Exception as e:
            self.logger.error(f"컴포넌트 상태 확인 실패: {e}")
            return {}

    async def _start_monitoring_tasks(self) -> None:
        """모니터링 태스크들 시작"""
        try:
            # 시스템 상태 모니터링
            system_monitor = asyncio.create_task(self._system_monitor_loop())
            self.monitoring_tasks.append(system_monitor)

            # 성능 모니터링
            performance_monitor = asyncio.create_task(self._performance_monitor_loop())
            self.monitoring_tasks.append(performance_monitor)

        except Exception as e:
            self.logger.error(f"모니터링 태스크 시작 실패: {e}")

    async def _stop_monitoring_tasks(self) -> None:
        """모니터링 태스크들 중지"""
        try:
            for task in self.monitoring_tasks:
                if not task.done():
                    task.cancel()

            self.monitoring_tasks.clear()

        except Exception as e:
            self.logger.error(f"모니터링 태스크 중지 실패: {e}")

    async def _system_monitor_loop(self):
        """시스템 모니터링 루프"""
        while self.is_running:
            try:
                # 시스템 지표 수집 및 기록
                status = await self.get_system_status()

                # 주요 지표만 로깅 (상세 로그는 비활성화)
                if self.total_signals_processed % 10 == 0:  # 10개 신호마다
                    self.logger.debug(f"시스템 요약 - 신호: {self.total_signals_processed}, "
                                    f"주문: {self.total_orders_executed}, "
                                    f"업타임: {self.system_uptime:.0f}초")

                await asyncio.sleep(60)  # 1분마다

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"시스템 모니터링 오류: {e}")
                await asyncio.sleep(30)

    async def _performance_monitor_loop(self):
        """성능 모니터링 루프"""
        while self.is_running:
            try:
                # 메모리 사용량, CPU 사용률 등 모니터링
                # 실제 구현에서는 psutil 등을 사용

                await asyncio.sleep(300)  # 5분마다

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"성능 모니터링 오류: {e}")
                await asyncio.sleep(60)

    async def _stop_phase1_components(self) -> None:
        """Phase 1 컴포넌트 중지"""
        try:
            self.realtime_display.stop_display()
            await self.websocket_manager.disconnect()
            await self.live_price_service.stop_service()

        except Exception as e:
            self.logger.error(f"Phase 1 중지 실패: {e}")

    async def _stop_phase2_components(self) -> None:
        """Phase 2 컴포넌트 중지"""
        try:
            await self.api_order_service.stop_service()
            await self.position_service.stop_service()
            await self.account_service.stop_service()

        except Exception as e:
            self.logger.error(f"Phase 2 중지 실패: {e}")

    async def _stop_phase3_components(self) -> None:
        """Phase 3 컴포넌트 중지"""
        try:
            await self.order_manager.stop_manager()
            await self.risk_manager.stop_monitoring()
            await self.signal_engine.stop_engine()

        except Exception as e:
            self.logger.error(f"Phase 3 중지 실패: {e}")

    async def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """이벤트 콜백 트리거"""
        try:
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        self.logger.error(f"이벤트 콜백 실행 실패 ({event_type}): {e}")

        except Exception as e:
            self.logger.error(f"이벤트 트리거 실패 ({event_type}): {e}")


# 테스트 함수
async def test_auto_trade_orchestrator():
    """AutoTradeOrchestrator 테스트"""
    print("\n=== Auto Trade Orchestrator 테스트 시작 ===")

    config = {
        'kis_websocket': {
            'url': 'ws://test',
            'app_key': 'test',
            'app_secret': 'test'
        },
        'kis_api': {
            'account_no': '12345678-01',
            'is_virtual': True
        },
        'risk_management': {
            'max_daily_loss': 0.05,
            'max_position_size': 0.1
        },
        'position_sizing': {
            'min_order_amount': 1000,
            'cash_reserve': 0.05
        },
        'signal_engine': {
            'min_confidence': 0.6,
            'consensus_threshold': 0.7
        },
        'order_management': {
            'max_slippage': 0.005,
            'default_time_limit': 30
        }
    }

    orchestrator = AutoTradeOrchestrator(config)

    try:
        # 이벤트 콜백 등록
        events_received = []

        async def event_callback(data):
            events_received.append(data)
            print(f"[이벤트] {data}")

        orchestrator.register_event_callback('signal_received', event_callback)
        orchestrator.register_event_callback('order_executed', event_callback)

        # 시스템 시작
        print("전체 시스템 시작...")
        success = await orchestrator.start_system()
        print(f"시스템 시작: {'성공' if success else '실패'}")

        if success:
            # 거래 활성화
            trading_enabled = await orchestrator.enable_trading()
            print(f"거래 활성화: {'성공' if trading_enabled else '실패'}")

            # 테스트 신호 추가
            from ..models.trading_models import TradingSignal, SignalType

            test_signals = [
                TradingSignal(
                    symbol='AAPL',
                    signal_type=SignalType.BUY,
                    confidence=0.85,
                    price=174.0,
                    timestamp=datetime.now(),
                    strategy_name='TestStrategy1'
                ),
                TradingSignal(
                    symbol='MSFT',
                    signal_type=SignalType.STRONG_BUY,
                    confidence=0.92,
                    price=338.0,
                    timestamp=datetime.now(),
                    strategy_name='TestStrategy2'
                )
            ]

            for signal in test_signals:
                signal_added = await orchestrator.add_trading_signal(signal)
                print(f"신호 추가 ({signal.symbol}): {'성공' if signal_added else '실패'}")

            # 시스템 실행 대기
            print("\n시스템 실행 및 모니터링 (10초)...")
            await asyncio.sleep(10)

            # 시스템 상태 확인
            status = await orchestrator.get_system_status()
            print(f"\n시스템 상태:")
            print(f"  실행 중: {status.get('is_running')}")
            print(f"  거래 활성: {status.get('is_trading_active')}")
            print(f"  업타임: {status.get('uptime_seconds', 0):.0f}초")
            print(f"  처리된 신호: {status.get('total_signals_processed')}")
            print(f"  실행된 주문: {status.get('total_orders_executed')}")

            # 거래 요약
            summary = await orchestrator.get_trading_summary()
            print(f"\n거래 요약:")
            print(f"  현재 신호: {summary.get('signals', {}).get('current_count', 0)}개")
            print(f"  활성 주문: {summary.get('orders', {}).get('active_count', 0)}개")
            print(f"  리스크 레벨: {summary.get('risk', {}).get('level', 'UNKNOWN')}")

            # 거래 비활성화
            await orchestrator.disable_trading()
            print("\n거래 비활성화 완료")

        # 시스템 중지
        stop_success = await orchestrator.stop_system()
        print(f"시스템 중지: {'성공' if stop_success else '실패'}")

        print(f"\n수신된 이벤트: {len(events_received)}개")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        await orchestrator.stop_system()

if __name__ == "__main__":
    asyncio.run(test_auto_trade_orchestrator())