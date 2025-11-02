"""
Backtest Report Service
Generates performance dashboards for backtest results
"""

from typing import Dict, Optional, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path


class BacktestReportService:
    """Service for creating backtest performance reports and dashboards"""

    def __init__(self):
        self.output_dir = Path('project/reporting/outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_performance_dashboard(
        self,
        backtest_results: Dict[str, Any],
        benchmark_data: Optional[pd.DataFrame] = None,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create a comprehensive backtest performance dashboard

        Args:
            backtest_results: Backtest results dictionary
            benchmark_data: Optional benchmark comparison data
            save_path: Optional path to save the dashboard

        Returns:
            Path to saved dashboard file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Portfolio Value Over Time',
                'Monthly Returns',
                'Drawdown Analysis',
                'Trade Statistics'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'bar'}],
                [{'type': 'scatter'}, {'type': 'bar'}]
            ]
        )

        # Extract metrics
        metrics = backtest_results.get('performance_metrics', {})

        # 1. Portfolio Value (if available in results)
        if 'portfolio_values' in backtest_results:
            dates = list(range(len(backtest_results['portfolio_values'])))
            values = backtest_results['portfolio_values']

            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )

        # 2. Monthly Returns (placeholder)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        returns = [0.02, -0.01, 0.03, 0.01, -0.02, 0.04]  # Sample data

        fig.add_trace(
            go.Bar(
                x=months,
                y=returns,
                name='Monthly Returns',
                marker_color=['green' if r > 0 else 'red' for r in returns]
            ),
            row=1, col=2
        )

        # 3. Drawdown (placeholder)
        if 'drawdown' in backtest_results:
            dates = list(range(len(backtest_results['drawdown'])))
            drawdown = backtest_results['drawdown']
        else:
            dates = list(range(100))
            drawdown = [-0.01 * i for i in range(100)]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color='red', width=1)
            ),
            row=2, col=1
        )

        # 4. Trade Statistics
        stats = ['Win Rate', 'Avg Win', 'Avg Loss', 'Total Trades']
        values = [
            metrics.get('win_rate', 0) * 100,
            metrics.get('avg_win', 0),
            abs(metrics.get('avg_loss', 0)),
            metrics.get('total_trades', 0)
        ]

        fig.add_trace(
            go.Bar(
                x=stats,
                y=values,
                name='Statistics',
                marker_color='lightblue'
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title=f"Backtest Performance Dashboard - {datetime.now().strftime('%Y-%m-%d')}",
            showlegend=False,
            height=800,
            template='plotly_white'
        )

        # Update axes
        fig.update_xaxes(title_text="Time", row=1, col=1)
        fig.update_yaxes(title_text="Value ($M)", row=1, col=1)
        fig.update_xaxes(title_text="Month", row=1, col=2)
        fig.update_yaxes(title_text="Return (%)", row=1, col=2)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_xaxes(title_text="Metric", row=2, col=2)
        fig.update_yaxes(title_text="Value", row=2, col=2)

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'backtest_dashboard_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)

    def create_summary_report(
        self,
        backtest_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a summary report of backtest results

        Args:
            backtest_results: Backtest results dictionary

        Returns:
            Summary dictionary
        """
        metrics = backtest_results.get('performance_metrics', {})

        summary = {
            'total_return': metrics.get('total_return', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'win_rate': metrics.get('win_rate', 0),
            'total_trades': metrics.get('total_trades', 0),
            'best_trade': metrics.get('best_trade', 0),
            'worst_trade': metrics.get('worst_trade', 0),
            'avg_trade': metrics.get('avg_trade', 0),
            'final_value': metrics.get('final_value', 0),
            'execution_time': backtest_results.get('execution_time', 0)
        }

        return summary