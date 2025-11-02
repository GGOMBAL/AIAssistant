#!/usr/bin/env python3
"""
Staged Data Loader - Indicator Layer
단계별 데이터 로딩 서비스

Architecture: Load data stage-by-stage based on filtered symbols
E → F → W → RS → D
"""

import pandas as pd
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import logging

from project.database.mongodb_operations import MongoDBOperations
from project.indicator.data_frame_generator import DataFrameGenerator

# Setup logging
logger = logging.getLogger(__name__)


class StagedDataLoader:
    """
    단계별 데이터 로딩 서비스

    각 단계에서 필터링된 종목만 다음 단계 데이터를 로드하여
    불필요한 데이터 로딩을 최소화
    """

    def __init__(self, market: str = 'US', area: str = 'US',
                 start_day: datetime = None, end_day: datetime = None, is_backtest: bool = False):
        """
        Initialize staged data loader

        Args:
            market: Market identifier (US, KR)
            area: Area identifier (US, KR)
            start_day: Start date for data loading
            end_day: End date for data loading
            is_backtest: True for backtest mode (prevents future reference), False for live trading
        """
        self.market = market
        self.area = area
        self.start_day = start_day or (datetime.now() - timedelta(days=365*3))
        self.end_day = end_day or datetime.now()
        self.is_backtest = is_backtest

        # Single MongoDB connection for all operations
        self.db = MongoDBOperations(db_address="MONGODB_LOCAL")

        # Data storage
        self.data = {
            'E': {},  # Earnings data
            'F': {},  # Fundamental data
            'W': {},  # Weekly data
            'RS': {}, # Relative Strength data
            'D': {}   # Daily data
        }

    def load_stage_data(self, stage: str, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        특정 단계의 데이터 로드

        Args:
            stage: Stage identifier ('E', 'F', 'W', 'RS', 'D')
            symbols: List of symbols to load

        Returns:
            Dictionary of {symbol: DataFrame}
        """
        logger.info(f"Loading {stage} data for {len(symbols)} symbols")

        # Create DataFrameGenerator for this stage
        df_generator = DataFrameGenerator(
            universe=symbols,
            market=self.market,
            area=self.area,
            start_day=self.start_day,
            end_day=self.end_day,
            is_backtest=self.is_backtest
        )

        # Load data from database
        df_generator.load_data_from_database()
        all_data = df_generator.get_dataframes()

        # Extract data for this stage
        if stage == 'E':
            stage_data = all_data.get('df_E', {})
        elif stage == 'F':
            stage_data = all_data.get('df_F', {})
        elif stage == 'W':
            stage_data = all_data.get('df_W', {})
        elif stage == 'RS':
            stage_data = all_data.get('df_RS', {})
        elif stage == 'D':
            stage_data = all_data.get('df_D', {})
        else:
            stage_data = {}

        # Store in cache
        self.data[stage].update(stage_data)

        logger.info(f"Loaded {stage} data: {len(stage_data)} symbols with data")
        return stage_data

    def load_stage_E(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Stage 1: Load Earnings data

        Args:
            symbols: Initial universe of symbols

        Returns:
            Dictionary of {symbol: DataFrame} for earnings data
        """
        return self.load_stage_data('E', symbols)

    def load_stage_F(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Stage 2: Load Fundamental data

        Args:
            symbols: Filtered symbols from Stage E

        Returns:
            Dictionary of {symbol: DataFrame} for fundamental data
        """
        return self.load_stage_data('F', symbols)

    def load_stage_W(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Stage 3: Load Weekly data

        Args:
            symbols: Filtered symbols from Stage F

        Returns:
            Dictionary of {symbol: DataFrame} for weekly data
        """
        return self.load_stage_data('W', symbols)

    def load_stage_RS(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Stage 4: Load RS data

        Args:
            symbols: Filtered symbols from Stage W

        Returns:
            Dictionary of {symbol: DataFrame} for RS data
        """
        return self.load_stage_data('RS', symbols)

    def load_stage_D(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Stage 5: Load Daily data

        Args:
            symbols: Filtered symbols from Stage RS

        Returns:
            Dictionary of {symbol: DataFrame} for daily data
        """
        return self.load_stage_data('D', symbols)

    def get_all_loaded_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get all loaded data across all stages

        Returns:
            Dictionary of {stage: {symbol: DataFrame}}
        """
        return self.data

    def get_loading_summary(self) -> str:
        """
        Get formatted loading summary

        Returns:
            Formatted string with loading statistics
        """
        summary = "\n" + "="*80 + "\n"
        summary += "STAGED DATA LOADING SUMMARY\n"
        summary += "="*80 + "\n\n"

        stages = ['W', 'F', 'E', 'RS', 'D']
        stage_names = {
            'W': 'Weekly',
            'F': 'Fundamental',
            'E': 'Earnings',
            'RS': 'Relative Strength',
            'D': 'Daily'
        }

        for i, stage in enumerate(stages):
            count = len(self.data.get(stage, {}))
            summary += f"Stage {i+1}: {stage_names[stage]:<20} {count:>6} symbols loaded\n"

        summary += "\n" + "="*80 + "\n"
        return summary

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
