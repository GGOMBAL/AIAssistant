"""
YAML Strategy Executor - Strategy Agent Management

Executes YAML-defined strategies on market data.
Generates entry/exit signals based on strategy rules.

Owner: Strategy Agent
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from project.strategy.yaml_strategy_loader import YAMLStrategyLoader, LoadedStrategy
from project.strategy.condition_evaluator import ConditionEvaluator

logger = logging.getLogger(__name__)


class YAMLStrategyExecutor:
    """
    Executes YAML-defined strategies

    Responsibilities:
    - Accept LoadedStrategy object
    - Calculate required indicators
    - Evaluate entry/exit conditions
    - Generate trading signals
    - Apply filters
    - Return signals with metadata
    """

    def __init__(self, loader: Optional[YAMLStrategyLoader] = None,
                 evaluator: Optional[ConditionEvaluator] = None):
        """
        Initialize YAML Strategy Executor

        Args:
            loader: Strategy loader instance
            evaluator: Condition evaluator instance
        """
        if loader is None:
            self.loader = YAMLStrategyLoader()
        else:
            self.loader = loader

        if evaluator is None:
            self.evaluator = ConditionEvaluator()
        else:
            self.evaluator = evaluator

        logger.info("Initialized YAMLStrategyExecutor")

    def execute_strategy(self, strategy: LoadedStrategy,
                        data: Dict[str, pd.DataFrame],
                        calculate_indicators: bool = False) -> Dict[str, Any]:
        """
        Execute strategy on data

        Args:
            strategy: Loaded strategy object
            data: Dictionary mapping symbol -> DataFrame with OHLCV data
            calculate_indicators: If True, will attempt to calculate missing indicators

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing strategy: {strategy.name}")

        results = {
            'strategy_name': strategy.name,
            'strategy_version': strategy.version,
            'symbols': list(data.keys()),
            'signals': {},
            'metadata': {}
        }

        # Execute strategy for each symbol
        for symbol, df in data.items():
            try:
                symbol_signals = self.execute_for_symbol(
                    strategy=strategy,
                    symbol=symbol,
                    df=df,
                    calculate_indicators=calculate_indicators
                )

                results['signals'][symbol] = symbol_signals

            except Exception as e:
                logger.error(f"Error executing strategy for {symbol}: {e}")
                results['signals'][symbol] = {
                    'error': str(e),
                    'entry': pd.Series(False, index=df.index),
                    'exit': {}
                }

        # Add summary statistics
        results['metadata'] = self._calculate_summary(results['signals'])

        return results

    def execute_for_symbol(self, strategy: LoadedStrategy,
                          symbol: str,
                          df: pd.DataFrame,
                          calculate_indicators: bool = False) -> Dict[str, Any]:
        """
        Execute strategy for a single symbol

        Args:
            strategy: Loaded strategy
            symbol: Symbol name
            df: DataFrame with OHLCV data
            calculate_indicators: If True, calculate missing indicators

        Returns:
            Dictionary with signals and metadata for this symbol
        """
        logger.debug(f"Executing strategy for symbol: {symbol}")

        # Step 1: Verify required columns exist
        missing_indicators = self._check_missing_indicators(strategy, df)

        if missing_indicators and calculate_indicators:
            logger.warning(f"Missing indicators for {symbol}: {missing_indicators}")
            logger.warning("Indicator calculation not yet implemented")
            # TODO: Implement indicator calculation

        # Step 2: Apply filters
        filter_result = self.evaluator.evaluate_filters(strategy.filters, df)

        # Step 3: Evaluate entry conditions
        entry_signals = self.evaluator.evaluate_entry_conditions(strategy, df)

        # Step 4: Combine entry signals with filters
        final_entry = entry_signals & filter_result

        # Step 5: Evaluate exit conditions
        exit_signals = self.evaluator.evaluate_exit_conditions(strategy, df)

        # Step 6: Package results
        result = {
            'symbol': symbol,
            'entry': final_entry,
            'entry_raw': entry_signals,  # Before filters
            'filter_pass': filter_result,
            'exit': exit_signals,
            'dates': df.index,
            'data': df,
            'stats': {
                'total_periods': len(df),
                'entry_signals': final_entry.sum(),
                'entry_rate': final_entry.sum() / len(df) if len(df) > 0 else 0,
                'filter_pass_rate': filter_result.sum() / len(df) if len(df) > 0 else 0
            }
        }

        return result

    def _check_missing_indicators(self, strategy: LoadedStrategy,
                                  df: pd.DataFrame) -> List[str]:
        """
        Check which indicators are missing from DataFrame

        Args:
            strategy: Loaded strategy
            df: DataFrame

        Returns:
            List of missing indicator names
        """
        required_indicators = strategy.get_indicator_names()
        missing = []

        for ind_name in required_indicators:
            if ind_name not in df.columns:
                missing.append(ind_name)

        return missing

    def _calculate_summary(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate summary statistics across all symbols

        Args:
            signals: Dictionary of symbol signals

        Returns:
            Summary statistics
        """
        total_symbols = len(signals)
        symbols_with_signals = 0
        total_entry_signals = 0

        for symbol, symbol_data in signals.items():
            if 'error' not in symbol_data:
                entry = symbol_data.get('entry', pd.Series(False))
                if entry.sum() > 0:
                    symbols_with_signals += 1
                total_entry_signals += entry.sum()

        return {
            'total_symbols': total_symbols,
            'symbols_with_signals': symbols_with_signals,
            'total_entry_signals': int(total_entry_signals),
            'avg_signals_per_symbol': total_entry_signals / total_symbols if total_symbols > 0 else 0
        }

    def get_current_signals(self, strategy: LoadedStrategy,
                           data: Dict[str, pd.DataFrame],
                           date: Optional[datetime] = None) -> Dict[str, bool]:
        """
        Get current entry signals for all symbols on a specific date

        Args:
            strategy: Loaded strategy
            data: Dictionary of symbol data
            date: Date to check (default: latest date)

        Returns:
            Dictionary mapping symbol -> entry signal (True/False)
        """
        current_signals = {}

        for symbol, df in data.items():
            try:
                # Execute for symbol
                result = self.execute_for_symbol(strategy, symbol, df)

                # Get signal for specified date
                if date is None:
                    # Use latest date
                    signal = result['entry'].iloc[-1] if len(result['entry']) > 0 else False
                else:
                    # Find signal for specific date
                    if date in result['entry'].index:
                        signal = result['entry'].loc[date]
                    else:
                        signal = False

                current_signals[symbol] = bool(signal)

            except Exception as e:
                logger.error(f"Error getting signal for {symbol}: {e}")
                current_signals[symbol] = False

        return current_signals

    def backtest_strategy(self, strategy: LoadedStrategy,
                         data: Dict[str, pd.DataFrame],
                         initial_capital: float = 100000000.0) -> Dict[str, Any]:
        """
        Simple backtest of strategy (basic version)

        Args:
            strategy: Loaded strategy
            data: Dictionary of symbol data
            initial_capital: Starting capital

        Returns:
            Backtest results dictionary
        """
        logger.info(f"Backtesting strategy: {strategy.name}")

        # Execute strategy to get signals
        execution_results = self.execute_strategy(strategy, data)

        # For Phase 2, we'll return execution results
        # In Phase 4, this will integrate with full backtest engine
        backtest_results = {
            'strategy': strategy.name,
            'initial_capital': initial_capital,
            'execution_results': execution_results,
            'note': 'Full backtest integration pending (Phase 4)'
        }

        return backtest_results


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test executor
    from pathlib import Path

    # Load strategy
    loader = YAMLStrategyLoader()
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    success, strategy, errors = loader.load_from_file(str(yaml_path))

    if success and strategy:
        # Create sample data for multiple symbols
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        data = {}
        for symbol in ['AAPL', 'MSFT', 'GOOGL']:
            df = pd.DataFrame({
                'close': 100 + np.cumsum(np.random.randn(100) * 2),
                'high': 102 + np.cumsum(np.random.randn(100) * 2),
                'low': 98 + np.cumsum(np.random.randn(100) * 2),
                'volume': 1000000 + np.random.randint(-100000, 100000, 100)
            }, index=dates)

            # Add mock indicators
            df['RSI_14'] = 50 + np.random.randn(100) * 15
            df['SMA_20'] = df['close'].rolling(20).mean()
            df['SMA_50'] = df['close'].rolling(50).mean()
            df['Volume_SMA_20'] = df['volume'].rolling(20).mean()
            df['RS_Rating'] = 50 + np.random.randn(100) * 20

            data[symbol] = df

        # Execute strategy
        executor = YAMLStrategyExecutor()
        results = executor.execute_strategy(strategy, data)

        # Print results
        print("=" * 60)
        print("YAML STRATEGY EXECUTOR TEST")
        print("=" * 60)
        print(f"Strategy: {results['strategy_name']} v{results['strategy_version']}")
        print(f"\nSymbols tested: {len(results['symbols'])}")
        print(f"Symbols with signals: {results['metadata']['symbols_with_signals']}")
        print(f"Total entry signals: {results['metadata']['total_entry_signals']}")
        print(f"Avg signals per symbol: {results['metadata']['avg_signals_per_symbol']:.2f}")

        print(f"\nPer-Symbol Results:")
        for symbol in results['symbols']:
            signal_data = results['signals'][symbol]
            if 'error' not in signal_data:
                stats = signal_data['stats']
                print(f"  {symbol}:")
                print(f"    Entry signals: {stats['entry_signals']}")
                print(f"    Entry rate: {stats['entry_rate']*100:.1f}%")
                print(f"    Filter pass rate: {stats['filter_pass_rate']*100:.1f}%")

        print("=" * 60)

        # Test current signals
        print("\nCurrent Signals (latest date):")
        current = executor.get_current_signals(strategy, data)
        for symbol, signal in current.items():
            print(f"  {symbol}: {'BUY' if signal else 'HOLD'}")
        print("=" * 60)

    else:
        print("[FAILED] Could not load strategy")
