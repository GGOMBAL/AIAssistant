"""
P/L Analyzer Module for Reporting Layer
Calculates profit/loss, win rate, and risk-reward ratios from trading history.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Logger setup
logger = logging.getLogger(__name__)


class PLAnalyzer:
    """
    Profit and Loss Analyzer

    Analyzes trading performance including:
    - Win rate calculations
    - Average profit/loss per trade
    - Risk-reward ratios
    - Maximum drawdowns
    - Consecutive wins/losses
    - Performance by market/sector
    """

    def __init__(self):
        """Initialize P/L Analyzer"""
        self.report_data = {}
        self.analysis_results = {}

    def analyze_trades(self, order_history: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze trading history and generate P/L report

        Args:
            order_history: DataFrame with columns:
                - ticker: Stock ticker
                - order_type: 'BUY' or 'SELL'
                - order_date: Order execution date
                - execution_price: Actual execution price
                - quantity: Number of shares
                - commission: Trading commission
                - order_id: Unique order identifier

        Returns:
            Dict containing P/L analysis results
        """
        try:
            # Validate input data
            if order_history.empty:
                logger.warning("Empty order history provided")
                return self._empty_report()

            # Calculate closed positions
            closed_positions = self._calculate_closed_positions(order_history)

            if closed_positions.empty:
                return self._empty_report()

            # Calculate P/L metrics
            report = {
                'summary': self._calculate_summary_stats(closed_positions),
                'performance_metrics': self._calculate_performance_metrics(closed_positions),
                'trade_distribution': self._analyze_trade_distribution(closed_positions),
                'time_analysis': self._analyze_by_time_period(closed_positions),
                'ticker_performance': self._analyze_by_ticker(closed_positions),
                'risk_metrics': self._calculate_risk_metrics(closed_positions),
                'streak_analysis': self._analyze_winning_losing_streaks(closed_positions),
                'report_generated': datetime.now().isoformat()
            }

            self.analysis_results = report
            return report

        except Exception as e:
            logger.error(f"Error analyzing trades: {str(e)}")
            return self._empty_report()

    def _calculate_closed_positions(self, order_history: pd.DataFrame) -> pd.DataFrame:
        """
        Match buy and sell orders to calculate closed positions

        Returns:
            DataFrame with closed position P/L calculations
        """
        positions = []
        order_history = order_history.sort_values('order_date')

        # Group by ticker
        for ticker in order_history['ticker'].unique():
            ticker_orders = order_history[order_history['ticker'] == ticker].copy()

            # FIFO matching for positions
            buy_queue = []

            for _, order in ticker_orders.iterrows():
                if order['order_type'] == 'BUY':
                    buy_queue.append({
                        'ticker': ticker,
                        'buy_date': order['order_date'],
                        'buy_price': order['execution_price'],
                        'quantity': order['quantity'],
                        'buy_commission': order.get('commission', 0)
                    })

                elif order['order_type'] == 'SELL' and buy_queue:
                    sell_quantity = order['quantity']
                    sell_price = order['execution_price']
                    sell_date = order['order_date']
                    sell_commission = order.get('commission', 0)

                    while sell_quantity > 0 and buy_queue:
                        buy_order = buy_queue[0]

                        # Calculate matched quantity
                        matched_qty = min(sell_quantity, buy_order['quantity'])

                        # Calculate P/L for this position
                        gross_pnl = (sell_price - buy_order['buy_price']) * matched_qty
                        commission_cost = (buy_order['buy_commission'] + sell_commission) * \
                                        (matched_qty / order['quantity'])
                        net_pnl = gross_pnl - commission_cost

                        # Calculate holding period
                        holding_days = (sell_date - buy_order['buy_date']).days

                        # Calculate return percentage
                        return_pct = ((sell_price - buy_order['buy_price']) /
                                    buy_order['buy_price'] * 100)

                        positions.append({
                            'ticker': ticker,
                            'buy_date': buy_order['buy_date'],
                            'sell_date': sell_date,
                            'buy_price': buy_order['buy_price'],
                            'sell_price': sell_price,
                            'quantity': matched_qty,
                            'gross_pnl': gross_pnl,
                            'commission': commission_cost,
                            'net_pnl': net_pnl,
                            'return_pct': return_pct,
                            'holding_days': holding_days,
                            'win': net_pnl > 0
                        })

                        # Update quantities
                        sell_quantity -= matched_qty
                        buy_order['quantity'] -= matched_qty

                        # Remove completed buy orders
                        if buy_order['quantity'] <= 0:
                            buy_queue.pop(0)

        return pd.DataFrame(positions)

    def _calculate_summary_stats(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total_trades = len(positions)
        winning_trades = positions[positions['win']].shape[0]
        losing_trades = total_trades - winning_trades

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': winning_trades / total_trades * 100 if total_trades > 0 else 0,
            'total_gross_pnl': positions['gross_pnl'].sum(),
            'total_commission': positions['commission'].sum(),
            'total_net_pnl': positions['net_pnl'].sum(),
            'avg_pnl_per_trade': positions['net_pnl'].mean(),
            'avg_return_pct': positions['return_pct'].mean(),
            'avg_holding_days': positions['holding_days'].mean(),
            'best_trade': positions['net_pnl'].max(),
            'worst_trade': positions['net_pnl'].min(),
            'best_return_pct': positions['return_pct'].max(),
            'worst_return_pct': positions['return_pct'].min()
        }

    def _calculate_performance_metrics(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        wins = positions[positions['win']]
        losses = positions[~positions['win']]

        avg_win = wins['net_pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['net_pnl'].mean()) if not losses.empty else 0

        # Profit factor: gross profits / gross losses
        gross_profits = wins['gross_pnl'].sum() if not wins.empty else 0
        gross_losses = abs(losses['gross_pnl'].sum()) if not losses.empty else 0
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')

        # Risk-Reward Ratio
        risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')

        # Expectancy (average expected profit per trade)
        win_rate = len(wins) / len(positions) if len(positions) > 0 else 0
        loss_rate = 1 - win_rate
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        # Sharpe Ratio approximation (simplified)
        returns = positions['return_pct'].values
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0

        return {
            'average_win': avg_win,
            'average_loss': avg_loss,
            'risk_reward_ratio': risk_reward_ratio,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe,
            'median_pnl': positions['net_pnl'].median(),
            'std_pnl': positions['net_pnl'].std(),
            'skewness': positions['net_pnl'].skew(),
            'kurtosis': positions['net_pnl'].kurtosis()
        }

    def _analyze_trade_distribution(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution of trades"""
        pnl_bins = [-float('inf'), -1000, -500, -100, 0, 100, 500, 1000, float('inf')]
        pnl_labels = ['< -1000', '-1000 to -500', '-500 to -100', '-100 to 0',
                     '0 to 100', '100 to 500', '500 to 1000', '> 1000']

        positions['pnl_bin'] = pd.cut(positions['net_pnl'], bins=pnl_bins, labels=pnl_labels)
        distribution = positions['pnl_bin'].value_counts().to_dict()

        # Holding period distribution
        holding_bins = [0, 1, 7, 30, 90, 365, float('inf')]
        holding_labels = ['Intraday', '1-7 days', '1-4 weeks', '1-3 months',
                         '3-12 months', '> 1 year']
        positions['holding_bin'] = pd.cut(positions['holding_days'],
                                         bins=holding_bins, labels=holding_labels)
        holding_distribution = positions['holding_bin'].value_counts().to_dict()

        return {
            'pnl_distribution': distribution,
            'holding_period_distribution': holding_distribution
        }

    def _analyze_by_time_period(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by time period"""
        positions['year_month'] = pd.to_datetime(positions['sell_date']).dt.to_period('M')

        monthly_performance = positions.groupby('year_month').agg({
            'net_pnl': 'sum',
            'return_pct': 'mean',
            'win': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0
        }).to_dict('index')

        # Convert Period to string for JSON serialization
        monthly_performance = {str(k): v for k, v in monthly_performance.items()}

        # Analyze by day of week
        positions['day_of_week'] = pd.to_datetime(positions['sell_date']).dt.day_name()
        daily_performance = positions.groupby('day_of_week')['net_pnl'].agg(['sum', 'mean']).to_dict('index')

        return {
            'monthly_performance': monthly_performance,
            'day_of_week_performance': daily_performance
        }

    def _analyze_by_ticker(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by ticker"""
        ticker_stats = positions.groupby('ticker').agg({
            'net_pnl': ['sum', 'mean', 'count'],
            'win': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0,
            'return_pct': 'mean'
        }).round(2)

        # Flatten column names
        ticker_stats.columns = ['_'.join(col).strip() for col in ticker_stats.columns.values]

        # Get top performers and worst performers
        top_5_profitable = positions.groupby('ticker')['net_pnl'].sum().nlargest(5).to_dict()
        worst_5_losers = positions.groupby('ticker')['net_pnl'].sum().nsmallest(5).to_dict()

        return {
            'ticker_statistics': ticker_stats.to_dict('index'),
            'top_5_profitable_tickers': top_5_profitable,
            'worst_5_losing_tickers': worst_5_losers
        }

    def _calculate_risk_metrics(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk-related metrics"""
        # Calculate running P/L for drawdown
        positions = positions.sort_values('sell_date')
        positions['cumulative_pnl'] = positions['net_pnl'].cumsum()
        positions['running_max'] = positions['cumulative_pnl'].cummax()
        positions['drawdown'] = positions['cumulative_pnl'] - positions['running_max']

        max_drawdown = positions['drawdown'].min()
        max_drawdown_pct = (max_drawdown / positions['running_max'].max() * 100) \
                          if positions['running_max'].max() > 0 else 0

        # Calculate Value at Risk (VaR) - 95% confidence
        var_95 = np.percentile(positions['net_pnl'], 5)

        # Calculate Conditional Value at Risk (CVaR)
        losses_below_var = positions[positions['net_pnl'] <= var_95]['net_pnl']
        cvar_95 = losses_below_var.mean() if not losses_below_var.empty else 0

        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'value_at_risk_95': var_95,
            'conditional_value_at_risk_95': cvar_95,
            'recovery_factor': positions['cumulative_pnl'].iloc[-1] / abs(max_drawdown)
                              if max_drawdown != 0 else float('inf')
        }

    def _analyze_winning_losing_streaks(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """Analyze consecutive winning and losing streaks"""
        positions = positions.sort_values('sell_date')
        wins = positions['win'].values

        # Calculate streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        current_is_win = None

        for win in wins:
            if current_is_win is None or current_is_win != win:
                # Streak changed
                if current_is_win is True:
                    max_win_streak = max(max_win_streak, current_streak)
                elif current_is_win is False:
                    max_loss_streak = max(max_loss_streak, current_streak)

                current_streak = 1
                current_is_win = win
            else:
                current_streak += 1

        # Check final streak
        if current_is_win is True:
            max_win_streak = max(max_win_streak, current_streak)
        elif current_is_win is False:
            max_loss_streak = max(max_loss_streak, current_streak)

        # Current streak
        if len(wins) > 0:
            current_streak_type = 'win' if wins[-1] else 'loss'
            current_streak_length = 1
            for i in range(len(wins) - 2, -1, -1):
                if wins[i] == wins[-1]:
                    current_streak_length += 1
                else:
                    break
        else:
            current_streak_type = None
            current_streak_length = 0

        return {
            'max_consecutive_wins': max_win_streak,
            'max_consecutive_losses': max_loss_streak,
            'current_streak_type': current_streak_type,
            'current_streak_length': current_streak_length
        }

    def _empty_report(self) -> Dict[str, Any]:
        """Return empty report structure"""
        return {
            'summary': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_net_pnl': 0
            },
            'performance_metrics': {},
            'trade_distribution': {},
            'time_analysis': {},
            'ticker_performance': {},
            'risk_metrics': {},
            'streak_analysis': {},
            'report_generated': datetime.now().isoformat(),
            'status': 'No closed positions found'
        }

    def generate_text_report(self) -> str:
        """
        Generate a formatted text report from analysis results

        Returns:
            Formatted text report string
        """
        if not self.analysis_results:
            return "No analysis results available. Please run analyze_trades() first."

        report_lines = [
            "=" * 80,
            "                     P/L ANALYSIS REPORT",
            "=" * 80,
            f"Generated: {self.analysis_results.get('report_generated', 'N/A')}",
            "",
            "-" * 40,
            "SUMMARY STATISTICS",
            "-" * 40
        ]

        summary = self.analysis_results.get('summary', {})
        report_lines.extend([
            f"Total Trades: {summary.get('total_trades', 0)}",
            f"Winning Trades: {summary.get('winning_trades', 0)}",
            f"Losing Trades: {summary.get('losing_trades', 0)}",
            f"Win Rate: {summary.get('win_rate', 0):.2f}%",
            f"Total Net P/L: ${summary.get('total_net_pnl', 0):,.2f}",
            f"Average P/L per Trade: ${summary.get('avg_pnl_per_trade', 0):,.2f}",
            f"Best Trade: ${summary.get('best_trade', 0):,.2f}",
            f"Worst Trade: ${summary.get('worst_trade', 0):,.2f}",
            "",
            "-" * 40,
            "PERFORMANCE METRICS",
            "-" * 40
        ])

        metrics = self.analysis_results.get('performance_metrics', {})
        report_lines.extend([
            f"Average Win: ${metrics.get('average_win', 0):,.2f}",
            f"Average Loss: ${metrics.get('average_loss', 0):,.2f}",
            f"Risk-Reward Ratio: {metrics.get('risk_reward_ratio', 0):.2f}",
            f"Profit Factor: {metrics.get('profit_factor', 0):.2f}",
            f"Expectancy: ${metrics.get('expectancy', 0):,.2f}",
            f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}",
            "",
            "-" * 40,
            "RISK METRICS",
            "-" * 40
        ])

        risk = self.analysis_results.get('risk_metrics', {})
        report_lines.extend([
            f"Maximum Drawdown: ${risk.get('max_drawdown', 0):,.2f}",
            f"Maximum Drawdown %: {risk.get('max_drawdown_pct', 0):.2f}%",
            f"Value at Risk (95%): ${risk.get('value_at_risk_95', 0):,.2f}",
            f"Recovery Factor: {risk.get('recovery_factor', 0):.2f}",
            "",
            "=" * 80
        ])

        return "\n".join(report_lines)