"""
Trading Monitor Service
Real-time trading dashboard and monitoring
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path


class TradingMonitorService:
    """Service for creating real-time trading monitoring dashboards"""

    def __init__(self):
        self.output_dir = Path('project/reporting/outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_monitor_dashboard(
        self,
        positions: List[Dict[str, Any]],
        pending_orders: List[str],
        market_status: Dict[str, Any],
        account_summary: Optional[Dict[str, Any]] = None,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create trading monitor dashboard

        Args:
            positions: List of current position dictionaries
            pending_orders: List of pending order symbols
            market_status: Market status information
            account_summary: Optional account summary data
            save_path: Optional path to save the dashboard

        Returns:
            Path to saved dashboard file
        """
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Current Positions P&L',
                'Position Distribution',
                'Account Summary',
                'Market Status & Orders'
            ),
            specs=[
                [{'type': 'bar'}, {'type': 'pie'}],
                [{'type': 'indicator'}, {'type': 'table'}]
            ]
        )

        # 1. Positions P&L Bar Chart
        if positions:
            symbols = [p['symbol'] for p in positions]
            pnl_values = [p.get('pnl', 0) for p in positions]
            colors = ['green' if pnl > 0 else 'red' for pnl in pnl_values]

            fig.add_trace(
                go.Bar(
                    x=symbols,
                    y=pnl_values,
                    name='P&L',
                    marker_color=colors,
                    text=[f"${pnl:.2f}" for pnl in pnl_values],
                    textposition='outside'
                ),
                row=1, col=1
            )

            # 2. Position Distribution Pie Chart
            quantities = [abs(p.get('quantity', 0) * p.get('current_price', 0)) for p in positions]

            fig.add_trace(
                go.Pie(
                    labels=symbols,
                    values=quantities,
                    hole=0.3,
                    textinfo='label+percent'
                ),
                row=1, col=2
            )

            # Calculate total P&L
            total_pnl = sum(pnl_values)
            total_value = sum(quantities)
        else:
            total_pnl = 0
            total_value = 0

        # 3. Account Summary (Indicator)
        if account_summary:
            cash = account_summary.get('cash', 0)
            total_equity = account_summary.get('total_equity', total_value)
        else:
            cash = 100000  # Default
            total_equity = total_value + cash

        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=total_equity,
                title={'text': "Total Equity"},
                delta={'reference': 100000, 'relative': True},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=1
        )

        # 4. Market Status & Pending Orders Table
        table_data = []

        # Add market status
        table_data.append(['Market Status', market_status.get('status', 'CLOSED')])
        table_data.append(['Last Update', market_status.get('time', 'N/A')])
        table_data.append(['Total P&L', f"${total_pnl:.2f}"])
        table_data.append(['Pending Orders', str(len(pending_orders))])

        # Add pending orders (first 5)
        for i, symbol in enumerate(pending_orders[:5]):
            table_data.append([f'Order {i+1}', symbol])

        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Item', 'Value'],
                    fill_color='lightgray',
                    align='left'
                ),
                cells=dict(
                    values=list(zip(*table_data)),
                    fill_color='white',
                    align='left'
                )
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title=f"Trading Monitor Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            showlegend=False,
            height=800,
            template='plotly_white'
        )

        # Update axes
        fig.update_xaxes(title_text="Symbol", row=1, col=1)
        fig.update_yaxes(title_text="P&L ($)", row=1, col=1)

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'trading_monitor_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)

    def create_position_summary(
        self,
        positions: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Create position summary DataFrame

        Args:
            positions: List of position dictionaries

        Returns:
            DataFrame with position summary
        """
        if not positions:
            return pd.DataFrame()

        df = pd.DataFrame(positions)

        # Calculate additional metrics
        if 'current_price' in df.columns and 'avg_price' in df.columns:
            df['pnl_percent'] = ((df['current_price'] - df['avg_price']) / df['avg_price'] * 100)
            df['market_value'] = df['quantity'] * df['current_price']

        return df

    def create_order_summary(
        self,
        orders: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Create order summary DataFrame

        Args:
            orders: List of order dictionaries

        Returns:
            DataFrame with order summary
        """
        if not orders:
            return pd.DataFrame()

        return pd.DataFrame(orders)