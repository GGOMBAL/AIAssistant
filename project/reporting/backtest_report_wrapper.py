#!/usr/bin/env python3
"""
Backtest Report Wrapper - Report Layer
Integrates Service Layer backtest results with QuantStats reporting

Updated: 2025-10-16
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Import Report Layer components
try:
    from project.reporting.quantstats_report_generator import QuantStatsReportGenerator
    REPORT_GEN_AVAILABLE = True
except ImportError:
    REPORT_GEN_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestReportWrapper:
    """
    백테스트 결과를 QuantStats 리포트로 변환하는 Wrapper

    Service Layer의 DailyBacktestService 결과를 받아서
    QuantStats 리포트를 생성합니다.
    """

    def __init__(self, output_dir: str = "visualization_output/reports"):
        """
        Initialize BacktestReportWrapper

        Args:
            output_dir: 리포트 저장 디렉토리
        """
        if not REPORT_GEN_AVAILABLE:
            raise ImportError("QuantStatsReportGenerator not available")

        self.report_generator = QuantStatsReportGenerator(output_dir)
        self.output_dir = output_dir

        logger.info(f"BacktestReportWrapper initialized. Output dir: {output_dir}")

    def convert_backtest_to_returns(self,
                                   backtest_result: Dict[str, Any],
                                   initial_capital: float = 100000.0) -> pd.Series:
        """
        Service Layer 백테스트 결과를 일간 수익률 시리즈로 변환

        Args:
            backtest_result: DailyBacktestService 결과
                Expected format:
                {
                    'summary': {...},
                    'trades': [...],
                    'daily_stats': pd.DataFrame,
                    'portfolio_value': pd.Series or Dict
                }
            initial_capital: 초기 자본금

        Returns:
            일간 수익률 시리즈
        """
        try:
            # Method 1: Use portfolio_value if available
            if 'portfolio_value' in backtest_result:
                portfolio_value = backtest_result['portfolio_value']

                if isinstance(portfolio_value, pd.Series):
                    returns = portfolio_value.pct_change().fillna(0)
                    return returns

                elif isinstance(portfolio_value, dict):
                    # Convert dict to Series
                    portfolio_value = pd.Series(portfolio_value)
                    returns = portfolio_value.pct_change().fillna(0)
                    return returns

            # Method 2: Use daily_stats if available
            if 'daily_stats' in backtest_result:
                daily_stats = backtest_result['daily_stats']

                if isinstance(daily_stats, pd.DataFrame):
                    if 'portfolio_value' in daily_stats.columns:
                        returns = daily_stats['portfolio_value'].pct_change().fillna(0)
                        return returns

                    elif 'total_value' in daily_stats.columns:
                        returns = daily_stats['total_value'].pct_change().fillna(0)
                        return returns

            # Method 3: Reconstruct from trades
            if 'trades' in backtest_result:
                trades = backtest_result['trades']
                returns = self._reconstruct_returns_from_trades(trades, initial_capital)
                return returns

            # Method 4: Use summary statistics
            if 'summary' in backtest_result:
                summary = backtest_result['summary']

                # Extract date range
                start_date = summary.get('start_date', datetime(2023, 1, 1))
                end_date = summary.get('end_date', datetime(2023, 12, 31))

                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)

                # Extract total return
                total_return = summary.get('total_return', 0)
                num_days = (end_date - start_date).days

                # Create uniform daily returns
                daily_return = (1 + total_return) ** (1/num_days) - 1
                dates = pd.date_range(start_date, end_date, freq='D')
                returns = pd.Series([daily_return] * len(dates), index=dates)

                return returns

            logger.error("Could not extract returns from backtest result")
            return pd.Series(dtype=float)

        except Exception as e:
            logger.error(f"Error converting backtest to returns: {e}")
            import traceback
            traceback.print_exc()
            return pd.Series(dtype=float)

    def _reconstruct_returns_from_trades(self,
                                        trades: List[Dict],
                                        initial_capital: float) -> pd.Series:
        """
        거래 내역으로부터 일간 수익률 재구성

        Args:
            trades: 거래 내역 리스트
            initial_capital: 초기 자본금

        Returns:
            일간 수익률 시리즈
        """
        try:
            if not trades:
                return pd.Series(dtype=float)

            # Extract all dates from trades
            all_dates = []
            for trade in trades:
                if 'entry_date' in trade:
                    all_dates.append(pd.to_datetime(trade['entry_date']))
                if 'exit_date' in trade:
                    all_dates.append(pd.to_datetime(trade['exit_date']))

            if not all_dates:
                return pd.Series(dtype=float)

            # Create date range
            min_date = min(all_dates)
            max_date = max(all_dates)
            date_range = pd.date_range(min_date, max_date, freq='D')

            # Initialize portfolio value
            portfolio_value = pd.Series(initial_capital, index=date_range)

            # Apply P/L from each trade
            cumulative_pnl = 0
            for trade in trades:
                exit_date = pd.to_datetime(trade.get('exit_date'))
                pnl = trade.get('pnl', 0)

                if exit_date in portfolio_value.index:
                    cumulative_pnl += pnl
                    portfolio_value.loc[exit_date:] = initial_capital + cumulative_pnl

            # Calculate returns
            returns = portfolio_value.pct_change().fillna(0)
            return returns

        except Exception as e:
            logger.error(f"Error reconstructing returns from trades: {e}")
            return pd.Series(dtype=float)

    def generate_report(self,
                       backtest_result: Dict[str, Any],
                       benchmark_ticker: str = None,
                       title: str = None,
                       initial_capital: float = 100000.0,
                       output_filename: str = None) -> Tuple[str, Dict[str, Any]]:
        """
        백테스트 결과로부터 QuantStats 리포트 생성

        Args:
            backtest_result: Service Layer 백테스트 결과
            benchmark_ticker: 벤치마크 티커 (예: "SPY", "^GSPC")
            title: 리포트 제목 (None이면 자동 생성)
            initial_capital: 초기 자본금
            output_filename: 출력 파일명 (None이면 자동 생성)

        Returns:
            (html_report_path, metrics_dict)
        """
        try:
            # 1. Convert backtest result to returns
            returns = self.convert_backtest_to_returns(backtest_result, initial_capital)

            if returns.empty:
                logger.error("Cannot generate report: returns series is empty")
                return None, {}

            # 2. Generate title if not provided
            if title is None:
                summary = backtest_result.get('summary', {})
                strategy_name = summary.get('strategy', 'Strategy')
                start_date = returns.index[0].strftime('%Y-%m-%d')
                end_date = returns.index[-1].strftime('%Y-%m-%d')
                title = f"{strategy_name} Backtest Report ({start_date} to {end_date})"

            # 3. Generate output filename
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"backtest_report_{timestamp}.html"

            # 4. Generate report
            html_path = self.report_generator.generate_html_report(
                returns=returns,
                benchmark=None,  # Will be fetched inside if benchmark_ticker is provided
                title=title,
                output_file=output_filename
            )

            # 5. Calculate metrics
            metrics = self.report_generator.generate_metrics_report(returns)

            # 6. Add backtest summary to metrics
            if 'summary' in backtest_result:
                metrics['backtest_summary'] = backtest_result['summary']

            # 7. Print summary
            self._print_report_summary(html_path, metrics)

            return html_path, metrics

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            import traceback
            traceback.print_exc()
            return None, {}

    def _print_report_summary(self, html_path: str, metrics: Dict[str, Any]):
        """리포트 생성 완료 메시지 출력"""
        print("\n" + "="*70)
        print("QuantStats Report Generated".center(70))
        print("="*70)

        if html_path:
            print(f"\n[HTML Report]")
            print(f"  Location: {html_path}")
            print(f"  Open in browser to view detailed analysis")

        if metrics:
            print(f"\n[Quick Summary]")
            if 'total_return' in metrics:
                print(f"  Total Return:     {metrics['total_return']:>10.2%}")
            if 'sharpe_ratio' in metrics:
                print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:>10.2f}")
            if 'max_drawdown' in metrics:
                print(f"  Max Drawdown:     {metrics['max_drawdown']:>10.2%}")

        print("\n" + "="*70 + "\n")


# Helper function for easy usage
def generate_backtest_report(backtest_result: Dict[str, Any],
                             output_dir: str = "visualization_output/reports",
                             benchmark: str = None,
                             title: str = None,
                             initial_capital: float = 100000.0) -> Tuple[str, Dict]:
    """
    간편한 백테스트 리포트 생성 함수

    Args:
        backtest_result: 백테스트 결과 딕셔너리
        output_dir: 출력 디렉토리
        benchmark: 벤치마크 티커
        title: 리포트 제목
        initial_capital: 초기 자본금

    Returns:
        (html_path, metrics)

    Example:
        >>> from project.service.daily_backtest_service import DailyBacktestService
        >>> backtest = DailyBacktestService(...)
        >>> result = backtest.run()
        >>> html_path, metrics = generate_backtest_report(result)
    """
    wrapper = BacktestReportWrapper(output_dir)
    return wrapper.generate_report(backtest_result, benchmark, title, initial_capital)


if __name__ == "__main__":
    # Test with sample data
    print("Testing BacktestReportWrapper...")

    # Create sample backtest result
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    portfolio_values = 100000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, len(dates))))

    sample_result = {
        'summary': {
            'strategy': 'TestStrategy',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'total_return': 0.15,
            'sharpe_ratio': 1.2
        },
        'portfolio_value': pd.Series(portfolio_values, index=dates),
        'trades': []
    }

    # Generate report
    html_path, metrics = generate_backtest_report(
        sample_result,
        title="Sample Backtest Report"
    )

    if html_path:
        print(f"\nSuccess! Report saved to: {html_path}")
