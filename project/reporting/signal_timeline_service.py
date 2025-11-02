"""
Signal Timeline Service
Creates timeline visualizations for multi-stage signals
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path


class SignalTimelineService:
    """Service for creating signal timeline visualizations"""

    def __init__(self):
        self.output_dir = Path('project/reporting/outputs')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_timeline_chart(
        self,
        ticker: str,
        signals_data: pd.DataFrame,
        stages: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create signal timeline chart

        Args:
            ticker: Stock symbol
            signals_data: DataFrame with columns [Date, Stage, Signal]
            stages: Optional list of stages to display
            save_path: Optional path to save the chart

        Returns:
            Path to saved chart file
        """
        if stages is None:
            stages = ['W', 'D', 'RS', 'E', 'F']

        # Create figure
        fig = go.Figure()

        # Define colors for different signals
        signal_colors = {
            'BUY': 'green',
            'SELL': 'red',
            'HOLD': 'gray',
            'STRONG_BUY': 'darkgreen',
            'STRONG_SELL': 'darkred'
        }

        # Process signals data
        if not signals_data.empty and 'Date' in signals_data.columns:
            # Convert Date to datetime if needed
            if not isinstance(signals_data['Date'].iloc[0], pd.Timestamp):
                signals_data['Date'] = pd.to_datetime(signals_data['Date'])

            # Create timeline for each stage
            for i, stage in enumerate(stages):
                stage_data = signals_data[signals_data.get('Stage', '') == stage] if 'Stage' in signals_data.columns else pd.DataFrame()

                if not stage_data.empty:
                    # Add scatter trace for this stage
                    fig.add_trace(
                        go.Scatter(
                            x=stage_data['Date'],
                            y=[i] * len(stage_data),
                            mode='markers',
                            name=stage,
                            marker=dict(
                                size=10,
                                color=[signal_colors.get(s, 'blue') for s in stage_data.get('Signal', ['HOLD'] * len(stage_data))],
                                symbol='circle'
                            ),
                            text=stage_data.get('Signal', ''),
                            hovertemplate='%{text}<br>%{x}<extra></extra>'
                        )
                    )

        # Add stage labels
        fig.add_trace(
            go.Scatter(
                x=[signals_data['Date'].min() if not signals_data.empty else datetime.now()],
                y=list(range(len(stages))),
                mode='text',
                text=stages,
                textposition='middle left',
                showlegend=False,
                hoverinfo='skip'
            )
        )

        # Update layout
        fig.update_layout(
            title=f'{ticker} - Signal Timeline',
            xaxis_title='Date',
            yaxis=dict(
                title='Signal Stage',
                tickmode='array',
                tickvals=list(range(len(stages))),
                ticktext=stages,
                range=[-0.5, len(stages) - 0.5]
            ),
            height=400 + 50 * len(stages),
            template='plotly_white',
            showlegend=True
        )

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'{ticker}_timeline_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)

    def create_signal_heatmap(
        self,
        ticker: str,
        signals_matrix: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> str:
        """
        Create signal strength heatmap

        Args:
            ticker: Stock symbol
            signals_matrix: DataFrame with dates as index and stages as columns
            save_path: Optional path to save the chart

        Returns:
            Path to saved chart file
        """
        fig = go.Figure(data=go.Heatmap(
            z=signals_matrix.values,
            x=signals_matrix.columns,
            y=signals_matrix.index,
            colorscale='RdYlGn',
            zmid=0
        ))

        fig.update_layout(
            title=f'{ticker} - Signal Strength Heatmap',
            xaxis_title='Signal Stage',
            yaxis_title='Date',
            height=600,
            template='plotly_white'
        )

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'{ticker}_heatmap_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)

    def create_multi_ticker_timeline(
        self,
        tickers: List[str],
        all_signals: Dict[str, pd.DataFrame],
        save_path: Optional[str] = None
    ) -> str:
        """
        Create timeline for multiple tickers

        Args:
            tickers: List of stock symbols
            all_signals: Dictionary of {ticker: signals_dataframe}
            save_path: Optional path to save the chart

        Returns:
            Path to saved chart file
        """
        # Create subplots
        fig = make_subplots(
            rows=len(tickers),
            cols=1,
            subplot_titles=tickers,
            shared_xaxes=True,
            vertical_spacing=0.05
        )

        # Add timeline for each ticker
        for i, ticker in enumerate(tickers):
            if ticker in all_signals:
                signals_data = all_signals[ticker]

                if not signals_data.empty and 'Date' in signals_data.columns:
                    # Add scatter for buy signals
                    buy_signals = signals_data[signals_data.get('Signal', '') == 'BUY']
                    if not buy_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=buy_signals['Date'],
                                y=[1] * len(buy_signals),
                                mode='markers',
                                name=f'{ticker} Buy',
                                marker=dict(size=8, color='green', symbol='triangle-up'),
                                showlegend=(i == 0)
                            ),
                            row=i+1, col=1
                        )

                    # Add scatter for sell signals
                    sell_signals = signals_data[signals_data.get('Signal', '') == 'SELL']
                    if not sell_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=sell_signals['Date'],
                                y=[0] * len(sell_signals),
                                mode='markers',
                                name=f'{ticker} Sell',
                                marker=dict(size=8, color='red', symbol='triangle-down'),
                                showlegend=(i == 0)
                            ),
                            row=i+1, col=1
                        )

        # Update layout
        fig.update_layout(
            title='Multi-Ticker Signal Timeline',
            height=200 * len(tickers),
            template='plotly_white',
            showlegend=True
        )

        # Update axes
        fig.update_xaxes(title_text="Date", row=len(tickers), col=1)
        for i in range(len(tickers)):
            fig.update_yaxes(title_text="Signal", row=i+1, col=1, range=[-0.5, 1.5])

        # Save to file
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = self.output_dir / f'multi_timeline_{timestamp}.html'

        fig.write_html(str(save_path))
        return str(save_path)