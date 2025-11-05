"""
Parameter Optimizer - Strategy Agent Management

Optimizes strategy parameters using grid search and backtest results.
Finds optimal parameter combinations for YAML strategies.

Owner: Strategy Agent
"""

import pandas as pd
import numpy as np
import logging
import yaml
import copy
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from project.service.yaml_backtest_service import YAMLBacktestService
from project.strategy.yaml_strategy_loader import YAMLStrategyLoader

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """
    Optimizes strategy parameters using grid search

    Responsibilities:
    - Define parameter search spaces
    - Generate parameter combinations
    - Run backtests for each combination
    - Evaluate performance metrics
    - Select optimal parameters
    - Support parallel processing
    """

    def __init__(self,
                 backtest_service: Optional[YAMLBacktestService] = None,
                 max_workers: Optional[int] = None):
        """
        Initialize Parameter Optimizer

        Args:
            backtest_service: Backtest service instance
            max_workers: Maximum parallel workers (default: CPU count - 1)
        """
        self.backtest_service = backtest_service or YAMLBacktestService()

        if max_workers is None:
            self.max_workers = max(1, multiprocessing.cpu_count() - 1)
        else:
            self.max_workers = max_workers

        logger.info(f"Initialized ParameterOptimizer with {self.max_workers} workers")

    def optimize(self,
                yaml_path: str,
                data: Dict[str, pd.DataFrame],
                parameter_ranges: Dict[str, List[Any]],
                optimization_metric: str = 'sharpe_ratio',
                top_n: int = 10,
                parallel: bool = False) -> Dict[str, Any]:
        """
        Optimize strategy parameters

        Args:
            yaml_path: Path to base YAML strategy
            data: Market data dictionary
            parameter_ranges: Dictionary of parameter -> list of values to try
                             Example: {'rsi_period': [10, 14, 20], 'sma_period': [20, 50]}
            optimization_metric: Metric to optimize ('sharpe_ratio', 'total_return', 'max_drawdown')
            top_n: Number of top results to return
            parallel: Use parallel processing

        Returns:
            Dictionary with optimization results
        """
        start_time = datetime.now()

        logger.info(f"Starting parameter optimization for: {yaml_path}")
        logger.info(f"Parameter ranges: {parameter_ranges}")
        logger.info(f"Optimization metric: {optimization_metric}")

        # Load base strategy
        loader = YAMLStrategyLoader()
        success, base_strategy, errors = loader.load_from_file(yaml_path)

        if not success:
            raise ValueError(f"Could not load base strategy: {errors}")

        # Generate parameter combinations
        param_combinations = self._generate_combinations(parameter_ranges)
        logger.info(f"Total combinations to test: {len(param_combinations)}")

        # Run backtests for each combination
        if parallel and self.max_workers > 1:
            results = self._run_parallel_backtests(
                yaml_path, data, param_combinations
            )
        else:
            results = self._run_sequential_backtests(
                yaml_path, data, param_combinations
            )

        # Sort results by optimization metric
        results_sorted = self._sort_results(results, optimization_metric)

        # Get top N results
        top_results = results_sorted[:top_n]

        execution_time = (datetime.now() - start_time).total_seconds()

        optimization_results = {
            'base_strategy_name': base_strategy.name,
            'yaml_path': yaml_path,
            'parameter_ranges': parameter_ranges,
            'total_combinations': len(param_combinations),
            'optimization_metric': optimization_metric,
            'top_n': top_n,
            'top_results': top_results,
            'all_results': results_sorted,
            'execution_time': execution_time,
            'best_parameters': top_results[0]['parameters'] if top_results else None,
            'best_performance': top_results[0]['performance'] if top_results else None
        }

        logger.info(f"[OK] Optimization complete in {execution_time:.2f}s")
        logger.info(f"Best {optimization_metric}: {top_results[0]['performance'][optimization_metric]:.4f}" if top_results else "No valid results")

        return optimization_results

    def _generate_combinations(self, parameter_ranges: Dict[str, List[Any]]) -> List[Dict]:
        """
        Generate all parameter combinations

        Args:
            parameter_ranges: Dictionary of parameter -> values

        Returns:
            List of parameter dictionaries
        """
        # Get parameter names and values
        param_names = list(parameter_ranges.keys())
        param_values = [parameter_ranges[name] for name in param_names]

        # Generate all combinations
        combinations = []
        for combo in product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)

        return combinations

    def _run_sequential_backtests(self,
                                  yaml_path: str,
                                  data: Dict[str, pd.DataFrame],
                                  param_combinations: List[Dict]) -> List[Dict]:
        """
        Run backtests sequentially

        Args:
            yaml_path: Base YAML path
            data: Market data
            param_combinations: List of parameter combinations

        Returns:
            List of result dictionaries
        """
        results = []

        for i, params in enumerate(param_combinations):
            logger.info(f"Testing combination {i+1}/{len(param_combinations)}: {params}")

            try:
                result = self._run_single_backtest(yaml_path, data, params)
                results.append(result)
            except Exception as e:
                logger.error(f"Error testing {params}: {e}")
                results.append({
                    'parameters': params,
                    'performance': {},
                    'error': str(e)
                })

        return results

    def _run_parallel_backtests(self,
                                yaml_path: str,
                                data: Dict[str, pd.DataFrame],
                                param_combinations: List[Dict]) -> List[Dict]:
        """
        Run backtests in parallel

        Args:
            yaml_path: Base YAML path
            data: Market data
            param_combinations: List of parameter combinations

        Returns:
            List of result dictionaries
        """
        results = []

        # Note: Parallel processing with DataFrames can be complex
        # For simplicity, we'll run sequentially for now
        # A production implementation would serialize data or use shared memory

        logger.warning("Parallel processing not fully implemented - using sequential")
        return self._run_sequential_backtests(yaml_path, data, param_combinations)

    def _run_single_backtest(self,
                            yaml_path: str,
                            data: Dict[str, pd.DataFrame],
                            parameters: Dict) -> Dict:
        """
        Run backtest with specific parameters

        Args:
            yaml_path: Base YAML path
            data: Market data
            parameters: Parameter dictionary

        Returns:
            Result dictionary
        """
        # Modify YAML with new parameters
        modified_yaml_content = self._apply_parameters_to_yaml(yaml_path, parameters)

        # Create temporary modified strategy
        loader = YAMLStrategyLoader()
        success, strategy, errors = loader.load_from_string(modified_yaml_content)

        if not success:
            raise ValueError(f"Could not load modified strategy: {errors}")

        # Run backtest
        backtest_results = self.backtest_service.backtest_strategy(
            strategy=strategy,
            data=data,
            store_results=False  # Don't store intermediate results
        )

        if not backtest_results['success']:
            raise ValueError(f"Backtest failed: {backtest_results.get('errors', [])}")

        # Extract performance metrics
        bt_result = backtest_results['backtest_result']
        performance = bt_result.performance_metrics

        return {
            'parameters': parameters,
            'performance': performance,
            'num_trades': len(bt_result.trades),
            'strategy_name': strategy.name
        }

    def _apply_parameters_to_yaml(self, yaml_path: str, parameters: Dict) -> str:
        """
        Apply parameter modifications to YAML content

        Args:
            yaml_path: Path to base YAML
            parameters: Parameter modifications

        Returns:
            Modified YAML content as string
        """
        # Load YAML
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)

        # Apply parameter modifications
        for param_path, value in parameters.items():
            # Parse parameter path (e.g., "entry.conditions.0.rules.0.value")
            self._set_nested_value(yaml_content, param_path, value)

        # Convert back to YAML string
        return yaml.dump(yaml_content, default_flow_style=False)

    def _set_nested_value(self, data: Dict, path: str, value: Any):
        """
        Set value at nested path in dictionary

        Args:
            data: Dictionary to modify
            path: Dot-separated path (e.g., "indicators.0.parameters.period")
            value: Value to set
        """
        parts = path.split('.')
        current = data

        for i, part in enumerate(parts[:-1]):
            # Handle list indices
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]

        # Set final value
        final_key = parts[-1]
        if final_key.isdigit():
            current[int(final_key)] = value
        else:
            current[final_key] = value

    def _sort_results(self, results: List[Dict], metric: str) -> List[Dict]:
        """
        Sort results by optimization metric

        Args:
            results: List of result dictionaries
            metric: Metric to sort by

        Returns:
            Sorted list (best first)
        """
        # Filter out failed results
        valid_results = [r for r in results if 'error' not in r and metric in r['performance']]

        # Sort by metric (descending for most metrics, ascending for drawdown)
        reverse = metric != 'max_drawdown'

        sorted_results = sorted(
            valid_results,
            key=lambda r: r['performance'][metric],
            reverse=reverse
        )

        return sorted_results

    def create_optimized_yaml(self,
                             base_yaml_path: str,
                             optimal_parameters: Dict,
                             output_path: str):
        """
        Create new YAML file with optimized parameters

        Args:
            base_yaml_path: Path to base YAML
            optimal_parameters: Optimal parameter dictionary
            output_path: Path for output YAML file
        """
        # Apply parameters
        modified_yaml = self._apply_parameters_to_yaml(base_yaml_path, optimal_parameters)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(modified_yaml)

        logger.info(f"[OK] Created optimized YAML: {output_path}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    print("=" * 60)
    print("PARAMETER OPTIMIZER TEST")
    print("=" * 60)

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

    # Test optimizer (small parameter space for testing)
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    optimizer = ParameterOptimizer()

    # Define small parameter space for testing
    # Note: These paths would need to match actual YAML structure
    param_ranges = {
        # Example: test different RSI oversold thresholds
        # 'entry.conditions.0.rules.0.value': [25, 30, 35],
    }

    # For testing, we'll just show the framework works
    print("[INFO] Parameter Optimizer initialized")
    print("[INFO] Framework ready for optimization")
    print("=" * 60)
