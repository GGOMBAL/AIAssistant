#!/usr/bin/env python3
"""
QuantStats Report Generator - Report Layer
Generates comprehensive backtest performance reports using quantstats_lumi

Updated: 2025-10-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import logging
import os
import sys

# Import quantstats_lumi
try:
    import quantstats_lumi as qs
    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    logging.warning("quantstats_lumi not available. Install with: pip install quantstats-lumi")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantStatsReportGenerator:
    """
    QuantStats 기반 백테스트 리포트 생성기

    Features:
    - HTML 형식의 종합 성과 리포트
    - 다양한 성과 지표 (Sharpe, Sortino, Max Drawdown 등)
    - 시각화 차트 (Equity Curve, Drawdown, Monthly Returns 등)
    - 벤치마크 비교
    """

    def __init__(self, output_dir: str = "visualization_output/reports"):
        """
        Initialize QuantStatsReportGenerator

        Args:
            output_dir: 리포트 저장 디렉토리
        """
        if not QUANTSTATS_AVAILABLE:
            raise ImportError("quantstats_lumi is required. Install with: pip install quantstats-lumi")

        self.output_dir = output_dir

        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"QuantStatsReportGenerator initialized. Output dir: {output_dir}")

    def prepare_returns_series(self,
                               backtest_results: Dict[str, Any],
                               capital: float = 100000.0) -> pd.Series:
        """
        백테스트 결과에서 일간 수익률 시리즈 생성

        Args:
            backtest_results: 백테스트 결과 딕셔너리
                {
                    'trades': List[Dict],  # 거래 내역
                    'daily_values': pd.Series,  # 일간 포트폴리오 가치
                    'dates': pd.DatetimeIndex  # 날짜 인덱스
                }
            capital: 초기 자본금

        Returns:
            일간 수익률 시리즈 (pandas Series)
        """
        try:
            # Check if daily_values are provided
            if 'daily_values' in backtest_results:
                daily_values = backtest_results['daily_values']
                if isinstance(daily_values, pd.Series):
                    # Calculate daily returns
                    returns = daily_values.pct_change().fillna(0)
                    return returns

            # If trades are provided, reconstruct portfolio value
            if 'trades' in backtest_results:
                trades = backtest_results['trades']
                dates = backtest_results.get('dates', None)

                if dates is None and len(trades) > 0:
                    # Extract dates from trades
                    dates = pd.DatetimeIndex([trade['entry_date'] for trade in trades])

                # Create daily portfolio value series
                portfolio_value = pd.Series(index=dates, dtype=float)
                portfolio_value.iloc[0] = capital

                # Calculate cumulative P/L
                for i, trade in enumerate(trades):
                    pnl = trade.get('pnl', 0)
                    entry_date = trade.get('entry_date')

                    if entry_date in portfolio_value.index:
                        portfolio_value.loc[entry_date] = capital + pnl
                        capital += pnl

                # Forward fill missing dates
                portfolio_value = portfolio_value.fillna(method='ffill')

                # Calculate returns
                returns = portfolio_value.pct_change().fillna(0)
                return returns

            # If no data available, return empty series
            logger.warning("No sufficient data to calculate returns")
            return pd.Series(dtype=float)

        except Exception as e:
            logger.error(f"Error preparing returns series: {e}")
            return pd.Series(dtype=float)

    def generate_html_report(self,
                            returns: pd.Series,
                            benchmark: Optional[pd.Series] = None,
                            title: str = "Backtest Performance Report",
                            output_file: str = None) -> str:
        """
        HTML 형식의 종합 리포트 생성

        Args:
            returns: 일간 수익률 시리즈
            benchmark: 벤치마크 수익률 시리즈 (선택, 예: SPY)
            title: 리포트 제목
            output_file: 저장할 파일명 (None이면 자동 생성)

        Returns:
            생성된 HTML 파일 경로
        """
        try:
            if returns.empty:
                logger.error("Returns series is empty. Cannot generate report.")
                return None

            # Generate output filename
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"backtest_report_{timestamp}.html"

            output_path = os.path.join(self.output_dir, output_file)

            # Generate HTML report using quantstats
            if benchmark is not None:
                qs.reports.html(returns,
                              benchmark=benchmark,
                              output=output_path,
                              title=title)
            else:
                qs.reports.html(returns,
                              output=output_path,
                              title=title)

            logger.info(f"HTML report generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_metrics_report(self,
                               returns: pd.Series,
                               benchmark: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        주요 성과 지표 계산

        Args:
            returns: 일간 수익률 시리즈
            benchmark: 벤치마크 수익률 시리즈 (선택)

        Returns:
            성과 지표 딕셔너리
        """
        try:
            metrics = {}

            # Basic metrics
            metrics['total_return'] = qs.stats.comp(returns)
            metrics['cagr'] = qs.stats.cagr(returns)
            metrics['sharpe_ratio'] = qs.stats.sharpe(returns)
            metrics['sortino_ratio'] = qs.stats.sortino(returns)
            metrics['max_drawdown'] = qs.stats.max_drawdown(returns)
            metrics['calmar_ratio'] = qs.stats.calmar(returns)
            metrics['volatility'] = qs.stats.volatility(returns)

            # Win rate metrics
            metrics['win_rate'] = qs.stats.win_rate(returns)
            metrics['avg_win'] = qs.stats.avg_win(returns)
            metrics['avg_loss'] = qs.stats.avg_loss(returns)
            metrics['win_loss_ratio'] = qs.stats.win_loss_ratio(returns)

            # Risk metrics
            metrics['var_95'] = qs.stats.var(returns, confidence=0.95)
            metrics['cvar_95'] = qs.stats.cvar(returns, confidence=0.95)

            # Benchmark comparison (if provided)
            if benchmark is not None:
                metrics['alpha'] = qs.stats.alpha(returns, benchmark)
                metrics['beta'] = qs.stats.beta(returns, benchmark)
                metrics['information_ratio'] = qs.stats.information_ratio(returns, benchmark)

            logger.info(f"Calculated {len(metrics)} performance metrics")
            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {}

    def generate_full_report(self,
                           backtest_results: Dict[str, Any],
                           benchmark_ticker: Optional[str] = None,
                           title: str = "Backtest Performance Report",
                           capital: float = 100000.0) -> Tuple[str, Dict[str, Any]]:
        """
        전체 리포트 생성 (HTML + Metrics)

        Args:
            backtest_results: 백테스트 결과
            benchmark_ticker: 벤치마크 티커 (예: "SPY", "^GSPC")
            title: 리포트 제목
            capital: 초기 자본금

        Returns:
            (html_report_path, metrics_dict)
        """
        try:
            # 1. Prepare returns series
            returns = self.prepare_returns_series(backtest_results, capital)

            if returns.empty:
                logger.error("Cannot generate report: returns series is empty")
                return None, {}

            # 2. Get benchmark data (if specified)
            benchmark = None
            if benchmark_ticker:
                try:
                    benchmark = qs.utils.download_returns(benchmark_ticker)
                    # Align benchmark with returns dates
                    benchmark = benchmark.reindex(returns.index, method='ffill')
                    logger.info(f"Downloaded benchmark data for {benchmark_ticker}")
                except Exception as e:
                    logger.warning(f"Could not download benchmark {benchmark_ticker}: {e}")

            # 3. Generate HTML report
            html_path = self.generate_html_report(returns, benchmark, title)

            # 4. Calculate metrics
            metrics = self.generate_metrics_report(returns, benchmark)

            # 5. Print summary
            self._print_summary(metrics)

            return html_path, metrics

        except Exception as e:
            logger.error(f"Error generating full report: {e}")
            import traceback
            traceback.print_exc()
            return None, {}

    def _print_summary(self, metrics: Dict[str, Any]):
        """성과 지표 요약 출력"""
        print("\n" + "="*60)
        print("Performance Summary".center(60))
        print("="*60)

        if not metrics:
            print("No metrics available")
            return

        # Format and print key metrics
        print(f"\n[Return Metrics]")
        if 'total_return' in metrics:
            print(f"  Total Return:        {metrics['total_return']:>10.2%}")
        if 'cagr' in metrics:
            print(f"  CAGR:                {metrics['cagr']:>10.2%}")

        print(f"\n[Risk Metrics]")
        if 'volatility' in metrics:
            print(f"  Volatility:          {metrics['volatility']:>10.2%}")
        if 'max_drawdown' in metrics:
            print(f"  Max Drawdown:        {metrics['max_drawdown']:>10.2%}")

        print(f"\n[Risk-Adjusted Returns]")
        if 'sharpe_ratio' in metrics:
            print(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:>10.2f}")
        if 'sortino_ratio' in metrics:
            print(f"  Sortino Ratio:       {metrics['sortino_ratio']:>10.2f}")
        if 'calmar_ratio' in metrics:
            print(f"  Calmar Ratio:        {metrics['calmar_ratio']:>10.2f}")

        print(f"\n[Win/Loss Statistics]")
        if 'win_rate' in metrics:
            print(f"  Win Rate:            {metrics['win_rate']:>10.2%}")
        if 'win_loss_ratio' in metrics:
            print(f"  Win/Loss Ratio:      {metrics['win_loss_ratio']:>10.2f}")

        print("\n" + "="*60 + "\n")


# Example usage
if __name__ == "__main__":
    # Test with sample data
    generator = QuantStatsReportGenerator()

    # Create sample returns
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)

    # Generate report
    html_path = generator.generate_html_report(returns, title="Sample Backtest Report")

    if html_path:
        print(f"Report generated successfully: {html_path}")

    # Calculate metrics
    metrics = generator.generate_metrics_report(returns)
    generator._print_summary(metrics)
