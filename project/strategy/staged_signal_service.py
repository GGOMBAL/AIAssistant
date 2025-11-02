#!/usr/bin/env python3
"""
Staged Signal Generation Service - Strategy Layer
단계별 필터링 시그널 생성 서비스

Architecture: W → F → E → RS → D
각 단계에서 신호가 1인 종목만 다음 단계로 전달
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from datetime import datetime
import logging

# Import StrategySignalConfigLoader to check enabled flags and get signal conditions
from project.strategy.strategy_signal_config_loader import StrategySignalConfigLoader

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
    1. W (Weekly) Signal → Filter symbols with W_signal == 1
    2. F (Fundamental) Signal → Filter symbols with F_signal == 1
    3. E (Earnings) Signal → Filter symbols with E_signal == 1
    4. RS (Relative Strength) Signal → Filter symbols with RS_signal == 1
    5. D (Daily) Signal → Final candidates
    """

    def __init__(self, config: dict = None, execution_mode: str = 'live'):
        """
        Initialize staged signal service

        Args:
            config: Configuration dictionary
            execution_mode: 'live' for real-time trading (current day high for breakout),
                          'analysis' for historical analysis (D-1 data for breakout)
                          Applies to Daily stage breakout detection
        """
        self.config = config or {}
        self.stage_results = {}
        self.execution_mode = execution_mode  # 'live' or 'analysis'

        # Signal thresholds for each stage
        # NOTE: All signals use binary logic (0 or 1), thresholds must be 1.0
        self.thresholds = {
            'E': 1.0,  # Earnings uses binary signal (0 or 1)
            'F': 1.0,  # Fundamental uses binary signal (0 or 1)
            'W': 1.0,  # Weekly uses binary signal (0 or 1)
            'RS': 1.0,  # RS uses binary signal (0 or 1)
            'D': self.config.get('daily_threshold', 0.5)  # Daily uses weighted signal
        }

        # Load strategy_signal_config.yaml to check enabled flags and get signal conditions
        try:
            self.signal_config_loader = StrategySignalConfigLoader()
            logger.info("Loaded signal configuration from strategy_signal_config.yaml")
        except Exception as e:
            logger.warning(f"Could not load strategy_signal_config.yaml: {e}")
            self.signal_config_loader = None

        logger.info(f"StagedSignalService initialized in '{execution_mode}' mode")

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

        IMPORTANT: If earnings_signal.enabled = false in signal_config.yaml,
                   this stage will pass ALL symbols through (no filtering)
        """
        # Check if earnings signal is enabled in signal_config.yaml
        if self.signal_config_loader and not self.signal_config_loader.is_signal_enabled('earnings'):
            logger.info("[Earnings Stage] SKIPPED - earnings_signal.enabled = false in signal_config.yaml")
            logger.info("[Earnings Stage] Passing ALL symbols through without filtering")

            # Return all symbols as passed (no filtering)
            return StageResult(
                passed_symbols=set(symbols),
                signals={symbol: 1.0 for symbol in symbols},  # All signals = 1.0 (passed)
                stage_name='Earnings (DISABLED)',
                total_input=len(symbols),
                total_passed=len(symbols),
                filter_rate=1.0  # 100% pass rate
            )

        # If enabled, proceed with normal filtering
        logger.info("[Earnings Stage] ENABLED - Applying earnings filters")
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            # Handle missing earnings data gracefully
            if symbol not in df_E:
                logger.debug(f"[Earnings Stage] {symbol} not in df_E - auto-pass (data not available)")
                # Auto-pass: Earnings data not available for this symbol
                signals[symbol] = 1.0  # Auto-pass signal
                passed_symbols.add(symbol)
                continue
            if df_E[symbol].empty:
                logger.debug(f"[Earnings Stage] {symbol} df_E is empty - auto-pass")
                # Auto-pass: Empty earnings data
                signals[symbol] = 1.0  # Auto-pass signal
                passed_symbols.add(symbol)
                continue

            df = df_E[symbol]

            try:
                # ========================================
                # BACKTEST-FRIENDLY EARNINGS SIGNAL LOGIC
                # Check entire period - pass if ANY quarter has signal = 1
                # ========================================

                if len(df) < 2:
                    signals[symbol] = 0.0
                    continue

                # Config에서 조건 값 읽기
                if self.signal_config_loader:
                    min_prev_rev_yoy = self.signal_config_loader.get_earnings_revenue_min_prev_yoy()
                    min_prev_eps_yoy = self.signal_config_loader.get_earnings_eps_min_prev_yoy()
                    require_rev_growth = self.signal_config_loader.get_earnings_revenue_require_growth()
                    require_eps_growth = self.signal_config_loader.get_earnings_eps_require_growth()
                else:
                    min_prev_rev_yoy = 0.0
                    min_prev_eps_yoy = 0.0
                    require_rev_growth = True
                    require_eps_growth = True

                # Check ENTIRE DataFrame - pass if ANY quarter has signal
                any_signal_found = False
                signal_count = 0

                for i in range(1, len(df)):  # Start from index 1 (need 1 previous quarter)
                    current = df.iloc[i]
                    previous = df.iloc[i-1]

                    # Extract values (safe extraction with None handling)
                    prev_rev_yoy = previous.get('rev_yoy')
                    prev_rev_yoy = 0 if prev_rev_yoy is None or pd.isna(prev_rev_yoy) else prev_rev_yoy

                    current_rev_yoy = current.get('rev_yoy')
                    current_rev_yoy = 0 if current_rev_yoy is None or pd.isna(current_rev_yoy) else current_rev_yoy

                    prev_eps_yoy = previous.get('eps_yoy')
                    prev_eps_yoy = 0 if prev_eps_yoy is None or pd.isna(prev_eps_yoy) else prev_eps_yoy

                    current_eps_yoy = current.get('eps_yoy')
                    current_eps_yoy = 0 if current_eps_yoy is None or pd.isna(current_eps_yoy) else current_eps_yoy

                    # Revenue growth conditions
                    rev_condition1 = prev_rev_yoy >= min_prev_rev_yoy
                    rev_condition2 = current_rev_yoy > prev_rev_yoy if require_rev_growth else True

                    # EPS growth conditions
                    eps_condition1 = prev_eps_yoy >= min_prev_eps_yoy
                    eps_condition2 = current_eps_yoy > prev_eps_yoy if require_eps_growth else True

                    # Pass if either revenue or EPS is growing
                    earnings_passed = (
                        (rev_condition1 and rev_condition2) or
                        (eps_condition1 and eps_condition2)
                    )

                    if earnings_passed:
                        any_signal_found = True
                        signal_count += 1

                # Signal = 1.0 if ANY quarter in entire period had signal
                signal = 1.0 if any_signal_found else 0.0
                signals[symbol] = signal

                # Debug logging
                if any_signal_found:
                    logger.info(f"[Earnings Stage] {symbol} PASSED - {signal_count}/{len(df)-1} quarters had signals")
                else:
                    logger.debug(f"[Earnings Stage] {symbol} FAILED - no signals in entire period")

                # Pass if signal == 1.0 (at least one quarter had signal)
                if signal >= self.thresholds['E']:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.debug(f"Error processing earnings for {symbol}: {e}")
                # Auto-pass on error to prevent blocking the pipeline
                signals[symbol] = 1.0
                passed_symbols.add(symbol)
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

        IMPORTANT: If fundamental_signal.enabled = false in signal_config.yaml,
                   this stage will pass ALL symbols through (no filtering)
        """
        # Check if fundamental signal is enabled in signal_config.yaml
        if self.signal_config_loader and not self.signal_config_loader.is_signal_enabled('fundamental'):
            logger.info("[Fundamental Stage] SKIPPED - fundamental_signal.enabled = false in signal_config.yaml")
            logger.info("[Fundamental Stage] Passing ALL symbols through without filtering")

            # Return all symbols as passed (no filtering)
            return StageResult(
                passed_symbols=symbols if isinstance(symbols, set) else set(symbols),
                signals={symbol: 1.0 for symbol in symbols},
                stage_name='Fundamental (DISABLED)',
                total_input=len(symbols),
                total_passed=len(symbols),
                filter_rate=1.0
            )

        # If enabled, proceed with normal filtering
        logger.info("[Fundamental Stage] ENABLED - Applying fundamental filters")
        logger.info(f"[Fundamental Stage] Input symbols: {symbols}")
        logger.info(f"[Fundamental Stage] Available data for: {list(df_F.keys())}")
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            # Handle missing fundamental data gracefully
            if symbol not in df_F:
                logger.debug(f"[Fundamental Stage] {symbol} not in df_F - auto-pass (data not available)")
                # Auto-pass: Fundamental data not available for this symbol
                signals[symbol] = 1.0  # Auto-pass signal
                passed_symbols.add(symbol)
                continue
            if df_F[symbol].empty:
                logger.debug(f"[Fundamental Stage] {symbol} df_F is empty - auto-pass")
                # Auto-pass: Empty fundamental data
                signals[symbol] = 1.0  # Auto-pass signal
                passed_symbols.add(symbol)
                continue

            df = df_F[symbol]

            try:
                # ========================================
                # BACKTEST-FRIENDLY FUNDAMENTAL SIGNAL LOGIC
                # Check entire period - pass if ANY quarter has signal = 1
                # ========================================

                if len(df) < 2:
                    signals[symbol] = 0.0
                    continue

                # Config에서 조건 값 읽기
                if self.signal_config_loader:
                    min_market_cap = self.signal_config_loader.get_fundamental_market_cap_min()
                    max_market_cap = self.signal_config_loader.get_fundamental_market_cap_max()
                    min_rev_yoy = self.signal_config_loader.get_fundamental_revenue_min_yoy()
                    min_prev_rev_yoy = self.signal_config_loader.get_fundamental_revenue_min_prev_yoy()
                    min_eps_yoy = self.signal_config_loader.get_fundamental_eps_min_yoy()
                    min_prev_eps_yoy = self.signal_config_loader.get_fundamental_eps_min_prev_yoy()
                    min_revenue = self.signal_config_loader.get_fundamental_revenue_min_value()
                else:
                    min_market_cap = 2000000000
                    max_market_cap = 20000000000000
                    min_rev_yoy = 0.1
                    min_prev_rev_yoy = 0.0
                    min_eps_yoy = 0.1
                    min_prev_eps_yoy = 0.0
                    min_revenue = 0

                # Check ENTIRE DataFrame - pass if ANY quarter has signal
                any_signal_found = False
                signal_count = 0

                for i in range(1, len(df)):  # Start from index 1 (need 1 previous quarter)
                    current = df.iloc[i]
                    previous = df.iloc[i-1]

                    # Extract fundamental values (safe extraction with None handling)
                    market_cap = current.get('MarketCapitalization')
                    market_cap = 0 if market_cap is None or pd.isna(market_cap) else market_cap

                    rev_yoy = current.get('REV_YOY')
                    rev_yoy = 0 if rev_yoy is None or pd.isna(rev_yoy) else rev_yoy

                    eps_yoy = current.get('EPS_YOY')
                    eps_yoy = 0 if eps_yoy is None or pd.isna(eps_yoy) else eps_yoy

                    revenue = current.get('revenue')
                    revenue = 0 if revenue is None or pd.isna(revenue) else revenue

                    prev_rev_yoy = previous.get('REV_YOY')
                    prev_rev_yoy = 0 if prev_rev_yoy is None or pd.isna(prev_rev_yoy) else prev_rev_yoy

                    prev_eps_yoy = previous.get('EPS_YOY')
                    prev_eps_yoy = 0 if prev_eps_yoy is None or pd.isna(prev_eps_yoy) else prev_eps_yoy

                    # Fundamental conditions (identical to SignalGenerationService)
                    f_condition1 = market_cap >= min_market_cap  # Market Cap minimum
                    f_condition2 = market_cap <= max_market_cap  # Market Cap maximum
                    f_condition3 = rev_yoy >= min_rev_yoy  # Revenue YoY minimum
                    f_condition4 = prev_rev_yoy >= min_prev_rev_yoy  # Previous Revenue YoY minimum
                    f_condition6 = eps_yoy >= min_eps_yoy  # EPS YoY minimum
                    f_condition7 = prev_eps_yoy >= min_prev_eps_yoy  # Previous EPS YoY minimum
                    f_condition9 = revenue > min_revenue  # Revenue minimum

                    # Final condition: (Revenue growth) OR (EPS growth)
                    fundamental_passed = (
                        f_condition1 and f_condition2 and
                        ((f_condition3 and f_condition4) or (f_condition6 and f_condition7)) and
                        f_condition9
                    )

                    if fundamental_passed:
                        any_signal_found = True
                        signal_count += 1

                # Signal = 1.0 if ANY quarter in entire period had signal
                signal = 1.0 if any_signal_found else 0.0
                signals[symbol] = signal

                # Debug logging
                if any_signal_found:
                    logger.info(f"[Fundamental Stage] {symbol} PASSED - {signal_count}/{len(df)-1} quarters had signals")
                else:
                    logger.debug(f"[Fundamental Stage] {symbol} FAILED - no signals in entire period")

                # Pass if signal == 1.0 (at least one quarter had signal)
                if signal >= self.thresholds['F']:
                    passed_symbols.add(symbol)

            except Exception as e:
                logger.warning(f"[Fundamental Stage] Error processing {symbol}: {e}")
                import traceback
                logger.warning(traceback.format_exc())
                # Auto-pass on error to prevent blocking the pipeline
                signals[symbol] = 1.0
                passed_symbols.add(symbol)
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

        IMPORTANT: If weekly_signal.enabled = false in signal_config.yaml,
                   this stage will pass ALL symbols through (no filtering)
        """
        # Check if weekly signal is enabled in signal_config.yaml
        if self.signal_config_loader and not self.signal_config_loader.is_signal_enabled('weekly'):
            logger.info("[Weekly Stage] SKIPPED - weekly_signal.enabled = false in signal_config.yaml")
            logger.info("[Weekly Stage] Passing ALL symbols through without filtering")

            # Return all symbols as passed (no filtering)
            return StageResult(
                passed_symbols=symbols if isinstance(symbols, set) else set(symbols),
                signals={symbol: 1.0 for symbol in symbols},
                stage_name='Weekly (DISABLED)',
                total_input=len(symbols),
                total_passed=len(symbols),
                filter_rate=1.0
            )

        # If enabled, proceed with normal filtering
        logger.info("[Weekly Stage] ENABLED - Applying weekly filters")
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_W or df_W[symbol].empty:
                continue

            df = df_W[symbol]

            try:
                # ========================================
                # BACKTEST-FRIENDLY WEEKLY SIGNAL LOGIC
                # Check entire period - pass if ANY row has signal = 1
                # ========================================

                if len(df) < 3:  # Need at least 3 weeks for shift(2)
                    signals[symbol] = 0.0
                    continue

                # Config에서 조건 값 읽기
                if self.signal_config_loader:
                    high_stability_factor = self.signal_config_loader.get_weekly_high_stability_factor()
                    low_distance_factor = self.signal_config_loader.get_weekly_low_distance_factor()
                    high_distance_factor = self.signal_config_loader.get_weekly_high_distance_factor()
                else:
                    high_stability_factor = 1.05
                    low_distance_factor = 1.3
                    high_distance_factor = 0.7

                # Check ENTIRE DataFrame - pass if ANY row has signal
                any_signal_found = False
                signal_count = 0

                for i in range(2, len(df)):  # Start from index 2 (need 2 previous rows)
                    current = df.iloc[i]
                    prev_1 = df.iloc[i-1]
                    prev_2 = df.iloc[i-2]

                    # Weekly conditions (identical to SignalGenerationService)
                    w_condition1 = current.get('1Year_H', 0) == current.get('2Year_H', 0)
                    w_condition2 = current.get('2Year_L', 0) < current.get('1Year_L', 0)
                    w_condition3 = current.get('52_H', 0) <= prev_2.get('52_H', 0) * high_stability_factor
                    w_condition4 = prev_1.get('Wclose', 0) > current.get('52_L', 0) * low_distance_factor
                    w_condition5 = prev_1.get('Wclose', 0) > current.get('52_H', 0) * high_distance_factor

                    # All conditions must be met for this row
                    weekly_passed = (
                        w_condition1 and w_condition2 and w_condition3 and
                        w_condition4 and w_condition5
                    )

                    if weekly_passed:
                        any_signal_found = True
                        signal_count += 1

                # Signal = 1.0 if ANY row in entire period had signal
                signal = 1.0 if any_signal_found else 0.0
                signals[symbol] = signal

                # Debug logging
                if any_signal_found:
                    logger.info(f"[Weekly Stage] {symbol} PASSED - {signal_count}/{len(df)-2} rows had signals")
                else:
                    logger.debug(f"[Weekly Stage] {symbol} FAILED - no signals in entire period")

                # Pass if signal == 1.0 (at least one row had signal)
                if signal >= self.thresholds['W']:
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

        IMPORTANT: If rs_signal.enabled = false in signal_config.yaml,
                   this stage will pass ALL symbols through (no filtering)
        """
        # Check if RS signal is enabled in signal_config.yaml
        if self.signal_config_loader and not self.signal_config_loader.is_signal_enabled('rs'):
            logger.info("[RS Stage] SKIPPED - rs_signal.enabled = false in signal_config.yaml")
            logger.info("[RS Stage] Passing ALL symbols through without filtering")

            # Return all symbols as passed (no filtering)
            return StageResult(
                passed_symbols=symbols if isinstance(symbols, set) else set(symbols),
                signals={symbol: 1.0 for symbol in symbols},
                stage_name='Relative Strength (DISABLED)',
                total_input=len(symbols),
                total_passed=len(symbols),
                filter_rate=1.0
            )

        # If enabled, proceed with normal filtering
        logger.info("[RS Stage] ENABLED - Applying RS filters")
        passed_symbols = set()
        signals = {}

        for symbol in symbols:
            if symbol not in df_RS or df_RS[symbol].empty:
                continue

            df = df_RS[symbol]

            try:
                # ========================================
                # BACKTEST-FRIENDLY RS SIGNAL LOGIC
                # Check entire period - pass if ANY row has signal = 1
                # ========================================

                if len(df) < 2:
                    signals[symbol] = 0.0
                    continue

                # Config에서 조건 값 읽기
                if self.signal_config_loader:
                    rs_threshold = self.signal_config_loader.get_rs_threshold()
                else:
                    # Fallback to default value (balanced strategy)
                    rs_threshold = 90

                # Check ENTIRE DataFrame - pass if ANY row has signal
                any_signal_found = False
                signal_count = 0

                for i in range(len(df)):
                    current = df.iloc[i]

                    rs_4w = current.get('RS_4W')
                    rs_4w = 0 if rs_4w is None or pd.isna(rs_4w) else rs_4w

                    # RS condition
                    rs_passed = rs_4w >= rs_threshold

                    if rs_passed:
                        any_signal_found = True
                        signal_count += 1

                # Signal = 1.0 if ANY row in entire period had signal
                signal = 1.0 if any_signal_found else 0.0
                signals[symbol] = signal

                # Debug logging
                if any_signal_found:
                    logger.info(f"[RS Stage] {symbol} PASSED - {signal_count}/{len(df)} days had RS >= {rs_threshold}")
                else:
                    logger.debug(f"[RS Stage] {symbol} FAILED - no signals in entire period")

                # Pass if signal == 1.0 (at least one row had signal)
                if signal >= self.thresholds['RS']:
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
        - **PRIMARY**: Current day high must break above Highest value (breakout)
        - Secondary: Trend alignment, volume confirmation
        - Target and losscut price determination

        IMPORTANT: If daily_rs_signal.enabled = false in signal_config.yaml,
                   this stage will pass ALL symbols through (no filtering)
        """
        # Check if daily RS signal is enabled in signal_config.yaml
        if self.signal_config_loader and not self.signal_config_loader.is_signal_enabled('daily_rs'):
            logger.info("[Daily Stage] SKIPPED - daily_rs_signal.enabled = false in signal_config.yaml")
            logger.info("[Daily Stage] Passing ALL symbols through without filtering")

            # Return all symbols as passed (no filtering)
            return StageResult(
                passed_symbols=symbols if isinstance(symbols, set) else set(symbols),
                signals={symbol: 1.0 for symbol in symbols},
                stage_name='Daily (DISABLED)',
                total_input=len(symbols),
                total_passed=len(symbols),
                filter_rate=1.0
            )

        # If enabled, proceed with normal filtering
        logger.info("[Daily Stage] ENABLED - Applying daily breakout filters")
        passed_symbols = set()
        signals = {}

        # Statistics for diagnostics
        stats = {
            'total_symbols': 0,
            'symbols_with_dhigh': 0,
            'symbols_with_highest_1m': 0,
            'symbols_with_highest_3m': 0,
            'symbols_with_highest_6m': 0,
            'symbols_with_highest_1y': 0,
            'symbols_with_highest_2y': 0,
            'symbols_with_sma20': 0,
            'symbols_with_sma50': 0,
            'breakout_1m_count': 0,
            'breakout_3m_count': 0,
            'breakout_6m_count': 0,
            'breakout_1y_count': 0,
            'breakout_2y_count': 0,
            'sma_condition_count': 0,
            'any_breakout_count': 0
        }

        for symbol in symbols:
            stats['total_symbols'] += 1
            if symbol not in df_D or df_D[symbol].empty:
                continue

            df = df_D[symbol]

            try:
                # ========================================
                # BACKTEST-FRIENDLY DAILY SIGNAL LOGIC
                # Check entire period - pass if ANY day has breakout signal
                # ========================================

                if len(df) < 2:
                    signals[symbol] = 0.0
                    continue

                # Check column existence for this symbol
                if 'Dhigh' in df.columns:
                    stats['symbols_with_dhigh'] += 1
                if 'Highest_1M' in df.columns:
                    stats['symbols_with_highest_1m'] += 1
                if 'Highest_3M' in df.columns:
                    stats['symbols_with_highest_3m'] += 1
                if 'Highest_6M' in df.columns:
                    stats['symbols_with_highest_6m'] += 1
                if 'Highest_1Y' in df.columns:
                    stats['symbols_with_highest_1y'] += 1
                if 'Highest_2Y' in df.columns:
                    stats['symbols_with_highest_2y'] += 1
                if 'SMA20' in df.columns:
                    stats['symbols_with_sma20'] += 1
                if 'SMA50' in df.columns:
                    stats['symbols_with_sma50'] += 1

                # DEBUG: Print sample data for first 3 symbols
                if stats['total_symbols'] <= 3:
                    logger.info(f"\n[DEBUG SAMPLE] {symbol} - Last 5 rows:")
                    sample_cols = ['Dhigh', 'Highest_1M', 'Highest_3M', 'Highest_6M', 'Highest_1Y', 'Highest_2Y']
                    available_cols = [c for c in sample_cols if c in df.columns]
                    if available_cols:
                        logger.info(f"\n{df[available_cols].tail(5).to_string()}")

                    # Check if Dhigh > Highest_1M anywhere
                    if 'Dhigh' in df.columns and 'Highest_1M' in df.columns:
                        dhigh_values = df['Dhigh'].dropna()
                        highest_1m_values = df['Highest_1M'].dropna()
                        if len(dhigh_values) > 0 and len(highest_1m_values) > 0:
                            logger.info(f"\n[DEBUG] Dhigh range: {dhigh_values.min():.2f} - {dhigh_values.max():.2f}")
                            logger.info(f"[DEBUG] Highest_1M range: {highest_1m_values.min():.2f} - {highest_1m_values.max():.2f}")

                            # Count how many times Dhigh > Highest_1M
                            breakout_mask = df['Dhigh'] > df['Highest_1M']
                            breakout_count_debug = breakout_mask.sum()
                            logger.info(f"[DEBUG] Days where Dhigh > Highest_1M: {breakout_count_debug} / {len(df)}")

                            if breakout_count_debug > 0:
                                logger.info(f"[DEBUG] Sample breakout rows:")
                                breakout_rows = df[breakout_mask][['Dhigh', 'Highest_1M']].head(3)
                                logger.info(f"\n{breakout_rows.to_string()}")

                # Initialize signal columns for backtest
                df['BuySig'] = 0.0  # Date-specific buy signals
                df['SellSig'] = 0.0  # Will be determined by backtest service (losscut/target)
                df['signal'] = 0.0  # Same as BuySig
                if 'Type' not in df.columns:
                    df['Type'] = 'Staged'  # Mark as staged pipeline candidate

                # Check ENTIRE DataFrame - pass if ANY day has breakout
                any_breakout_found = False
                breakout_count = 0
                max_signal = 0.0
                symbol_breakouts = {
                    '1M': False,
                    '3M': False,
                    '6M': False,
                    '1Y': False,
                    '2Y': False
                }

                for i in range(len(df)):
                    current = df.iloc[i]

                    # PRIMARY CONDITION: Check for breakout (current high > previous Highest)
                    breakout_detected = False
                    day_signal = 0.0

                    if 'Dhigh' in current:
                        current_high = current['Dhigh']

                        if not pd.isna(current_high) and current_high > 0:
                            # Check breakout for each timeframe
                            for timeframe_col, weight, timeframe_name in [
                                ('Highest_1M', 0.5, '1M'),   # 1 month breakout
                                ('Highest_3M', 0.5, '3M'),   # 3 month breakout
                                ('Highest_6M', 0.5, '6M'),   # 6 month breakout
                                ('Highest_1Y', 0.5, '1Y'),   # 1 year breakout
                                ('Highest_2Y', 0.5, '2Y')    # 2 year breakout
                            ]:
                                if timeframe_col in current:
                                    highest_val = current[timeframe_col]
                                    if not pd.isna(highest_val) and highest_val > 0:
                                        # Breakout: current high > previous highest
                                        if current_high > highest_val:
                                            day_signal += weight
                                            breakout_detected = True
                                            symbol_breakouts[timeframe_name] = True

                    if breakout_detected:
                        # SECONDARY CONDITIONS (only checked if breakout detected)

                        # Trend alignment - SMA20 > SMA50
                        if 'SMA20' in current and 'SMA50' in current:
                            if not pd.isna(current['SMA20']) and not pd.isna(current['SMA50']):
                                if current['SMA20'] > current['SMA50']:
                                    day_signal += 0.5

                        # Track best signal across all days
                        if day_signal > max_signal:
                            max_signal = day_signal

                        any_breakout_found = True
                        breakout_count += 1

                    # Store date-specific signal values in DataFrame
                    df.loc[df.index[i], 'BuySig'] = day_signal
                    df.loc[df.index[i], 'signal'] = day_signal  # Same as BuySig

                # Update statistics for this symbol's breakouts
                if symbol_breakouts['1M']:
                    stats['breakout_1m_count'] += 1
                if symbol_breakouts['3M']:
                    stats['breakout_3m_count'] += 1
                if symbol_breakouts['6M']:
                    stats['breakout_6m_count'] += 1
                if symbol_breakouts['1Y']:
                    stats['breakout_1y_count'] += 1
                if symbol_breakouts['2Y']:
                    stats['breakout_2y_count'] += 1
                if any_breakout_found:
                    stats['any_breakout_count'] += 1

                # Signal = max signal found across entire period
                signal = max_signal if any_breakout_found else 0.0
                signals[symbol] = signal

                # Debug logging
                if any_breakout_found:
                    logger.info(f"[Daily Stage] {symbol} PASSED - {breakout_count}/{len(df)} days had breakouts (max signal: {max_signal:.2f})")
                else:
                    logger.debug(f"[Daily Stage] {symbol} FAILED - no breakouts in entire period")

                # Pass if signal >= threshold (at least one day had breakout)
                if signal >= self.thresholds['D']:
                    passed_symbols.add(symbol)

                # Update DataFrame in dictionary with signal columns
                df_D[symbol] = df
                signal_days = (df['BuySig'] > 0).sum()
                logger.debug(f"[Daily Stage] {symbol} - Signal columns added: {signal_days} days with signals (total: {df['BuySig'].sum():.2f})")

            except Exception as e:
                logger.debug(f"Error processing daily for {symbol}: {e}")
                continue

        # Print detailed statistics
        logger.info("\n" + "="*80)
        logger.info("DAILY STAGE DIAGNOSTIC STATISTICS")
        logger.info("="*80)

        total = stats['total_symbols']
        if total > 0:
            logger.info(f"\nTotal symbols processed: {total}")
            logger.info(f"\n[Column Availability]")
            logger.info(f"  Symbols with Dhigh:      {stats['symbols_with_dhigh']:>6} / {total:>6} ({stats['symbols_with_dhigh']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with Highest_1M: {stats['symbols_with_highest_1m']:>6} / {total:>6} ({stats['symbols_with_highest_1m']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with Highest_3M: {stats['symbols_with_highest_3m']:>6} / {total:>6} ({stats['symbols_with_highest_3m']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with Highest_6M: {stats['symbols_with_highest_6m']:>6} / {total:>6} ({stats['symbols_with_highest_6m']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with Highest_1Y: {stats['symbols_with_highest_1y']:>6} / {total:>6} ({stats['symbols_with_highest_1y']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with Highest_2Y: {stats['symbols_with_highest_2y']:>6} / {total:>6} ({stats['symbols_with_highest_2y']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with SMA20:      {stats['symbols_with_sma20']:>6} / {total:>6} ({stats['symbols_with_sma20']/total*100:>6.2f}%)")
            logger.info(f"  Symbols with SMA50:      {stats['symbols_with_sma50']:>6} / {total:>6} ({stats['symbols_with_sma50']/total*100:>6.2f}%)")

            logger.info(f"\n[Breakout Conditions Met]")
            logger.info(f"  Highest_1M breakout:     {stats['breakout_1m_count']:>6} / {total:>6} ({stats['breakout_1m_count']/total*100:>6.2f}%)")
            logger.info(f"  Highest_3M breakout:     {stats['breakout_3m_count']:>6} / {total:>6} ({stats['breakout_3m_count']/total*100:>6.2f}%)")
            logger.info(f"  Highest_6M breakout:     {stats['breakout_6m_count']:>6} / {total:>6} ({stats['breakout_6m_count']/total*100:>6.2f}%)")
            logger.info(f"  Highest_1Y breakout:     {stats['breakout_1y_count']:>6} / {total:>6} ({stats['breakout_1y_count']/total*100:>6.2f}%)")
            logger.info(f"  Highest_2Y breakout:     {stats['breakout_2y_count']:>6} / {total:>6} ({stats['breakout_2y_count']/total*100:>6.2f}%)")
            logger.info(f"  ANY breakout detected:   {stats['any_breakout_count']:>6} / {total:>6} ({stats['any_breakout_count']/total*100:>6.2f}%)")

            logger.info(f"\n[Final Results]")
            logger.info(f"  Threshold: {self.thresholds['D']}")
            logger.info(f"  Passed symbols:          {len(passed_symbols):>6} / {total:>6} ({len(passed_symbols)/total*100:>6.2f}%)")

        logger.info("="*80 + "\n")

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

        stages = ['W', 'F', 'E', 'RS', 'D']
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

        stages = ['W', 'F', 'E', 'RS', 'D']
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
