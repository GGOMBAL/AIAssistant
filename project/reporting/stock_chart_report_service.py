"""
Stock Chart Report Service
Generates stock charts with buy/sell signals
"""

from typing import Optional, Dict, Any
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path


class StockChartReportService:
    """Service for creating stock charts with technical indicators and signals"""

    def __init__(self):
        self.output_dir = Path('project/reporting/outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_candlestick_chart(
        self,
        ticker: str,
        stock_data: pd.DataFrame,
        buy_signals: Optional[pd.DataFrame] = None,
        sell_signals: Optional[pd.DataFrame] = None,
        show_volume: bool = True,
        show_sma: bool = True,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create candlestick chart with signals

        Args:
            ticker: Stock symbol
            stock_data: DataFrame with OHLCV data
            buy_signals: DataFrame with buy signals
            sell_signals: DataFrame with sell signals
            show_volume: Whether to show volume subplot
            show_sma: Whether to show moving averages
            save_path: Optional path to save the chart

        Returns:
            Path to saved chart file
        """
        # Create figure with subplots
        rows = 2 if show_volume else 1
        row_heights = [0.7, 0.3] if show_volume else [1.0]

        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=(f'{ticker} Stock Chart', 'Volume') if show_volume else (f'{ticker} Stock Chart',)
        )

        # Prepare data
        if not isinstance(stock_data.index, pd.DatetimeIndex):
            if 'Date' in stock_data.columns:
                stock_data = stock_data.set_index('Date')
            stock_data.index = pd.to_datetime(stock_data.index)

        # Map column names
        open_col = next((col for col in ['Dopen', 'open', 'Open'] if col in stock_data.columns), None)
        high_col = next((col for col in ['Dhigh', 'high', 'High'] if col in stock_data.columns), None)
        low_col = next((col for col in ['Dlow', 'low', 'Low'] if col in stock_data.columns), None)
        close_col = next((col for col in ['Dclose', 'close', 'Close', 'ad_close'] if col in stock_data.columns), None)
        volume_col = next((col for col in ['Dvolume', 'volume', 'Volume'] if col in stock_data.columns), None)

        # Add candlestick
        if all([open_col, high_col, low_col, close_col]):
            fig.add_trace(
                go.Candlestick(
                    x=stock_data.index,
                    open=stock_data[open_col],
                    high=stock_data[high_col],
                    low=stock_data[low_col],
                    close=stock_data[close_col],
                    name='OHLC',
                    increasing=dict(line=dict(color='green')),
                    decreasing=dict(line=dict(color='red'))
                ),
                row=1, col=1
            )

            # Add SMAs if requested
            if show_sma:
                for sma_period in [20, 50, 200]:
                    sma_col = f'SMA{sma_period}'
                    if sma_col in stock_data.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=stock_data.index,
                                y=stock_data[sma_col],
                                mode='lines',
                                name=sma_col,
                                line=dict(width=1)
                            ),
                            row=1, col=1
                        )

            # Add buy signals
            if buy_signals is not None and not buy_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals.index if isinstance(buy_signals.index, pd.DatetimeIndex) else buy_signals['Date'],
                        y=buy_signals['Price'] if 'Price' in buy_signals.columns else stock_data[close_col].iloc[-1],
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(
                            symbol='triangle-up',
                            size=12,
                            color='green',
                            line=dict(color='darkgreen', width=2)
                        )
                    ),
                    row=1, col=1
                )

            # Add sell signals
            if sell_signals is not None and not sell_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals.index if isinstance(sell_signals.index, pd.DatetimeIndex) else sell_signals['Date'],
                        y=sell_signals['Price'] if 'Price' in sell_signals.columns else stock_data[close_col].iloc[-1],
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(
                            symbol='triangle-down',
                            size=12,
                            color='red',
                            line=dict(color='darkred', width=2)
                        )
                    ),
                    row=1, col=1
                )

            # Add volume subplot
            if show_volume and volume_col:
                colors = ['green' if stock_data[close_col].iloc[i] >= stock_data[open_col].iloc[i] else 'red'
                         for i in range(len(stock_data))]

                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=stock_data[volume_col],
                        name='Volume',
                        marker_color=colors,
                        showlegend=False
                    ),
                    row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=f'{ticker} - Stock Chart with Signals',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )

        # Update x-axis
        fig.update_xaxes(title_text="Date", row=rows, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'{ticker}_chart_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)

    def create_signal_distribution_chart(
        self,
        ticker: str,
        signals_data: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create signal distribution chart

        Args:
            ticker: Stock symbol
            signals_data: DataFrame with signal data
            save_path: Optional path to save the chart

        Returns:
            Path to saved chart file
        """
        # Create simple bar chart for signal distribution
        fig = go.Figure()

        # Count signals by type
        if 'Signal_Type' in signals_data.columns:
            signal_counts = signals_data['Signal_Type'].value_counts()

            fig.add_trace(
                go.Bar(
                    x=signal_counts.index,
                    y=signal_counts.values,
                    marker_color='lightblue'
                )
            )

        fig.update_layout(
            title=f'{ticker} - Signal Distribution',
            xaxis_title='Signal Type',
            yaxis_title='Count',
            template='plotly_white',
            height=400
        )

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'{ticker}_signal_dist_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)


def make_subplots(**kwargs):
    """Import make_subplots from plotly if available, otherwise return a mock"""
    try:
        from plotly.subplots import make_subplots as _make_subplots
        return _make_subplots(**kwargs)
    except ImportError:
        # Return a mock figure if plotly is not available
        return go.Figure()