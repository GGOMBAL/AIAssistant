"""
Simple Report Agent
Simplified version using local service classes
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

# Import local services
from .backtest_report_service import BacktestReportService
from .stock_chart_report_service import StockChartReportService
from .trading_monitor_service import TradingMonitorService
from .signal_timeline_service import SignalTimelineService

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Simplified Report Agent - Manages all visualization and reporting
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Report Agent

        Args:
            config: Configuration dictionary from myStockInfo.yaml
        """
        self.config = config or {}
        self.output_dir = Path('project/reporting/outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.backtest_service = BacktestReportService()
        self.stock_chart_service = StockChartReportService()
        self.trading_monitor_service = TradingMonitorService()
        self.signal_timeline_service = SignalTimelineService()

        logger.info("[Report Agent] Initialized successfully")

    def generate_backtest_report(
        self,
        backtest_results: Any,
        benchmark_data: Optional[pd.DataFrame] = None,
        save: bool = True
    ) -> Optional[str]:
        """
        Generate backtest performance dashboard

        Args:
            backtest_results: Backtest results from DailyBacktestService
            benchmark_data: Optional benchmark comparison data
            save: Whether to save the file

        Returns:
            Path to saved dashboard file or None
        """
        try:
            logger.info("[Report Agent] Creating backtest dashboard...")

            # Convert backtest results to dictionary format
            results_dict = self._convert_backtest_results(backtest_results)

            # Create performance dashboard
            dashboard_path = self.backtest_service.create_performance_dashboard(
                backtest_results=results_dict,
                benchmark_data=benchmark_data,
                save_path=None if save else "temp.html"
            )

            logger.info(f"[Report Agent] Backtest dashboard created: {dashboard_path}")
            return dashboard_path

        except Exception as e:
            logger.error(f"[Report Agent] Error creating backtest dashboard: {e}")
            return None

    def generate_stock_signal_chart(
        self,
        ticker: str,
        stock_data: Optional[pd.DataFrame] = None,
        buy_signals: Optional[pd.DataFrame] = None,
        sell_signals: Optional[pd.DataFrame] = None,
        save: bool = True
    ) -> Optional[str]:
        """
        Generate stock chart with buy/sell signals

        Args:
            ticker: Stock symbol
            stock_data: DataFrame with OHLCV data
            buy_signals: DataFrame with buy signal information
            sell_signals: DataFrame with sell signal information
            save: Whether to save the file

        Returns:
            Path to saved chart file or None
        """
        try:
            logger.info(f"[Report Agent] Creating stock chart for {ticker}...")

            if stock_data is None or stock_data.empty:
                logger.warning(f"[Report Agent] No stock data provided for {ticker}")
                return None

            # Map column names to standard format if needed
            stock_data_mapped = stock_data.copy()
            column_mapping = {
                'open': 'Open', 'Dopen': 'Open',
                'high': 'High', 'Dhigh': 'High',
                'low': 'Low', 'Dlow': 'Low',
                'close': 'Close', 'Dclose': 'Close', 'ad_close': 'Close',
                'volume': 'Volume', 'Dvolume': 'Volume'
            }

            for old_col, new_col in column_mapping.items():
                if old_col in stock_data_mapped.columns and new_col not in stock_data_mapped.columns:
                    stock_data_mapped[new_col] = stock_data_mapped[old_col]

            # Create candlestick chart with signals
            chart_path = self.stock_chart_service.create_candlestick_chart(
                ticker=ticker,
                stock_data=stock_data_mapped,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                show_volume=True,
                show_sma=True,
                save_path=None if save else "temp.html"
            )

            logger.info(f"[Report Agent] Stock chart created: {chart_path}")
            return chart_path

        except Exception as e:
            logger.error(f"[Report Agent] Error creating stock chart: {e}")
            return None

    def generate_trading_monitor_dashboard(
        self,
        positions: List[Dict[str, Any]],
        pending_orders: List[str],
        market_status: Dict[str, Any],
        save: bool = True
    ) -> Optional[str]:
        """
        Generate trading monitor dashboard

        Args:
            positions: List of current position dictionaries
            pending_orders: List of pending order symbols
            market_status: Market status information
            save: Whether to save the file

        Returns:
            Path to saved dashboard file or None
        """
        try:
            logger.info("[Report Agent] Creating trading monitor dashboard...")

            # Create monitor dashboard
            dashboard_path = self.trading_monitor_service.create_monitor_dashboard(
                positions=positions,
                pending_orders=pending_orders,
                market_status=market_status,
                account_summary=None,
                save_path=None if save else "temp.html"
            )

            logger.info(f"[Report Agent] Trading monitor created: {dashboard_path}")
            return dashboard_path

        except Exception as e:
            logger.error(f"[Report Agent] Error creating trading monitor: {e}")
            return None

    def generate_signal_timeline_chart(
        self,
        ticker: str,
        signals_data: pd.DataFrame,
        save: bool = True
    ) -> Optional[str]:
        """
        Generate signal timeline chart

        Args:
            ticker: Stock symbol
            signals_data: DataFrame with signal timeline data
            save: Whether to save the file

        Returns:
            Path to saved chart file or None
        """
        try:
            logger.info(f"[Report Agent] Creating signal timeline for {ticker}...")

            # Create timeline chart
            timeline_path = self.signal_timeline_service.create_timeline_chart(
                ticker=ticker,
                signals_data=signals_data,
                stages=['W', 'D', 'RS', 'E', 'F'],
                save_path=None if save else "temp.html"
            )

            logger.info(f"[Report Agent] Signal timeline created: {timeline_path}")
            return timeline_path

        except Exception as e:
            logger.error(f"[Report Agent] Error creating signal timeline: {e}")
            return None

    def _convert_backtest_results(self, backtest_results: Any) -> Dict[str, Any]:
        """
        Convert backtest results to dictionary format for visualization

        Args:
            backtest_results: Results from DailyBacktestService

        Returns:
            Dictionary with formatted results
        """
        results_dict = {}

        # Extract performance metrics
        if hasattr(backtest_results, 'performance_metrics'):
            results_dict['performance_metrics'] = backtest_results.performance_metrics
        elif isinstance(backtest_results, dict) and 'performance_metrics' in backtest_results:
            results_dict['performance_metrics'] = backtest_results['performance_metrics']
        else:
            results_dict['performance_metrics'] = {}

        # Extract portfolio values if available
        if hasattr(backtest_results, 'portfolio_values'):
            results_dict['portfolio_values'] = backtest_results.portfolio_values
        elif hasattr(backtest_results, 'portfolio_history'):
            results_dict['portfolio_values'] = backtest_results.portfolio_history

        # Extract drawdown if available
        if hasattr(backtest_results, 'drawdown'):
            results_dict['drawdown'] = backtest_results.drawdown
        elif hasattr(backtest_results, 'drawdowns'):
            results_dict['drawdown'] = backtest_results.drawdowns

        # Extract trade history if available
        if hasattr(backtest_results, 'trade_history'):
            results_dict['trade_history'] = backtest_results.trade_history
        elif hasattr(backtest_results, 'trades'):
            results_dict['trade_history'] = backtest_results.trades

        return results_dict

    def get_summary(self) -> Dict[str, Any]:
        """
        Get Report Agent summary

        Returns:
            Dictionary with agent status and capabilities
        """
        return {
            'agent': 'ReportAgent',
            'status': 'active',
            'output_directory': str(self.output_dir),
            'services': [
                'Backtest Dashboard',
                'Stock Charts',
                'Trading Monitor',
                'Signal Timeline'
            ],
            'initialized': datetime.now().isoformat()
        }