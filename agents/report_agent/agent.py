"""
Report Agent - Analysis and Reporting Specialist
Generates comprehensive trading performance reports using Reporting Layer modules.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import json
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import Reporting Layer modules
from project.reporting.pl_analyzer import PLAnalyzer
from project.reporting.balance_analyzer import BalanceAnalyzer
from project.reporting.gap_analyzer import GAPAnalyzer

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportAgent:
    """
    Report Agent for comprehensive trading analysis and reporting

    Responsibilities:
    - Generate P/L analysis reports
    - Analyze balance evolution
    - Track performance metrics
    - Identify trading patterns
    - Create actionable insights
    - Compare backtest vs live results (future)

    Access Rights:
    - READ: All layers
    - WRITE: Only Reporting Layer
    - INPUT: OrderInfo (trading history)
    - OUTPUT: Analysis reports
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Report Agent

        Args:
            config: Agent configuration dictionary
        """
        self.config = config or {}
        self.name = "Report Agent"
        self.version = "1.0.0"

        # Initialize analyzers
        self.pl_analyzer = PLAnalyzer()
        self.balance_analyzer = BalanceAnalyzer(
            initial_balance=self.config.get('initial_balance', 100000.0)
        )
        self.gap_analyzer = GAPAnalyzer()

        # Report storage
        self.generated_reports = []
        self.last_report = None

        logger.info(f"[{self.name}] Initialized (v{self.version})")

    def generate_comprehensive_report(self,
                                     order_history: pd.DataFrame,
                                     market_prices: Optional[pd.DataFrame] = None,
                                     report_type: str = 'full') -> Dict[str, Any]:
        """
        Generate comprehensive trading performance report

        Args:
            order_history: DataFrame with trading history
            market_prices: Optional current market prices
            report_type: Type of report ('full', 'pl', 'balance', 'summary')

        Returns:
            Dict containing comprehensive analysis report
        """
        logger.info(f"[{self.name}] Generating {report_type} report...")

        try:
            report = {
                'agent': self.name,
                'version': self.version,
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'data': {}
            }

            # Generate requested report components
            if report_type in ['full', 'pl']:
                logger.info("[Report Agent] Analyzing P/L...")
                pl_analysis = self.pl_analyzer.analyze_trades(order_history)
                report['data']['pl_analysis'] = pl_analysis

            if report_type in ['full', 'balance']:
                logger.info("[Report Agent] Analyzing balance history...")
                balance_analysis = self.balance_analyzer.analyze_balance_history(
                    order_history, market_prices
                )
                report['data']['balance_analysis'] = balance_analysis

            if report_type == 'full':
                # Add executive summary
                report['data']['executive_summary'] = self._generate_executive_summary(
                    pl_analysis=report['data'].get('pl_analysis'),
                    balance_analysis=report['data'].get('balance_analysis')
                )

                # Add insights and recommendations
                report['data']['insights'] = self._generate_insights(report['data'])
                report['data']['recommendations'] = self._generate_recommendations(report['data'])

            if report_type == 'summary':
                report['data'] = self._generate_summary_report(order_history, market_prices)

            # Store report
            self.last_report = report
            self.generated_reports.append({
                'timestamp': datetime.now(),
                'type': report_type,
                'report': report
            })

            logger.info(f"[{self.name}] Report generation complete")
            return report

        except Exception as e:
            logger.error(f"[{self.name}] Error generating report: {str(e)}")
            return self._error_report(str(e))

    def generate_pl_report(self, order_history: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate P/L focused report

        Args:
            order_history: Trading history DataFrame

        Returns:
            P/L analysis report
        """
        return self.generate_comprehensive_report(order_history, report_type='pl')

    def generate_balance_report(self,
                               order_history: pd.DataFrame,
                               market_prices: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generate balance evolution report

        Args:
            order_history: Trading history DataFrame
            market_prices: Current market prices

        Returns:
            Balance analysis report
        """
        return self.generate_comprehensive_report(order_history, market_prices, report_type='balance')

    def analyze_gap(self,
                   backtest_orders: pd.DataFrame,
                   live_orders: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze gaps between backtest and live trading

        Args:
            backtest_orders: Backtest order history
            live_orders: Live trading order history

        Returns:
            GAP analysis report
        """
        logger.info(f"[{self.name}] Generating GAP analysis...")

        gap_analysis = self.gap_analyzer.analyze_gaps(backtest_orders, live_orders)

        report = {
            'agent': self.name,
            'report_type': 'gap_analysis',
            'generated_at': datetime.now().isoformat(),
            'data': gap_analysis
        }

        self.last_report = report
        return report

    def _generate_executive_summary(self,
                                   pl_analysis: Optional[Dict] = None,
                                   balance_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate executive summary from analyses"""
        summary = {
            'performance_grade': 'N/A',
            'key_metrics': {},
            'strengths': [],
            'weaknesses': [],
            'trend': 'neutral'
        }

        # Extract key metrics
        if pl_analysis:
            pl_summary = pl_analysis.get('summary', {})
            summary['key_metrics'].update({
                'total_trades': pl_summary.get('total_trades', 0),
                'win_rate': pl_summary.get('win_rate', 0),
                'total_pnl': pl_summary.get('total_net_pnl', 0),
                'avg_pnl': pl_summary.get('avg_pnl_per_trade', 0)
            })

            # Identify strengths and weaknesses
            win_rate = pl_summary.get('win_rate', 0)
            if win_rate > 60:
                summary['strengths'].append(f"High win rate: {win_rate:.1f}%")
            elif win_rate < 40:
                summary['weaknesses'].append(f"Low win rate: {win_rate:.1f}%")

        if balance_analysis:
            balance_summary = balance_analysis.get('summary', {})
            growth_metrics = balance_analysis.get('growth_metrics', {})

            summary['key_metrics'].update({
                'total_return_pct': balance_summary.get('total_return_pct', 0),
                'sharpe_ratio': growth_metrics.get('sharpe_ratio', 0),
                'max_drawdown_pct': balance_analysis.get('drawdown_analysis', {}).get('max_drawdown_pct', 0)
            })

            # Determine trend
            total_return = balance_summary.get('total_return_pct', 0)
            if total_return > 10:
                summary['trend'] = 'strongly positive'
            elif total_return > 0:
                summary['trend'] = 'positive'
            elif total_return > -10:
                summary['trend'] = 'negative'
            else:
                summary['trend'] = 'strongly negative'

        # Calculate performance grade
        summary['performance_grade'] = self._calculate_performance_grade(summary['key_metrics'])

        return summary

    def _generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis data"""
        insights = []

        # P/L insights
        if 'pl_analysis' in data:
            pl = data['pl_analysis']
            perf = pl.get('performance_metrics', {})

            # Risk-reward insights
            rr_ratio = perf.get('risk_reward_ratio', 0)
            if rr_ratio < 1.5:
                insights.append(
                    f"Risk-reward ratio is {rr_ratio:.2f}. Consider improving exit strategies "
                    "to increase average wins relative to losses."
                )

            # Profit factor insights
            profit_factor = perf.get('profit_factor', 0)
            if profit_factor < 1.5:
                insights.append(
                    f"Profit factor is {profit_factor:.2f}. Focus on reducing losing trades "
                    "or increasing winning trade sizes."
                )

            # Expectancy insights
            expectancy = perf.get('expectancy', 0)
            if expectancy < 0:
                insights.append(
                    "Negative expectancy detected. The current strategy is not profitable "
                    "in the long run. Major adjustments needed."
                )

        # Balance insights
        if 'balance_analysis' in data:
            balance = data['balance_analysis']
            drawdown = balance.get('drawdown_analysis', {})

            # Drawdown insights
            max_dd = drawdown.get('max_drawdown_pct', 0)
            if abs(max_dd) > 20:
                insights.append(
                    f"Maximum drawdown of {abs(max_dd):.1f}% indicates high risk. "
                    "Consider implementing stricter risk management."
                )

            # Cash utilization insights
            cash_util = balance.get('cash_utilization', {})
            avg_cash = cash_util.get('avg_cash_percentage', 0)
            if avg_cash > 50:
                insights.append(
                    f"Average cash position of {avg_cash:.1f}% suggests underutilization. "
                    "Consider more aggressive position sizing."
                )
            elif avg_cash < 10:
                insights.append(
                    f"Low average cash of {avg_cash:.1f}% increases risk. "
                    "Maintain higher cash reserves for flexibility."
                )

            # Volatility insights
            volatility = balance.get('volatility_metrics', {})
            annual_vol = volatility.get('annual_volatility', 0)
            if annual_vol > 30:
                insights.append(
                    f"High annual volatility of {annual_vol:.1f}% detected. "
                    "Consider diversification or position size reduction."
                )

        return insights[:5]  # Return top 5 insights

    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on executive summary
        if 'executive_summary' in data:
            summary = data['executive_summary']
            metrics = summary.get('key_metrics', {})

            # Win rate recommendations
            win_rate = metrics.get('win_rate', 0)
            if win_rate < 45:
                recommendations.append(
                    "Improve entry signals: Consider adding confirmation indicators "
                    "or tightening entry criteria."
                )

            # Sharpe ratio recommendations
            sharpe = metrics.get('sharpe_ratio', 0)
            if sharpe < 1:
                recommendations.append(
                    "Enhance risk-adjusted returns: Focus on reducing volatility "
                    "while maintaining returns."
                )

            # Drawdown recommendations
            max_dd = metrics.get('max_drawdown_pct', 0)
            if abs(max_dd) > 15:
                recommendations.append(
                    "Implement dynamic position sizing: Reduce exposure during "
                    "market downturns."
                )

        # Based on P/L analysis
        if 'pl_analysis' in data:
            pl = data['pl_analysis']
            streak = pl.get('streak_analysis', {})

            # Streak recommendations
            max_losses = streak.get('max_consecutive_losses', 0)
            if max_losses > 5:
                recommendations.append(
                    f"Max consecutive losses: {max_losses}. Consider implementing "
                    "a circuit breaker after 3-4 consecutive losses."
                )

        # Based on balance analysis
        if 'balance_analysis' in data:
            balance = data['balance_analysis']
            health = balance.get('health_indicators', {})

            # Health score recommendations
            health_score = health.get('health_score', 0)
            if health_score < 50:
                recommendations.append(
                    "Account health is concerning. Reduce position sizes and "
                    "review risk management immediately."
                )

            # Add any auto-generated recommendations
            auto_recs = health.get('recommended_actions', [])
            recommendations.extend(auto_recs[:2])

        return recommendations[:5]  # Return top 5 recommendations

    def _generate_summary_report(self,
                                order_history: pd.DataFrame,
                                market_prices: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Generate concise summary report"""
        # Quick analysis
        pl_analysis = self.pl_analyzer.analyze_trades(order_history)
        balance_analysis = self.balance_analyzer.analyze_balance_history(order_history, market_prices)

        # Extract key points
        pl_summary = pl_analysis.get('summary', {})
        balance_summary = balance_analysis.get('summary', {})
        growth = balance_analysis.get('growth_metrics', {})
        drawdown = balance_analysis.get('drawdown_analysis', {})

        return {
            'overview': {
                'total_trades': pl_summary.get('total_trades', 0),
                'win_rate': f"{pl_summary.get('win_rate', 0):.1f}%",
                'total_return': f"${pl_summary.get('total_net_pnl', 0):,.2f}",
                'return_pct': f"{balance_summary.get('total_return_pct', 0):.1f}%"
            },
            'performance': {
                'sharpe_ratio': f"{growth.get('sharpe_ratio', 0):.2f}",
                'profit_factor': f"{pl_analysis.get('performance_metrics', {}).get('profit_factor', 0):.2f}",
                'max_drawdown': f"{abs(drawdown.get('max_drawdown_pct', 0)):.1f}%",
                'cagr': f"{growth.get('cagr', 0):.1f}%"
            },
            'current_status': {
                'balance': f"${balance_summary.get('current_balance', 0):,.2f}",
                'positions': balance_summary.get('current_positions', 0),
                'cash_pct': f"{balance_analysis.get('cash_utilization', {}).get('current_cash_percentage', 0):.1f}%",
                'health_score': balance_analysis.get('health_indicators', {}).get('health_score', 0)
            }
        }

    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> str:
        """Calculate overall performance grade (A-F)"""
        score = 0
        max_score = 100

        # Win rate scoring (0-25 points)
        win_rate = metrics.get('win_rate', 0)
        if win_rate >= 60:
            score += 25
        elif win_rate >= 50:
            score += 20
        elif win_rate >= 45:
            score += 15
        elif win_rate >= 40:
            score += 10
        else:
            score += 5

        # Return scoring (0-25 points)
        return_pct = metrics.get('total_return_pct', 0)
        if return_pct >= 30:
            score += 25
        elif return_pct >= 20:
            score += 20
        elif return_pct >= 10:
            score += 15
        elif return_pct >= 0:
            score += 10
        else:
            score += 0

        # Sharpe ratio scoring (0-25 points)
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe >= 2:
            score += 25
        elif sharpe >= 1.5:
            score += 20
        elif sharpe >= 1:
            score += 15
        elif sharpe >= 0.5:
            score += 10
        else:
            score += 5

        # Drawdown scoring (0-25 points)
        max_dd = abs(metrics.get('max_drawdown_pct', 0))
        if max_dd <= 10:
            score += 25
        elif max_dd <= 15:
            score += 20
        elif max_dd <= 20:
            score += 15
        elif max_dd <= 30:
            score += 10
        else:
            score += 5

        # Convert to grade
        percentage = (score / max_score) * 100
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'

    def get_text_report(self, report_type: str = 'last') -> str:
        """
        Get formatted text report

        Args:
            report_type: 'last', 'pl', 'balance', or 'gap'

        Returns:
            Formatted text report string
        """
        if report_type == 'last' and self.last_report:
            return self._format_report_as_text(self.last_report)
        elif report_type == 'pl':
            return self.pl_analyzer.generate_text_report()
        elif report_type == 'balance':
            return self.balance_analyzer.generate_text_report()
        elif report_type == 'gap':
            return self.gap_analyzer.generate_text_report()
        else:
            return "No report available. Generate a report first."

    def _format_report_as_text(self, report: Dict[str, Any]) -> str:
        """Format report dictionary as readable text"""
        lines = [
            "=" * 80,
            f"                    {report.get('report_type', 'REPORT').upper()} REPORT",
            "=" * 80,
            f"Generated by: {report.get('agent', 'Report Agent')}",
            f"Generated at: {report.get('generated_at', 'N/A')}",
            "",
        ]

        # Format data section
        data = report.get('data', {})

        # Executive Summary
        if 'executive_summary' in data:
            summary = data['executive_summary']
            lines.extend([
                "-" * 40,
                "EXECUTIVE SUMMARY",
                "-" * 40,
                f"Performance Grade: {summary.get('performance_grade', 'N/A')}",
                f"Trend: {summary.get('trend', 'N/A')}",
                ""
            ])

            # Key Metrics
            metrics = summary.get('key_metrics', {})
            if metrics:
                lines.append("Key Metrics:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        lines.append(f"  {key}: {value:.2f}")
                    else:
                        lines.append(f"  {key}: {value}")
                lines.append("")

        # Insights
        if 'insights' in data:
            lines.extend([
                "-" * 40,
                "KEY INSIGHTS",
                "-" * 40
            ])
            for i, insight in enumerate(data['insights'], 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        # Recommendations
        if 'recommendations' in data:
            lines.extend([
                "-" * 40,
                "RECOMMENDATIONS",
                "-" * 40
            ])
            for i, rec in enumerate(data['recommendations'], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def save_report(self, filepath: str, format: str = 'json') -> bool:
        """
        Save last report to file

        Args:
            filepath: Output file path
            format: 'json' or 'text'

        Returns:
            Success status
        """
        try:
            if not self.last_report:
                logger.warning("[Report Agent] No report to save")
                return False

            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(self.last_report, f, indent=2, default=str)
            else:  # text format
                with open(filepath, 'w') as f:
                    f.write(self.get_text_report('last'))

            logger.info(f"[Report Agent] Report saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"[Report Agent] Error saving report: {str(e)}")
            return False

    def _error_report(self, error_msg: str) -> Dict[str, Any]:
        """Generate error report"""
        return {
            'agent': self.name,
            'status': 'error',
            'error': error_msg,
            'generated_at': datetime.now().isoformat()
        }