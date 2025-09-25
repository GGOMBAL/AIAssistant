"""
Strategy Agent - Multi-Agent Trading System

매매 전략 수립 및 신호 생성을 담당하는 전문 에이전트
NASDAQ과 NYSE 시장별 차별화된 전략 적용

버전: 1.0
작성일: 2025-09-22
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)


class StrategyAgent:
    """
    Strategy Agent

    시장별 차별화된 전략을 적용하여 매매 신호를 생성
    - NASDAQ: 기술주/성장주 전략
    - NYSE: 대형주/가치주 전략
    """

    def __init__(self, config: Dict[str, Any]):
        """Strategy Agent 초기화"""
        self.config = config
        self.execution_log = []

        # 전략 파라미터 설정
        self.strategy_params = {
            'NASDAQ': {
                'ma_fast': 5,
                'ma_slow': 20,
                'rsi_oversold': 25,
                'rsi_overbought': 75,
                'volume_threshold': 1.5,  # 평균 대비 1.5배 이상
                'momentum_period': 10,
                'volatility_threshold': 0.02  # 2% 이상 변동성
            },
            'NYSE': {
                'ma_fast': 10,
                'ma_slow': 50,
                'rsi_oversold': 35,
                'rsi_overbought': 65,
                'volume_threshold': 1.2,  # 평균 대비 1.2배 이상
                'momentum_period': 20,
                'volatility_threshold': 0.015  # 1.5% 이상 변동성
            }
        }

        self._log("[Strategy Agent] 초기화 완료")
        self._log(f"[Strategy Agent] NASDAQ 전략 파라미터: {self.strategy_params['NASDAQ']}")
        self._log(f"[Strategy Agent] NYSE 전략 파라미터: {self.strategy_params['NYSE']}")

    def generate_trading_signals(self,
                                market_data: Dict[str, pd.DataFrame],
                                prompt: str = "") -> Dict[str, Any]:
        """
        매매 신호 생성

        Args:
            market_data: 시장 데이터
            prompt: 오케스트레이터로부터의 작업 지시

        Returns:
            생성된 매매 신호
        """
        start_time = time.time()

        try:
            self._log("[Strategy Agent] 매매 신호 생성 작업 시작")
            self._log(f"[Strategy Agent] 작업 지시 수신: {len(prompt)} 문자")
            self._log(f"[Strategy Agent] 대상 종목 수: {len(market_data)}")

            # 시장별 데이터 분리
            nasdaq_data, nyse_data = self._separate_market_data(market_data)

            # 시장별 신호 생성
            nasdaq_signals = self._generate_nasdaq_signals(nasdaq_data)
            nyse_signals = self._generate_nyse_signals(nyse_data)

            # 신호 통합
            all_signals = {}
            all_signals.update(nasdaq_signals)
            all_signals.update(nyse_signals)

            # 포트폴리오 레벨 최적화
            optimized_signals = self._optimize_portfolio_signals(all_signals, market_data)

            # 신호 품질 검증
            validated_signals = self._validate_signals(optimized_signals, market_data)

            execution_time = time.time() - start_time
            self._log(f"[Strategy Agent] 신호 생성 완료 - 실행시간: {execution_time:.2f}초")

            # 신호 요약
            self._log_signal_summary(validated_signals)

            return validated_signals

        except Exception as e:
            self._log(f"[Strategy Agent] 신호 생성 실패: {e}")
            return {}

    def _separate_market_data(self, market_data: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
        """시장별 데이터 분리"""
        nasdaq_data = {}
        nyse_data = {}

        for symbol, df in market_data.items():
            if 'NASDAQ' in symbol:
                nasdaq_data[symbol] = df
            elif 'NYSE' in symbol:
                nyse_data[symbol] = df
            else:
                # 시장 정보가 없으면 심볼로 추정
                symbol_only = symbol.split('_')[0] if '_' in symbol else symbol
                if symbol_only in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']:
                    nasdaq_data[symbol] = df
                else:
                    nyse_data[symbol] = df

        self._log(f"[Strategy Agent] NASDAQ: {len(nasdaq_data)}개, NYSE: {len(nyse_data)}개 종목 분리")
        return nasdaq_data, nyse_data

    def _generate_nasdaq_signals(self, nasdaq_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """NASDAQ 전용 신호 생성 (성장주/기술주 전략)"""
        self._log(f"[Strategy Agent] NASDAQ 신호 생성 시작 ({len(nasdaq_data)}개 종목)")

        signals = {}
        params = self.strategy_params['NASDAQ']

        for symbol, df in nasdaq_data.items():
            try:
                self._log(f"[Strategy Agent] {symbol} NASDAQ 신호 생성 중...")

                buy_signals = []
                sell_signals = []

                # 필수 지표 확인
                if not self._has_required_indicators(df, ['MA5', 'MA20', 'RSI', 'Volume_Ratio']):
                    self._log(f"[Strategy Agent] {symbol}: 필수 지표 부족")
                    continue

                for i in range(1, len(df)):
                    date = df.index[i]
                    current_price = df.iloc[i]['Close']

                    # NASDAQ 성장주 매수 신호
                    if self._nasdaq_buy_condition(df, i, params):
                        buy_signals.append({
                            'date': date,
                            'price': current_price,
                            'signal': 'NASDAQ_GROWTH_BUY',
                            'confidence': self._calculate_signal_confidence(df, i, 'buy', 'NASDAQ')
                        })

                    # NASDAQ 성장주 매도 신호
                    elif self._nasdaq_sell_condition(df, i, params):
                        sell_signals.append({
                            'date': date,
                            'price': current_price,
                            'signal': 'NASDAQ_GROWTH_SELL',
                            'confidence': self._calculate_signal_confidence(df, i, 'sell', 'NASDAQ')
                        })

                signals[symbol] = {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'market': 'NASDAQ',
                    'strategy': 'growth'
                }

                self._log(f"[Strategy Agent] {symbol}: 매수 {len(buy_signals)}개, 매도 {len(sell_signals)}개")

            except Exception as e:
                self._log(f"[Strategy Agent] {symbol} NASDAQ 신호 생성 실패: {e}")
                signals[symbol] = {'buy_signals': [], 'sell_signals': [], 'market': 'NASDAQ', 'strategy': 'growth'}

        return signals

    def _generate_nyse_signals(self, nyse_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """NYSE 전용 신호 생성 (대형주/가치주 전략)"""
        self._log(f"[Strategy Agent] NYSE 신호 생성 시작 ({len(nyse_data)}개 종목)")

        signals = {}
        params = self.strategy_params['NYSE']

        for symbol, df in nyse_data.items():
            try:
                self._log(f"[Strategy Agent] {symbol} NYSE 신호 생성 중...")

                buy_signals = []
                sell_signals = []

                # 필수 지표 확인
                if not self._has_required_indicators(df, ['MA10', 'MA50', 'RSI', 'Volume_Ratio']):
                    self._log(f"[Strategy Agent] {symbol}: 필수 지표 부족")
                    continue

                for i in range(1, len(df)):
                    date = df.index[i]
                    current_price = df.iloc[i]['Close']

                    # NYSE 가치주 매수 신호
                    if self._nyse_buy_condition(df, i, params):
                        buy_signals.append({
                            'date': date,
                            'price': current_price,
                            'signal': 'NYSE_VALUE_BUY',
                            'confidence': self._calculate_signal_confidence(df, i, 'buy', 'NYSE')
                        })

                    # NYSE 가치주 매도 신호
                    elif self._nyse_sell_condition(df, i, params):
                        sell_signals.append({
                            'date': date,
                            'price': current_price,
                            'signal': 'NYSE_VALUE_SELL',
                            'confidence': self._calculate_signal_confidence(df, i, 'sell', 'NYSE')
                        })

                signals[symbol] = {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'market': 'NYSE',
                    'strategy': 'value'
                }

                self._log(f"[Strategy Agent] {symbol}: 매수 {len(buy_signals)}개, 매도 {len(sell_signals)}개")

            except Exception as e:
                self._log(f"[Strategy Agent] {symbol} NYSE 신호 생성 실패: {e}")
                signals[symbol] = {'buy_signals': [], 'sell_signals': [], 'market': 'NYSE', 'strategy': 'value'}

        return signals

    def _nasdaq_buy_condition(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """NASDAQ 매수 조건 (성장주 전략)"""
        try:
            current = df.iloc[i]
            previous = df.iloc[i-1]

            # 1. 골든 크로스 (빠른 MA가 느린 MA 돌파)
            golden_cross = (current['MA5'] > current['MA20'] and previous['MA5'] <= previous['MA20'])

            # 2. RSI 과매도 구간에서 반등
            rsi_condition = (current['RSI'] > params['rsi_oversold'] and
                           previous['RSI'] <= params['rsi_oversold'])

            # 3. 거래량 급증
            volume_surge = current['Volume_Ratio'] > params['volume_threshold']

            # 4. 가격 모멘텀 (기술주 특성)
            if 'Price_Momentum' in current:
                momentum_positive = current['Price_Momentum'] > 0

                # 모든 조건 중 3개 이상 만족
                conditions = [golden_cross, rsi_condition, volume_surge, momentum_positive]
                return sum(conditions) >= 3

            # Price_Momentum이 없으면 3개 조건 중 2개 이상
            conditions = [golden_cross, rsi_condition, volume_surge]
            return sum(conditions) >= 2

        except (KeyError, IndexError):
            return False

    def _nasdaq_sell_condition(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """NASDAQ 매도 조건 (성장주 전략)"""
        try:
            current = df.iloc[i]
            previous = df.iloc[i-1]

            # 1. 데드 크로스 (빠른 MA가 느린 MA 하향 돌파)
            dead_cross = (current['MA5'] < current['MA20'] and previous['MA5'] >= previous['MA20'])

            # 2. RSI 과매수 구간에서 하락
            rsi_condition = (current['RSI'] < params['rsi_overbought'] and
                           previous['RSI'] >= params['rsi_overbought'])

            # 3. 볼링거 밴드 상단 이탈
            if 'BB_Upper' in current and 'BB_Lower' in current:
                bb_condition = (current['Close'] < current['BB_Upper'] and
                              previous['Close'] >= current['BB_Upper'])
            else:
                bb_condition = False

            # 4. 가격 모멘텀 하락 (기술주 특성)
            if 'Price_Momentum' in current:
                momentum_negative = current['Price_Momentum'] < -0.05  # 5% 이상 하락 모멘텀

                conditions = [dead_cross, rsi_condition, bb_condition, momentum_negative]
                return sum(conditions) >= 2

            conditions = [dead_cross, rsi_condition, bb_condition]
            return sum(conditions) >= 2

        except (KeyError, IndexError):
            return False

    def _nyse_buy_condition(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """NYSE 매수 조건 (가치주 전략)"""
        try:
            current = df.iloc[i]
            previous = df.iloc[i-1]

            # 1. 중장기 골든 크로스 (10일선이 50일선 돌파)
            golden_cross = (current['MA10'] > current['MA50'] and previous['MA10'] <= previous['MA50'])

            # 2. RSI 보수적 진입 (가치주 특성)
            rsi_condition = (params['rsi_oversold'] < current['RSI'] < 60)

            # 3. 안정적인 거래량 증가
            volume_condition = (current['Volume_Ratio'] > params['volume_threshold'] and
                              current['Volume_Ratio'] < 3.0)  # 과도한 급등 방지

            # 4. 가격 안정성 (가치주 특성)
            if 'Price_Stability' in current:
                stability_condition = current['Price_Stability'] < 0.03  # 3% 미만 변동성

                conditions = [golden_cross, rsi_condition, volume_condition, stability_condition]
                return sum(conditions) >= 3

            conditions = [golden_cross, rsi_condition, volume_condition]
            return sum(conditions) >= 2

        except (KeyError, IndexError):
            return False

    def _nyse_sell_condition(self, df: pd.DataFrame, i: int, params: Dict[str, Any]) -> bool:
        """NYSE 매도 조건 (가치주 전략)"""
        try:
            current = df.iloc[i]
            previous = df.iloc[i-1]

            # 1. 중장기 데드 크로스
            dead_cross = (current['MA10'] < current['MA50'] and previous['MA10'] >= previous['MA50'])

            # 2. RSI 과매수 구간
            rsi_condition = current['RSI'] > params['rsi_overbought']

            # 3. MACD 하락 전환
            if 'MACD' in current and 'MACD_Signal' in current:
                macd_condition = (current['MACD'] < current['MACD_Signal'] and
                                previous['MACD'] >= previous['MACD_Signal'])
            else:
                macd_condition = False

            # 4. 장기 추세 약화
            if 'MA200' in current:
                trend_condition = current['Close'] < current['MA200']
            else:
                trend_condition = False

            conditions = [dead_cross, rsi_condition, macd_condition, trend_condition]
            return sum(conditions) >= 2

        except (KeyError, IndexError):
            return False

    def _has_required_indicators(self, df: pd.DataFrame, required: List[str]) -> bool:
        """필수 지표 존재 확인"""
        return all(indicator in df.columns for indicator in required)

    def _calculate_signal_confidence(self, df: pd.DataFrame, i: int, signal_type: str, market: str) -> float:
        """신호 확신도 계산 (0.0 ~ 1.0)"""
        try:
            current = df.iloc[i]
            confidence_factors = []

            # RSI 기반 확신도
            if 'RSI' in current:
                if signal_type == 'buy':
                    # RSI가 30에 가까울수록 확신도 높음
                    rsi_confidence = max(0, (50 - current['RSI']) / 20)
                else:
                    # RSI가 70에 가까울수록 확신도 높음
                    rsi_confidence = max(0, (current['RSI'] - 50) / 20)
                confidence_factors.append(min(1.0, rsi_confidence))

            # 거래량 기반 확신도
            if 'Volume_Ratio' in current:
                volume_confidence = min(1.0, (current['Volume_Ratio'] - 1) / 2)
                confidence_factors.append(max(0.0, volume_confidence))

            # 시장별 특수 확신도
            if market == 'NASDAQ' and 'Price_Momentum' in current:
                if signal_type == 'buy':
                    momentum_confidence = max(0, min(1.0, current['Price_Momentum'] * 10))
                else:
                    momentum_confidence = max(0, min(1.0, -current['Price_Momentum'] * 10))
                confidence_factors.append(momentum_confidence)

            # 평균 확신도 계산
            if confidence_factors:
                return sum(confidence_factors) / len(confidence_factors)
            else:
                return 0.5  # 기본값

        except (KeyError, IndexError):
            return 0.5

    def _optimize_portfolio_signals(self, signals: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """포트폴리오 레벨 신호 최적화"""
        self._log("[Strategy Agent] 포트폴리오 레벨 신호 최적화 시작")

        # 상관관계 분석
        correlation_matrix = self._calculate_correlation_matrix(market_data)

        # 신호 타이밍 최적화
        optimized_signals = self._optimize_signal_timing(signals, correlation_matrix)

        # 포지션 크기 제안
        position_suggestions = self._suggest_position_sizes(optimized_signals, market_data)

        # 최적화 결과 추가
        for symbol in optimized_signals:
            optimized_signals[symbol]['position_suggestion'] = position_suggestions.get(symbol, 1.0)
            optimized_signals[symbol]['correlation_risk'] = self._assess_correlation_risk(symbol, correlation_matrix)

        self._log("[Strategy Agent] 포트폴리오 최적화 완료")
        return optimized_signals

    def _calculate_correlation_matrix(self, market_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """종목간 상관관계 계산"""
        try:
            # 수익률 계산
            returns_data = {}
            for symbol, df in market_data.items():
                if 'Daily_Return' in df.columns:
                    returns_data[symbol] = df['Daily_Return'].dropna()

            if returns_data:
                returns_df = pd.DataFrame(returns_data)
                return returns_df.corr()
            else:
                return pd.DataFrame()

        except Exception as e:
            self._log(f"[Strategy Agent] 상관관계 계산 실패: {e}")
            return pd.DataFrame()

    def _optimize_signal_timing(self, signals: Dict[str, Any], correlation_matrix: pd.DataFrame) -> Dict[str, Any]:
        """신호 타이밍 최적화"""
        # 현재는 단순히 원본 반환 (향후 고도화 가능)
        return signals

    def _suggest_position_sizes(self, signals: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """포지션 크기 제안"""
        position_suggestions = {}

        for symbol in signals:
            # 기본 포지션 크기
            base_size = 1.0

            # 시장별 조정
            if signals[symbol].get('market') == 'NASDAQ':
                base_size *= 0.8  # NASDAQ은 변동성이 높으므로 작게
            elif signals[symbol].get('market') == 'NYSE':
                base_size *= 1.2  # NYSE는 안정적이므로 크게

            # 변동성 기반 조정
            if symbol in market_data and 'ATR' in market_data[symbol].columns:
                recent_atr = market_data[symbol]['ATR'].iloc[-1]
                if recent_atr > 0:
                    # ATR이 높으면 포지션 크기 감소
                    volatility_adjustment = 1 / (1 + recent_atr * 10)
                    base_size *= volatility_adjustment

            position_suggestions[symbol] = max(0.1, min(2.0, base_size))

        return position_suggestions

    def _assess_correlation_risk(self, symbol: str, correlation_matrix: pd.DataFrame) -> float:
        """상관관계 위험도 평가"""
        try:
            if symbol in correlation_matrix.columns:
                # 다른 종목들과의 평균 상관관계
                correlations = correlation_matrix[symbol].drop(symbol)
                avg_correlation = abs(correlations).mean()
                return min(1.0, avg_correlation)
            else:
                return 0.5  # 정보 없으면 중간값

        except Exception:
            return 0.5

    def _validate_signals(self, signals: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """신호 품질 검증"""
        self._log("[Strategy Agent] 신호 품질 검증 시작")

        validated_signals = {}

        for symbol, signal_data in signals.items():
            try:
                # 기본 구조 확인
                if not isinstance(signal_data, dict):
                    continue

                buy_signals = signal_data.get('buy_signals', [])
                sell_signals = signal_data.get('sell_signals', [])

                # 신호 수 검증
                if len(buy_signals) == 0 and len(sell_signals) == 0:
                    self._log(f"[Strategy Agent] {symbol}: 신호 없음 - 제외")
                    continue

                # 신호 밸런스 확인
                signal_imbalance = abs(len(buy_signals) - len(sell_signals)) / max(len(buy_signals) + len(sell_signals), 1)
                if signal_imbalance > 0.8:  # 80% 이상 불균형
                    self._log(f"[Strategy Agent] {symbol}: 신호 불균형 ({signal_imbalance:.1%}) - 경고")

                # 확신도 검증
                if buy_signals:
                    avg_buy_confidence = np.mean([s.get('confidence', 0.5) for s in buy_signals])
                    if avg_buy_confidence < 0.3:
                        self._log(f"[Strategy Agent] {symbol}: 매수 신호 확신도 낮음 ({avg_buy_confidence:.2f})")

                if sell_signals:
                    avg_sell_confidence = np.mean([s.get('confidence', 0.5) for s in sell_signals])
                    if avg_sell_confidence < 0.3:
                        self._log(f"[Strategy Agent] {symbol}: 매도 신호 확신도 낮음 ({avg_sell_confidence:.2f})")

                validated_signals[symbol] = signal_data
                self._log(f"[Strategy Agent] {symbol}: 품질 검증 통과")

            except Exception as e:
                self._log(f"[Strategy Agent] {symbol} 검증 실패: {e}")

        self._log(f"[Strategy Agent] 신호 검증 완료: {len(validated_signals)}/{len(signals)} 종목 통과")
        return validated_signals

    def _log_signal_summary(self, signals: Dict[str, Any]):
        """신호 요약 로그"""
        total_buy = sum(len(s.get('buy_signals', [])) for s in signals.values())
        total_sell = sum(len(s.get('sell_signals', [])) for s in signals.values())

        nasdaq_symbols = [k for k, v in signals.items() if v.get('market') == 'NASDAQ']
        nyse_symbols = [k for k, v in signals.items() if v.get('market') == 'NYSE']

        self._log("="*60)
        self._log("[Strategy Agent] 신호 생성 요약")
        self._log(f"[신호 통계] 총 매수 신호: {total_buy}개")
        self._log(f"[신호 통계] 총 매도 신호: {total_sell}개")
        self._log(f"[시장 분포] NASDAQ: {len(nasdaq_symbols)}개 종목")
        self._log(f"[시장 분포] NYSE: {len(nyse_symbols)}개 종목")
        self._log("="*60)

    def get_strategy_performance(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """전략 성과 요약"""
        performance = {
            'total_symbols': len(signals),
            'total_signals': sum(len(s.get('buy_signals', [])) + len(s.get('sell_signals', []))
                               for s in signals.values()),
            'market_breakdown': {
                'NASDAQ': len([s for s in signals.values() if s.get('market') == 'NASDAQ']),
                'NYSE': len([s for s in signals.values() if s.get('market') == 'NYSE'])
            },
            'avg_confidence': {
                'buy': np.mean([s.get('confidence', 0.5)
                              for signals_data in signals.values()
                              for s in signals_data.get('buy_signals', [])]),
                'sell': np.mean([s.get('confidence', 0.5)
                               for signals_data in signals.values()
                               for s in signals_data.get('sell_signals', [])])
            }
        }
        return performance

    def _log(self, message: str):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)

    def get_execution_log(self) -> List[str]:
        """실행 로그 반환"""
        return self.execution_log.copy()