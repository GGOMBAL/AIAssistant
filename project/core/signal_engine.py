"""
Signal Engine

다중 전략으로부터 받은 매매 신호를 통합하고 분석하여
최종 거래 신호를 생성하는 엔진
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import json

from ..models.trading_models import (
    TradingSignal, SignalType, PriceData, MarketType
)


class SignalEngine:
    """신호 통합 및 분석 엔진"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 신호 통합 설정
        self.signal_config = config.get('signal_engine', {})
        self.min_confidence_threshold = self.signal_config.get('min_confidence', 0.6)
        self.signal_expiry_minutes = self.signal_config.get('expiry_minutes', 15)
        self.consensus_threshold = self.signal_config.get('consensus_threshold', 0.7)

        # 전략별 가중치 설정
        self.strategy_weights = self.signal_config.get('strategy_weights', {})
        self.default_strategy_weight = 1.0

        # 신호 저장 및 관리
        self.raw_signals: Dict[str, List[TradingSignal]] = defaultdict(list)  # symbol -> signals
        self.processed_signals: Dict[str, TradingSignal] = {}  # symbol -> final signal
        self.signal_history: deque = deque(maxlen=1000)

        # 전략별 성과 추적
        self.strategy_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_signals': 0,
            'successful_signals': 0,
            'avg_confidence': 0.0,
            'success_rate': 0.0,
            'avg_return': 0.0,
            'last_signal_time': None
        })

        # 신호 품질 메트릭
        self.quality_metrics: Dict[str, Any] = {
            'signal_count_24h': 0,
            'avg_confidence_24h': 0.0,
            'strategy_diversity': 0.0,
            'signal_latency_ms': 0.0,
            'consensus_rate': 0.0
        }

        # 실시간 가격 데이터
        self.price_data_cache: Dict[str, PriceData] = {}

        # 콜백 관리
        self.signal_callbacks: List[Callable] = []

        # 통계
        self.total_signals_received = 0
        self.total_signals_generated = 0
        self.signals_rejected = 0

        # 실행 상태
        self.is_running = False
        self.cleanup_task = None

    async def start_engine(self) -> bool:
        """신호 엔진 시작"""
        try:
            self.logger.info("[SignalEngine] 신호 엔진 시작")

            # 설정 검증
            await self._validate_configuration()

            # 주기적 정리 태스크 시작
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            self.is_running = True
            self.logger.info("[SignalEngine] 신호 엔진 시작 완료")
            return True

        except Exception as e:
            self.logger.error(f"신호 엔진 시작 실패: {e}")
            return False

    async def stop_engine(self) -> bool:
        """신호 엔진 중지"""
        try:
            self.logger.info("[SignalEngine] 신호 엔진 중지")

            self.is_running = False

            # 정리 태스크 중지
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()

            return True

        except Exception as e:
            self.logger.error(f"신호 엔진 중지 실패: {e}")
            return False

    async def add_signal(self, signal: TradingSignal) -> bool:
        """새로운 매매 신호 추가"""
        try:
            self.total_signals_received += 1

            # 신호 기본 검증
            if not await self._validate_signal(signal):
                self.signals_rejected += 1
                return False

            # 중복 신호 확인
            if await self._is_duplicate_signal(signal):
                self.logger.debug(f"[SignalEngine] 중복 신호 무시: {signal.symbol} from {signal.strategy_name}")
                return False

            # 신호 저장
            self.raw_signals[signal.symbol].append(signal)

            # 전략 성과 업데이트
            await self._update_strategy_performance(signal)

            # 신호 통합 및 처리
            final_signal = await self._process_signals_for_symbol(signal.symbol)

            if final_signal:
                self.processed_signals[signal.symbol] = final_signal
                self.total_signals_generated += 1

                # 콜백 알림
                await self._notify_signal_callbacks(final_signal)

                # 히스토리 저장
                self.signal_history.append({
                    'signal': final_signal,
                    'raw_signals_count': len(self.raw_signals[signal.symbol]),
                    'timestamp': datetime.now()
                })

                self.logger.info(f"[SignalEngine] 통합 신호 생성: {final_signal.symbol} "
                               f"{final_signal.signal_type.value} (신뢰도: {final_signal.confidence:.3f})")

            return True

        except Exception as e:
            self.logger.error(f"신호 추가 실패 ({signal.symbol}): {e}")
            return False

    async def get_current_signals(self) -> List[TradingSignal]:
        """현재 유효한 통합 신호 목록"""
        try:
            current_time = datetime.now()
            valid_signals = []

            for symbol, signal in self.processed_signals.items():
                # 신호 만료 시간 확인
                if self._is_signal_expired(signal, current_time):
                    continue

                # 현재 가격 정보 업데이트
                if symbol in self.price_data_cache:
                    current_price = self.price_data_cache[symbol].price
                    # 신호 생성 시점과 현재 가격 차이가 큰 경우 제외
                    price_change_pct = abs((current_price - signal.price) / signal.price) * 100
                    if price_change_pct > 5:  # 5% 이상 가격 변동 시 제외
                        continue

                valid_signals.append(signal)

            # 신뢰도 순으로 정렬
            valid_signals.sort(key=lambda s: s.confidence, reverse=True)
            return valid_signals

        except Exception as e:
            self.logger.error(f"현재 신호 조회 실패: {e}")
            return []

    async def get_signal_for_symbol(self, symbol: str) -> Optional[TradingSignal]:
        """특정 종목의 현재 신호"""
        try:
            if symbol not in self.processed_signals:
                return None

            signal = self.processed_signals[symbol]

            # 만료 확인
            if self._is_signal_expired(signal, datetime.now()):
                return None

            return signal

        except Exception as e:
            self.logger.error(f"종목 신호 조회 실패 ({symbol}): {e}")
            return None

    def set_price_data(self, symbol: str, price_data: PriceData) -> None:
        """실시간 가격 데이터 업데이트"""
        self.price_data_cache[symbol] = price_data

        # 해당 종목 신호가 있으면 가격 정보 업데이트
        if symbol in self.processed_signals:
            asyncio.create_task(self._update_signal_with_price(symbol, price_data))

    def register_signal_callback(self, callback: Callable) -> None:
        """신호 생성 시 호출될 콜백 등록"""
        if callback not in self.signal_callbacks:
            self.signal_callbacks.append(callback)
            self.logger.debug(f"[SignalEngine] 콜백 등록: {callback.__name__}")

    def unregister_signal_callback(self, callback: Callable) -> None:
        """콜백 등록 해제"""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
            self.logger.debug(f"[SignalEngine] 콜백 해제: {callback.__name__}")

    async def get_strategy_performance(self) -> Dict[str, Any]:
        """전략별 성과 조회"""
        return dict(self.strategy_performance)

    async def get_signal_quality_metrics(self) -> Dict[str, Any]:
        """신호 품질 지표"""
        try:
            await self._calculate_quality_metrics()
            return self.quality_metrics.copy()
        except Exception as e:
            self.logger.error(f"품질 지표 조회 실패: {e}")
            return {}

    async def _validate_signal(self, signal: TradingSignal) -> bool:
        """신호 유효성 검증"""
        try:
            # 필수 필드 확인
            if not signal.symbol or not signal.strategy_name:
                return False

            if signal.price <= 0 or signal.confidence <= 0:
                return False

            # 신뢰도 임계값 확인
            if signal.confidence < self.min_confidence_threshold:
                return False

            # 신호 시간 확인 (너무 오래된 신호 제외)
            signal_age = datetime.now() - signal.timestamp
            if signal_age.total_seconds() > 300:  # 5분 이상
                return False

            return True

        except Exception as e:
            self.logger.error(f"신호 검증 실패: {e}")
            return False

    async def _is_duplicate_signal(self, new_signal: TradingSignal) -> bool:
        """중복 신호 확인"""
        try:
            if new_signal.symbol not in self.raw_signals:
                return False

            existing_signals = self.raw_signals[new_signal.symbol]

            for existing in existing_signals:
                # 같은 전략에서 최근 5분 이내 동일한 신호
                if (existing.strategy_name == new_signal.strategy_name and
                    existing.signal_type == new_signal.signal_type):

                    time_diff = abs((new_signal.timestamp - existing.timestamp).total_seconds())
                    if time_diff < 300:  # 5분 이내
                        return True

            return False

        except Exception as e:
            self.logger.error(f"중복 신호 확인 실패: {e}")
            return False

    async def _process_signals_for_symbol(self, symbol: str) -> Optional[TradingSignal]:
        """특정 종목의 신호들을 통합 처리"""
        try:
            raw_signals = self.raw_signals.get(symbol, [])
            if not raw_signals:
                return None

            # 만료된 신호 제거
            current_time = datetime.now()
            valid_signals = [
                s for s in raw_signals
                if (current_time - s.timestamp).total_seconds() < self.signal_expiry_minutes * 60
            ]

            if not valid_signals:
                return None

            # 신호 통합 방법 결정
            if len(valid_signals) == 1:
                return valid_signals[0]
            else:
                return await self._merge_signals(valid_signals)

        except Exception as e:
            self.logger.error(f"신호 통합 처리 실패 ({symbol}): {e}")
            return None

    async def _merge_signals(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """여러 신호를 하나로 통합"""
        try:
            if not signals:
                return None

            symbol = signals[0].symbol

            # 신호 타입별 그룹화
            signal_groups = defaultdict(list)
            for signal in signals:
                signal_groups[signal.signal_type].append(signal)

            # 가장 많은 신호 타입 선택
            dominant_type = max(signal_groups.keys(), key=lambda k: len(signal_groups[k]))
            dominant_signals = signal_groups[dominant_type]

            # 컨센서스 확인 (70% 이상 동의)
            consensus_ratio = len(dominant_signals) / len(signals)
            if consensus_ratio < self.consensus_threshold:
                return None

            # 가중 평균 계산
            total_weight = 0
            weighted_confidence = 0
            weighted_price = 0
            latest_timestamp = None

            strategies = []
            expected_returns = []
            target_prices = []

            for signal in dominant_signals:
                # 전략 가중치 적용
                weight = self.strategy_weights.get(signal.strategy_name, self.default_strategy_weight)
                # 성과 기반 추가 가중치
                perf = self.strategy_performance.get(signal.strategy_name, {})
                success_rate = perf.get('success_rate', 0.5)
                performance_weight = 0.5 + success_rate  # 0.5 ~ 1.5

                final_weight = weight * performance_weight

                total_weight += final_weight
                weighted_confidence += signal.confidence * final_weight
                weighted_price += signal.price * final_weight

                strategies.append(signal.strategy_name)

                if signal.expected_return:
                    expected_returns.append(signal.expected_return)
                if signal.target_price:
                    target_prices.append(signal.target_price)

                if latest_timestamp is None or signal.timestamp > latest_timestamp:
                    latest_timestamp = signal.timestamp

            # 최종 신호 생성
            final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
            final_price = weighted_price / total_weight if total_weight > 0 else signals[0].price

            # 메타데이터 정리
            metadata = {
                'source_strategies': strategies,
                'source_count': len(dominant_signals),
                'consensus_ratio': consensus_ratio,
                'merge_timestamp': datetime.now().isoformat()
            }

            merged_signal = TradingSignal(
                symbol=symbol,
                signal_type=dominant_type,
                confidence=min(final_confidence, 1.0),  # 1.0 이하로 제한
                price=final_price,
                timestamp=latest_timestamp or datetime.now(),
                strategy_name=f"Merged({len(strategies)})",
                metadata=metadata,
                expected_return=statistics.mean(expected_returns) if expected_returns else None,
                target_price=statistics.mean(target_prices) if target_prices else None
            )

            return merged_signal

        except Exception as e:
            self.logger.error(f"신호 병합 실패: {e}")
            return None

    async def _update_strategy_performance(self, signal: TradingSignal) -> None:
        """전략 성과 업데이트"""
        try:
            strategy = signal.strategy_name
            perf = self.strategy_performance[strategy]

            perf['total_signals'] += 1
            perf['last_signal_time'] = signal.timestamp

            # 신뢰도 평균 업데이트 (이동평균)
            if perf['avg_confidence'] == 0:
                perf['avg_confidence'] = signal.confidence
            else:
                perf['avg_confidence'] = (perf['avg_confidence'] * 0.9 + signal.confidence * 0.1)

            # 성공률은 별도로 업데이트 (실제 거래 결과가 필요)

        except Exception as e:
            self.logger.error(f"전략 성과 업데이트 실패: {e}")

    async def _notify_signal_callbacks(self, signal: TradingSignal) -> None:
        """신호 생성 콜백 알림"""
        try:
            for callback in self.signal_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(signal)
                    else:
                        callback(signal)
                except Exception as e:
                    self.logger.error(f"콜백 실행 실패 ({callback.__name__}): {e}")

        except Exception as e:
            self.logger.error(f"콜백 알림 실패: {e}")

    async def _update_signal_with_price(self, symbol: str, price_data: PriceData) -> None:
        """신호에 최신 가격 정보 반영"""
        try:
            if symbol not in self.processed_signals:
                return

            signal = self.processed_signals[symbol]

            # 가격 변동이 너무 큰 경우 신호 무효화
            price_change_pct = abs((price_data.price - signal.price) / signal.price) * 100
            if price_change_pct > 10:  # 10% 이상 변동
                self.logger.warning(f"[SignalEngine] 큰 가격 변동으로 신호 무효화: {symbol} "
                                  f"{price_change_pct:.1f}% 변동")
                del self.processed_signals[symbol]

        except Exception as e:
            self.logger.error(f"신호 가격 업데이트 실패 ({symbol}): {e}")

    def _is_signal_expired(self, signal: TradingSignal, current_time: datetime) -> bool:
        """신호 만료 확인"""
        signal_age = (current_time - signal.timestamp).total_seconds()
        return signal_age > self.signal_expiry_minutes * 60

    async def _cleanup_loop(self):
        """만료된 신호 정리 루프"""
        while self.is_running:
            try:
                await self._cleanup_expired_signals()
                await asyncio.sleep(60)  # 1분마다 정리
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"신호 정리 루프 오류: {e}")
                await asyncio.sleep(10)

    async def _cleanup_expired_signals(self) -> None:
        """만료된 신호 정리"""
        try:
            current_time = datetime.now()
            expiry_threshold = current_time - timedelta(minutes=self.signal_expiry_minutes)

            # 원시 신호 정리
            for symbol in list(self.raw_signals.keys()):
                signals = self.raw_signals[symbol]
                valid_signals = [s for s in signals if s.timestamp > expiry_threshold]

                if valid_signals:
                    self.raw_signals[symbol] = valid_signals
                else:
                    del self.raw_signals[symbol]

            # 처리된 신호 정리
            for symbol in list(self.processed_signals.keys()):
                signal = self.processed_signals[symbol]
                if self._is_signal_expired(signal, current_time):
                    del self.processed_signals[symbol]

        except Exception as e:
            self.logger.error(f"만료 신호 정리 실패: {e}")

    async def _calculate_quality_metrics(self) -> None:
        """신호 품질 지표 계산"""
        try:
            current_time = datetime.now()
            day_ago = current_time - timedelta(hours=24)

            # 24시간 내 신호 수집
            recent_signals = [
                entry['signal'] for entry in self.signal_history
                if entry['timestamp'] > day_ago
            ]

            self.quality_metrics['signal_count_24h'] = len(recent_signals)

            if recent_signals:
                # 평균 신뢰도
                confidences = [s.confidence for s in recent_signals]
                self.quality_metrics['avg_confidence_24h'] = statistics.mean(confidences)

                # 전략 다양성 (사용된 전략 수 / 총 신호 수)
                strategies = set(s.strategy_name for s in recent_signals)
                self.quality_metrics['strategy_diversity'] = len(strategies) / len(recent_signals)

                # 컨센서스 비율 (병합된 신호 비율)
                merged_signals = sum(1 for s in recent_signals if 'Merged' in s.strategy_name)
                self.quality_metrics['consensus_rate'] = merged_signals / len(recent_signals)

        except Exception as e:
            self.logger.error(f"품질 지표 계산 실패: {e}")

    async def _validate_configuration(self) -> None:
        """설정 유효성 검증"""
        if not 0 < self.min_confidence_threshold <= 1:
            raise ValueError("Invalid min_confidence_threshold")

        if self.signal_expiry_minutes <= 0:
            raise ValueError("Invalid signal_expiry_minutes")

        if not 0 < self.consensus_threshold <= 1:
            raise ValueError("Invalid consensus_threshold")

        self.logger.info(f"[SignalEngine] 설정 검증 완료: "
                        f"최소신뢰도={self.min_confidence_threshold:.2f}, "
                        f"만료시간={self.signal_expiry_minutes}분")

    def get_engine_stats(self) -> Dict[str, Any]:
        """엔진 통계"""
        return {
            'is_running': self.is_running,
            'total_signals_received': self.total_signals_received,
            'total_signals_generated': self.total_signals_generated,
            'signals_rejected': self.signals_rejected,
            'current_raw_signals': sum(len(signals) for signals in self.raw_signals.values()),
            'current_processed_signals': len(self.processed_signals),
            'active_strategies': len(self.strategy_performance),
            'callback_count': len(self.signal_callbacks),
            'min_confidence_threshold': self.min_confidence_threshold,
            'signal_expiry_minutes': self.signal_expiry_minutes,
            'consensus_threshold': self.consensus_threshold
        }


# 테스트 함수
async def test_signal_engine():
    """SignalEngine 테스트"""
    print("\n=== SignalEngine 테스트 시작 ===")

    config = {
        'signal_engine': {
            'min_confidence': 0.6,
            'expiry_minutes': 15,
            'consensus_threshold': 0.7,
            'strategy_weights': {
                'Strategy_A': 1.2,
                'Strategy_B': 1.0,
                'Strategy_C': 0.8
            }
        }
    }

    engine = SignalEngine(config)

    try:
        # 엔진 시작
        success = await engine.start_engine()
        print(f"엔진 시작: {'성공' if success else '실패'}")

        # 콜백 등록
        received_signals = []

        async def signal_callback(signal: TradingSignal):
            received_signals.append(signal)
            print(f"[콜백] 신호 수신: {signal.symbol} {signal.signal_type.value} "
                  f"(신뢰도: {signal.confidence:.3f})")

        engine.register_signal_callback(signal_callback)

        # 테스트 신호들 생성
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']

        print("\n단일 신호 테스트...")

        # 1. 단일 신호 테스트
        signal1 = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            confidence=0.8,
            price=174.25,
            timestamp=datetime.now(),
            strategy_name='Strategy_A',
            expected_return=0.1,
            target_price=191.68
        )

        await engine.add_signal(signal1)
        await asyncio.sleep(0.1)

        # 2. 다중 신호 통합 테스트
        print("\n다중 신호 통합 테스트...")

        signals_msft = [
            TradingSignal(
                symbol='MSFT',
                signal_type=SignalType.BUY,
                confidence=0.7,
                price=338.92,
                timestamp=datetime.now(),
                strategy_name='Strategy_A',
                expected_return=0.08
            ),
            TradingSignal(
                symbol='MSFT',
                signal_type=SignalType.BUY,
                confidence=0.75,
                price=339.50,
                timestamp=datetime.now(),
                strategy_name='Strategy_B',
                expected_return=0.09
            ),
            TradingSignal(
                symbol='MSFT',
                signal_type=SignalType.STRONG_BUY,
                confidence=0.9,
                price=340.00,
                timestamp=datetime.now(),
                strategy_name='Strategy_C',
                expected_return=0.12
            )
        ]

        for signal in signals_msft:
            await engine.add_signal(signal)
            await asyncio.sleep(0.05)

        # 3. 상충 신호 테스트 (컨센서스 미달)
        print("\n상충 신호 테스트...")

        conflicting_signals = [
            TradingSignal(
                symbol='GOOGL',
                signal_type=SignalType.BUY,
                confidence=0.7,
                price=125.87,
                timestamp=datetime.now(),
                strategy_name='Strategy_A'
            ),
            TradingSignal(
                symbol='GOOGL',
                signal_type=SignalType.SELL,
                confidence=0.6,
                price=125.50,
                timestamp=datetime.now(),
                strategy_name='Strategy_B'
            )
        ]

        for signal in conflicting_signals:
            await engine.add_signal(signal)
            await asyncio.sleep(0.05)

        # 현재 신호 조회
        current_signals = await engine.get_current_signals()
        print(f"\n현재 활성 신호 ({len(current_signals)}개):")
        for signal in current_signals:
            print(f"  {signal.symbol}: {signal.signal_type.value} "
                  f"(신뢰도: {signal.confidence:.3f}, 전략: {signal.strategy_name})")

        # 특정 종목 신호 조회
        aapl_signal = await engine.get_signal_for_symbol('AAPL')
        if aapl_signal:
            print(f"\nAAPL 신호: {aapl_signal.signal_type.value} "
                  f"(신뢰도: {aapl_signal.confidence:.3f})")

        # 가격 데이터 업데이트 테스트
        print("\n가격 데이터 업데이트 테스트...")

        from ..models.trading_models import PriceData, MarketType

        price_data = PriceData(
            symbol='AAPL',
            price=175.50,  # 약간 상승
            volume=100000,
            timestamp=datetime.now(),
            market=MarketType.NASDAQ
        )

        engine.set_price_data('AAPL', price_data)

        # 전략 성과 조회
        performance = await engine.get_strategy_performance()
        print(f"\n전략별 성과:")
        for strategy, perf in performance.items():
            print(f"  {strategy}: 신호 {perf['total_signals']}개, "
                  f"평균 신뢰도 {perf['avg_confidence']:.3f}")

        # 신호 품질 지표
        quality = await engine.get_signal_quality_metrics()
        print(f"\n신호 품질 지표:")
        for metric, value in quality.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")

        # 엔진 통계
        stats = engine.get_engine_stats()
        print(f"\n엔진 통계:")
        print(f"  수신 신호: {stats['total_signals_received']}개")
        print(f"  생성 신호: {stats['total_signals_generated']}개")
        print(f"  거부 신호: {stats['signals_rejected']}개")
        print(f"  활성 전략: {stats['active_strategies']}개")

        # 콜백 수신 확인
        print(f"\n콜백으로 수신된 신호: {len(received_signals)}개")

        # 엔진 중지
        await engine.stop_engine()
        print("\n엔진 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signal_engine())