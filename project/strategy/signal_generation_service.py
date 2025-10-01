#!/usr/bin/env python3
"""
Signal Generation Service - Strategy Layer
Based on refer/Strategy/Strategy_A.py
Implements trend-following signal generation with multi-timeframe analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal types for trading decisions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class BreakoutType(Enum):
    """Breakout timeframe types"""
    BREAKOUT_2Y = "Breakout_2Y"
    BREAKOUT_1Y = "Breakout_1Y"
    BREAKOUT_6M = "Breakout_6M"
    BREAKOUT_3M = "Breakout_3M"
    BREAKOUT_1M = "Breakout_1M"
    RS_12W_1M = "RS_12W_1M"

class SignalGenerationService:
    """
    추세추종 신호 생성 서비스
    다중 타임프레임 분석을 통한 매매 신호 생성
    """

    def __init__(self, area: str = 'US', trading_mode: bool = False):
        self.area = area
        self.trading_mode = trading_mode
        self.signals_cache = {}

    def generate_comprehensive_signals(self,
                                     df_daily: pd.DataFrame,
                                     df_weekly: pd.DataFrame = None,
                                     df_rs: pd.DataFrame = None,
                                     df_fundamental: pd.DataFrame = None,
                                     df_earnings: pd.DataFrame = None) -> Dict[str, Any]:
        """
        종합적인 매매 신호 생성
        Strategy_A.py의 메인 로직 구현

        Args:
            df_daily: 일봉 데이터
            df_weekly: 주봉 데이터 (선택)
            df_rs: RS 데이터 (선택)
            df_fundamental: 펀더멘털 데이터 (선택)
            df_earnings: 어닝스 데이터 (선택)

        Returns:
            종합 신호 정보 딕셔너리
        """
        try:
            signals = {
                'final_signal': SignalType.HOLD,
                'signal_strength': 0.0,
                'signal_components': {},
                'target_price': 0.0,
                'losscut_price': 0.0,
                'signal_type': None,
                'confidence': 0.0
            }

            # 1. 주봉 신호 생성
            weekly_signal = self._generate_weekly_signals(df_weekly) if df_weekly is not None else 0
            signals['signal_components']['weekly'] = weekly_signal

            # 2. RS 신호 생성
            rs_signal = self._generate_rs_signals(df_rs) if df_rs is not None else 0
            signals['signal_components']['rs'] = rs_signal

            # 3. 펀더멘털 신호 생성
            fundamental_signal = self._generate_fundamental_signals(df_fundamental) if df_fundamental is not None else 0
            signals['signal_components']['fundamental'] = fundamental_signal

            # 4. 어닝스 신호 생성
            earnings_signal = self._generate_earnings_signals(df_earnings) if df_earnings is not None else 0
            signals['signal_components']['earnings'] = earnings_signal

            # 5. 일봉 + RS 결합 신호 생성 (핵심)
            daily_rs_result = self._generate_daily_rs_combined_signals(df_daily, df_rs)
            signals['signal_components']['daily_rs'] = daily_rs_result['signal']
            signals['target_price'] = daily_rs_result['target_price']
            signals['losscut_price'] = daily_rs_result['losscut_price']
            signals['signal_type'] = daily_rs_result['signal_type']

            # 6. 최종 신호 결합
            final_result = self._combine_signals(signals['signal_components'])
            signals['final_signal'] = final_result['signal']
            signals['signal_strength'] = final_result['strength']
            signals['confidence'] = final_result['confidence']

            return signals

        except Exception as e:
            logger.error(f"Error generating comprehensive signals: {e}")
            return self._get_default_signals()

    def _generate_weekly_signals(self, df_weekly: pd.DataFrame) -> int:
        """
        주봉 신호 생성 - refer Strategy_A.py lines 99-105와 완전 동일한 로직
        """
        try:
            if df_weekly.empty or len(df_weekly) < 3:  # shift(2) 때문에 최소 3개 필요
                return 0

            latest = df_weekly.iloc[-1]

            # 이전 데이터들
            if len(df_weekly) >= 2:
                prev_1 = df_weekly.iloc[-2]
            else:
                return 0

            if len(df_weekly) >= 3:
                prev_2 = df_weekly.iloc[-3]
            else:
                return 0

            # refer Strategy_A.py lines 99-103: 정확한 조건들
            # wCondition1 = 1Year_H == 2Year_H
            w_condition1 = latest.get('1Year_H', 0) == latest.get('2Year_H', 0)

            # wCondition2 = 2Year_L < 1Year_L
            w_condition2 = latest.get('2Year_L', 0) < latest.get('1Year_L', 0)

            # wCondition3 = 52_H <= 52_H.shift(2) * 1.05
            w_condition3 = latest.get('52_H', 0) <= prev_2.get('52_H', 0) * 1.05

            # wCondition4 = Wclose.shift(1) > 52_L * 1.3
            w_condition4 = prev_1.get('Wclose', 0) > latest.get('52_L', 0) * 1.3

            # wCondition5 = Wclose.shift(1) > 52_H * 0.7
            w_condition5 = prev_1.get('Wclose', 0) > latest.get('52_H', 0) * 0.7

            # refer line 105: 모든 조건을 AND로 결합
            if w_condition1 and w_condition2 and w_condition3 and w_condition4 and w_condition5:
                return 1

            return 0

        except Exception as e:
            logger.error(f"Error in weekly signal generation: {e}")
            return 0

    def _generate_rs_signals(self, df_rs: pd.DataFrame) -> int:
        """
        RS 신호 생성
        """
        try:
            if df_rs.empty:
                return 0

            latest = df_rs.iloc[-1]
            rs_4w = latest.get('RS_4W', 0)

            # RS >= 90 조건
            if rs_4w >= 90:
                return 1

            return 0

        except Exception as e:
            logger.error(f"Error in RS signal generation: {e}")
            return 0

    def _generate_fundamental_signals(self, df_fundamental: pd.DataFrame) -> int:
        """
        펀더멘털 신호 생성
        Strategy_A.py의 generate_signals_F 로직
        """
        try:
            if df_fundamental.empty:
                return 0

            latest = df_fundamental.iloc[-1]

            if self.area == 'KR':
                # 한국 시장 조건
                market_cap = latest.get('capital', 0)
                eps = latest.get('eps', 0)

                condition1 = market_cap >= 100000000000  # 시가총액 > 1000억
                condition2 = market_cap <= 20000000000000  # 시가총액 < 20조
                condition3 = eps > 0

                if all([condition1, condition2, condition3]):
                    return 1

            else:
                # 미국 시장 조건 - refer Strategy_A.py line 184와 동일한 조건
                market_cap = latest.get('MarketCapitalization', 0)
                rev_yoy = latest.get('REV_YOY', 0)
                eps_yoy = latest.get('EPS_YOY', 0)
                revenue = latest.get('revenue', 0)

                # 이전 데이터가 있는지 확인
                if len(df_fundamental) >= 2:
                    prev = df_fundamental.iloc[-2]
                    prev_rev_yoy = prev.get('REV_YOY', 0)
                    prev_eps_yoy = prev.get('EPS_YOY', 0)
                else:
                    prev_rev_yoy = 0
                    prev_eps_yoy = 0

                # refer와 동일한 조건식
                f_condition1 = market_cap >= 2000000000  # 시가총액 > 20억USD
                f_condition2 = market_cap <= 20000000000000  # 시가총액 < 20조USD
                f_condition3 = rev_yoy >= 0.1  # 매출 YoY >= 10%
                f_condition4 = prev_rev_yoy >= 0  # 전기 매출 YoY >= 0%
                f_condition6 = eps_yoy >= 0.1  # EPS YoY >= 10%
                f_condition7 = prev_eps_yoy >= 0  # 전기 EPS YoY >= 0%
                f_condition9 = revenue > 0  # 매출 > 0

                # refer line 184: (매출 성장 조건) OR (EPS 성장 조건)
                if f_condition1 and ((f_condition3 and f_condition4) or (f_condition6 and f_condition7)) and f_condition9:
                    return 1

            return 0

        except Exception as e:
            logger.error(f"Error in fundamental signal generation: {e}")
            return 0

    def _generate_earnings_signals(self, df_earnings: pd.DataFrame) -> int:
        """
        어닝스 신호 생성
        Strategy_A.py의 generate_signals_E 로직
        """
        try:
            if df_earnings.empty or len(df_earnings) < 2:
                return 0

            latest = df_earnings.iloc[-1]
            previous = df_earnings.iloc[-2]

            # 매출 성장 조건
            rev_condition1 = previous.get('rev_yoy', 0) >= 0
            rev_condition2 = latest.get('rev_yoy', 0) > previous.get('rev_yoy', 0)

            # EPS 성장 조건
            eps_condition1 = previous.get('eps_yoy', 0) >= 0
            eps_condition2 = latest.get('eps_yoy', 0) > previous.get('eps_yoy', 0)

            # 둘 중 하나라도 성장하면 매수 신호
            if (rev_condition1 and rev_condition2) or (eps_condition1 and eps_condition2):
                return 1

            return 0

        except Exception as e:
            logger.error(f"Error in earnings signal generation: {e}")
            return 0

    def _generate_daily_rs_combined_signals(self, df_daily: pd.DataFrame, df_rs: pd.DataFrame = None) -> Dict[str, Any]:
        """
        일봉 + RS 결합 신호 생성 (Strategy_A.py의 핵심 로직)
        다양한 타임프레임 브레이크아웃 감지
        """
        try:
            if df_daily.empty:
                return {'signal': 0, 'target_price': 0.0, 'losscut_price': 0.0, 'signal_type': None}

            latest = df_daily.iloc[-1]

            # RS 조건
            rs_condition = 0
            if df_rs is not None and not df_rs.empty:
                rs_latest = df_rs.iloc[-1]
                rs_4w = rs_latest.get('RS_4W', 0)
                rs_12w = rs_latest.get('RS_12W', 0)
                rs_condition = 1 if rs_4w >= 90 else 0
                rs_12w_condition = 1 if rs_12w >= 90 else 0
            else:
                rs_12w_condition = 0

            # 일봉 기본 조건
            sma200_momentum = latest.get('SMA200_M', 0) > 0
            sma_condition = latest.get('SMA200', 0) < latest.get('SMA50', 0)
            highest_1m_condition = latest.get('Highest_1M', 0) != latest.get('Dhigh', 0)

            # 기본 조건 결합
            base_conditions = sma200_momentum and sma_condition and rs_condition

            if not base_conditions and not rs_12w_condition:
                return {'signal': 0, 'target_price': 0.0, 'losscut_price': 0.0, 'signal_type': None}

            # 브레이크아웃 조건들 체크
            current_high = latest.get('Dhigh', 0)
            timeframes = ['2Y', '1Y', '6M', '3M', '1M']

            signal_result = {'signal': 0, 'target_price': 0.0, 'losscut_price': 0.0, 'signal_type': None}

            for timeframe in timeframes:
                highest_col = f'Highest_{timeframe}'
                highest_value = latest.get(highest_col, 0)

                if highest_value == 0:
                    continue

                # 브레이크아웃 조건
                if self.trading_mode:
                    breakout_condition = highest_value > current_high
                else:
                    breakout_condition = highest_value <= current_high

                # 안정성 조건 (5일간 동일한 최고가 유지)
                # 여기서는 단순화하여 현재 조건만 체크
                stability_condition = True

                if base_conditions and breakout_condition and stability_condition:
                    signal_result = {
                        'signal': 1,
                        'target_price': float(highest_value),
                        'losscut_price': float(highest_value * 0.97),
                        'signal_type': f'Breakout_{timeframe}'
                    }
                    break

            # RS_12W + 1M 조건 추가 체크
            if signal_result['signal'] == 0 and rs_12w_condition:
                highest_1m = latest.get('Highest_1M', 0)
                if self.trading_mode:
                    condition_1m = highest_1m > current_high
                else:
                    condition_1m = highest_1m <= current_high

                if condition_1m and highest_1m > 0:
                    signal_result = {
                        'signal': 1,
                        'target_price': float(highest_1m),
                        'losscut_price': float(highest_1m * 0.97),
                        'signal_type': 'RS_12W_1M'
                    }

            return signal_result

        except Exception as e:
            logger.error(f"Error in daily RS combined signal generation: {e}")
            return {'signal': 0, 'target_price': 0.0, 'losscut_price': 0.0, 'signal_type': None}

    def _combine_signals(self, signal_components: Dict[str, Any]) -> Dict[str, Any]:
        """
        개별 신호들을 결합하여 최종 신호 생성
        Strategy_A.py의 generate_signals 로직
        """
        try:
            weekly_signal = signal_components.get('weekly', 0)
            daily_rs_signal = signal_components.get('daily_rs', 0)
            rs_signal = signal_components.get('rs', 0)
            fundamental_signal = signal_components.get('fundamental', 0)
            earnings_signal = signal_components.get('earnings', 0)

            # 최종 매수 조건
            if self.area == 'US':
                buy_condition = (weekly_signal == 1 and
                               daily_rs_signal == 1 and
                               rs_signal == 1 and
                               fundamental_signal == 1)
            else:
                buy_condition = (weekly_signal == 1 and
                               daily_rs_signal == 1 and
                               rs_signal == 1)

            # 신호 강도 계산
            total_signals = sum([weekly_signal, daily_rs_signal, rs_signal, fundamental_signal, earnings_signal])
            max_signals = 5 if self.area == 'US' else 3
            signal_strength = total_signals / max_signals

            # 신뢰도 계산
            confidence = 0.7 if buy_condition else signal_strength * 0.5

            final_signal = SignalType.BUY if buy_condition else SignalType.HOLD

            return {
                'signal': final_signal,
                'strength': signal_strength,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {'signal': SignalType.HOLD, 'strength': 0.0, 'confidence': 0.0}

    def generate_sell_signals(self, df_daily: pd.DataFrame) -> Dict[str, Any]:
        """
        매도 신호 생성
        """
        try:
            if df_daily.empty:
                return {'signal': SignalType.HOLD, 'reason': None}

            latest = df_daily.iloc[-1]

            # 매도 조건: 종가가 SMA20 아래로 떨어질 때
            close_price = latest.get('Dclose', 0)
            sma20 = latest.get('SMA20', 0)

            if close_price > 0 and sma20 > 0 and close_price < sma20:
                return {
                    'signal': SignalType.SELL,
                    'reason': 'Price below SMA20',
                    'close_price': close_price,
                    'sma20': sma20
                }

            return {'signal': SignalType.HOLD, 'reason': None}

        except Exception as e:
            logger.error(f"Error generating sell signals: {e}")
            return {'signal': SignalType.HOLD, 'reason': f'Error: {e}'}

    def calculate_signal_strength(self, signal_data: Dict[str, Any]) -> float:
        """
        신호 강도 계산 (Strategy_A.py의 _calculate_signal_strength 로직)
        """
        try:
            strength = 0.0
            weight_sum = 0.0

            components = signal_data.get('signal_components', {})

            # 기술적 신호 구성요소 (40% 가중치)
            if components.get('weekly', 0) == 1:
                strength += 0.1
                weight_sum += 0.1

            if components.get('daily_rs', 0) == 1:
                strength += 0.15
                weight_sum += 0.15

            if components.get('rs', 0) == 1:
                strength += 0.15
                weight_sum += 0.15

            # 펀더멘털 구성요소 (30% 가중치)
            if components.get('fundamental', 0) == 1:
                strength += 0.15
                weight_sum += 0.15

            if components.get('earnings', 0) == 1:
                strength += 0.15
                weight_sum += 0.15

            # RS 강도 구성요소 (20% 가중치)
            rs_value = signal_data.get('rs_value', 0)
            if rs_value > 0:
                rs_strength = min(rs_value / 100.0, 1.0)
                strength += rs_strength * 0.2
                weight_sum += 0.2

            # 브레이크아웃 강도 구성요소 (10% 가중치)
            target_price = signal_data.get('target_price', 0)
            current_price = signal_data.get('current_price', 0)
            if target_price > 0 and current_price > 0:
                breakout_ratio = current_price / target_price
                if breakout_ratio >= 1.0:
                    strength += 0.1
                    weight_sum += 0.1

            # 정규화
            final_strength = strength / weight_sum if weight_sum > 0 else 0.0
            return min(max(final_strength, 0.0), 1.0)

        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 0.5

    def _get_default_signals(self) -> Dict[str, Any]:
        """기본 신호 반환"""
        return {
            'final_signal': SignalType.HOLD,
            'signal_strength': 0.0,
            'signal_components': {},
            'target_price': 0.0,
            'losscut_price': 0.0,
            'signal_type': None,
            'confidence': 0.0
        }

# 사용 예시 및 테스트를 위한 헬퍼 함수들
def create_sample_data() -> Dict[str, pd.DataFrame]:
    """테스트용 샘플 데이터 생성"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    # 샘플 일봉 데이터
    df_daily = pd.DataFrame({
        'Dhigh': np.random.uniform(100, 120, 100),
        'Dclose': np.random.uniform(95, 115, 100),
        'SMA20': np.random.uniform(90, 110, 100),
        'SMA50': np.random.uniform(85, 105, 100),
        'SMA200': np.random.uniform(80, 100, 100),
        'SMA200_M': np.random.uniform(-5, 5, 100),
        'Highest_1M': np.random.uniform(105, 125, 100),
        'Highest_3M': np.random.uniform(110, 130, 100),
        'Highest_6M': np.random.uniform(115, 135, 100),
        'Highest_1Y': np.random.uniform(120, 140, 100),
        'Highest_2Y': np.random.uniform(125, 145, 100),
    }, index=dates)

    # 샘플 RS 데이터
    df_rs = pd.DataFrame({
        'RS_4W': np.random.uniform(70, 95, 100),
        'RS_12W': np.random.uniform(75, 95, 100),
    }, index=dates)

    return {'daily': df_daily, 'rs': df_rs}

if __name__ == "__main__":
    # 테스트 실행
    service = SignalGenerationService(area='US', trading_mode=False)
    sample_data = create_sample_data()

    signals = service.generate_comprehensive_signals(
        df_daily=sample_data['daily'],
        df_rs=sample_data['rs']
    )

    print("Signal Generation Service Test Results:")
    print(f"Final Signal: {signals['final_signal']}")
    print(f"Signal Strength: {signals['signal_strength']:.3f}")
    print(f"Target Price: {signals['target_price']:.2f}")
    print(f"Loss Cut Price: {signals['losscut_price']:.2f}")
    print(f"Signal Type: {signals['signal_type']}")
    print(f"Confidence: {signals['confidence']:.3f}")