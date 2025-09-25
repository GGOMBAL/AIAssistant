"""
Risk Manager

실시간 리스크 모니터링 및 관리 시스템
포트폴리오 리스크를 지속적으로 감시하고 위험 상황에서 자동 대응
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import statistics
import math

from ..models.trading_models import (
    Portfolio, PortfolioPosition, TradingSignal, PriceData,
    OrderRequest, SignalType, MarketType
)


class RiskLevel(Enum):
    """리스크 레벨"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAction(Enum):
    """리스크 대응 액션"""
    NONE = "NONE"
    REDUCE_POSITION = "REDUCE_POSITION"
    STOP_NEW_ORDERS = "STOP_NEW_ORDERS"
    EMERGENCY_SELL = "EMERGENCY_SELL"
    HALT_TRADING = "HALT_TRADING"


@dataclass
class RiskAlert:
    """리스크 경고"""
    risk_type: str
    level: RiskLevel
    message: str
    affected_symbols: List[str]
    recommended_action: RiskAction
    metrics: Dict[str, float]
    timestamp: datetime


class RiskManager:
    """실시간 리스크 관리자"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 리스크 설정
        self.risk_config = config.get('risk_management', {})

        # 포트폴리오 리스크 한도
        self.max_portfolio_risk = self.risk_config.get('max_portfolio_risk', 0.03)  # 3%
        self.max_daily_loss = self.risk_config.get('max_daily_loss', 0.05)         # 5%
        self.max_drawdown = self.risk_config.get('max_drawdown', 0.15)             # 15%
        self.max_concentration = self.risk_config.get('max_concentration', 0.20)    # 20%

        # 포지션 리스크 한도
        self.max_position_size = self.risk_config.get('max_position_size', 0.10)   # 10%
        self.max_sector_exposure = self.risk_config.get('max_sector_exposure', 0.30) # 30%
        self.max_market_exposure = self.risk_config.get('max_market_exposure', 0.70) # 70%

        # 동적 리스크 조정
        self.volatility_adjustment = self.risk_config.get('volatility_adjustment', True)
        self.correlation_adjustment = self.risk_config.get('correlation_adjustment', True)

        # 현재 상태
        self.current_portfolio: Optional[Portfolio] = None
        self.current_positions: Dict[str, PortfolioPosition] = {}
        self.price_data_cache: Dict[str, PriceData] = {}

        # 리스크 메트릭
        self.risk_metrics: Dict[str, float] = {}
        self.portfolio_var: float = 0.0  # Value at Risk
        self.portfolio_beta: float = 1.0
        self.sharpe_ratio: float = 0.0

        # 알림 및 액션
        self.active_alerts: List[RiskAlert] = []
        self.risk_callbacks: List[Callable] = []
        self.emergency_callbacks: List[Callable] = []

        # 히스토리
        self.price_history: Dict[str, List[float]] = {}  # 가격 히스토리 (변동성 계산용)
        self.pnl_history: List[float] = []  # 일별 손익 히스토리

        # 모니터링 상태
        self.is_monitoring = False
        self.monitoring_task = None
        self.is_trading_halted = False

        # 통계
        self.total_alerts = 0
        self.risk_violations = 0
        self.emergency_actions = 0

    async def start_monitoring(self) -> bool:
        """리스크 모니터링 시작"""
        try:
            self.logger.info("[RiskManager] 리스크 모니터링 시작")

            # 설정 검증
            await self._validate_configuration()

            # 모니터링 태스크 시작
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            self.is_monitoring = True
            self.logger.info("[RiskManager] 리스크 모니터링 시작 완료")
            return True

        except Exception as e:
            self.logger.error(f"리스크 모니터링 시작 실패: {e}")
            return False

    async def stop_monitoring(self) -> bool:
        """리스크 모니터링 중지"""
        try:
            self.logger.info("[RiskManager] 리스크 모니터링 중지")

            self.is_monitoring = False

            # 모니터링 태스크 중지
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()

            return True

        except Exception as e:
            self.logger.error(f"리스크 모니터링 중지 실패: {e}")
            return False

    async def update_portfolio(self, portfolio: Portfolio) -> None:
        """포트폴리오 정보 업데이트"""
        try:
            self.current_portfolio = portfolio
            self.current_positions = portfolio.positions.copy()

            # 일별 손익 히스토리 업데이트
            if portfolio.day_pnl_pct != 0:
                self.pnl_history.append(portfolio.day_pnl_pct)
                # 최대 252일 (1년) 히스토리 유지
                if len(self.pnl_history) > 252:
                    self.pnl_history = self.pnl_history[-252:]

            # 리스크 메트릭 계산
            await self._calculate_risk_metrics()

            # 리스크 점검 (비동기)
            asyncio.create_task(self._check_portfolio_risks())

        except Exception as e:
            self.logger.error(f"포트폴리오 업데이트 실패: {e}")

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """실시간 가격 데이터 업데이트"""
        try:
            self.price_data_cache[symbol] = price_data

            # 가격 히스토리 업데이트
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            self.price_history[symbol].append(price_data.price)

            # 최대 100개 가격 히스토리 유지
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]

            # 실시간 포지션 가치 업데이트
            if symbol in self.current_positions:
                asyncio.create_task(self._update_position_risk(symbol, price_data))

        except Exception as e:
            self.logger.error(f"가격 데이터 업데이트 실패 ({symbol}): {e}")

    async def check_signal_risk(self, signal: TradingSignal) -> Dict[str, Any]:
        """신호 리스크 검증"""
        try:
            risk_assessment = {
                'approved': True,
                'risk_level': RiskLevel.LOW,
                'warnings': [],
                'recommendations': []
            }

            if not self.current_portfolio:
                risk_assessment['warnings'].append("포트폴리오 정보 없음")
                return risk_assessment

            # 1. 포지션 크기 리스크
            position_risk = await self._assess_position_size_risk(signal)
            if position_risk['risk_level'] != RiskLevel.LOW:
                risk_assessment['warnings'].extend(position_risk['warnings'])
                risk_assessment['risk_level'] = max(risk_assessment['risk_level'], position_risk['risk_level'])

            # 2. 집중도 리스크
            concentration_risk = await self._assess_concentration_risk(signal)
            if concentration_risk['risk_level'] != RiskLevel.LOW:
                risk_assessment['warnings'].extend(concentration_risk['warnings'])
                risk_assessment['risk_level'] = max(risk_assessment['risk_level'], concentration_risk['risk_level'])

            # 3. 시장 리스크
            market_risk = await self._assess_market_risk(signal)
            if market_risk['risk_level'] != RiskLevel.LOW:
                risk_assessment['warnings'].extend(market_risk['warnings'])
                risk_assessment['risk_level'] = max(risk_assessment['risk_level'], market_risk['risk_level'])

            # 4. 변동성 리스크
            volatility_risk = await self._assess_volatility_risk(signal)
            if volatility_risk['risk_level'] != RiskLevel.LOW:
                risk_assessment['warnings'].extend(volatility_risk['warnings'])

            # 최종 승인 결정
            if risk_assessment['risk_level'] in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risk_assessment['approved'] = False
            elif self.is_trading_halted:
                risk_assessment['approved'] = False
                risk_assessment['warnings'].append("거래 중단 상태")

            return risk_assessment

        except Exception as e:
            self.logger.error(f"신호 리스크 검증 실패 ({signal.symbol}): {e}")
            return {
                'approved': False,
                'risk_level': RiskLevel.CRITICAL,
                'warnings': [f"리스크 검증 오류: {e}"],
                'recommendations': []
            }

    async def get_risk_metrics(self) -> Dict[str, Any]:
        """현재 리스크 지표"""
        return {
            'portfolio_var': self.portfolio_var,
            'portfolio_beta': self.portfolio_beta,
            'sharpe_ratio': self.sharpe_ratio,
            'risk_metrics': self.risk_metrics.copy(),
            'active_alerts': len(self.active_alerts),
            'is_trading_halted': self.is_trading_halted
        }

    async def get_active_alerts(self) -> List[RiskAlert]:
        """현재 활성 경고"""
        return self.active_alerts.copy()

    def register_risk_callback(self, callback: Callable) -> None:
        """리스크 경고 콜백 등록"""
        if callback not in self.risk_callbacks:
            self.risk_callbacks.append(callback)

    def register_emergency_callback(self, callback: Callable) -> None:
        """긴급 상황 콜백 등록"""
        if callback not in self.emergency_callbacks:
            self.emergency_callbacks.append(callback)

    async def force_risk_check(self) -> Dict[str, Any]:
        """수동 리스크 점검"""
        await self._calculate_risk_metrics()
        await self._check_portfolio_risks()
        return await self.get_risk_metrics()

    async def _monitoring_loop(self):
        """리스크 모니터링 루프"""
        while self.is_monitoring:
            try:
                # 포트폴리오 리스크 점검
                if self.current_portfolio:
                    await self._check_portfolio_risks()

                # 알림 정리 (오래된 알림 제거)
                await self._cleanup_old_alerts()

                # 30초마다 모니터링
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"리스크 모니터링 루프 오류: {e}")
                await asyncio.sleep(10)

    async def _calculate_risk_metrics(self) -> None:
        """리스크 지표 계산"""
        try:
            if not self.current_portfolio or not self.current_positions:
                return

            # 1. 포트폴리오 변동성 (Portfolio Volatility)
            if len(self.pnl_history) >= 10:
                self.risk_metrics['portfolio_volatility'] = statistics.stdev(self.pnl_history) * math.sqrt(252)
            else:
                self.risk_metrics['portfolio_volatility'] = 0.15  # 기본값

            # 2. 최대 낙폭 (Maximum Drawdown)
            if self.pnl_history:
                cumulative_returns = []
                cumulative = 0
                for ret in self.pnl_history:
                    cumulative = (1 + cumulative) * (1 + ret/100) - 1
                    cumulative_returns.append(cumulative)

                peak = cumulative_returns[0]
                max_drawdown = 0
                for ret in cumulative_returns:
                    peak = max(peak, ret)
                    drawdown = (peak - ret) / (1 + peak) if peak != -1 else 0
                    max_drawdown = max(max_drawdown, drawdown)

                self.risk_metrics['max_drawdown'] = max_drawdown
            else:
                self.risk_metrics['max_drawdown'] = 0

            # 3. 집중도 리스크 (Concentration Risk)
            if self.current_portfolio.stock_value > 0:
                position_weights = [
                    pos.market_value / self.current_portfolio.stock_value
                    for pos in self.current_positions.values()
                ]

                if position_weights:
                    self.risk_metrics['max_position_weight'] = max(position_weights)
                    self.risk_metrics['top3_concentration'] = sum(sorted(position_weights, reverse=True)[:3])

                    # Herfindahl Index (집중도 지수)
                    hhi = sum(w**2 for w in position_weights)
                    self.risk_metrics['herfindahl_index'] = hhi

            # 4. 시장 노출도 (Market Exposure)
            market_allocation = self.current_portfolio.get_market_allocation()
            if market_allocation:
                self.risk_metrics['max_market_exposure'] = max(market_allocation.values())
                self.risk_metrics['market_diversification'] = len(market_allocation)

            # 5. VaR (Value at Risk) - 95% 신뢰수준
            if len(self.pnl_history) >= 20:
                sorted_returns = sorted(self.pnl_history)
                var_index = int(len(sorted_returns) * 0.05)  # 5% tail
                daily_var = abs(sorted_returns[var_index]) / 100  # 백분율을 소수로 변환
                self.portfolio_var = daily_var * self.current_portfolio.total_value
            else:
                self.portfolio_var = self.current_portfolio.total_value * 0.02  # 2% 기본값

            # 6. 베타 (시장 대비 민감도) - 단순화된 계산
            self.portfolio_beta = 1.0  # 실제로는 시장 지수와의 상관관계 필요

            # 7. 샤프 비율 - 단순화된 계산
            if len(self.pnl_history) >= 30 and self.risk_metrics.get('portfolio_volatility', 0) > 0:
                avg_return = statistics.mean(self.pnl_history) * 252  # 연율화
                risk_free_rate = 0.04  # 4% 무위험 수익률 가정
                excess_return = avg_return - risk_free_rate
                self.sharpe_ratio = excess_return / self.risk_metrics['portfolio_volatility']

        except Exception as e:
            self.logger.error(f"리스크 지표 계산 실패: {e}")

    async def _check_portfolio_risks(self) -> None:
        """포트폴리오 리스크 점검"""
        try:
            if not self.current_portfolio:
                return

            alerts_to_add = []

            # 1. 일일 손실 한도 점검
            daily_loss_pct = abs(min(0, self.current_portfolio.day_pnl_pct))
            if daily_loss_pct > self.max_daily_loss * 100:
                alerts_to_add.append(RiskAlert(
                    risk_type="daily_loss_limit",
                    level=RiskLevel.HIGH,
                    message=f"일일 손실 한도 초과: {daily_loss_pct:.2f}% (한도: {self.max_daily_loss*100:.1f}%)",
                    affected_symbols=list(self.current_positions.keys()),
                    recommended_action=RiskAction.STOP_NEW_ORDERS,
                    metrics={'daily_loss_pct': daily_loss_pct},
                    timestamp=datetime.now()
                ))

            # 2. 최대 낙폭 점검
            max_drawdown = self.risk_metrics.get('max_drawdown', 0)
            if max_drawdown > self.max_drawdown:
                alerts_to_add.append(RiskAlert(
                    risk_type="max_drawdown",
                    level=RiskLevel.CRITICAL,
                    message=f"최대 낙폭 한도 초과: {max_drawdown:.2f}% (한도: {self.max_drawdown*100:.1f}%)",
                    affected_symbols=list(self.current_positions.keys()),
                    recommended_action=RiskAction.EMERGENCY_SELL,
                    metrics={'max_drawdown': max_drawdown},
                    timestamp=datetime.now()
                ))

            # 3. 집중도 리스크 점검
            max_position_weight = self.risk_metrics.get('max_position_weight', 0)
            if max_position_weight > self.max_concentration:
                # 집중도가 높은 종목 찾기
                concentrated_symbols = []
                if self.current_portfolio.stock_value > 0:
                    for symbol, pos in self.current_positions.items():
                        weight = pos.market_value / self.current_portfolio.stock_value
                        if weight > self.max_concentration:
                            concentrated_symbols.append(symbol)

                alerts_to_add.append(RiskAlert(
                    risk_type="concentration_risk",
                    level=RiskLevel.MEDIUM,
                    message=f"포지션 집중도 위험: 최대 {max_position_weight:.1%} (한도: {self.max_concentration:.1%})",
                    affected_symbols=concentrated_symbols,
                    recommended_action=RiskAction.REDUCE_POSITION,
                    metrics={'max_position_weight': max_position_weight},
                    timestamp=datetime.now()
                ))

            # 4. VaR 한도 점검
            var_ratio = self.portfolio_var / self.current_portfolio.total_value
            if var_ratio > self.max_portfolio_risk:
                alerts_to_add.append(RiskAlert(
                    risk_type="var_limit",
                    level=RiskLevel.HIGH,
                    message=f"VaR 한도 초과: {var_ratio:.2%} (한도: {self.max_portfolio_risk:.1%})",
                    affected_symbols=list(self.current_positions.keys()),
                    recommended_action=RiskAction.REDUCE_POSITION,
                    metrics={'var_ratio': var_ratio, 'portfolio_var': self.portfolio_var},
                    timestamp=datetime.now()
                ))

            # 새로운 알림 추가
            for alert in alerts_to_add:
                await self._add_risk_alert(alert)

        except Exception as e:
            self.logger.error(f"포트폴리오 리스크 점검 실패: {e}")

    async def _assess_position_size_risk(self, signal: TradingSignal) -> Dict[str, Any]:
        """포지션 크기 리스크 평가"""
        try:
            # 예상 포지션 크기 계산 (간단한 추정)
            estimated_position_value = self.current_portfolio.total_value * 0.05  # 5% 가정

            # 최대 포지션 한도 확인
            position_ratio = estimated_position_value / self.current_portfolio.total_value
            if position_ratio > self.max_position_size:
                return {
                    'risk_level': RiskLevel.HIGH,
                    'warnings': [f"포지션 크기 한도 초과 위험: {position_ratio:.1%} > {self.max_position_size:.1%}"]
                }

            return {'risk_level': RiskLevel.LOW, 'warnings': []}

        except Exception as e:
            return {'risk_level': RiskLevel.MEDIUM, 'warnings': [f"포지션 크기 평가 오류: {e}"]}

    async def _assess_concentration_risk(self, signal: TradingSignal) -> Dict[str, Any]:
        """집중도 리스크 평가"""
        try:
            warnings = []

            # 이미 보유 중인 종목인지 확인
            if signal.symbol in self.current_positions:
                current_weight = self.current_positions[signal.symbol].market_value / self.current_portfolio.stock_value
                if current_weight > self.max_concentration * 0.8:  # 한도의 80%
                    warnings.append(f"기존 포지션 집중도 높음: {signal.symbol} {current_weight:.1%}")

            # 시장 집중도 확인
            market_type = self._get_market_type(signal.symbol)
            market_allocation = self.current_portfolio.get_market_allocation()
            current_market_exposure = market_allocation.get(market_type.value, 0)

            if current_market_exposure > self.max_market_exposure * 0.9:  # 한도의 90%
                warnings.append(f"시장 집중도 위험: {market_type.value} {current_market_exposure:.1%}")
                return {'risk_level': RiskLevel.MEDIUM, 'warnings': warnings}

            return {'risk_level': RiskLevel.LOW, 'warnings': warnings}

        except Exception as e:
            return {'risk_level': RiskLevel.MEDIUM, 'warnings': [f"집중도 평가 오류: {e}"]}

    async def _assess_market_risk(self, signal: TradingSignal) -> Dict[str, Any]:
        """시장 리스크 평가"""
        try:
            warnings = []

            # 변동성 기반 리스크
            if signal.symbol in self.price_history and len(self.price_history[signal.symbol]) >= 10:
                prices = self.price_history[signal.symbol]
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                volatility = statistics.stdev(returns) if returns else 0

                # 일일 변동성 2% 이상이면 위험
                if volatility > 0.02:
                    warnings.append(f"높은 변동성: {signal.symbol} {volatility:.2%}")
                    return {'risk_level': RiskLevel.MEDIUM, 'warnings': warnings}

            return {'risk_level': RiskLevel.LOW, 'warnings': warnings}

        except Exception as e:
            return {'risk_level': RiskLevel.LOW, 'warnings': [f"시장 리스크 평가 오류: {e}"]}

    async def _assess_volatility_risk(self, signal: TradingSignal) -> Dict[str, Any]:
        """변동성 리스크 평가"""
        try:
            # 포트폴리오 전체 변동성 확인
            portfolio_volatility = self.risk_metrics.get('portfolio_volatility', 0.15)

            if portfolio_volatility > 0.30:  # 30% 이상
                return {
                    'risk_level': RiskLevel.HIGH,
                    'warnings': [f"포트폴리오 변동성 높음: {portfolio_volatility:.1%}"]
                }
            elif portfolio_volatility > 0.25:  # 25% 이상
                return {
                    'risk_level': RiskLevel.MEDIUM,
                    'warnings': [f"포트폴리오 변동성 주의: {portfolio_volatility:.1%}"]
                }

            return {'risk_level': RiskLevel.LOW, 'warnings': []}

        except Exception as e:
            return {'risk_level': RiskLevel.LOW, 'warnings': [f"변동성 평가 오류: {e}"]}

    async def _add_risk_alert(self, alert: RiskAlert) -> None:
        """리스크 알림 추가"""
        try:
            # 중복 알림 확인
            for existing_alert in self.active_alerts:
                if (existing_alert.risk_type == alert.risk_type and
                    existing_alert.level == alert.level):
                    return  # 중복 알림 무시

            self.active_alerts.append(alert)
            self.total_alerts += 1

            # 심각한 리스크는 즉시 대응
            if alert.level == RiskLevel.CRITICAL:
                await self._handle_critical_risk(alert)

            # 콜백 알림
            await self._notify_risk_callbacks(alert)

            self.logger.warning(f"[RiskManager] {alert.level.value} 리스크 알림: {alert.message}")

        except Exception as e:
            self.logger.error(f"리스크 알림 추가 실패: {e}")

    async def _handle_critical_risk(self, alert: RiskAlert) -> None:
        """긴급 리스크 대응"""
        try:
            self.emergency_actions += 1

            if alert.recommended_action == RiskAction.HALT_TRADING:
                self.is_trading_halted = True
                self.logger.critical("[RiskManager] 거래 중단 실행")

            elif alert.recommended_action == RiskAction.EMERGENCY_SELL:
                self.logger.critical("[RiskManager] 긴급 매도 권고")
                # 실제로는 긴급 매도 신호 생성

            # 긴급 상황 콜백 호출
            await self._notify_emergency_callbacks(alert)

        except Exception as e:
            self.logger.error(f"긴급 리스크 대응 실패: {e}")

    async def _notify_risk_callbacks(self, alert: RiskAlert) -> None:
        """리스크 콜백 알림"""
        try:
            for callback in self.risk_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    self.logger.error(f"리스크 콜백 실행 실패: {e}")
        except Exception as e:
            self.logger.error(f"리스크 콜백 알림 실패: {e}")

    async def _notify_emergency_callbacks(self, alert: RiskAlert) -> None:
        """긴급 상황 콜백 알림"""
        try:
            for callback in self.emergency_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    self.logger.error(f"긴급 콜백 실행 실패: {e}")
        except Exception as e:
            self.logger.error(f"긴급 콜백 알림 실패: {e}")

    async def _update_position_risk(self, symbol: str, price_data: PriceData) -> None:
        """포지션 리스크 실시간 업데이트"""
        try:
            if symbol not in self.current_positions:
                return

            position = self.current_positions[symbol]

            # 급격한 가격 변동 확인
            if position.current_price > 0:
                price_change_pct = abs((price_data.price - position.current_price) / position.current_price)

                # 10% 이상 급변동 시 알림
                if price_change_pct > 0.10:
                    alert = RiskAlert(
                        risk_type="price_shock",
                        level=RiskLevel.HIGH,
                        message=f"급격한 가격 변동: {symbol} {price_change_pct:.1%}",
                        affected_symbols=[symbol],
                        recommended_action=RiskAction.REDUCE_POSITION,
                        metrics={'price_change_pct': price_change_pct},
                        timestamp=datetime.now()
                    )
                    await self._add_risk_alert(alert)

        except Exception as e:
            self.logger.error(f"포지션 리스크 업데이트 실패 ({symbol}): {e}")

    async def _cleanup_old_alerts(self) -> None:
        """오래된 알림 정리"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1)  # 1시간 이전

            self.active_alerts = [
                alert for alert in self.active_alerts
                if alert.timestamp > cutoff_time
            ]

        except Exception as e:
            self.logger.error(f"알림 정리 실패: {e}")

    def _get_market_type(self, symbol: str) -> MarketType:
        """심볼로 시장 유형 판단"""
        nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMZN']
        if symbol in nasdaq_symbols:
            return MarketType.NASDAQ
        else:
            return MarketType.NYSE

    async def _validate_configuration(self) -> None:
        """설정 유효성 검증"""
        if not 0 < self.max_portfolio_risk <= 1:
            raise ValueError("Invalid max_portfolio_risk")

        if not 0 < self.max_daily_loss <= 1:
            raise ValueError("Invalid max_daily_loss")

        self.logger.info(f"[RiskManager] 설정 검증 완료: "
                        f"최대일일손실={self.max_daily_loss:.1%}, "
                        f"최대포트폴리오위험={self.max_portfolio_risk:.1%}")

    def get_manager_stats(self) -> Dict[str, Any]:
        """리스크 매니저 통계"""
        return {
            'is_monitoring': self.is_monitoring,
            'is_trading_halted': self.is_trading_halted,
            'total_alerts': self.total_alerts,
            'active_alerts': len(self.active_alerts),
            'risk_violations': self.risk_violations,
            'emergency_actions': self.emergency_actions,
            'portfolio_var': self.portfolio_var,
            'portfolio_beta': self.portfolio_beta,
            'sharpe_ratio': self.sharpe_ratio,
            'risk_callbacks': len(self.risk_callbacks),
            'emergency_callbacks': len(self.emergency_callbacks)
        }


# 테스트 함수
async def test_risk_manager():
    """RiskManager 테스트"""
    print("\n=== RiskManager 테스트 시작 ===")

    config = {
        'risk_management': {
            'max_portfolio_risk': 0.03,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.15,
            'max_concentration': 0.20,
            'max_position_size': 0.10,
            'max_market_exposure': 0.70
        }
    }

    manager = RiskManager(config)

    try:
        # 모니터링 시작
        success = await manager.start_monitoring()
        print(f"모니터링 시작: {'성공' if success else '실패'}")

        # 콜백 등록
        received_alerts = []

        async def risk_callback(alert: RiskAlert):
            received_alerts.append(alert)
            print(f"[리스크 알림] {alert.level.value}: {alert.message}")

        async def emergency_callback(alert: RiskAlert):
            print(f"[긴급 상황] {alert.level.value}: {alert.message}")

        manager.register_risk_callback(risk_callback)
        manager.register_emergency_callback(emergency_callback)

        # 테스트 포트폴리오 설정
        from ..models.trading_models import Portfolio, PortfolioPosition

        # 정상 포트폴리오
        portfolio = Portfolio(
            total_value=100000.0,
            cash=20000.0,
            stock_value=80000.0,
            day_pnl=-1000.0,  # -1% 손실
            total_pnl=5000.0,
            day_pnl_pct=-1.0,
            total_pnl_pct=5.0
        )

        # 포지션 추가
        positions = {
            'AAPL': PortfolioPosition(
                symbol='AAPL',
                quantity=200,
                avg_price=170.0,
                current_price=174.0,
                market_value=34800.0,
                unrealized_pnl=800.0,
                unrealized_pnl_pct=2.35,
                market=MarketType.NASDAQ
            ),
            'MSFT': PortfolioPosition(
                symbol='MSFT',
                quantity=100,
                avg_price=330.0,
                current_price=338.0,
                market_value=33800.0,
                unrealized_pnl=800.0,
                unrealized_pnl_pct=2.42,
                market=MarketType.NASDAQ
            )
        }

        for symbol, position in positions.items():
            portfolio.add_position(position)

        await manager.update_portfolio(portfolio)
        print("정상 포트폴리오 업데이트 완료")

        # 가격 데이터 업데이트
        from ..models.trading_models import PriceData

        price_data = PriceData(
            symbol='AAPL',
            price=174.0,
            volume=100000,
            timestamp=datetime.now()
        )
        manager.set_price_data('AAPL', price_data)

        # 리스크 지표 확인
        risk_metrics = await manager.get_risk_metrics()
        print(f"\n리스크 지표:")
        for metric, value in risk_metrics.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.4f}")
            else:
                print(f"  {metric}: {value}")

        # 신호 리스크 검증 테스트
        print("\n신호 리스크 검증 테스트...")

        test_signal = TradingSignal(
            symbol='TSLA',
            signal_type=SignalType.BUY,
            confidence=0.8,
            price=248.0,
            timestamp=datetime.now(),
            strategy_name='TestStrategy'
        )

        signal_risk = await manager.check_signal_risk(test_signal)
        print(f"신호 승인: {signal_risk['approved']}")
        print(f"리스크 레벨: {signal_risk['risk_level'].value}")
        if signal_risk['warnings']:
            print(f"경고: {signal_risk['warnings']}")

        # 리스크 한도 초과 시나리오 테스트
        print("\n리스크 한도 초과 시나리오 테스트...")

        # 일일 손실 한도 초과
        risky_portfolio = Portfolio(
            total_value=90000.0,
            cash=20000.0,
            stock_value=70000.0,
            day_pnl=-6000.0,  # -6% 손실 (한도 5% 초과)
            total_pnl=-4000.0,
            day_pnl_pct=-6.0,
            total_pnl_pct=-4.0
        )

        await manager.update_portfolio(risky_portfolio)
        await asyncio.sleep(1)  # 리스크 점검 시간 대기

        # 급격한 가격 변동 시뮬레이션
        shock_price = PriceData(
            symbol='AAPL',
            price=156.0,  # 10% 하락
            volume=200000,
            timestamp=datetime.now()
        )
        manager.set_price_data('AAPL', shock_price)
        await asyncio.sleep(0.5)

        # 활성 알림 확인
        alerts = await manager.get_active_alerts()
        print(f"\n활성 리스크 알림 ({len(alerts)}개):")
        for alert in alerts:
            print(f"  {alert.level.value}: {alert.message}")
            print(f"    권고 액션: {alert.recommended_action.value}")

        # 수동 리스크 점검
        manual_check = await manager.force_risk_check()
        print(f"\n수동 리스크 점검:")
        print(f"  거래 중단: {manual_check['is_trading_halted']}")
        print(f"  활성 알림: {manual_check['active_alerts']}")

        # 매니저 통계
        stats = manager.get_manager_stats()
        print(f"\n매니저 통계:")
        print(f"  총 알림: {stats['total_alerts']}")
        print(f"  긴급 액션: {stats['emergency_actions']}")
        print(f"  포트폴리오 VaR: ${stats['portfolio_var']:.0f}")

        print(f"\n콜백으로 수신된 알림: {len(received_alerts)}개")

        # 모니터링 중지
        await manager.stop_monitoring()
        print("\n모니터링 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_risk_manager())