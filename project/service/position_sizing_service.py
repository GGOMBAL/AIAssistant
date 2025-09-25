"""
Position Sizing Service

포지션 사이징 및 매수 후보 종목 관리 서비스
전략 에이전트로부터 받은 신호를 바탕으로 실제 매매할 종목과 수량을 결정
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import math

from ..interfaces.service_interfaces import IPositionSizingService, BaseService
from ..models.trading_models import (
    TradingSignal, CandidateStock, Portfolio, PortfolioPosition,
    PriceData, SignalType, MarketType
)


class PositionSizingService(BaseService, IPositionSizingService):
    """포지션 사이징 서비스 구현"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # 설정 로드
        self.risk_config = config.get('risk_management', {})
        self.sizing_config = config.get('position_sizing', {})

        # 리스크 관리 설정
        self.max_position_size = self.risk_config.get('max_position_size', 0.1)  # 10%
        self.max_single_loss = self.risk_config.get('max_single_loss', 0.02)    # 2%
        self.max_daily_risk = self.risk_config.get('max_daily_risk', 0.05)      # 5%
        self.max_correlation_exposure = self.risk_config.get('max_correlation', 0.3)  # 30%

        # 포지션 사이징 설정
        self.min_order_amount = self.sizing_config.get('min_order_amount', 1000)  # $1,000
        self.max_order_amount = self.sizing_config.get('max_order_amount', 50000) # $50,000
        self.cash_reserve_ratio = self.sizing_config.get('cash_reserve', 0.05)   # 5%

        # 신호 및 후보 관리
        self.trading_signals: List[TradingSignal] = []
        self.candidate_stocks: List[CandidateStock] = []
        self.rejected_signals: List[Dict[str, Any]] = []

        # 포트폴리오 정보 (AccountAnalysisService로부터)
        self.current_portfolio: Optional[Portfolio] = None
        self.available_cash = 0.0

        # 가격 데이터 (LivePriceService로부터)
        self.price_data_cache: Dict[str, PriceData] = {}

        # 통계
        self.processed_signals = 0
        self.generated_candidates = 0
        self.risk_rejected_count = 0

    async def start_service(self) -> bool:
        """서비스 시작"""
        try:
            self.logger.info("[PositionSizingService] 서비스 시작")

            # 설정 검증
            await self._validate_configuration()

            # 초기화
            await self.initialize()

            self.logger.info("[PositionSizingService] 서비스 시작 완료")
            return True

        except Exception as e:
            self.log_error(f"서비스 시작 실패: {e}")
            return False

    async def stop_service(self) -> bool:
        """서비스 중지"""
        try:
            self.logger.info("[PositionSizingService] 서비스 중지")
            await self.cleanup()
            return True

        except Exception as e:
            self.log_error(f"서비스 중지 실패: {e}")
            return False

    async def process_trading_signal(self, signal: TradingSignal) -> Optional[CandidateStock]:
        """매매 신호 처리 및 후보 종목 생성"""
        try:
            self.processed_signals += 1

            # 신호 기본 검증
            if not await self._validate_signal(signal):
                return None

            # 매수 신호만 처리 (매도는 별도 로직)
            if not signal.is_buy_signal():
                self.logger.debug(f"[PositionSizing] 매수 신호가 아님: {signal.symbol} {signal.signal_type}")
                return None

            # 이미 보유 종목인지 확인
            if await self._is_already_owned(signal.symbol):
                self.logger.debug(f"[PositionSizing] 이미 보유 중인 종목: {signal.symbol}")
                return None

            # 리스크 검증
            risk_check = await self._check_risk_constraints(signal)
            if not risk_check['passed']:
                self._record_rejection(signal, risk_check['reason'])
                return None

            # 포지션 사이즈 계산
            position_size = await self._calculate_position_size(signal)
            if position_size <= 0:
                self._record_rejection(signal, "Position size too small")
                return None

            # 후보 종목 생성
            candidate = await self._create_candidate_stock(signal, position_size)
            if candidate:
                self.candidate_stocks.append(candidate)
                self.generated_candidates += 1

                self.logger.info(f"[PositionSizing] 후보 생성: {candidate.symbol} "
                               f"(Score: {candidate.score:.3f}, Size: ${position_size:,.0f})")

            return candidate

        except Exception as e:
            self.log_error(f"신호 처리 실패 ({signal.symbol}): {e}")
            return None

    async def get_buy_candidates(self, max_count: int = 10) -> List[CandidateStock]:
        """매수 후보 종목 목록 (점수순 정렬)"""
        try:
            # 후보 목록을 점수순으로 정렬
            sorted_candidates = sorted(
                self.candidate_stocks,
                key=lambda c: c.score,
                reverse=True
            )

            # 현재 시장 상황 고려하여 필터링
            filtered_candidates = await self._filter_candidates_by_market_condition(
                sorted_candidates[:max_count]
            )

            return filtered_candidates

        except Exception as e:
            self.log_error(f"후보 목록 조회 실패: {e}")
            return []

    async def calculate_order_quantity(self, symbol: str, target_amount: float) -> Tuple[int, float]:
        """주문 수량 계산"""
        try:
            # 현재 가격 조회
            current_price = await self._get_current_price(symbol)
            if not current_price or current_price <= 0:
                return 0, 0.0

            # 기본 수량 계산 (소수점 버림)
            base_quantity = int(target_amount / current_price)

            # 최소 주문 수량 확인 (보통 1주)
            min_quantity = 1
            if base_quantity < min_quantity:
                return 0, 0.0

            # 실제 주문 금액
            actual_amount = base_quantity * current_price

            # 사용 가능 현금 확인
            if actual_amount > self.available_cash:
                # 현금 한도 내에서 수량 조정
                adjusted_quantity = int(self.available_cash / current_price)
                actual_amount = adjusted_quantity * current_price

                return max(adjusted_quantity, 0), actual_amount

            return base_quantity, actual_amount

        except Exception as e:
            self.log_error(f"주문 수량 계산 실패 ({symbol}): {e}")
            return 0, 0.0

    async def update_portfolio_info(self, portfolio: Portfolio) -> None:
        """포트폴리오 정보 업데이트"""
        self.current_portfolio = portfolio

        # 사용 가능 현금 계산 (현금 보유량 - 예비 자금)
        reserve_amount = portfolio.total_value * self.cash_reserve_ratio
        self.available_cash = max(0, portfolio.cash - reserve_amount)

        self.logger.debug(f"[PositionSizing] 포트폴리오 업데이트: "
                         f"총자산 ${portfolio.total_value:,.0f}, "
                         f"사용가능현금 ${self.available_cash:,.0f}")

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """가격 데이터 업데이트"""
        self.price_data_cache[symbol] = price_data

    async def remove_candidate(self, symbol: str) -> bool:
        """후보에서 제거 (주문 실행 후)"""
        try:
            original_count = len(self.candidate_stocks)
            self.candidate_stocks = [c for c in self.candidate_stocks if c.symbol != symbol]

            removed = len(self.candidate_stocks) < original_count
            if removed:
                self.logger.info(f"[PositionSizing] 후보 제거: {symbol}")

            return removed

        except Exception as e:
            self.log_error(f"후보 제거 실패 ({symbol}): {e}")
            return False

    async def get_risk_analysis(self) -> Dict[str, Any]:
        """리스크 분석 결과"""
        try:
            analysis = {}

            if not self.current_portfolio:
                return analysis

            # 현재 포지션 위험도
            analysis['current_risk'] = await self._analyze_current_risk()

            # 후보 종목들의 추가 위험도
            analysis['candidate_risk'] = await self._analyze_candidate_risk()

            # 포트폴리오 집중도
            analysis['concentration'] = await self._analyze_concentration()

            # 시장별 노출도
            analysis['market_exposure'] = await self._analyze_market_exposure()

            return analysis

        except Exception as e:
            self.log_error(f"리스크 분석 실패: {e}")
            return {}

    async def _validate_signal(self, signal: TradingSignal) -> bool:
        """신호 유효성 검증"""
        try:
            # 기본 필드 확인
            if not signal.symbol or signal.price <= 0:
                return False

            # 신뢰도 확인
            if signal.confidence < 0.5:  # 50% 미만은 무시
                return False

            # 신호 시간 확인 (너무 오래된 신호는 무시)
            signal_age = datetime.now() - signal.timestamp
            if signal_age.total_seconds() > 300:  # 5분 이상 된 신호
                return False

            return True

        except Exception as e:
            self.log_error(f"신호 검증 실패: {e}")
            return False

    async def _is_already_owned(self, symbol: str) -> bool:
        """이미 보유한 종목인지 확인"""
        if not self.current_portfolio:
            return False

        return symbol in self.current_portfolio.positions

    async def _check_risk_constraints(self, signal: TradingSignal) -> Dict[str, Any]:
        """리스크 제약 조건 확인"""
        try:
            result = {'passed': True, 'reason': ''}

            if not self.current_portfolio:
                return {'passed': False, 'reason': 'No portfolio data'}

            # 1. 최대 포지션 크기 확인
            max_position_value = self.current_portfolio.total_value * self.max_position_size
            if signal.price * 100 > max_position_value:  # 임시로 100주 가정
                return {'passed': False, 'reason': 'Exceeds max position size'}

            # 2. 현금 부족 확인
            min_required = self.min_order_amount
            if self.available_cash < min_required:
                return {'passed': False, 'reason': 'Insufficient cash'}

            # 3. 일일 리스크 한도 확인
            daily_risk_check = await self._check_daily_risk_limit()
            if not daily_risk_check:
                return {'passed': False, 'reason': 'Daily risk limit exceeded'}

            # 4. 상관관계 확인 (같은 섹터/시장 과다 노출)
            correlation_check = await self._check_correlation_limit(signal.symbol)
            if not correlation_check:
                return {'passed': False, 'reason': 'Correlation limit exceeded'}

            return result

        except Exception as e:
            self.log_error(f"리스크 확인 실패: {e}")
            return {'passed': False, 'reason': f'Risk check error: {e}'}

    async def _calculate_position_size(self, signal: TradingSignal) -> float:
        """포지션 사이즈 계산"""
        try:
            if not self.current_portfolio:
                return 0.0

            # 포트폴리오 기반 사이징 방법 사용

            # 1. 기본 사이징 (포트폴리오 비율 기반)
            base_size = self.current_portfolio.total_value * 0.02  # 기본 2%

            # 2. 신뢰도 기반 조정
            confidence_multiplier = signal.confidence  # 0.5 ~ 1.0
            adjusted_size = base_size * confidence_multiplier

            # 3. 볼라틸리티 기반 조정 (임시로 고정값 사용)
            volatility_adjustment = 1.0  # 실제로는 종목별 변동성 계산 필요
            volatility_adjusted_size = adjusted_size * volatility_adjustment

            # 4. Kelly Criterion 적용 (단순화된 버전)
            if signal.expected_return and signal.expected_return > 0:
                kelly_fraction = min(signal.expected_return * signal.confidence, 0.05)  # 최대 5%
                kelly_size = self.current_portfolio.total_value * kelly_fraction
                volatility_adjusted_size = min(volatility_adjusted_size, kelly_size)

            # 5. 한도 적용
            max_allowed = self.current_portfolio.total_value * self.max_position_size
            min_required = self.min_order_amount

            final_size = max(min(volatility_adjusted_size, max_allowed), min_required)

            # 6. 사용 가능 현금 확인
            final_size = min(final_size, self.available_cash)

            return final_size

        except Exception as e:
            self.log_error(f"포지션 사이즈 계산 실패: {e}")
            return 0.0

    async def _create_candidate_stock(self, signal: TradingSignal, position_size: float) -> Optional[CandidateStock]:
        """후보 종목 생성"""
        try:
            # 점수 계산 (신뢰도 + 수익률 예상 + 기타 팩터)
            base_score = signal.confidence

            # 수익률 예상이 있으면 가점
            if signal.expected_return and signal.expected_return > 0:
                return_bonus = min(signal.expected_return * 0.1, 0.2)  # 최대 0.2 가점
                base_score += return_bonus

            # 신호 강도에 따른 가점
            if signal.signal_type == SignalType.STRONG_BUY:
                base_score += 0.1
            elif signal.signal_type == SignalType.BUY:
                base_score += 0.05

            # 최종 점수 (0~1 범위로 정규화)
            final_score = min(base_score, 1.0)

            # 매수 이유 생성
            reasons = []
            reasons.append(f"{signal.strategy_name} 전략 신호")
            reasons.append(f"신뢰도 {signal.confidence:.1%}")

            if signal.expected_return:
                reasons.append(f"예상 수익률 {signal.expected_return:.1%}")

            if signal.signal_type == SignalType.STRONG_BUY:
                reasons.append("강한 매수 신호")

            # 목표가 설정
            target_price = signal.target_price if signal.target_price else signal.price * 1.1

            # 후보 종목 생성
            candidate = CandidateStock(
                symbol=signal.symbol,
                score=final_score,
                strategy=signal.strategy_name,
                reasons=reasons,
                target_price=target_price,
                expected_return=signal.expected_return,
                risk_level=self._assess_risk_level(signal),
                market=self._get_market_type(signal.symbol),
                last_analysis=datetime.now()
            )

            return candidate

        except Exception as e:
            self.log_error(f"후보 종목 생성 실패: {e}")
            return None

    async def _filter_candidates_by_market_condition(self, candidates: List[CandidateStock]) -> List[CandidateStock]:
        """시장 상황에 따른 후보 필터링"""
        try:
            # 현재는 단순 필터링, 실제로는 시장 지수, VIX 등 고려
            filtered = []

            for candidate in candidates:
                # 1. 중복 시장 과다 방지
                market_exposure = await self._get_market_exposure(candidate.market)
                if market_exposure > 0.7:  # 70% 이상 노출 시 제한
                    continue

                # 2. 리스크 레벨 확인
                if candidate.risk_level == 'HIGH' and len(filtered) >= 2:
                    continue  # 고위험 종목은 최대 2개

                # 3. 최신성 확인
                if candidate.last_analysis:
                    age = datetime.now() - candidate.last_analysis
                    if age.total_seconds() > 3600:  # 1시간 이상 된 분석
                        continue

                filtered.append(candidate)

            return filtered

        except Exception as e:
            self.log_error(f"후보 필터링 실패: {e}")
            return candidates

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""
        try:
            if symbol in self.price_data_cache:
                return self.price_data_cache[symbol].price

            # 가격 데이터가 없으면 0 반환 (실제로는 API 호출)
            return None

        except Exception as e:
            self.log_error(f"가격 조회 실패 ({symbol}): {e}")
            return None

    async def _check_daily_risk_limit(self) -> bool:
        """일일 리스크 한도 확인"""
        try:
            if not self.current_portfolio:
                return True

            # 현재 일일 손실이 한도를 초과했는지 확인
            daily_loss_pct = abs(min(0, self.current_portfolio.day_pnl_pct))
            return daily_loss_pct < self.max_daily_risk * 100

        except Exception as e:
            self.log_error(f"일일 리스크 확인 실패: {e}")
            return False

    async def _check_correlation_limit(self, symbol: str) -> bool:
        """상관관계 한도 확인"""
        try:
            if not self.current_portfolio:
                return True

            # 같은 시장 노출도 확인 (간단한 구현)
            market_type = self._get_market_type(symbol)
            current_exposure = await self._get_market_exposure(market_type)

            return current_exposure < self.max_correlation_exposure

        except Exception as e:
            self.log_error(f"상관관계 확인 실패: {e}")
            return True

    async def _get_market_exposure(self, market: MarketType) -> float:
        """시장별 노출도 계산"""
        try:
            if not self.current_portfolio:
                return 0.0

            market_allocation = self.current_portfolio.get_market_allocation()
            return market_allocation.get(market.value, 0.0)

        except Exception as e:
            self.log_error(f"시장 노출도 계산 실패: {e}")
            return 0.0

    def _assess_risk_level(self, signal: TradingSignal) -> str:
        """리스크 레벨 평가"""
        try:
            # 신뢰도 기반 리스크 평가
            if signal.confidence >= 0.8:
                return 'LOW'
            elif signal.confidence >= 0.6:
                return 'MEDIUM'
            else:
                return 'HIGH'

        except Exception:
            return 'MEDIUM'

    def _get_market_type(self, symbol: str) -> MarketType:
        """심볼로 시장 유형 판단"""
        nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMZN']
        if symbol in nasdaq_symbols:
            return MarketType.NASDAQ
        else:
            return MarketType.NYSE

    def _record_rejection(self, signal: TradingSignal, reason: str) -> None:
        """거부 사유 기록"""
        rejection = {
            'symbol': signal.symbol,
            'reason': reason,
            'confidence': signal.confidence,
            'timestamp': datetime.now(),
            'strategy': signal.strategy_name
        }

        self.rejected_signals.append(rejection)
        self.risk_rejected_count += 1

        # 최대 100개 기록 유지
        if len(self.rejected_signals) > 100:
            self.rejected_signals = self.rejected_signals[-100:]

        self.logger.debug(f"[PositionSizing] 신호 거부: {signal.symbol} - {reason}")

    async def _analyze_current_risk(self) -> Dict[str, float]:
        """현재 포지션 위험도 분석"""
        risk_metrics = {}

        if self.current_portfolio:
            risk_metrics['portfolio_volatility'] = 0.15  # 임시값
            risk_metrics['max_drawdown'] = abs(min(0, self.current_portfolio.total_pnl_pct)) / 100
            risk_metrics['concentration_risk'] = len(self.current_portfolio.positions) / 10.0 if self.current_portfolio.positions else 0

        return risk_metrics

    async def _analyze_candidate_risk(self) -> Dict[str, Any]:
        """후보 종목 위험도 분석"""
        return {
            'candidate_count': len(self.candidate_stocks),
            'high_risk_count': sum(1 for c in self.candidate_stocks if c.risk_level == 'HIGH'),
            'avg_confidence': sum(c.score for c in self.candidate_stocks) / len(self.candidate_stocks) if self.candidate_stocks else 0
        }

    async def _analyze_concentration(self) -> Dict[str, float]:
        """포트폴리오 집중도 분석"""
        if not self.current_portfolio or not self.current_portfolio.positions:
            return {}

        position_weights = [pos.market_value / self.current_portfolio.stock_value
                          for pos in self.current_portfolio.positions.values()]

        return {
            'max_position_weight': max(position_weights) if position_weights else 0,
            'top3_concentration': sum(sorted(position_weights, reverse=True)[:3]) if len(position_weights) >= 3 else sum(position_weights)
        }

    async def _analyze_market_exposure(self) -> Dict[str, float]:
        """시장별 노출도 분석"""
        if not self.current_portfolio:
            return {}

        return self.current_portfolio.get_market_allocation()

    async def _validate_configuration(self) -> None:
        """설정 유효성 검증"""
        if self.max_position_size <= 0 or self.max_position_size > 1:
            raise ValueError("Invalid max_position_size")

        if self.min_order_amount <= 0:
            raise ValueError("Invalid min_order_amount")

        self.logger.info(f"[PositionSizing] 설정 검증 완료: "
                        f"최대포지션={self.max_position_size:.1%}, "
                        f"최소주문=${self.min_order_amount:,}")

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계"""
        return {
            'processed_signals': self.processed_signals,
            'generated_candidates': self.generated_candidates,
            'current_candidates': len(self.candidate_stocks),
            'risk_rejected': self.risk_rejected_count,
            'available_cash': self.available_cash,
            'max_position_size': self.max_position_size,
            **self.get_health_status()
        }

    # IPositionSizingService 인터페이스 구현
    async def calculate_buy_quantity(self, symbol: str, price: float, strategy: str = "default") -> int:
        """매수 수량 계산"""
        try:
            # 포지션 크기 계산
            target_amount = await self._calculate_position_size(symbol, price, strategy)

            if target_amount <= 0:
                return 0

            # 수량 계산
            quantity = int(target_amount / price)

            # 최소 주문 단위 확인
            if quantity * price < self.min_order_amount:
                return 0

            return quantity

        except Exception as e:
            self.log_error(f"매수 수량 계산 실패 ({symbol}): {e}")
            return 0

    async def get_candidates(self, strategy: str = "all") -> List[str]:
        """매수 후보 종목"""
        try:
            if strategy == "all":
                return [candidate.symbol for candidate in self.candidate_stocks]
            else:
                return [candidate.symbol for candidate in self.candidate_stocks
                       if candidate.strategy == strategy]
        except Exception as e:
            self.log_error(f"후보 종목 조회 실패: {e}")
            return []

    async def update_candidates(self, candidates: List[str]) -> bool:
        """매수 후보 종목 업데이트"""
        try:
            # 기존 후보 목록 클리어
            self.candidate_stocks.clear()

            # 새로운 후보 종목들을 CandidateStock 객체로 변환
            for symbol in candidates:
                if symbol in self.price_data_cache:
                    price_data = self.price_data_cache[symbol]
                    candidate = CandidateStock(
                        symbol=symbol,
                        signal_strength=0.7,  # 기본값
                        confidence=0.7,       # 기본값
                        expected_return=0.08, # 기본값
                        risk_level="medium",
                        strategy="manual_update",
                        target_price=price_data.price * 1.1,
                        stop_loss=price_data.price * 0.95,
                        score=0.7,
                        last_updated=datetime.now()
                    )
                    self.candidate_stocks.append(candidate)

            self.logger.info(f"후보 종목 업데이트 완료: {len(candidates)}개")
            return True

        except Exception as e:
            self.log_error(f"후보 종목 업데이트 실패: {e}")
            return False

    async def check_position_limits(self, symbol: str, quantity: int, price: float) -> Dict[str, Any]:
        """포지션 제한 확인"""
        try:
            result = {
                'is_valid': True,
                'violations': [],
                'warnings': [],
                'max_allowed_quantity': quantity,
                'position_size_pct': 0.0
            }

            if not self.current_portfolio:
                result['warnings'].append("포트폴리오 정보 없음")
                return result

            order_value = quantity * price
            total_value = self.current_portfolio.total_value

            if total_value > 0:
                position_size_pct = order_value / total_value
                result['position_size_pct'] = position_size_pct

                # 최대 포지션 크기 확인
                if position_size_pct > self.max_position_size:
                    max_allowed_value = total_value * self.max_position_size
                    max_allowed_quantity = int(max_allowed_value / price)
                    result['is_valid'] = False
                    result['violations'].append(f"포지션 크기 초과: {position_size_pct:.1%} > {self.max_position_size:.1%}")
                    result['max_allowed_quantity'] = max_allowed_quantity

            # 현금 잔고 확인
            if order_value > self.available_cash:
                result['is_valid'] = False
                result['violations'].append(f"현금 부족: ${order_value:,.0f} > ${self.available_cash:,.0f}")

            # 최소/최대 주문 금액 확인
            if order_value < self.min_order_amount:
                result['is_valid'] = False
                result['violations'].append(f"최소 주문 금액 미달: ${order_value:,.0f} < ${self.min_order_amount:,.0f}")

            if order_value > self.max_order_amount:
                result['warnings'].append(f"큰 주문 금액: ${order_value:,.0f} > ${self.max_order_amount:,.0f}")

            return result

        except Exception as e:
            self.log_error(f"포지션 제한 확인 실패 ({symbol}): {e}")
            return {
                'is_valid': False,
                'violations': [f"검증 오류: {e}"],
                'warnings': [],
                'max_allowed_quantity': 0,
                'position_size_pct': 0.0
            }

    async def apply_risk_constraints(self, orders: List[Dict]) -> List[Dict]:
        """리스크 제약 조건 적용"""
        try:
            validated_orders = []

            for order in orders:
                symbol = order.get('symbol', '')
                quantity = order.get('quantity', 0)
                price = order.get('price', 0.0)

                if not all([symbol, quantity > 0, price > 0]):
                    continue

                # 포지션 제한 확인
                limits_check = await self.check_position_limits(symbol, quantity, price)

                if limits_check['is_valid']:
                    validated_orders.append(order)
                else:
                    # 최대 허용 수량으로 조정
                    max_qty = limits_check['max_allowed_quantity']
                    if max_qty > 0:
                        adjusted_order = order.copy()
                        adjusted_order['quantity'] = max_qty
                        adjusted_order['risk_adjusted'] = True
                        adjusted_order['original_quantity'] = quantity
                        validated_orders.append(adjusted_order)

                        self.logger.info(f"주문 수량 조정: {symbol} {quantity} -> {max_qty}")
                    else:
                        self.logger.warning(f"리스크 제약으로 주문 거부: {symbol}")
                        self.risk_rejected_count += 1

            return validated_orders

        except Exception as e:
            self.log_error(f"리스크 제약 적용 실패: {e}")
            return []


# 테스트 함수
async def test_position_sizing_service():
    """PositionSizingService 테스트"""
    print("\n=== PositionSizingService 테스트 시작 ===")

    config = {
        'risk_management': {
            'max_position_size': 0.1,
            'max_single_loss': 0.02,
            'max_daily_risk': 0.05
        },
        'position_sizing': {
            'min_order_amount': 1000,
            'max_order_amount': 50000,
            'cash_reserve': 0.05
        }
    }

    service = PositionSizingService(config)

    try:
        # 서비스 시작
        success = await service.start_service()
        print(f"서비스 시작: {'성공' if success else '실패'}")

        # 포트폴리오 설정
        from ..models.trading_models import Portfolio, TradingSignal, PriceData

        portfolio = Portfolio(
            total_value=100000.0,
            cash=20000.0,
            stock_value=80000.0,
            day_pnl=1000.0,
            total_pnl=5000.0,
            day_pnl_pct=1.0,
            total_pnl_pct=5.0
        )

        await service.update_portfolio_info(portfolio)
        print(f"포트폴리오 업데이트 완료: 사용가능현금 ${service.available_cash:,.0f}")

        # 가격 데이터 설정
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        prices = [174.25, 338.92, 125.87, 248.33, 421.45]

        for symbol, price in zip(symbols, prices):
            price_data = PriceData(
                symbol=symbol,
                price=price,
                volume=100000,
                timestamp=datetime.now()
            )
            service.set_price_data(symbol, price_data)

        # 매매 신호 테스트
        print("\n매매 신호 처리 테스트...")

        for i, (symbol, price) in enumerate(zip(symbols, prices)):
            signal = TradingSignal(
                symbol=symbol,
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.STRONG_BUY,
                confidence=0.6 + (i * 0.1),
                price=price,
                timestamp=datetime.now(),
                strategy_name=f"Strategy_{i+1}",
                expected_return=0.05 + (i * 0.02),
                target_price=price * 1.15
            )

            candidate = await service.process_trading_signal(signal)
            if candidate:
                print(f"✓ 후보 생성: {candidate.symbol} (점수: {candidate.score:.3f})")
            else:
                print(f"✗ 후보 생성 실패: {symbol}")

        # 후보 목록 조회
        candidates = await service.get_buy_candidates(5)
        print(f"\n매수 후보 ({len(candidates)}개):")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.symbol}: {candidate.score:.3f} ({candidate.strategy})")
            print(f"     목표가: ${candidate.target_price:.2f}, 리스크: {candidate.risk_level}")

        # 주문 수량 계산 테스트
        if candidates:
            test_symbol = candidates[0].symbol
            target_amount = 5000.0  # $5,000 주문

            quantity, actual_amount = await service.calculate_order_quantity(test_symbol, target_amount)
            print(f"\n주문 수량 계산:")
            print(f"  종목: {test_symbol}")
            print(f"  목표 금액: ${target_amount:,.0f}")
            print(f"  계산된 수량: {quantity}주")
            print(f"  실제 금액: ${actual_amount:,.0f}")

        # 리스크 분석
        risk_analysis = await service.get_risk_analysis()
        print(f"\n리스크 분석:")
        for category, metrics in risk_analysis.items():
            print(f"  {category}: {metrics}")

        # 서비스 통계
        stats = service.get_service_stats()
        print(f"\n서비스 통계: {stats}")

        # 서비스 중지
        await service.stop_service()
        print("\n서비스 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_position_sizing_service())