"""
Strategy Report Generator - Report Agent Management

Generates comprehensive, user-friendly reports from backtest results.
Supports text, formatted console output, and structured data formats.

Owner: Report Agent
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class StrategyReportGenerator:
    """
    Generates comprehensive strategy backtest reports

    Responsibilities:
    - Format backtest results for human consumption
    - Generate summary statistics
    - Create trade analysis
    - Highlight key insights
    - Support multiple output formats (text, JSON, HTML)
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize Report Generator

        Args:
            output_dir: Directory to save report files
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "reports"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized StrategyReportGenerator with output dir: {self.output_dir}")

    def generate_report(
        self,
        strategy_name: str,
        backtest_result: Any,
        execution_time: float,
        include_trades: bool = True,
        save_to_file: bool = False
    ) -> str:
        """
        Generate comprehensive backtest report

        Args:
            strategy_name: Name of the strategy
            backtest_result: BacktestResult object
            execution_time: Time taken to run backtest (seconds)
            include_trades: Include individual trade details
            save_to_file: Save report to file

        Returns:
            Formatted report string
        """
        logger.info(f"Generating report for strategy: {strategy_name}")

        # Build report sections
        report_sections = []

        # Header
        report_sections.append(self._generate_header(strategy_name))

        # Executive Summary
        report_sections.append(self._generate_executive_summary(
            backtest_result, execution_time
        ))

        # Performance Metrics
        report_sections.append(self._generate_performance_metrics(backtest_result))

        # Trade Analysis
        report_sections.append(self._generate_trade_analysis(backtest_result))

        # Risk Analysis
        report_sections.append(self._generate_risk_analysis(backtest_result))

        # Individual Trades (if requested)
        if include_trades and len(backtest_result.trades) > 0:
            report_sections.append(self._generate_trade_details(
                backtest_result.trades
            ))

        # Key Insights
        report_sections.append(self._generate_key_insights(backtest_result))

        # Footer
        report_sections.append(self._generate_footer())

        # Combine all sections
        full_report = '\n\n'.join(report_sections)

        # Save to file if requested
        if save_to_file:
            self._save_report(strategy_name, full_report)

        return full_report

    def _generate_header(self, strategy_name: str) -> str:
        """Generate report header"""
        border = "=" * 80
        return f"""{border}
STRATEGY BACKTEST REPORT
{border}

Strategy: {strategy_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _generate_executive_summary(
        self,
        backtest_result: Any,
        execution_time: float
    ) -> str:
        """Generate executive summary"""
        perf = backtest_result.performance_metrics

        summary = f"""{'='*80}
EXECUTIVE SUMMARY
{'='*80}

Execution Time: {execution_time:.2f}s
Total Trades: {len(backtest_result.trades)}
Initial Capital: ${perf.get('initial_capital', 100000000):,.2f}
Final Value: ${perf.get('final_value', 0):,.2f}
Total Return: {perf.get('total_return', 0):.2%}
"""
        return summary

    def _generate_performance_metrics(self, backtest_result: Any) -> str:
        """Generate performance metrics section"""
        perf = backtest_result.performance_metrics

        metrics = f"""{'='*80}
PERFORMANCE METRICS
{'='*80}

Returns:
  Total Return:           {perf.get('total_return', 0):>10.2%}
  Annualized Return:      {perf.get('annualized_return', 0):>10.2%}
  Benchmark Return:       {perf.get('benchmark_return', 0):>10.2%}
  Alpha:                  {perf.get('alpha', 0):>10.2%}

Risk-Adjusted Metrics:
  Sharpe Ratio:           {perf.get('sharpe_ratio', 0):>10.2f}
  Sortino Ratio:          {perf.get('sortino_ratio', 0):>10.2f}
  Calmar Ratio:           {perf.get('calmar_ratio', 0):>10.2f}

Risk Metrics:
  Max Drawdown:           {perf.get('max_drawdown', 0):>10.2%}
  Volatility (Annual):    {perf.get('volatility', 0):>10.2%}
  VaR (95%):              {perf.get('var_95', 0):>10.2%}

Efficiency:
  Win Rate:               {perf.get('win_rate', 0):>10.2%}
  Profit Factor:          {perf.get('profit_factor', 0):>10.2f}
  Average Win/Loss:       {perf.get('avg_win_loss_ratio', 0):>10.2f}
"""
        return metrics

    def _generate_trade_analysis(self, backtest_result: Any) -> str:
        """Generate trade analysis section"""
        trades = backtest_result.trades
        perf = backtest_result.performance_metrics

        if not trades:
            return f"""{'='*80}
TRADE ANALYSIS
{'='*80}

No trades executed.
"""

        # Calculate trade statistics
        # Note: Trade object has 'pnl' not 'profit_loss'
        winning_trades = [t for t in trades if getattr(t, 'pnl', 0) > 0]
        losing_trades = [t for t in trades if getattr(t, 'pnl', 0) <= 0]

        avg_win = sum(getattr(t, 'pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(getattr(t, 'pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Calculate holding periods
        # Note: Trade may have 'holding_days' attribute
        holding_periods = []
        for t in trades:
            try:
                if hasattr(t, 'holding_days') and t.holding_days is not None and t.holding_days > 0:
                    holding_periods.append(t.holding_days)
                elif hasattr(t, 'exit_date') and hasattr(t, 'entry_date') and t.exit_date and t.entry_date:
                    holding_periods.append((t.exit_date - t.entry_date).days)
                elif hasattr(t, 'buy_date') and hasattr(t, 'timestamp') and t.buy_date and t.timestamp:
                    holding_periods.append((t.timestamp - t.buy_date).days)
            except (TypeError, AttributeError):
                # Skip trades with invalid dates
                continue

        avg_holding = sum(holding_periods) / len(holding_periods) if holding_periods else 0

        analysis = f"""{'='*80}
TRADE ANALYSIS
{'='*80}

Trade Count:
  Total Trades:           {len(trades):>10}
  Winning Trades:         {len(winning_trades):>10}
  Losing Trades:          {len(losing_trades):>10}
  Win Rate:               {perf.get('win_rate', 0):>10.2%}

Trade Performance:
  Average Win:            {avg_win:>10.2%}
  Average Loss:           {avg_loss:>10.2%}
  Largest Win:            {max((getattr(t, 'pnl', 0) for t in trades), default=0):>10.2%}
  Largest Loss:           {min((getattr(t, 'pnl', 0) for t in trades), default=0):>10.2%}
  Win/Loss Ratio:         {abs(avg_win / avg_loss) if avg_loss != 0 else 0:>10.2f}

Holding Periods:
  Average Days Held:      {avg_holding:>10.1f}
  Shortest Hold:          {min(holding_periods, default=0):>10} days
  Longest Hold:           {max(holding_periods, default=0):>10} days
"""
        return analysis

    def _generate_risk_analysis(self, backtest_result: Any) -> str:
        """Generate risk analysis section"""
        perf = backtest_result.performance_metrics

        risk = f"""{'='*80}
RISK ANALYSIS
{'='*80}

Drawdown Analysis:
  Maximum Drawdown:       {perf.get('max_drawdown', 0):>10.2%}
  Avg Drawdown:           {perf.get('avg_drawdown', 0):>10.2%}
  Max Drawdown Duration:  {perf.get('max_drawdown_duration', 0):>10} days

Exposure:
  Average Exposure:       {perf.get('avg_exposure', 0):>10.2%}
  Max Concurrent Pos:     {perf.get('max_positions', 0):>10}

Capital Efficiency:
  Capital Utilization:    {perf.get('capital_utilization', 0):>10.2%}
  Turnover Rate:          {perf.get('turnover_rate', 0):>10.2f}
"""
        return risk

    def _generate_trade_details(self, trades: List[Any]) -> str:
        """Generate individual trade details"""
        if not trades:
            return ""

        # Show first 10 trades and last 5 trades
        num_to_show = min(15, len(trades))
        sample_trades = trades[:10] + trades[-5:] if len(trades) > 15 else trades

        details = f"""{'='*80}
TRADE DETAILS (Sample)
{'='*80}

Showing {num_to_show} of {len(trades)} trades

{"Symbol":<10} {"Entry Date":<12} {"Exit Date":<12} {"Entry $":<10} {"Exit $":<10} {"P/L":<10} {"Days":<6}
{"-"*80}
"""

        for trade in sample_trades:
            try:
                # Extract attributes safely (Trade object structure varies)
                symbol = getattr(trade, 'symbol', None) or getattr(trade, 'ticker', 'N/A')

                # Get dates
                entry_date = None
                exit_date = None
                if hasattr(trade, 'entry_date') and trade.entry_date:
                    entry_date = trade.entry_date
                if hasattr(trade, 'exit_date') and trade.exit_date:
                    exit_date = trade.exit_date
                elif hasattr(trade, 'buy_date') and trade.buy_date:
                    entry_date = trade.buy_date
                if hasattr(trade, 'timestamp') and trade.timestamp:
                    exit_date = trade.timestamp

                # Get prices
                entry_price = getattr(trade, 'entry_price', None) or getattr(trade, 'buy_price', 0)
                exit_price = getattr(trade, 'exit_price', None) or getattr(trade, 'price', 0)

                # Get P/L
                pnl = getattr(trade, 'pnl', 0)
                if pnl is None:
                    pnl = getattr(trade, 'profit_loss', 0)

                # Get holding days
                days_held = 0
                if hasattr(trade, 'holding_days') and trade.holding_days is not None:
                    days_held = trade.holding_days
                elif entry_date and exit_date:
                    try:
                        days_held = (exit_date - entry_date).days
                    except:
                        days_held = 0

                # Format row
                details += f"{symbol:<10} "
                details += f"{entry_date.strftime('%Y-%m-%d') if entry_date else 'N/A':<12} "
                details += f"{exit_date.strftime('%Y-%m-%d') if exit_date else 'N/A':<12} "
                details += f"${entry_price:>8.2f} "
                details += f"${exit_price:>8.2f} "

                # P/L
                pl_str = f"{pnl:>8.2%}"
                details += f"{pl_str:<10} "
                details += f"{days_held:<6}\n"
            except Exception as e:
                # Skip trades that can't be formatted
                details += f"{'ERROR':<10} {str(e)[:60]}\n"
                continue

        if len(trades) > num_to_show:
            details += f"\n... and {len(trades) - num_to_show} more trades"

        return details

    def _generate_key_insights(self, backtest_result: Any) -> str:
        """Generate key insights and recommendations"""
        perf = backtest_result.performance_metrics
        trades = backtest_result.trades

        insights = []

        # Performance insight
        total_return = perf.get('total_return', 0)
        if total_return > 0.15:
            insights.append("[POSITIVE] Strong performance with >15% total return")
        elif total_return > 0:
            insights.append("[NEUTRAL] Positive but moderate returns")
        else:
            insights.append("[NEGATIVE] Strategy generated losses")

        # Risk insight
        sharpe = perf.get('sharpe_ratio', 0)
        if sharpe > 2.0:
            insights.append("[POSITIVE] Excellent risk-adjusted returns (Sharpe > 2)")
        elif sharpe > 1.0:
            insights.append("[NEUTRAL] Good risk-adjusted returns (Sharpe > 1)")
        else:
            insights.append("[NEGATIVE] Poor risk-adjusted returns (Sharpe < 1)")

        # Win rate insight
        win_rate = perf.get('win_rate', 0)
        if win_rate > 0.6:
            insights.append(f"[POSITIVE] High win rate ({win_rate:.1%})")
        elif win_rate < 0.4:
            insights.append(f"[NEGATIVE] Low win rate ({win_rate:.1%})")

        # Trade frequency insight
        if len(trades) < 5:
            insights.append("[WARNING] Very few trades - may need more lenient entry conditions")
        elif len(trades) > 100:
            insights.append("[WARNING] Very high trade frequency - may incur high transaction costs")

        # Drawdown insight
        max_dd = perf.get('max_drawdown', 0)
        if abs(max_dd) > 0.30:
            insights.append(f"[NEGATIVE] Large drawdown ({abs(max_dd):.1%}) - high risk")
        elif abs(max_dd) < 0.10:
            insights.append(f"[POSITIVE] Small drawdown ({abs(max_dd):.1%}) - low risk")

        insights_section = f"""{'='*80}
KEY INSIGHTS
{'='*80}

"""
        for insight in insights:
            insights_section += f"{insight}\n"

        return insights_section

    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""{'='*80}
End of Report
Generated by AI Assistant Multi-Agent Trading System
{'='*80}
"""

    def _save_report(self, strategy_name: str, report_content: str):
        """Save report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{strategy_name}_{timestamp}.txt"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"[OK] Report saved to: {filepath}")

    def generate_json_report(
        self,
        strategy_name: str,
        backtest_result: Any,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Generate JSON report for programmatic access

        Args:
            strategy_name: Strategy name
            backtest_result: BacktestResult object
            execution_time: Execution time

        Returns:
            Dictionary with structured report data
        """
        perf = backtest_result.performance_metrics
        trades = backtest_result.trades

        json_report = {
            'strategy_name': strategy_name,
            'generated_at': datetime.now().isoformat(),
            'execution_time': execution_time,
            'summary': {
                'total_trades': len(trades),
                'initial_capital': perf.get('initial_capital', 100000000),
                'final_value': perf.get('final_value', 0),
                'total_return': perf.get('total_return', 0)
            },
            'performance': {
                'total_return': perf.get('total_return', 0),
                'annualized_return': perf.get('annualized_return', 0),
                'sharpe_ratio': perf.get('sharpe_ratio', 0),
                'sortino_ratio': perf.get('sortino_ratio', 0),
                'max_drawdown': perf.get('max_drawdown', 0),
                'win_rate': perf.get('win_rate', 0),
                'profit_factor': perf.get('profit_factor', 0)
            },
            'trades': [
                {
                    'symbol': getattr(t, 'symbol', None) or getattr(t, 'ticker', 'N/A'),
                    'entry_date': (getattr(t, 'entry_date', None) or getattr(t, 'buy_date', None)).isoformat() if (getattr(t, 'entry_date', None) or getattr(t, 'buy_date', None)) else 'N/A',
                    'exit_date': (getattr(t, 'exit_date', None) or getattr(t, 'timestamp', None)).isoformat() if (getattr(t, 'exit_date', None) or getattr(t, 'timestamp', None)) else 'N/A',
                    'entry_price': getattr(t, 'entry_price', None) or getattr(t, 'buy_price', 0),
                    'exit_price': getattr(t, 'exit_price', None) or getattr(t, 'price', 0),
                    'profit_loss': getattr(t, 'pnl', None) or getattr(t, 'profit_loss', 0),
                    'days_held': getattr(t, 'holding_days', 0) if hasattr(t, 'holding_days') else 0
                }
                for t in trades
            ]
        }

        return json_report


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    print("[INFO] StrategyReportGenerator initialized")
    print("[INFO] Use with AutomatedWorkflow for complete reports")
