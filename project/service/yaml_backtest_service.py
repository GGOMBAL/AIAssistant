"""
YAML Backtest Service - Service Layer Implementation

Integrates YAML-defined strategies with the existing backtest engine.
Bridges the gap between YAML Strategy Executor and Daily Backtest Service.

Owner: Service Agent
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from project.strategy.yaml_strategy_loader import YAMLStrategyLoader, LoadedStrategy
from project.strategy.yaml_strategy_executor import YAMLStrategyExecutor
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig, BacktestResult
from project.reporting.backtest_result_manager import BacktestResultManager

logger = logging.getLogger(__name__)


class YAMLBacktestService:
    """
    YAML-based Strategy Backtesting Service

    Responsibilities:
    - Load YAML strategy files
    - Execute strategies to generate signals
    - Convert signals to backtest engine format
    - Run backtest using DailyBacktestService
    - Store results in MongoDB using BacktestResultManager
    """

    def __init__(self,
                 loader: Optional[YAMLStrategyLoader] = None,
                 executor: Optional[YAMLStrategyExecutor] = None,
                 result_manager: Optional[BacktestResultManager] = None):
        """
        Initialize YAML Backtest Service

        Args:
            loader: Strategy loader instance
            executor: Strategy executor instance
            result_manager: Result manager instance
        """
        self.loader = loader or YAMLStrategyLoader()
        self.executor = executor or YAMLStrategyExecutor()
        self.result_manager = result_manager or BacktestResultManager()

        logger.info("Initialized YAMLBacktestService")

    def backtest_from_file(self,
                          yaml_path: str,
                          data: Dict[str, pd.DataFrame],
                          backtest_config: Optional[BacktestConfig] = None,
                          store_results: bool = True) -> Dict[str, Any]:
        """
        Load YAML strategy and run backtest

        Args:
            yaml_path: Path to YAML strategy file
            data: Dictionary mapping symbol -> DataFrame with OHLCV + indicators
            backtest_config: Backtest configuration (uses defaults if None)
            store_results: Whether to store results in MongoDB

        Returns:
            Dictionary with backtest results and metadata
        """
        logger.info(f"Starting YAML backtest from file: {yaml_path}")

        # Step 1: Load strategy
        success, strategy, errors = self.loader.load_from_file(yaml_path)

        if not success or not strategy:
            logger.error(f"Failed to load strategy: {errors}")
            return {
                'success': False,
                'errors': errors,
                'strategy': None,
                'backtest_result': None
            }

        # Step 2: Run backtest
        return self.backtest_strategy(
            strategy=strategy,
            data=data,
            backtest_config=backtest_config,
            store_results=store_results
        )

    def backtest_strategy(self,
                         strategy: LoadedStrategy,
                         data: Dict[str, pd.DataFrame],
                         backtest_config: Optional[BacktestConfig] = None,
                         store_results: bool = True) -> Dict[str, Any]:
        """
        Run backtest for loaded strategy

        Args:
            strategy: Loaded strategy object
            data: Market data dictionary
            backtest_config: Backtest configuration
            store_results: Whether to store results in MongoDB

        Returns:
            Dictionary with complete backtest results
        """
        start_time = datetime.now()

        logger.info(f"Backtesting strategy: {strategy.name} v{strategy.version}")

        try:
            # Step 1: Execute strategy to generate signals
            logger.info("Generating signals from YAML strategy...")
            execution_results = self.executor.execute_strategy(strategy, data)

            # Step 2: Convert signals to backtest engine format
            logger.info("Converting signals to backtest format...")
            backtest_data = self._convert_signals_to_backtest_format(
                execution_results, data
            )

            # Step 3: Prepare backtest configuration
            if backtest_config is None:
                backtest_config = self._create_backtest_config_from_strategy(strategy)

            # Step 4: Run backtest using existing engine
            logger.info("Running backtest engine...")
            universe = list(backtest_data.keys())
            backtest_service = DailyBacktestService(config=backtest_config)
            backtest_result = backtest_service.run_backtest(
                universe=universe,
                df_data=backtest_data,
                market='US',
                area='US'
            )

            # Step 5: Package results
            execution_time = (datetime.now() - start_time).total_seconds()

            results = {
                'success': True,
                'strategy': strategy,
                'strategy_name': strategy.name,
                'strategy_version': strategy.version,
                'execution_results': execution_results,
                'backtest_result': backtest_result,
                'execution_time': execution_time,
                'backtest_config': backtest_config,
                'errors': []
            }

            # Step 6: Store results in MongoDB (if enabled)
            if store_results:
                logger.info("Storing results in MongoDB...")
                self._store_backtest_results(strategy, backtest_result, results)

            logger.info(f"[OK] Backtest completed in {execution_time:.2f}s")
            return results

        except Exception as e:
            logger.error(f"Error during backtest: {e}")
            return {
                'success': False,
                'strategy': strategy,
                'errors': [str(e)],
                'backtest_result': None
            }

    def _convert_signals_to_backtest_format(self,
                                           execution_results: Dict[str, Any],
                                           original_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Convert YAML executor signals to daily backtest service format

        Args:
            execution_results: Results from YAMLStrategyExecutor
            original_data: Original market data

        Returns:
            Dictionary of DataFrames in backtest engine format
        """
        backtest_data = {}

        for symbol, symbol_results in execution_results['signals'].items():
            if 'error' in symbol_results:
                logger.warning(f"Skipping {symbol} due to error: {symbol_results['error']}")
                continue

            # Get original data
            df = original_data[symbol].copy()

            # Add signal columns expected by backtest engine
            # BuySig: Entry signals from YAML strategy
            df['BuySig'] = symbol_results['entry'].astype(int)

            # SellSig: Exit signals from YAML strategy
            if 'signal_exit' in symbol_results.get('exit', {}):
                df['SellSig'] = symbol_results['exit']['signal_exit'].astype(int)
            else:
                df['SellSig'] = 0

            # signal: Combined signal (1 for buy, -1 for sell, 0 for hold)
            df['signal'] = 0
            df.loc[df['BuySig'] == 1, 'signal'] = 1
            df.loc[df['SellSig'] == 1, 'signal'] = -1

            # Add placeholder columns if not present
            if 'ADR' not in df.columns:
                df['ADR'] = (df['high'] - df['low']) / df['close']

            if 'Type' not in df.columns:
                df['Type'] = 'YAML'

            if 'LossCutPrice' not in df.columns:
                df['LossCutPrice'] = df['close'] * 0.97  # Default 3% stop loss

            if 'TargetPrice' not in df.columns:
                df['TargetPrice'] = df['close'] * 1.10  # Default 10% target

            # Add sophisticated signal columns (as placeholders)
            for sig_col in ['wBuySig', 'dBuySig', 'rsBuySig', 'fBuySig', 'eBuySig']:
                if sig_col not in df.columns:
                    df[sig_col] = 0

            # Copy primary buy signal to main signal column
            df['wBuySig'] = df['BuySig']

            backtest_data[symbol] = df

        return backtest_data

    def _create_backtest_config_from_strategy(self, strategy: LoadedStrategy) -> BacktestConfig:
        """
        Create BacktestConfig from strategy YAML parameters

        Args:
            strategy: Loaded strategy

        Returns:
            BacktestConfig object
        """
        # Extract config from strategy YAML
        backtest_params = strategy.backtest
        risk_params = strategy.risk_management
        entry_constraints = strategy.entry.constraints if strategy.entry else {}

        # Build config
        config = BacktestConfig(
            initial_cash=backtest_params.get('initial_capital', 100000000.0),
            max_positions=entry_constraints.get('max_positions', 10),
            slippage=backtest_params.get('costs', {}).get('slippage', 0.002),
            std_risk=risk_params.get('base_risk', 0.05),
            init_risk=strategy.exit.stop_loss.get('initial_stop', 0.03) if strategy.exit and strategy.exit.stop_loss else 0.03,
            half_sell_threshold=0.20,
            half_sell_risk_multiplier=2.0,
            enable_whipsaw=True,
            enable_half_sell=True,
            enable_rebuying=True,
            message_output=False
        )

        return config

    def _store_backtest_results(self,
                                strategy: LoadedStrategy,
                                backtest_result: BacktestResult,
                                full_results: Dict[str, Any]) -> None:
        """
        Store backtest results in MongoDB

        Args:
            strategy: Strategy object
            backtest_result: Backtest result from engine
            full_results: Complete results dictionary
        """
        try:
            # Step 1: Store strategy configuration
            strategy_id = self.result_manager.store_strategy_config(
                strategy=strategy.raw_yaml
            )

            # Step 2: Generate backtest ID
            backtest_id = self.result_manager.generate_backtest_id(strategy_id)

            # Step 3: Extract performance metrics
            performance = backtest_result.performance_metrics

            # Step 4: Calculate trade statistics
            trade_stats = {
                'total_trades': len(backtest_result.trades),
                'winning_trades': sum(1 for t in backtest_result.trades if getattr(t, 'pnl', 0) > 0),
                'losing_trades': sum(1 for t in backtest_result.trades if getattr(t, 'pnl', 0) < 0),
                'avg_profit': np.mean([getattr(t, 'pnl', 0) for t in backtest_result.trades]) if backtest_result.trades else 0,
                'max_profit': max([getattr(t, 'pnl', 0) for t in backtest_result.trades]) if backtest_result.trades else 0,
                'max_loss': min([getattr(t, 'pnl', 0) for t in backtest_result.trades]) if backtest_result.trades else 0
            }

            # Step 5: Get backtest period
            if backtest_result.portfolio_history:
                first_date = backtest_result.portfolio_history[0].timestamp if hasattr(backtest_result.portfolio_history[0], 'timestamp') else None
                last_date = backtest_result.portfolio_history[-1].timestamp if hasattr(backtest_result.portfolio_history[-1], 'timestamp') else None
                backtest_period = {
                    'start_date': first_date.strftime('%Y-%m-%d') if first_date else 'unknown',
                    'end_date': last_date.strftime('%Y-%m-%d') if last_date else 'unknown',
                    'total_days': len(backtest_result.portfolio_history)
                }
            else:
                backtest_period = {'start_date': 'unknown', 'end_date': 'unknown', 'total_days': 0}

            # Step 6: Store backtest result
            self.result_manager.store_backtest_result(
                backtest_id=backtest_id,
                strategy_id=strategy_id,
                performance=performance,
                trade_stats=trade_stats,
                backtest_period=backtest_period,
                strategy_name=strategy.name,
                execution_time_seconds=full_results['execution_time']
            )

            # Step 7: Store individual trades
            for trade in backtest_result.trades:
                trade_dict = {
                    'ticker': trade.ticker,
                    'trade_type': trade.trade_type.value if hasattr(trade.trade_type, 'value') else str(trade.trade_type),
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'reason': trade.reason.value if hasattr(trade, 'reason') and hasattr(trade.reason, 'value') else None,
                    'pnl': getattr(trade, 'pnl', 0),
                    'portfolio_value': getattr(trade, 'portfolio_value', 0)
                }

                self.result_manager.store_trade(
                    backtest_id=backtest_id,
                    strategy_id=strategy_id,
                    trade=trade_dict
                )

            logger.info(f"[OK] Stored results: strategy_id={strategy_id}, backtest_id={backtest_id}")

        except Exception as e:
            logger.error(f"Error storing backtest results: {e}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Test YAML backtest service
    from pathlib import Path

    # Load strategy
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "config" / "strategies" / "rsi_mean_reversion_v1.yaml"

    # Create sample data for backtesting
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    data = {}
    for symbol in ['AAPL', 'MSFT', 'GOOGL']:
        df = pd.DataFrame({
            'open': 100 + np.cumsum(np.random.randn(100) * 2),
            'high': 102 + np.cumsum(np.random.randn(100) * 2),
            'low': 98 + np.cumsum(np.random.randn(100) * 2),
            'close': 100 + np.cumsum(np.random.randn(100) * 2),
            'volume': 1000000 + np.random.randint(-100000, 100000, 100)
        }, index=dates)

        # Add required indicators
        df['RSI_14'] = 50 + np.random.randn(100) * 15
        df['SMA_20'] = df['close'].rolling(20).mean()
        df['SMA_50'] = df['close'].rolling(50).mean()
        df['Volume_SMA_20'] = df['volume'].rolling(20).mean()
        df['RS_Rating'] = 50 + np.random.randn(100) * 20

        data[symbol] = df

    # Run backtest
    service = YAMLBacktestService()
    results = service.backtest_from_file(
        yaml_path=str(yaml_path),
        data=data,
        store_results=False  # Don't store for test
    )

    # Print results
    print("=" * 60)
    print("YAML BACKTEST SERVICE TEST")
    print("=" * 60)

    if results['success']:
        print(f"Strategy: {results['strategy_name']} v{results['strategy_version']}")
        print(f"Execution time: {results['execution_time']:.2f}s")

        # Print signal statistics
        exec_results = results['execution_results']
        print(f"\nSignal Generation:")
        print(f"  Total symbols: {exec_results['metadata']['total_symbols']}")
        print(f"  Symbols with signals: {exec_results['metadata']['symbols_with_signals']}")
        print(f"  Total entry signals: {exec_results['metadata']['total_entry_signals']}")

        # Print backtest performance
        bt_result = results['backtest_result']
        perf = bt_result.performance_metrics

        print(f"\nBacktest Performance:")
        print(f"  Total trades: {len(bt_result.trades)}")
        print(f"  Final portfolio value: ${perf.get('final_value', 0):,.2f}")
        print(f"  Total return: {perf.get('total_return', 0):.2%}")
        print(f"  Sharpe ratio: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"  Max drawdown: {perf.get('max_drawdown', 0):.2%}")

    else:
        print(f"[FAILED] Backtest failed:")
        for error in results['errors']:
            print(f"  - {error}")

    print("=" * 60)
