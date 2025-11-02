"""
Balance Analyzer Module for Reporting Layer
Tracks and analyzes account balance changes over time.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

# Logger setup
logger = logging.getLogger(__name__)


class BalanceAnalyzer:
    """
    Account Balance Analyzer

    Analyzes account balance evolution including:
    - Daily/Monthly/Yearly balance tracking
    - Growth rate calculations
    - Peak and trough analysis
    - Cash utilization metrics
    - Portfolio value tracking
    - Liquidity analysis
    """

    def __init__(self, initial_balance: float = 100000.0):
        """
        Initialize Balance Analyzer

        Args:
            initial_balance: Starting account balance
        """
        self.initial_balance = initial_balance
        self.balance_history = []
        self.analysis_results = {}

    def analyze_balance_history(self,
                               order_history: pd.DataFrame,
                               market_prices: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze account balance evolution from trading history

        Args:
            order_history: DataFrame with columns:
                - ticker: Stock ticker
                - order_type: 'BUY' or 'SELL'
                - order_date: Order execution date
                - execution_price: Actual execution price
                - quantity: Number of shares
                - commission: Trading commission
            market_prices: Optional DataFrame with current market prices
                - ticker: Stock ticker
                - date: Price date
                - close: Closing price

        Returns:
            Dict containing balance analysis results
        """
        try:
            # Validate input
            if order_history.empty:
                logger.warning("Empty order history provided")
                return self._empty_report()

            # Calculate daily balance
            daily_balance = self._calculate_daily_balance(order_history, market_prices)

            if daily_balance.empty:
                return self._empty_report()

            # Perform analysis
            report = {
                'summary': self._calculate_balance_summary(daily_balance),
                'growth_metrics': self._calculate_growth_metrics(daily_balance),
                'volatility_metrics': self._calculate_volatility_metrics(daily_balance),
                'drawdown_analysis': self._analyze_drawdowns(daily_balance),
                'cash_utilization': self._analyze_cash_utilization(daily_balance),
                'period_analysis': self._analyze_by_period(daily_balance),
                'milestone_analysis': self._analyze_milestones(daily_balance),
                'health_indicators': self._calculate_health_indicators(daily_balance),
                'forecast': self._generate_forecast(daily_balance),
                'report_generated': datetime.now().isoformat()
            }

            self.analysis_results = report
            return report

        except Exception as e:
            logger.error(f"Error analyzing balance history: {str(e)}")
            return self._empty_report()

    def _calculate_daily_balance(self,
                                order_history: pd.DataFrame,
                                market_prices: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Calculate daily account balance including cash and positions

        Returns:
            DataFrame with daily balance calculations
        """
        # Initialize tracking variables
        cash_balance = self.initial_balance
        positions = {}  # {ticker: quantity}
        balance_records = []

        # Sort orders by date
        order_history = order_history.sort_values('order_date').copy()

        # Get date range
        start_date = order_history['order_date'].min()
        end_date = datetime.now()
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # Track positions and cash changes
        for date in date_range:
            # Process orders for this date
            daily_orders = order_history[
                pd.to_datetime(order_history['order_date']).dt.date == date.date()
            ]

            for _, order in daily_orders.iterrows():
                ticker = order['ticker']
                quantity = order['quantity']
                price = order['execution_price']
                commission = order.get('commission', 0)

                if order['order_type'] == 'BUY':
                    # Buy order - decrease cash, increase position
                    cash_balance -= (price * quantity + commission)
                    if ticker not in positions:
                        positions[ticker] = 0
                    positions[ticker] += quantity

                elif order['order_type'] == 'SELL':
                    # Sell order - increase cash, decrease position
                    cash_balance += (price * quantity - commission)
                    if ticker in positions:
                        positions[ticker] -= quantity
                        if positions[ticker] <= 0:
                            del positions[ticker]

            # Calculate portfolio value
            portfolio_value = 0
            position_details = {}

            if market_prices is not None:
                # Use actual market prices if available
                daily_prices = market_prices[
                    pd.to_datetime(market_prices['date']).dt.date == date.date()
                ]

                for ticker, qty in positions.items():
                    ticker_price = daily_prices[
                        daily_prices['ticker'] == ticker
                    ]['close'].values

                    if len(ticker_price) > 0:
                        value = ticker_price[0] * qty
                    else:
                        # Use last known price or order price
                        last_order = order_history[
                            (order_history['ticker'] == ticker) &
                            (order_history['order_date'] <= date)
                        ].iloc[-1] if not order_history.empty else None

                        value = last_order['execution_price'] * qty if last_order is not None else 0

                    portfolio_value += value
                    position_details[ticker] = {
                        'quantity': qty,
                        'value': value
                    }
            else:
                # Estimate portfolio value using last execution prices
                for ticker, qty in positions.items():
                    last_order = order_history[
                        (order_history['ticker'] == ticker) &
                        (pd.to_datetime(order_history['order_date']) <= date)
                    ]

                    if not last_order.empty:
                        last_price = last_order.iloc[-1]['execution_price']
                        value = last_price * qty
                        portfolio_value += value
                        position_details[ticker] = {
                            'quantity': qty,
                            'value': value
                        }

            # Calculate total balance
            total_balance = cash_balance + portfolio_value

            # Calculate metrics
            balance_records.append({
                'date': date,
                'cash_balance': cash_balance,
                'portfolio_value': portfolio_value,
                'total_balance': total_balance,
                'num_positions': len(positions),
                'positions': position_details.copy(),
                'cash_percentage': (cash_balance / total_balance * 100) if total_balance > 0 else 0,
                'invested_percentage': (portfolio_value / total_balance * 100) if total_balance > 0 else 0,
                'daily_change': 0,  # Will be calculated next
                'daily_return': 0,   # Will be calculated next
                'cumulative_return': ((total_balance - self.initial_balance) /
                                     self.initial_balance * 100)
            })

        # Convert to DataFrame
        balance_df = pd.DataFrame(balance_records)

        # Calculate daily changes
        if not balance_df.empty:
            balance_df['daily_change'] = balance_df['total_balance'].diff()
            balance_df['daily_return'] = balance_df['total_balance'].pct_change() * 100
            balance_df['cumulative_balance'] = balance_df['total_balance']
            balance_df['high_water_mark'] = balance_df['total_balance'].cummax()
            balance_df['drawdown'] = balance_df['total_balance'] - balance_df['high_water_mark']
            balance_df['drawdown_pct'] = (balance_df['drawdown'] /
                                         balance_df['high_water_mark'] * 100)

        return balance_df

    def _calculate_balance_summary(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate balance summary statistics"""
        current_balance = balance_df.iloc[-1]['total_balance'] if not balance_df.empty else self.initial_balance
        peak_balance = balance_df['total_balance'].max() if not balance_df.empty else self.initial_balance
        trough_balance = balance_df['total_balance'].min() if not balance_df.empty else self.initial_balance

        return {
            'initial_balance': self.initial_balance,
            'current_balance': current_balance,
            'peak_balance': peak_balance,
            'trough_balance': trough_balance,
            'peak_date': balance_df.loc[balance_df['total_balance'].idxmax(), 'date'].strftime('%Y-%m-%d')
                        if not balance_df.empty else None,
            'trough_date': balance_df.loc[balance_df['total_balance'].idxmin(), 'date'].strftime('%Y-%m-%d')
                          if not balance_df.empty else None,
            'total_return': current_balance - self.initial_balance,
            'total_return_pct': ((current_balance - self.initial_balance) /
                                self.initial_balance * 100),
            'days_tracked': len(balance_df),
            'current_cash': balance_df.iloc[-1]['cash_balance'] if not balance_df.empty else self.initial_balance,
            'current_portfolio_value': balance_df.iloc[-1]['portfolio_value'] if not balance_df.empty else 0,
            'current_positions': balance_df.iloc[-1]['num_positions'] if not balance_df.empty else 0
        }

    def _calculate_growth_metrics(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate growth and performance metrics"""
        if balance_df.empty:
            return {}

        # Calculate returns
        daily_returns = balance_df['daily_return'].dropna()
        trading_days = len(daily_returns)

        # Annualized metrics
        annual_return = daily_returns.mean() * 252 if trading_days > 0 else 0
        annual_volatility = daily_returns.std() * np.sqrt(252) if trading_days > 0 else 0

        # CAGR (Compound Annual Growth Rate)
        years = trading_days / 252 if trading_days > 0 else 1
        ending_value = balance_df.iloc[-1]['total_balance']
        cagr = (((ending_value / self.initial_balance) ** (1/years)) - 1) * 100 if years > 0 else 0

        # Monthly returns
        balance_df['month'] = pd.to_datetime(balance_df['date']).dt.to_period('M')
        monthly_returns = balance_df.groupby('month')['total_balance'].last().pct_change() * 100

        return {
            'cagr': cagr,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': (annual_return / annual_volatility) if annual_volatility > 0 else 0,
            'avg_daily_return': daily_returns.mean(),
            'best_day_return': daily_returns.max(),
            'worst_day_return': daily_returns.min(),
            'positive_days': (daily_returns > 0).sum(),
            'negative_days': (daily_returns < 0).sum(),
            'win_rate_days': ((daily_returns > 0).sum() / len(daily_returns) * 100)
                            if len(daily_returns) > 0 else 0,
            'avg_monthly_return': monthly_returns.mean() if not monthly_returns.empty else 0,
            'best_month_return': monthly_returns.max() if not monthly_returns.empty else 0,
            'worst_month_return': monthly_returns.min() if not monthly_returns.empty else 0
        }

    def _calculate_volatility_metrics(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volatility and risk metrics"""
        if balance_df.empty:
            return {}

        daily_returns = balance_df['daily_return'].dropna()

        # Calculate rolling volatility
        rolling_vol_30d = daily_returns.rolling(window=30).std() * np.sqrt(252)
        current_vol = rolling_vol_30d.iloc[-1] if not rolling_vol_30d.empty else 0

        # Downside deviation (only negative returns)
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0

        # Sortino ratio (excess return / downside deviation)
        avg_return = daily_returns.mean() * 252
        sortino_ratio = avg_return / downside_deviation if downside_deviation > 0 else 0

        # Value at Risk (VaR)
        var_95 = np.percentile(daily_returns, 5)
        var_99 = np.percentile(daily_returns, 1)

        return {
            'daily_volatility': daily_returns.std(),
            'annual_volatility': daily_returns.std() * np.sqrt(252),
            'current_30d_volatility': current_vol,
            'max_30d_volatility': rolling_vol_30d.max() if not rolling_vol_30d.empty else 0,
            'min_30d_volatility': rolling_vol_30d.min() if not rolling_vol_30d.empty else 0,
            'downside_deviation': downside_deviation,
            'sortino_ratio': sortino_ratio,
            'value_at_risk_95': var_95,
            'value_at_risk_99': var_99,
            'skewness': daily_returns.skew(),
            'kurtosis': daily_returns.kurtosis()
        }

    def _analyze_drawdowns(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze drawdown periods"""
        if balance_df.empty:
            return {}

        # Find all drawdown periods
        drawdown_periods = []
        in_drawdown = False
        drawdown_start = None
        peak_value = self.initial_balance

        for idx, row in balance_df.iterrows():
            if row['total_balance'] < row['high_water_mark']:
                if not in_drawdown:
                    in_drawdown = True
                    drawdown_start = row['date']
                    peak_value = row['high_water_mark']
            else:
                if in_drawdown:
                    # Drawdown ended
                    drawdown_end = row['date']
                    trough_idx = balance_df[
                        (balance_df['date'] >= drawdown_start) &
                        (balance_df['date'] <= drawdown_end)
                    ]['total_balance'].idxmin()

                    trough_value = balance_df.loc[trough_idx, 'total_balance']
                    trough_date = balance_df.loc[trough_idx, 'date']

                    drawdown_periods.append({
                        'start_date': drawdown_start,
                        'end_date': drawdown_end,
                        'trough_date': trough_date,
                        'peak_value': peak_value,
                        'trough_value': trough_value,
                        'drawdown_amount': peak_value - trough_value,
                        'drawdown_pct': ((peak_value - trough_value) / peak_value * 100),
                        'duration_days': (drawdown_end - drawdown_start).days,
                        'recovery_days': (drawdown_end - trough_date).days
                    })

                    in_drawdown = False

        # Current drawdown if still in one
        if in_drawdown and not balance_df.empty:
            current_balance = balance_df.iloc[-1]['total_balance']
            current_date = balance_df.iloc[-1]['date']

            trough_idx = balance_df[
                balance_df['date'] >= drawdown_start
            ]['total_balance'].idxmin()

            current_drawdown = {
                'start_date': drawdown_start,
                'current_date': current_date,
                'peak_value': peak_value,
                'current_value': current_balance,
                'trough_value': balance_df.loc[trough_idx, 'total_balance'],
                'drawdown_amount': peak_value - current_balance,
                'drawdown_pct': ((peak_value - current_balance) / peak_value * 100),
                'duration_days': (current_date - drawdown_start).days
            }
        else:
            current_drawdown = None

        # Calculate max drawdown
        max_dd = balance_df['drawdown'].min() if not balance_df.empty else 0
        max_dd_pct = balance_df['drawdown_pct'].min() if not balance_df.empty else 0

        # Find longest drawdown
        longest_dd = max(drawdown_periods, key=lambda x: x['duration_days']) \
                    if drawdown_periods else None

        return {
            'max_drawdown': abs(max_dd),
            'max_drawdown_pct': abs(max_dd_pct),
            'current_drawdown': current_drawdown,
            'num_drawdowns': len(drawdown_periods),
            'avg_drawdown_pct': np.mean([dd['drawdown_pct'] for dd in drawdown_periods])
                               if drawdown_periods else 0,
            'avg_recovery_days': np.mean([dd['recovery_days'] for dd in drawdown_periods])
                                if drawdown_periods else 0,
            'longest_drawdown': longest_dd,
            'drawdown_periods': drawdown_periods[:5]  # Top 5 drawdowns
        }

    def _analyze_cash_utilization(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze cash utilization patterns"""
        if balance_df.empty:
            return {}

        # Cash utilization metrics
        avg_cash_pct = balance_df['cash_percentage'].mean()
        avg_invested_pct = balance_df['invested_percentage'].mean()
        max_invested_pct = balance_df['invested_percentage'].max()
        min_cash_balance = balance_df['cash_balance'].min()

        # Periods of high/low cash
        high_cash_days = (balance_df['cash_percentage'] > 50).sum()
        low_cash_days = (balance_df['cash_percentage'] < 10).sum()

        # Calculate cash efficiency (return generated per unit of invested capital)
        avg_invested = balance_df['portfolio_value'].mean()
        total_return = balance_df.iloc[-1]['total_balance'] - self.initial_balance

        cash_efficiency = (total_return / avg_invested * 100) if avg_invested > 0 else 0

        return {
            'avg_cash_percentage': avg_cash_pct,
            'avg_invested_percentage': avg_invested_pct,
            'max_invested_percentage': max_invested_pct,
            'min_cash_balance': min_cash_balance,
            'current_cash_percentage': balance_df.iloc[-1]['cash_percentage']
                                      if not balance_df.empty else 100,
            'days_high_cash': high_cash_days,
            'days_low_cash': low_cash_days,
            'cash_efficiency': cash_efficiency,
            'avg_positions_held': balance_df['num_positions'].mean(),
            'max_positions_held': balance_df['num_positions'].max()
        }

    def _analyze_by_period(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by different time periods"""
        if balance_df.empty:
            return {}

        balance_df = balance_df.copy()
        balance_df['date'] = pd.to_datetime(balance_df['date'])

        # Monthly analysis
        balance_df['year_month'] = balance_df['date'].dt.to_period('M')
        monthly = balance_df.groupby('year_month').agg({
            'total_balance': ['first', 'last'],
            'daily_return': 'mean',
            'num_positions': 'mean'
        })

        monthly_returns = {}
        for period in monthly.index:
            first = monthly.loc[period, ('total_balance', 'first')]
            last = monthly.loc[period, ('total_balance', 'last')]
            monthly_returns[str(period)] = {
                'return_pct': ((last - first) / first * 100) if first > 0 else 0,
                'avg_daily_return': monthly.loc[period, ('daily_return', 'mean')],
                'avg_positions': monthly.loc[period, ('num_positions', 'mean')]
            }

        # Quarterly analysis
        balance_df['quarter'] = balance_df['date'].dt.to_period('Q')
        quarterly = balance_df.groupby('quarter')['total_balance'].agg(['first', 'last'])
        quarterly_returns = {}

        for period in quarterly.index:
            first = quarterly.loc[period, 'first']
            last = quarterly.loc[period, 'last']
            quarterly_returns[str(period)] = ((last - first) / first * 100) if first > 0 else 0

        # Recent performance
        current_date = balance_df['date'].max()
        last_7d = balance_df[balance_df['date'] > current_date - timedelta(days=7)]
        last_30d = balance_df[balance_df['date'] > current_date - timedelta(days=30)]
        last_90d = balance_df[balance_df['date'] > current_date - timedelta(days=90)]

        def calc_period_return(df):
            if df.empty:
                return 0
            first = df.iloc[0]['total_balance']
            last = df.iloc[-1]['total_balance']
            return ((last - first) / first * 100) if first > 0 else 0

        return {
            'monthly_returns': monthly_returns,
            'quarterly_returns': quarterly_returns,
            'last_7d_return': calc_period_return(last_7d),
            'last_30d_return': calc_period_return(last_30d),
            'last_90d_return': calc_period_return(last_90d),
            'ytd_return': self._calculate_ytd_return(balance_df),
            'best_quarter': max(quarterly_returns.items(), key=lambda x: x[1])[0]
                          if quarterly_returns else None,
            'worst_quarter': min(quarterly_returns.items(), key=lambda x: x[1])[0]
                           if quarterly_returns else None
        }

    def _calculate_ytd_return(self, balance_df: pd.DataFrame) -> float:
        """Calculate year-to-date return"""
        if balance_df.empty:
            return 0

        current_year = datetime.now().year
        balance_df['year'] = pd.to_datetime(balance_df['date']).dt.year

        ytd_data = balance_df[balance_df['year'] == current_year]
        if ytd_data.empty:
            return 0

        first = ytd_data.iloc[0]['total_balance']
        last = ytd_data.iloc[-1]['total_balance']

        return ((last - first) / first * 100) if first > 0 else 0

    def _analyze_milestones(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze balance milestones"""
        if balance_df.empty:
            return {}

        milestones = []
        milestone_values = [50000, 100000, 150000, 200000, 250000, 500000, 1000000]

        for milestone in milestone_values:
            crossed = balance_df[balance_df['total_balance'] >= milestone]
            if not crossed.empty:
                first_cross = crossed.iloc[0]
                milestones.append({
                    'value': milestone,
                    'date_reached': first_cross['date'].strftime('%Y-%m-%d'),
                    'days_from_start': (first_cross['date'] - balance_df.iloc[0]['date']).days
                })

        # Time to double
        double_value = self.initial_balance * 2
        doubled = balance_df[balance_df['total_balance'] >= double_value]
        time_to_double = (doubled.iloc[0]['date'] - balance_df.iloc[0]['date']).days \
                        if not doubled.empty else None

        return {
            'milestones_reached': milestones,
            'time_to_double_days': time_to_double,
            'next_milestone': next((m for m in milestone_values
                                  if m > balance_df.iloc[-1]['total_balance']), None)
                            if not balance_df.empty else milestone_values[0]
        }

    def _calculate_health_indicators(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate account health indicators"""
        if balance_df.empty:
            return {}

        current_balance = balance_df.iloc[-1]['total_balance']
        current_cash = balance_df.iloc[-1]['cash_balance']

        # Risk indicators
        is_overleveraged = current_cash < 0
        cash_cushion = current_cash / current_balance * 100 if current_balance > 0 else 0

        # Trend indicators
        sma_20 = balance_df['total_balance'].rolling(20).mean().iloc[-1] \
                if len(balance_df) >= 20 else current_balance
        sma_50 = balance_df['total_balance'].rolling(50).mean().iloc[-1] \
                if len(balance_df) >= 50 else current_balance

        trend_strength = ((current_balance - sma_50) / sma_50 * 100) if sma_50 > 0 else 0

        # Recovery metrics
        from_peak = ((current_balance - balance_df['total_balance'].max()) /
                    balance_df['total_balance'].max() * 100)

        # Health score (0-100)
        health_score = self._calculate_health_score(
            cash_cushion=cash_cushion,
            trend_strength=trend_strength,
            from_peak=from_peak,
            is_overleveraged=is_overleveraged
        )

        return {
            'health_score': health_score,
            'is_overleveraged': is_overleveraged,
            'cash_cushion_pct': cash_cushion,
            'trend_direction': 'up' if current_balance > sma_20 else 'down',
            'trend_strength': trend_strength,
            'distance_from_peak_pct': from_peak,
            'risk_level': self._determine_risk_level(health_score),
            'recommended_actions': self._generate_recommendations(health_score, cash_cushion)
        }

    def _calculate_health_score(self, cash_cushion, trend_strength,
                               from_peak, is_overleveraged) -> float:
        """Calculate overall health score (0-100)"""
        score = 50  # Base score

        # Cash cushion factor (0-25 points)
        if cash_cushion > 30:
            score += 25
        elif cash_cushion > 20:
            score += 20
        elif cash_cushion > 10:
            score += 15
        elif cash_cushion > 5:
            score += 10
        else:
            score += 5

        # Trend factor (0-25 points)
        if trend_strength > 10:
            score += 25
        elif trend_strength > 5:
            score += 20
        elif trend_strength > 0:
            score += 15
        elif trend_strength > -5:
            score += 10
        else:
            score += 0

        # Drawdown factor (0-25 points)
        if from_peak >= -5:
            score += 25
        elif from_peak >= -10:
            score += 20
        elif from_peak >= -15:
            score += 15
        elif from_peak >= -20:
            score += 10
        else:
            score += 5

        # Penalties
        if is_overleveraged:
            score -= 25

        return max(0, min(100, score))

    def _determine_risk_level(self, health_score: float) -> str:
        """Determine risk level based on health score"""
        if health_score >= 80:
            return "Low Risk"
        elif health_score >= 60:
            return "Moderate Risk"
        elif health_score >= 40:
            return "High Risk"
        else:
            return "Critical Risk"

    def _generate_recommendations(self, health_score: float, cash_cushion: float) -> List[str]:
        """Generate recommendations based on account health"""
        recommendations = []

        if health_score < 40:
            recommendations.append("Consider reducing position sizes")
            recommendations.append("Review and tighten stop-loss levels")

        if cash_cushion < 10:
            recommendations.append("Increase cash reserves for opportunities")

        if cash_cushion > 50:
            recommendations.append("Consider deploying more capital")

        if health_score >= 80:
            recommendations.append("Account health excellent - maintain strategy")

        return recommendations

    def _generate_forecast(self, balance_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate simple statistical forecast"""
        if len(balance_df) < 30:
            return {'note': 'Insufficient data for forecast (need 30+ days)'}

        # Calculate growth rate
        daily_returns = balance_df['daily_return'].dropna()
        avg_daily_return = daily_returns.mean() / 100
        volatility = daily_returns.std() / 100

        current_balance = balance_df.iloc[-1]['total_balance']

        # Simple Monte Carlo projection
        projections = {}
        for days in [30, 90, 180, 365]:
            # Expected value
            expected = current_balance * (1 + avg_daily_return) ** days

            # Confidence intervals (simplified)
            std_dev = current_balance * volatility * np.sqrt(days)
            lower_bound = expected - 1.96 * std_dev  # 95% confidence
            upper_bound = expected + 1.96 * std_dev

            projections[f'{days}_days'] = {
                'expected': expected,
                'lower_95': lower_bound,
                'upper_95': upper_bound
            }

        return {
            'projections': projections,
            'assumptions': {
                'avg_daily_return': avg_daily_return * 100,
                'daily_volatility': volatility * 100,
                'method': 'Simple statistical projection'
            }
        }

    def _empty_report(self) -> Dict[str, Any]:
        """Return empty report structure"""
        return {
            'summary': {
                'initial_balance': self.initial_balance,
                'current_balance': self.initial_balance,
                'total_return': 0,
                'total_return_pct': 0
            },
            'growth_metrics': {},
            'volatility_metrics': {},
            'drawdown_analysis': {},
            'cash_utilization': {},
            'period_analysis': {},
            'milestone_analysis': {},
            'health_indicators': {},
            'forecast': {},
            'report_generated': datetime.now().isoformat(),
            'status': 'No data available'
        }

    def generate_text_report(self) -> str:
        """
        Generate a formatted text report from analysis results

        Returns:
            Formatted text report string
        """
        if not self.analysis_results:
            return "No analysis results available. Please run analyze_balance_history() first."

        report_lines = [
            "=" * 80,
            "                  BALANCE ANALYSIS REPORT",
            "=" * 80,
            f"Generated: {self.analysis_results.get('report_generated', 'N/A')}",
            "",
            "-" * 40,
            "BALANCE SUMMARY",
            "-" * 40
        ]

        summary = self.analysis_results.get('summary', {})
        report_lines.extend([
            f"Initial Balance: ${summary.get('initial_balance', 0):,.2f}",
            f"Current Balance: ${summary.get('current_balance', 0):,.2f}",
            f"Peak Balance: ${summary.get('peak_balance', 0):,.2f}",
            f"Total Return: ${summary.get('total_return', 0):,.2f}",
            f"Total Return %: {summary.get('total_return_pct', 0):.2f}%",
            "",
            "-" * 40,
            "GROWTH METRICS",
            "-" * 40
        ])

        growth = self.analysis_results.get('growth_metrics', {})
        report_lines.extend([
            f"CAGR: {growth.get('cagr', 0):.2f}%",
            f"Sharpe Ratio: {growth.get('sharpe_ratio', 0):.2f}",
            f"Win Rate (Days): {growth.get('win_rate_days', 0):.2f}%",
            "",
            "-" * 40,
            "RISK METRICS",
            "-" * 40
        ])

        drawdown = self.analysis_results.get('drawdown_analysis', {})
        report_lines.extend([
            f"Max Drawdown: ${drawdown.get('max_drawdown', 0):,.2f}",
            f"Max Drawdown %: {drawdown.get('max_drawdown_pct', 0):.2f}%",
            "",
            "-" * 40,
            "HEALTH INDICATORS",
            "-" * 40
        ])

        health = self.analysis_results.get('health_indicators', {})
        report_lines.extend([
            f"Health Score: {health.get('health_score', 0):.0f}/100",
            f"Risk Level: {health.get('risk_level', 'N/A')}",
            f"Cash Cushion: {health.get('cash_cushion_pct', 0):.2f}%",
            "",
            "=" * 80
        ])

        return "\n".join(report_lines)