"""
Strategy Combiner - Strategy Agent Management

Combines multiple YAML strategies into composite strategies.
Supports AND, OR, and WEIGHTED combination methods.

Owner: Strategy Agent
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from project.strategy.yaml_strategy_loader import YAMLStrategyLoader, LoadedStrategy
from project.strategy.yaml_strategy_executor import YAMLStrategyExecutor

logger = logging.getLogger(__name__)


class CombinationMethod(Enum):
    """Strategy combination methods"""
    AND = "AND"           # All strategies must signal
    OR = "OR"             # Any strategy can signal
    WEIGHTED = "WEIGHTED" # Weighted voting system
    MAJORITY = "MAJORITY" # Majority vote


class StrategyCombiner:
    """
    Combines multiple strategies into composite strategies

    Responsibilities:
    - Load multiple YAML strategies
    - Execute all strategies on same data
    - Combine signals using specified method
    - Generate composite entry/exit signals
    - Track individual strategy performance
    """

    def __init__(self,
                 loader: Optional[YAMLStrategyLoader] = None,
                 executor: Optional[YAMLStrategyExecutor] = None):
        """
        Initialize Strategy Combiner

        Args:
            loader: Strategy loader instance
            executor: Strategy executor instance
        """
        self.loader = loader or YAMLStrategyLoader()
        self.executor = executor or YAMLStrategyExecutor()

        logger.info("Initialized StrategyCombiner")

    def load_strategies(self, yaml_paths: List[str]) -> Tuple[List[LoadedStrategy], List[str]]:
        """
        Load multiple strategies from YAML files

        Args:
            yaml_paths: List of paths to YAML strategy files

        Returns:
            Tuple of (loaded_strategies, error_messages)
        """
        strategies = []
        errors = []

        for yaml_path in yaml_paths:
            success, strategy, errs = self.loader.load_from_file(yaml_path)

            if success and strategy:
                strategies.append(strategy)
                logger.info(f"[OK] Loaded strategy: {strategy.name}")
            else:
                errors.extend(errs)
                logger.error(f"[FAILED] Could not load: {yaml_path}")

        return strategies, errors

    def combine_strategies(self,
                          strategies: List[LoadedStrategy],
                          data: Dict[str, pd.DataFrame],
                          method: CombinationMethod = CombinationMethod.AND,
                          weights: Optional[List[float]] = None,
                          calculate_indicators: bool = True) -> Dict[str, Any]:
        """
        Combine multiple strategies into composite signals

        Args:
            strategies: List of loaded strategies
            data: Market data dictionary
            method: Combination method (AND, OR, WEIGHTED, MAJORITY)
            weights: Weights for WEIGHTED method (must sum to 1.0)
            calculate_indicators: Auto-calculate missing indicators

        Returns:
            Dictionary with combined results
        """
        logger.info(f"Combining {len(strategies)} strategies using {method.value} method")

        # Validate inputs
        if method == CombinationMethod.WEIGHTED:
            if weights is None or len(weights) != len(strategies):
                raise ValueError(f"WEIGHTED method requires {len(strategies)} weights")
            if not np.isclose(sum(weights), 1.0):
                raise ValueError(f"Weights must sum to 1.0, got {sum(weights)}")

        # Execute all strategies
        strategy_results = []
        for i, strategy in enumerate(strategies):
            logger.info(f"Executing strategy {i+1}/{len(strategies)}: {strategy.name}")

            results = self.executor.execute_strategy(
                strategy=strategy,
                data=data,
                calculate_indicators=calculate_indicators
            )

            strategy_results.append({
                'strategy': strategy,
                'results': results,
                'weight': weights[i] if weights else 1.0 / len(strategies)
            })

        # Combine signals
        combined_signals = self._combine_signals(
            strategy_results=strategy_results,
            method=method,
            symbols=list(data.keys())
        )

        # Package results
        composite_results = {
            'method': method.value,
            'num_strategies': len(strategies),
            'strategy_names': [s.name for s in strategies],
            'weights': weights,
            'individual_results': strategy_results,
            'combined_signals': combined_signals,
            'metadata': self._calculate_composite_metadata(combined_signals)
        }

        return composite_results

    def _combine_signals(self,
                        strategy_results: List[Dict],
                        method: CombinationMethod,
                        symbols: List[str]) -> Dict[str, Any]:
        """
        Combine signals from multiple strategies

        Args:
            strategy_results: List of strategy execution results
            method: Combination method
            symbols: List of symbols

        Returns:
            Dictionary with combined signals for each symbol
        """
        combined = {}

        for symbol in symbols:
            # Collect entry signals from all strategies
            entry_signals = []
            exit_signals = []

            for result in strategy_results:
                signals = result['results']['signals'].get(symbol, {})

                if 'error' not in signals:
                    entry_signals.append(signals['entry'])

                    # Collect exit signals if available
                    if 'exit' in signals and 'signal_exit' in signals['exit']:
                        exit_signals.append(signals['exit']['signal_exit'])

            if not entry_signals:
                # No valid signals for this symbol
                combined[symbol] = {
                    'entry': pd.Series(False, index=strategy_results[0]['results']['signals'][symbol]['data'].index),
                    'exit': pd.Series(False, index=strategy_results[0]['results']['signals'][symbol]['data'].index),
                    'num_strategies_signaled': 0,
                    'strategy_votes': []
                }
                continue

            # Combine entry signals based on method
            if method == CombinationMethod.AND:
                combined_entry = self._combine_and(entry_signals)

            elif method == CombinationMethod.OR:
                combined_entry = self._combine_or(entry_signals)

            elif method == CombinationMethod.WEIGHTED:
                weights = [r['weight'] for r in strategy_results if 'error' not in r['results']['signals'].get(symbol, {})]
                combined_entry = self._combine_weighted(entry_signals, weights)

            elif method == CombinationMethod.MAJORITY:
                combined_entry = self._combine_majority(entry_signals)

            else:
                raise ValueError(f"Unknown combination method: {method}")

            # Combine exit signals (using OR - exit if any strategy signals)
            if exit_signals:
                combined_exit = self._combine_or(exit_signals)
            else:
                combined_exit = pd.Series(False, index=combined_entry.index)

            # Track which strategies voted
            strategy_votes = [sig.astype(int) for sig in entry_signals]

            combined[symbol] = {
                'entry': combined_entry,
                'exit': combined_exit,
                'num_strategies_signaled': sum(sig.sum() > 0 for sig in entry_signals),
                'strategy_votes': strategy_votes,
                'total_entry_signals': int(combined_entry.sum()),
                'total_exit_signals': int(combined_exit.sum())
            }

        return combined

    def _combine_and(self, signals: List[pd.Series]) -> pd.Series:
        """Combine signals using AND logic (all must agree)"""
        result = signals[0].copy()
        for sig in signals[1:]:
            result = result & sig
        return result

    def _combine_or(self, signals: List[pd.Series]) -> pd.Series:
        """Combine signals using OR logic (any can trigger)"""
        result = signals[0].copy()
        for sig in signals[1:]:
            result = result | sig
        return result

    def _combine_weighted(self, signals: List[pd.Series], weights: List[float]) -> pd.Series:
        """
        Combine signals using weighted voting

        A signal is triggered if weighted sum >= 0.5
        """
        # Convert boolean to int
        signal_values = [sig.astype(float) for sig in signals]

        # Calculate weighted sum
        weighted_sum = sum(sig * weight for sig, weight in zip(signal_values, weights))

        # Threshold at 0.5
        result = weighted_sum >= 0.5

        return result

    def _combine_majority(self, signals: List[pd.Series]) -> pd.Series:
        """
        Combine signals using majority vote

        A signal is triggered if more than 50% of strategies agree
        """
        # Sum signals
        signal_sum = sum(sig.astype(int) for sig in signals)

        # Majority threshold
        threshold = len(signals) / 2.0

        result = signal_sum > threshold

        return result

    def _calculate_composite_metadata(self, combined_signals: Dict) -> Dict:
        """
        Calculate metadata for composite strategy

        Args:
            combined_signals: Combined signals dictionary

        Returns:
            Metadata dictionary
        """
        total_symbols = len(combined_signals)
        symbols_with_signals = sum(1 for s in combined_signals.values() if s['total_entry_signals'] > 0)
        total_entry_signals = sum(s['total_entry_signals'] for s in combined_signals.values())

        return {
            'total_symbols': total_symbols,
            'symbols_with_signals': symbols_with_signals,
            'total_entry_signals': total_entry_signals,
            'avg_signals_per_symbol': total_entry_signals / total_symbols if total_symbols > 0 else 0
        }


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    from pathlib import Path

    # Test combiner
    combiner = StrategyCombiner()

    # Load RSI strategy (we only have one for now, but testing framework)
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    strategies, errors = combiner.load_strategies([str(yaml_path)])

    if errors:
        print(f"[FAILED] Errors: {errors}")
    else:
        print(f"[OK] Loaded {len(strategies)} strategies")

        # Create test data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = {}
        for symbol in ['AAPL', 'MSFT']:
            df = pd.DataFrame({
                'open': 100 + np.cumsum(np.random.randn(100) * 2),
                'high': 102 + np.cumsum(np.random.randn(100) * 2),
                'low': 98 + np.cumsum(np.random.randn(100) * 2),
                'close': 100 + np.cumsum(np.random.randn(100) * 2),
                'volume': 1000000 + np.random.randint(-100000, 100000, 100)
            }, index=dates)
            data[symbol] = df

        # Test combination (with single strategy, should work same as individual)
        print("\n" + "=" * 60)
        print("STRATEGY COMBINER TEST")
        print("=" * 60)

        results = combiner.combine_strategies(
            strategies=strategies,
            data=data,
            method=CombinationMethod.AND,
            calculate_indicators=True
        )

        print(f"Method: {results['method']}")
        print(f"Strategies: {results['num_strategies']}")
        print(f"Total symbols: {results['metadata']['total_symbols']}")
        print(f"Symbols with signals: {results['metadata']['symbols_with_signals']}")
        print(f"Total entry signals: {results['metadata']['total_entry_signals']}")

        print("=" * 60)
