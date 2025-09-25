"""
Simple Technical Indicators

간단한 기술지표 계산을 위한 독립적인 클래스
통합 백테스트에서 사용하기 위해 의존성 없이 구현

버전: 1.0
작성일: 2025-09-21
"""

import pandas as pd
import numpy as np
from typing import List, Optional


class SimpleTechnicalIndicators:
    """
    간단한 기술지표 계산 클래스

    의존성 없이 기본적인 기술지표들을 계산
    """

    def __init__(self):
        pass

    def add_moving_averages(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """
        이동평균선 추가

        Args:
            df: OHLCV 데이터프레임
            periods: 이동평균 기간 리스트

        Returns:
            이동평균선이 추가된 데이터프레임
        """
        df = df.copy()

        for period in periods:
            if 'Close' in df.columns:
                df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
            elif 'close' in df.columns:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()

        return df

    def add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        RSI 지표 추가

        Args:
            df: OHLCV 데이터프레임
            period: RSI 계산 기간

        Returns:
            RSI가 추가된 데이터프레임
        """
        df = df.copy()

        # Close 또는 close 컬럼 찾기
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if close_col in df.columns:
            delta = df[close_col].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            df['RSI'] = rsi

        return df

    def add_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """
        볼린저 밴드 추가

        Args:
            df: OHLCV 데이터프레임
            period: 이동평균 기간
            std_dev: 표준편차 배수

        Returns:
            볼린저 밴드가 추가된 데이터프레임
        """
        df = df.copy()

        # Close 또는 close 컬럼 찾기
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if close_col in df.columns:
            # 중심선 (이동평균)
            df['BB_Middle'] = df[close_col].rolling(window=period).mean()

            # 표준편차
            std = df[close_col].rolling(window=period).std()

            # 상한선과 하한선
            df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
            df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)

        return df

    def add_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        MACD 지표 추가

        Args:
            df: OHLCV 데이터프레임
            fast: 빠른 이동평균 기간
            slow: 느린 이동평균 기간
            signal: 시그널 이동평균 기간

        Returns:
            MACD가 추가된 데이터프레임
        """
        df = df.copy()

        # Close 또는 close 컬럼 찾기
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if close_col in df.columns:
            # 지수이동평균 계산
            ema_fast = df[close_col].ewm(span=fast).mean()
            ema_slow = df[close_col].ewm(span=slow).mean()

            # MACD 라인
            df['MACD'] = ema_fast - ema_slow

            # 시그널 라인
            df['MACD_Signal'] = df['MACD'].ewm(span=signal).mean()

            # 히스토그램
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        return df

    def add_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """
        스토캐스틱 지표 추가

        Args:
            df: OHLCV 데이터프레임
            k_period: %K 계산 기간
            d_period: %D 계산 기간

        Returns:
            스토캐스틱이 추가된 데이터프레임
        """
        df = df.copy()

        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if all(col in df.columns for col in [high_col, low_col, close_col]):
            # 최고가와 최저가
            highest_high = df[high_col].rolling(window=k_period).max()
            lowest_low = df[low_col].rolling(window=k_period).min()

            # %K
            df['Stoch_K'] = ((df[close_col] - lowest_low) / (highest_high - lowest_low)) * 100

            # %D
            df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()

        return df

    def add_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        ATR (Average True Range) 지표 추가

        Args:
            df: OHLCV 데이터프레임
            period: ATR 계산 기간

        Returns:
            ATR이 추가된 데이터프레임
        """
        df = df.copy()

        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if all(col in df.columns for col in [high_col, low_col, close_col]):
            # True Range 계산
            df['prev_close'] = df[close_col].shift(1)

            df['tr1'] = df[high_col] - df[low_col]
            df['tr2'] = abs(df[high_col] - df['prev_close'])
            df['tr3'] = abs(df[low_col] - df['prev_close'])

            df['TR'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

            # ATR 계산 (이동평균)
            df['ATR'] = df['TR'].rolling(window=period).mean()

            # 임시 컬럼 제거
            df = df.drop(['prev_close', 'tr1', 'tr2', 'tr3'], axis=1)

        return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        거래량 지표 추가

        Args:
            df: OHLCV 데이터프레임

        Returns:
            거래량 지표가 추가된 데이터프레임
        """
        df = df.copy()

        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'

        if volume_col in df.columns:
            # 거래량 이동평균
            df['Volume_MA10'] = df[volume_col].rolling(window=10).mean()
            df['Volume_MA20'] = df[volume_col].rolling(window=20).mean()

            # 거래량 비율
            df['Volume_Ratio'] = df[volume_col] / df['Volume_MA20']

        return df

    def add_price_change(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        가격 변화율 지표 추가

        Args:
            df: OHLCV 데이터프레임

        Returns:
            가격 변화율이 추가된 데이터프레임
        """
        df = df.copy()

        close_col = 'Close' if 'Close' in df.columns else 'close'

        if close_col in df.columns:
            # 일일 변화율
            df['Daily_Return'] = df[close_col].pct_change()

            # 누적 수익률
            df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1

            # N일 변화율
            for period in [5, 10, 20]:
                df[f'Return_{period}d'] = df[close_col].pct_change(periods=period)

        return df

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 기술지표를 한번에 추가

        Args:
            df: OHLCV 데이터프레임

        Returns:
            모든 기술지표가 추가된 데이터프레임
        """
        # 이동평균선
        df = self.add_moving_averages(df, [5, 10, 20, 50, 200])

        # RSI
        df = self.add_rsi(df)

        # 볼린저 밴드
        df = self.add_bollinger_bands(df)

        # MACD
        df = self.add_macd(df)

        # 스토캐스틱
        df = self.add_stochastic(df)

        # ATR
        df = self.add_atr(df)

        # 거래량 지표
        df = self.add_volume_indicators(df)

        # 가격 변화율
        df = self.add_price_change(df)

        return df

    def calculate_adr(self, df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        ADR (Average Daily Range) 계산

        Args:
            df: OHLCV 데이터프레임
            period: 평균 계산 기간

        Returns:
            ADR이 추가된 데이터프레임
        """
        df = df.copy()

        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        close_col = 'Close' if 'Close' in df.columns else 'close'

        if all(col in df.columns for col in [high_col, low_col, close_col]):
            # 일일 범위 계산
            daily_range = (df[high_col] - df[low_col]) / df[close_col] * 100

            # ADR (평균 일일 범위)
            df['ADR'] = daily_range.rolling(window=period).mean()

        return df