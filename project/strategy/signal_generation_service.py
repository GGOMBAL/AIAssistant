#!/usr/bin/env python3
"""
Signal Generation Service - Strategy Layer
Based on refer/Strategy/Strategy_A.py
Implements trend-following signal generation with multi-timeframe analysis

Updated: 2025-10-13 - 설정 파일 기반 시그널 생성 지원
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import logging

# Import config loader
try:
    from project.strategy.signal_config_loader import SignalConfigLoader
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    CONFIG_LOADER_AVAILABLE = False
    logger.warning("SignalConfigLoader not available - using hardcoded values")

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

    Updated: 설정 파일 기반 시그널 조건 지원
    """

    def __init__(self, area: str = 'US', trading_mode: bool = False, config_path: Optional[str] = None):
        """
        Initialize SignalGenerationService

        Args:
            area: 시장 지역 (US, KR 등)
            trading_mode: 트레이딩 모드 여부
            config_path: 시그널 설정 파일 경로 (None이면 기본 경로 사용)
        """
        self.area = area
        self.trading_mode = trading_mode
        self.signals_cache = {}

        # 설정 로더 초기화
        if CONFIG_LOADER_AVAILABLE:
            try:
                self.config_loader = SignalConfigLoader(config_path)
                self.use_config = True
                logger.info("SignalConfigLoader initialized successfully")
                self.config_loader.print_summary()
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using default values.")
                self.config_loader = None
                self.use_config = False
        else:
            self.config_loader = None
            self.use_config = False
            logger.info("Using hardcoded signal conditions")

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

        Note:
            데이터 타입별 사용 시점:
            - RS, D (일봉): iloc[-2] (T-1, 전날 데이터) - 당일 종가는 장 마감 후 확정
            - W, F, E (주봉, 펀더멘털, 어닝스): iloc[-1] (T, 최신 데이터) - 이미 확정된 과거 데이터
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

    def generate_signals_timeseries(self,
                                   df_daily: pd.DataFrame,
                                   df_weekly: pd.DataFrame = None,
                                   df_rs: pd.DataFrame = None,
                                   df_fundamental: pd.DataFrame = None,
                                   df_earnings: pd.DataFrame = None,
                                   start_date: str = None,
                                   end_date: str = None) -> pd.DataFrame:
        """
        백테스트용 시계열 신호 생성
        전체 기간에 대해 일별 신호를 생성하여 DataFrame으로 반환

        Args:
            df_daily: 일봉 데이터
            df_weekly: 주봉 데이터 (선택)
            df_rs: RS 데이터 (선택)
            df_fundamental: 펀더멘털 데이터 (선택)
            df_earnings: 어닝스 데이터 (선택)
            start_date: 시작 날짜 (YYYY-MM-DD), None이면 데이터 시작부터
            end_date: 종료 날짜 (YYYY-MM-DD), None이면 데이터 끝까지

        Returns:
            시계열 신호 DataFrame
            Columns: ['Date', 'signal', 'signal_strength', 'confidence',
                     'target_price', 'losscut_price', 'signal_type',
                     'weekly_signal', 'rs_signal', 'fundamental_signal',
                     'earnings_signal', 'daily_rs_signal']
        """
        try:
            if df_daily is None or df_daily.empty:
                logger.warning("Daily dataframe is empty")
                return pd.DataFrame()

            # 날짜 인덱스 확인
            if 'Date' in df_daily.columns:
                dates = df_daily['Date']
            elif isinstance(df_daily.index, pd.DatetimeIndex):
                dates = df_daily.index
            else:
                logger.error("Cannot find date column in daily dataframe")
                return pd.DataFrame()

            # 시작/종료 날짜 필터링
            if start_date:
                start_dt = pd.to_datetime(start_date)
                dates = dates[dates >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                dates = dates[dates <= end_dt]

            if len(dates) == 0:
                logger.warning("No data in specified date range")
                return pd.DataFrame()

            # 결과 저장할 리스트
            signals_list = []

            # 최소 2일 데이터 필요 (T-1 사용)
            if len(df_daily) < 2:
                logger.warning("Need at least 2 days of data")
                return pd.DataFrame()

            # 각 날짜에 대해 신호 생성
            for i in range(1, len(df_daily)):  # 1부터 시작 (최소 1일 전 데이터 필요)
                current_date = df_daily.index[i] if isinstance(df_daily.index, pd.DatetimeIndex) else df_daily.iloc[i]['Date']

                # 날짜 범위 체크
                if start_date and current_date < pd.to_datetime(start_date):
                    continue
                if end_date and current_date > pd.to_datetime(end_date):
                    break

                # 해당 시점까지의 데이터만 사용 (Look-ahead bias 방지)
                df_daily_slice = df_daily.iloc[:i+1]

                df_weekly_slice = None
                if df_weekly is not None and not df_weekly.empty:
                    if isinstance(df_weekly.index, pd.DatetimeIndex):
                        df_weekly_slice = df_weekly[df_weekly.index <= current_date]
                    else:
                        df_weekly_slice = df_weekly[df_weekly['Date'] <= current_date]

                df_rs_slice = None
                if df_rs is not None and not df_rs.empty:
                    if isinstance(df_rs.index, pd.DatetimeIndex):
                        df_rs_slice = df_rs[df_rs.index <= current_date]
                    else:
                        df_rs_slice = df_rs[df_rs['Date'] <= current_date]

                df_fundamental_slice = None
                if df_fundamental is not None and not df_fundamental.empty:
                    if isinstance(df_fundamental.index, pd.DatetimeIndex):
                        df_fundamental_slice = df_fundamental[df_fundamental.index <= current_date]
                    else:
                        df_fundamental_slice = df_fundamental[df_fundamental['Date'] <= current_date]

                df_earnings_slice = None
                if df_earnings is not None and not df_earnings.empty:
                    if isinstance(df_earnings.index, pd.DatetimeIndex):
                        df_earnings_slice = df_earnings[df_earnings.index <= current_date]
                    else:
                        df_earnings_slice = df_earnings[df_earnings['Date'] <= current_date]

                # 신호 생성 (내부에서 T-1 데이터 사용)
                signal_data = self.generate_comprehensive_signals(
                    df_daily=df_daily_slice,
                    df_weekly=df_weekly_slice,
                    df_rs=df_rs_slice,
                    df_fundamental=df_fundamental_slice,
                    df_earnings=df_earnings_slice
                )

                # 결과 저장
                signal_row = {
                    'Date': current_date,
                    'signal': 1 if signal_data['final_signal'] == SignalType.BUY else 0,
                    'signal_strength': signal_data['signal_strength'],
                    'confidence': signal_data['confidence'],
                    'target_price': signal_data['target_price'],
                    'losscut_price': signal_data['losscut_price'],
                    'signal_type': str(signal_data['signal_type']) if signal_data['signal_type'] else None,
                    'weekly_signal': signal_data['signal_components'].get('weekly', 0),
                    'rs_signal': signal_data['signal_components'].get('rs', 0),
                    'fundamental_signal': signal_data['signal_components'].get('fundamental', 0),
                    'earnings_signal': signal_data['signal_components'].get('earnings', 0),
                    'daily_rs_signal': signal_data['signal_components'].get('daily_rs', 0)
                }
                signals_list.append(signal_row)

            # DataFrame으로 변환
            if len(signals_list) == 0:
                logger.warning("No signals generated")
                return pd.DataFrame()

            signals_df = pd.DataFrame(signals_list)
            signals_df.set_index('Date', inplace=True)

            logger.info(f"Generated {len(signals_df)} timeseries signals")
            return signals_df

        except Exception as e:
            logger.error(f"Error generating timeseries signals: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

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

        Note: RS는 항상 T-1 (전날) 데이터 사용
        Updated: 설정 파일의 RS 임계값 사용
        """
        try:
            if df_rs.empty or len(df_rs) < 2:
                return 0

            # 설정에서 활성화 여부 확인
            if self.use_config and not self.config_loader.is_signal_enabled('rs'):
                return 0

            # RS는 항상 전날 데이터 사용 (iloc[-2])
            latest = df_rs.iloc[-2]
            rs_4w = latest.get('RS_4W')
            rs_4w = 0 if rs_4w is None or pd.isna(rs_4w) else rs_4w

            # 설정 파일에서 RS 임계값 가져오기 (기본값 90)
            rs_threshold = self.config_loader.get_rs_threshold() if self.use_config else 90

            # RS 조건 평가
            if self.use_config and self.config_loader.signal_config.rs_signal.conditions:
                # 설정 파일의 조건들을 모두 평가
                all_conditions_met = True
                for condition in self.config_loader.signal_config.rs_signal.conditions:
                    if condition.indicator == 'RS_4W':
                        condition_met = self.config_loader.evaluate_condition(condition, rs_4w)
                        if not condition_met:
                            all_conditions_met = False
                            break
                    # 다른 RS 지표 추가 가능 (RS_12W 등)

                return 1 if all_conditions_met else 0
            else:
                # 기본 로직: RS >= threshold
                if rs_4w >= rs_threshold:
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
                # 안전한 값 추출 (None을 0으로 변환)
                market_cap = latest.get('MarketCapitalization')
                market_cap = 0 if market_cap is None or pd.isna(market_cap) else market_cap

                rev_yoy = latest.get('REV_YOY')
                rev_yoy = 0 if rev_yoy is None or pd.isna(rev_yoy) else rev_yoy

                eps_yoy = latest.get('EPS_YOY')
                eps_yoy = 0 if eps_yoy is None or pd.isna(eps_yoy) else eps_yoy

                revenue = latest.get('revenue')
                revenue = 0 if revenue is None or pd.isna(revenue) else revenue

                # 이전 데이터가 있는지 확인
                if len(df_fundamental) >= 2:
                    prev = df_fundamental.iloc[-2]
                    prev_rev_yoy = prev.get('REV_YOY')
                    prev_rev_yoy = 0 if prev_rev_yoy is None or pd.isna(prev_rev_yoy) else prev_rev_yoy

                    prev_eps_yoy = prev.get('EPS_YOY')
                    prev_eps_yoy = 0 if prev_eps_yoy is None or pd.isna(prev_eps_yoy) else prev_eps_yoy
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

            # 안전한 값 추출 (None을 0으로 변환)
            prev_rev_yoy = previous.get('rev_yoy')
            prev_rev_yoy = 0 if prev_rev_yoy is None or pd.isna(prev_rev_yoy) else prev_rev_yoy

            latest_rev_yoy = latest.get('rev_yoy')
            latest_rev_yoy = 0 if latest_rev_yoy is None or pd.isna(latest_rev_yoy) else latest_rev_yoy

            prev_eps_yoy = previous.get('eps_yoy')
            prev_eps_yoy = 0 if prev_eps_yoy is None or pd.isna(prev_eps_yoy) else prev_eps_yoy

            latest_eps_yoy = latest.get('eps_yoy')
            latest_eps_yoy = 0 if latest_eps_yoy is None or pd.isna(latest_eps_yoy) else latest_eps_yoy

            # 매출 성장 조건
            rev_condition1 = prev_rev_yoy >= 0
            rev_condition2 = latest_rev_yoy > prev_rev_yoy

            # EPS 성장 조건
            eps_condition1 = prev_eps_yoy >= 0
            eps_condition2 = latest_eps_yoy > prev_eps_yoy

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

        Note: Daily와 RS 모두 T-1 (전날) 데이터 사용
        """
        try:
            if df_daily.empty or len(df_daily) < 2:
                return {'signal': 0, 'target_price': 0.0, 'losscut_price': 0.0, 'signal_type': None}

            # Daily는 항상 전날 데이터 사용 (iloc[-2])
            latest = df_daily.iloc[-2]

            # RS 조건
            rs_condition = 0
            if df_rs is not None and not df_rs.empty and len(df_rs) >= 2:
                # RS도 항상 전날 데이터 사용 (iloc[-2])
                rs_latest = df_rs.iloc[-2]
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