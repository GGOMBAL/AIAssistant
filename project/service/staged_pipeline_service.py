#!/usr/bin/env python3
"""
Staged Pipeline Service - Service Layer
단계별 필터링 파이프라인 통합 서비스

Complete workflow: Database → Indicator → Strategy
E → F → W → RS → D
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time

from project.indicator.staged_data_loader import StagedDataLoader
from project.strategy.staged_signal_service import StagedSignalService

# Setup logging
logger = logging.getLogger(__name__)


class StagedPipelineService:
    """
    단계별 필터링 파이프라인 서비스

    Complete Flow:
    1. Load E data (all symbols) → Generate E signals → Filter
    2. Load F data (E-passed symbols) → Generate F signals → Filter
    3. Load W data (F-passed symbols) → Generate W signals → Filter
    4. Load RS data (W-passed symbols) → Generate RS signals → Filter
    5. Load D data (RS-passed symbols) → Generate D signals → Final candidates
    """

    def __init__(self, config: dict, market: str = 'US', area: str = 'US',
                 start_day: datetime = None, end_day: datetime = None):
        """
        Initialize staged pipeline service

        Args:
            config: Configuration dictionary
            market: Market identifier
            area: Area identifier
            start_day: Start date
            end_day: End date
        """
        self.config = config
        self.market = market
        self.area = area
        self.start_day = start_day or (datetime.now() - timedelta(days=365*3))
        self.end_day = end_day or datetime.now()

        # Initialize services
        self.data_loader = StagedDataLoader(
            market=market,
            area=area,
            start_day=start_day,
            end_day=end_day
        )

        self.signal_service = StagedSignalService(config=config)

        # Performance tracking
        self.performance_stats = {}

    def run_staged_pipeline(self, initial_universe: List[str]) -> Dict[str, Any]:
        """
        Run complete staged filtering pipeline

        Args:
            initial_universe: Initial list of symbols to process

        Returns:
            Final trading candidates and pipeline statistics
        """
        logger.info(f"Starting staged pipeline with {len(initial_universe)} symbols")
        pipeline_start = time.time()

        results = {
            'stages': {},
            'final_candidates': [],
            'performance': {},
            'data_summary': {},
            'signal_summary': {}
        }

        try:
            # ========== Stage 1: Earnings (E) ==========
            logger.info("\n" + "="*80)
            logger.info("Stage 1: Earnings Filter")
            logger.info("="*80)
            stage1_start = time.time()

            # Load E data for all symbols
            df_E = self.data_loader.load_stage_E(initial_universe)
            logger.info(f"Loaded E data: {len(df_E)} symbols")

            # Generate E signals
            stage1_result = self.signal_service._stage_earnings_signal(initial_universe, df_E)
            results['stages']['E'] = stage1_result

            stage1_time = time.time() - stage1_start
            logger.info(f"Stage 1 complete: {stage1_result.total_passed}/{stage1_result.total_input} passed ({stage1_time:.2f}s)")

            # If no symbols passed, stop pipeline
            if stage1_result.total_passed == 0:
                logger.warning("No symbols passed Stage 1 (Earnings)")
                results['final_candidates'] = []
                results['total_candidates'] = 0
                return results

            # ========== Stage 2: Fundamental (F) ==========
            logger.info("\n" + "="*80)
            logger.info("Stage 2: Fundamental Filter")
            logger.info("="*80)
            stage2_start = time.time()

            # Load F data only for E-passed symbols
            stage2_symbols = list(stage1_result.passed_symbols)
            df_F = self.data_loader.load_stage_F(stage2_symbols)
            logger.info(f"Loaded F data: {len(df_F)} symbols")

            # Generate F signals
            stage2_result = self.signal_service._stage_fundamental_signal(stage1_result.passed_symbols, df_F)
            results['stages']['F'] = stage2_result

            stage2_time = time.time() - stage2_start
            logger.info(f"Stage 2 complete: {stage2_result.total_passed}/{stage2_result.total_input} passed ({stage2_time:.2f}s)")

            if stage2_result.total_passed == 0:
                logger.warning("No symbols passed Stage 2 (Fundamental)")
                results['final_candidates'] = []
                results['total_candidates'] = 0
                return results

            # ========== Stage 3: Weekly (W) ==========
            logger.info("\n" + "="*80)
            logger.info("Stage 3: Weekly Filter")
            logger.info("="*80)
            stage3_start = time.time()

            # Load W data only for F-passed symbols
            stage3_symbols = list(stage2_result.passed_symbols)
            df_W = self.data_loader.load_stage_W(stage3_symbols)
            logger.info(f"Loaded W data: {len(df_W)} symbols")

            # Generate W signals
            stage3_result = self.signal_service._stage_weekly_signal(stage2_result.passed_symbols, df_W)
            results['stages']['W'] = stage3_result

            stage3_time = time.time() - stage3_start
            logger.info(f"Stage 3 complete: {stage3_result.total_passed}/{stage3_result.total_input} passed ({stage3_time:.2f}s)")

            if stage3_result.total_passed == 0:
                logger.warning("No symbols passed Stage 3 (Weekly)")
                results['final_candidates'] = []
                results['total_candidates'] = 0
                return results

            # ========== Stage 4: Relative Strength (RS) ==========
            logger.info("\n" + "="*80)
            logger.info("Stage 4: Relative Strength Filter")
            logger.info("="*80)
            stage4_start = time.time()

            # Load RS data only for W-passed symbols
            stage4_symbols = list(stage3_result.passed_symbols)
            df_RS = self.data_loader.load_stage_RS(stage4_symbols)
            logger.info(f"Loaded RS data: {len(df_RS)} symbols")

            # Generate RS signals
            stage4_result = self.signal_service._stage_rs_signal(stage3_result.passed_symbols, df_RS)
            results['stages']['RS'] = stage4_result

            stage4_time = time.time() - stage4_start
            logger.info(f"Stage 4 complete: {stage4_result.total_passed}/{stage4_result.total_input} passed ({stage4_time:.2f}s)")

            if stage4_result.total_passed == 0:
                logger.warning("No symbols passed Stage 4 (RS)")
                results['final_candidates'] = []
                results['total_candidates'] = 0
                return results

            # ========== Stage 5: Daily (D) - Final ==========
            logger.info("\n" + "="*80)
            logger.info("Stage 5: Daily Filter (Final)")
            logger.info("="*80)
            stage5_start = time.time()

            # Load D data only for RS-passed symbols
            stage5_symbols = list(stage4_result.passed_symbols)
            df_D = self.data_loader.load_stage_D(stage5_symbols)
            logger.info(f"Loaded D data: {len(df_D)} symbols")

            # Generate final D signals
            stage5_result = self.signal_service._stage_daily_signal(
                stage4_result.passed_symbols,
                df_D,
                df_W,  # Need W data for context
                df_RS  # Need RS data for context
            )
            results['stages']['D'] = stage5_result

            stage5_time = time.time() - stage5_start
            logger.info(f"Stage 5 complete: {stage5_result.total_passed}/{stage5_result.total_input} passed ({stage5_time:.2f}s)")

            # ========== Compile Results ==========
            pipeline_time = time.time() - pipeline_start

            results['final_candidates'] = list(stage5_result.passed_symbols)
            results['total_candidates'] = len(stage5_result.passed_symbols)

            results['performance'] = {
                'total_time': f"{pipeline_time:.2f}s",
                'stage_times': {
                    'E': f"{stage1_time:.2f}s",
                    'F': f"{stage2_time:.2f}s",
                    'W': f"{stage3_time:.2f}s",
                    'RS': f"{stage4_time:.2f}s",
                    'D': f"{stage5_time:.2f}s"
                }
            }

            results['data_summary'] = self._create_data_summary()
            results['signal_summary'] = self.signal_service._create_funnel_summary()

            # Print summary
            print(self._format_pipeline_summary(results))

            return results

        except Exception as e:
            logger.error(f"Error in staged pipeline: {e}")
            import traceback
            traceback.print_exc()
            return results

    def _create_data_summary(self) -> Dict[str, int]:
        """Create summary of loaded data"""
        summary = {}
        all_data = self.data_loader.get_all_loaded_data()

        for stage, data in all_data.items():
            summary[stage] = len(data)

        return summary

    def _format_pipeline_summary(self, results: Dict[str, Any]) -> str:
        """Format pipeline results as readable summary"""
        summary = "\n" + "="*80 + "\n"
        summary += "STAGED PIPELINE EXECUTION SUMMARY\n"
        summary += "="*80 + "\n\n"

        # Funnel visualization
        summary += "Filtering Funnel:\n"
        summary += "-"*80 + "\n"

        stages = ['E', 'F', 'W', 'RS', 'D']
        stage_names = {
            'E': 'Earnings',
            'F': 'Fundamental',
            'W': 'Weekly',
            'RS': 'Relative Strength',
            'D': 'Daily'
        }

        for i, stage in enumerate(stages):
            if stage in results['stages']:
                stage_result = results['stages'][stage]
                reduction = stage_result.total_input - stage_result.total_passed
                summary += f"\nStage {i+1}: {stage_names[stage]}\n"
                summary += f"  Input:     {stage_result.total_input:>6} symbols\n"
                summary += f"  Passed:    {stage_result.total_passed:>6} symbols\n"
                summary += f"  Filtered:  {reduction:>6} symbols ({stage_result.filter_rate*100:.2f}%)\n"

        summary += "\n" + "-"*80 + "\n"
        summary += f"\nFinal Candidates: {results['total_candidates']} symbols\n"

        # Performance summary
        if 'performance' in results:
            perf = results['performance']
            summary += f"\nTotal Pipeline Time: {perf['total_time']}\n"

            summary += "\nStage Execution Times:\n"
            for stage, time_str in perf['stage_times'].items():
                summary += f"  {stage_names[stage]:<20}: {time_str}\n"

        summary += "\n" + "="*80 + "\n"

        return summary

    def get_final_candidates_with_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get final candidates with all their loaded data

        Returns:
            Dictionary of {symbol: {stage: DataFrame}}
        """
        final_candidates = {}
        all_data = self.data_loader.get_all_loaded_data()

        # Get final symbols from last stage
        if 'D' in self.signal_service.stage_results:
            final_symbols = self.signal_service.stage_results['D'].passed_symbols

            for symbol in final_symbols:
                final_candidates[symbol] = {}

                # Collect data from all stages
                for stage in ['E', 'F', 'W', 'RS', 'D']:
                    if symbol in all_data.get(stage, {}):
                        final_candidates[symbol][stage] = all_data[stage][symbol]

        return final_candidates

    def close(self):
        """Close all connections"""
        if self.data_loader:
            self.data_loader.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
