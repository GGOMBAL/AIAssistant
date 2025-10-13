#!/usr/bin/env python3
"""
Staged Signal Generation Service - Strategy Layer
단계별 필터링 시그널 생성 서비스

Architecture: E → F → W → RS → D
각 단계에서 신호가 1인 종목만 다음 단계로 전달
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """각 단계의 결과"""
    passed_symbols: Set[str]  # 통과한 종목들
    signals: Dict[str, float]  # 종목별 신호 강도
    stage_name: str  # 단계 이름
    total_input: int  # 입력 종목 수
    total_passed: int  # 통과 종목 수
    filter_rate: float  # 필터링 비율


class StagedSignalService:
    """
    단계별 필터링 신호 생성 서비스

    Process Flow:
    1. E (Earnings) Signal → Filter symbols with E_signal == 1
    2. F (Fundamental) Signal → Filter symbols with F_signal == 1
    3. W (Weekly) Signal → Filter symbols with W_signal == 1
    4. RS (Relative Strength) Signal → Filter symbols with RS_signal == 1
    5. D (Daily) Signal → Final candidates
    """

    def __init__(self, config: dict = None):
        """
        Initialize staged signal service

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.stage_results = {}

        # Signal thresholds for each stage
        self.thresholds = {
            'E': self.config.get('earnings_threshold', 0.5),
            'F': self.config.get('fundamental_threshold', 0.5),
            'W': self.config.get('weekly_threshold', 0.5),
            'RS': self.config.get('rs_threshold', 0.5),
            'D': self.config.get('daily_threshold', 0.5)
        }

    def generate_staged_signals(self,
                                initial_universe: List[str],
                                df_E: Dict[str, pd.DataFrame],
                                df_F: Dict[str, pd.DataFrame],
                                df_W: Dict[str, pd.DataFrame],
                                df_RS: Dict[str, pd.DataFrame],
                                df_D: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        단계별 필터링을 통한 최종 매매 신호 생성

        Args:
            initial_universe: 초기 종목 유니버스
            df_E: Earnings 데이터 (symbol: DataFrame)
            df_F: Fundamental 데이터 (symbol: DataFrame)
            df_W: Weekly 데이터 (symbol: DataFrame)
            df_RS: Relative Strength 데이터 (symbol: DataFrame)
            df_D: Daily 데이터 (symbol: DataFrame)

        Returns:
            최종 매매 후보 종목 및 단계별 결과
        """
        logger.info(f"Starting staged signal generation with {len(initial_universe)} symbols")

        # Stage 1: Earnings Signal
        stage1_result = self._stage_earnings_signal(initial_universe, df_E)
        self.stage_results['E'] = stage1_result
        logger.info(f"Stage 1 (Earnings): {stage1_result.total_passed}/{stage1_result.total_input} passed")

        # Stage 2: Fundamental Signal
        stage2_result = self._stage_fundamental_signal(stage1_result.passed_symbols, df_F)
        self.stage_results['F'] = stage2_result
        logger.info(f"Stage 2 (Fundamental): {stage2_result.total_passed}/{stage2_result.total_input} passed")

        # Stage 3: Weekly Signal
        stage3_result = self._stage_weekly_signal(stage2_result.passed_symbols, df_W)
        self.stage_results['W'] = stage3_result
        logger.info(f"Stage 3 (Weekly): {stage3_result.total_passed}/{stage3_result.total_input} passed")

        # Stage 4: RS Signal
        stage4_result = self._stage_rs_signal(stage3_result.passed_symbols, df_RS)
        self.stage_results['RS'] = stage4_result
        logger.info(f"Stage 4 (RS): {stage4_result.total_passed}/{stage4_result.total_input} passed")

        # Stage 5: Daily Signal (Final)
        stage5_result = self._stage_daily_signal(stage4_result.passed_symbols, df_D, df_W, df_RS)
        self.stage_results['D'] = stage5_result
        logger.info(f"Stage 5 (Daily): {stage5_result.total_passed}/{stage5_result.total_input} passed")

        # Compile final results
        final_results = {
            'final_candidates': list(stage5_result.passed_symbols),
            'total_candidates': len(stage5_result.passed_symbols),
            'stage_results': self.stage_results,
            'final_signals': stage5_result.signals,
            'funnel_summary': self._create_funnel_summary()
        }

        return final_results

    def _stage_earnings_signal(self,
                               symbols: List[str],
                               df_E: Dict[str, pd.DataFrame]) -> StageResult:
        """
        Stage 1: Earnings Signal Generation

        Criteria:
        - Positive EPS YoY growth
        - Positive Revenue YoY growth
        - Recent earnings beat
        """
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_E or df_E[symbol].empty:
                continue

            df = df_E[symbol]

            try:
                # Get latest earnings data
                latest = df.iloc[-1]

                signal = 0.0

                # EPS YoY growth check
                if 'eps_yoy' in latest and not pd.isna(latest['eps_yoy']):
                    if latest['eps_yoy'] > 0:
                        signal += 0.4

                # Revenue YoY growth check
                if 'rev_yoy' in latest and not pd.isna(latest['rev_yoy']):
                    if latest['rev_yoy'] > 0:
                        signal += 0.4

                # Earnings surprise check
                if 'eps_surprise' in latest and not pd.isna(latest['eps_surprise']):
                    if latest['eps_surprise'] > 0:
                        signal += 0.2

                signals[symbol] = signal

                # Pass if signal > 0 (any positive signal)
                if signal > 0:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing earnings for {symbol}: {e}")
                continue

        return StageResult(
            passed_symbols=passed_symbols,
            signals=signals,
            stage_name='Earnings',
            total_input=len(symbols),
            total_passed=len(passed_symbols),
            filter_rate=len(passed_symbols) / len(symbols) if symbols else 0
        )

    def _stage_fundamental_signal(self,
                                  symbols: Set[str],
                                  df_F: Dict[str, pd.DataFrame]) -> StageResult:
        """
        Stage 2: Fundamental Signal Generation

        Criteria:
        - Positive ROE
        - Reasonable valuation (PBR, PSR)
        - Any positive fundamental metric
        """
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_F or df_F[symbol].empty:
                continue

            df = df_F[symbol]

            try:
                latest = df.iloc[-1]

                signal = 0.0

                # Use raw fundamental data since ROE/ROA/PBR/PSR are not computed
                # Check for positive net income
                if 'netIncome' in latest and not pd.isna(latest['netIncome']):
                    if latest['netIncome'] > 0:
                        signal += 0.3

                # Check for positive revenue growth (YoY)
                if 'REV_YOY' in latest and not pd.isna(latest['REV_YOY']):
                    if latest['REV_YOY'] > 0:
                        signal += 0.3

                # Check for positive EPS growth (YoY)
                if 'EPS_YOY' in latest and not pd.isna(latest['EPS_YOY']):
                    if latest['EPS_YOY'] > 0:
                        signal += 0.2

                # Check for positive shareholder equity
                if 'totalShareholderEquity' in latest and not pd.isna(latest['totalShareholderEquity']):
                    if latest['totalShareholderEquity'] > 0:
                        signal += 0.2

                signals[symbol] = signal

                # Pass if signal > 0 (any positive signal)
                if signal > 0:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing fundamentals for {symbol}: {e}")
                continue

        return StageResult(
            passed_symbols=passed_symbols,
            signals=signals,
            stage_name='Fundamental',
            total_input=len(symbols),
            total_passed=len(passed_symbols),
            filter_rate=len(passed_symbols) / len(symbols) if symbols else 0
        )

    def _stage_weekly_signal(self,
                            symbols: Set[str],
                            df_W: Dict[str, pd.DataFrame]) -> StageResult:
        """
        Stage 3: Weekly Signal Generation

        Criteria:
        - Price near 52-week high
        - Uptrend (SMA20 > SMA50)
        - Breakout pattern
        """
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_W or df_W[symbol].empty:
                continue

            df = df_W[symbol]

            try:
                latest = df.iloc[-1]

                signal = 0.0

                # 52-week high proximity
                if '52_H' in latest and 'Wclose' in latest:
                    if not pd.isna(latest['52_H']) and not pd.isna(latest['Wclose']):
                        distance_from_high = (latest['52_H'] - latest['Wclose']) / latest['52_H']
                        if distance_from_high < 0.10:  # Within 10% of 52W high
                            signal += 0.4

                # Trend check (SMA comparison)
                if 'SMA20' in latest and 'SMA50' in latest:
                    if not pd.isna(latest['SMA20']) and not pd.isna(latest['SMA50']):
                        if latest['SMA20'] > latest['SMA50']:
                            signal += 0.3

                # Volume check
                if 'volume' in df.columns and len(df) >= 20:
                    avg_volume = df['volume'].tail(20).mean()
                    if not pd.isna(latest.get('volume', np.nan)) and not pd.isna(avg_volume):
                        if latest['volume'] > avg_volume * 1.2:
                            signal += 0.3

                signals[symbol] = signal

                # Pass if signal > 0 (any positive signal)
                if signal > 0:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing weekly for {symbol}: {e}")
                continue

        return StageResult(
            passed_symbols=passed_symbols,
            signals=signals,
            stage_name='Weekly',
            total_input=len(symbols),
            total_passed=len(passed_symbols),
            filter_rate=len(passed_symbols) / len(symbols) if symbols else 0
        )

    def _stage_rs_signal(self,
                        symbols: Set[str],
                        df_RS: Dict[str, pd.DataFrame]) -> StageResult:
        """
        Stage 4: Relative Strength Signal Generation

        Criteria:
        - RS_4W > 0 (outperforming market)
        - RS_12W > 0
        - Sector RS positive
        """
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_RS or df_RS[symbol].empty:
                continue

            df = df_RS[symbol]

            try:
                latest = df.iloc[-1]

                signal = 0.0

                # RS_4W check
                if 'RS_4W' in latest and not pd.isna(latest['RS_4W']):
                    if latest['RS_4W'] > 0:
                        signal += 0.4

                # RS_12W check
                if 'RS_12W' in latest and not pd.isna(latest['RS_12W']):
                    if latest['RS_12W'] > 0:
                        signal += 0.3

                # Sector RS check
                if 'Sector_RS_4W' in latest and not pd.isna(latest['Sector_RS_4W']):
                    if latest['Sector_RS_4W'] > 0:
                        signal += 0.3

                signals[symbol] = signal

                # Pass if signal > 0 (any positive signal)
                if signal > 0:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing RS for {symbol}: {e}")
                continue

        return StageResult(
            passed_symbols=passed_symbols,
            signals=signals,
            stage_name='Relative Strength',
            total_input=len(symbols),
            total_passed=len(passed_symbols),
            filter_rate=len(passed_symbols) / len(symbols) if symbols else 0
        )

    def _stage_daily_signal(self,
                           symbols: Set[str],
                           df_D: Dict[str, pd.DataFrame],
                           df_W: Dict[str, pd.DataFrame],
                           df_RS: Dict[str, pd.DataFrame]) -> StageResult:
        """
        Stage 5: Daily Signal Generation (Final Stage)

        Criteria:
        - Entry timing based on daily patterns
        - Risk/reward calculation
        - Target and losscut price determination
        """
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_D or df_D[symbol].empty:
                continue

            df = df_D[symbol]

            try:
                latest = df.iloc[-1]

                signal = 0.0

                # Price action check - just needs valid close price
                if 'Dclose' in latest and not pd.isna(latest['Dclose']):
                    if latest['Dclose'] > 0:
                        signal += 0.2

                    # Bonus for bullish candle
                    if 'Dopen' in latest and not pd.isna(latest['Dopen']):
                        if latest['Dclose'] > latest['Dopen']:
                            signal += 0.2

                # ADR check (volatility) - more lenient
                if 'ADR' in latest and not pd.isna(latest['ADR']):
                    if 1.0 < latest['ADR'] < 15.0:  # Very wide range
                        signal += 0.2

                # Trend alignment - check any uptrend
                if 'SMA20' in latest and 'Dclose' in latest:
                    if not pd.isna(latest['SMA20']) and not pd.isna(latest['Dclose']):
                        # Just above SMA20
                        if latest['Dclose'] > latest['SMA20']:
                            signal += 0.2

                # Volume check - has volume data
                if 'volume' in df.columns and len(df) > 1:
                    signal += 0.2

                signals[symbol] = signal

                # Pass if signal > 0 (any positive signal)
                if signal > 0:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing daily for {symbol}: {e}")
                continue

        return StageResult(
            passed_symbols=passed_symbols,
            signals=signals,
            stage_name='Daily',
            total_input=len(symbols),
            total_passed=len(passed_symbols),
            filter_rate=len(passed_symbols) / len(symbols) if symbols else 0
        )

    def _create_funnel_summary(self) -> Dict[str, Any]:
        """Create funnel summary showing filtering progression"""
        funnel = {}

        stages = ['E', 'F', 'W', 'RS', 'D']
        for stage in stages:
            if stage in self.stage_results:
                result = self.stage_results[stage]
                funnel[stage] = {
                    'stage_name': result.stage_name,
                    'input': result.total_input,
                    'output': result.total_passed,
                    'filter_rate': f"{result.filter_rate * 100:.2f}%",
                    'reduction': result.total_input - result.total_passed
                }

        return funnel

    def get_stage_summary(self) -> str:
        """Get formatted stage summary"""
        summary = "\n" + "="*80 + "\n"
        summary += "STAGED FILTERING SUMMARY\n"
        summary += "="*80 + "\n\n"

        stages = ['E', 'F', 'W', 'RS', 'D']
        for i, stage in enumerate(stages):
            if stage in self.stage_results:
                result = self.stage_results[stage]
                summary += f"Stage {i+1}: {result.stage_name}\n"
                summary += f"  Input:  {result.total_input:>6} symbols\n"
                summary += f"  Output: {result.total_passed:>6} symbols\n"
                summary += f"  Filter: {result.filter_rate*100:>6.2f}%\n"
                summary += "\n"

        summary += "="*80 + "\n"
        return summary
