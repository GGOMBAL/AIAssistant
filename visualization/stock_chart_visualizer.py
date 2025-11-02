"""
Stock Chart Visualizer
주식 차트 시각화 모듈 - 가격 차트와 매수/매도 시그널 표시

Features:
- 캔들스틱 차트
- 매수/매도 시그널 오버레이
- 기술지표 (SMA, Volume)
- 인터랙티브 차트 (Plotly)
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class StockChartVisualizer:
    """
    주식 차트 시각화 클래스

    캔들스틱 차트에 매수/매도 시그널과 기술지표를 표시합니다.
    """

    def __init__(self):
        """초기화"""
        self.default_colors = {
            'buy': '#00FF00',  # Green
            'sell': '#FF0000',  # Red
            'up': '#26a69a',    # Teal
            'down': '#ef5350',  # Light Red
            'sma20': '#FFA500', # Orange
            'sma50': '#0000FF', # Blue
            'sma200': '#800080' # Purple
        }

    def create_candlestick_chart(
        self,
        df: pd.DataFrame,
        ticker: str,
        buy_signals: Optional[pd.DataFrame] = None,
        sell_signals: Optional[pd.DataFrame] = None,
        show_volume: bool = True,
        show_sma: bool = True,
        interactive: bool = True
    ) -> go.Figure:
        """
        캔들스틱 차트 생성 (Plotly Interactive)

        Args:
            df: 주가 데이터 (columns: Date, Open, High, Low, Close, Volume)
            ticker: 종목 코드
            buy_signals: 매수 시그널 데이터
            sell_signals: 매도 시그널 데이터
            show_volume: 거래량 표시 여부
            show_sma: 이동평균선 표시 여부
            interactive: 인터랙티브 차트 여부

        Returns:
            Plotly Figure 객체
        """
        # 데이터 검증
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Required columns missing. Need: {required_cols}")
            return None

        # 날짜 인덱스 확인
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # 서브플롯 생성
        rows = 2 if show_volume else 1
        row_heights = [0.7, 0.3] if show_volume else [1]

        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=row_heights,
            subplot_titles=(f'{ticker} Stock Price', 'Volume') if show_volume else (f'{ticker} Stock Price',)
        )

        # 캔들스틱 차트
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color=self.default_colors['up'],
                decreasing_line_color=self.default_colors['down']
            ),
            row=1, col=1
        )

        # 이동평균선 추가
        if show_sma:
            if 'SMA20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['SMA20'],
                        name='SMA20',
                        line=dict(color=self.default_colors['sma20'], width=1)
                    ),
                    row=1, col=1
                )

            if 'SMA50' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['SMA50'],
                        name='SMA50',
                        line=dict(color=self.default_colors['sma50'], width=1)
                    ),
                    row=1, col=1
                )

            if 'SMA200' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['SMA200'],
                        name='SMA200',
                        line=dict(color=self.default_colors['sma200'], width=1.5)
                    ),
                    row=1, col=1
                )

        # 매수 시그널 추가
        if buy_signals is not None and not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['Price'] if 'Price' in buy_signals.columns else buy_signals['Close'],
                    mode='markers',
                    name='Buy Signal',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color=self.default_colors['buy'],
                        line=dict(color='black', width=1)
                    ),
                    text=buy_signals['Signal_Type'] if 'Signal_Type' in buy_signals.columns else 'Buy',
                    hovertemplate='Buy<br>Date: %{x}<br>Price: %{y:.2f}<br>%{text}<extra></extra>'
                ),
                row=1, col=1
            )

        # 매도 시그널 추가
        if sell_signals is not None and not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_signals['Price'] if 'Price' in sell_signals.columns else sell_signals['Close'],
                    mode='markers',
                    name='Sell Signal',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color=self.default_colors['sell'],
                        line=dict(color='black', width=1)
                    ),
                    text=sell_signals['Signal_Type'] if 'Signal_Type' in sell_signals.columns else 'Sell',
                    hovertemplate='Sell<br>Date: %{x}<br>Price: %{y:.2f}<br>%{text}<extra></extra>'
                ),
                row=1, col=1
            )

        # 거래량 차트
        if show_volume:
            colors = ['green' if row['Close'] >= row['Open'] else 'red'
                     for idx, row in df.iterrows()]

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False
                ),
                row=2, col=1
            )

        # 레이아웃 설정
        fig.update_layout(
            title=f'{ticker} - Stock Price with Buy/Sell Signals',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            height=700 if show_volume else 500,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Y축 설정
        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)

        # X축 설정
        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor="lightgray",
                x=0.01,
                y=1.05
            )
        )

        return fig

    def create_signal_distribution_chart(
        self,
        buy_signals: pd.DataFrame,
        sell_signals: pd.DataFrame,
        ticker: str
    ) -> go.Figure:
        """
        매수/매도 시그널 분포 차트

        Args:
            buy_signals: 매수 시그널 데이터
            sell_signals: 매도 시그널 데이터
            ticker: 종목 코드

        Returns:
            Plotly Figure 객체
        """
        # 월별 시그널 집계
        buy_monthly = buy_signals.groupby(pd.Grouper(freq='M')).size()
        sell_monthly = sell_signals.groupby(pd.Grouper(freq='M')).size()

        fig = go.Figure()

        # 매수 시그널
        fig.add_trace(go.Bar(
            x=buy_monthly.index,
            y=buy_monthly.values,
            name='Buy Signals',
            marker_color=self.default_colors['buy']
        ))

        # 매도 시그널
        fig.add_trace(go.Bar(
            x=sell_monthly.index,
            y=sell_monthly.values,
            name='Sell Signals',
            marker_color=self.default_colors['sell']
        ))

        fig.update_layout(
            title=f'{ticker} - Monthly Signal Distribution',
            xaxis_title='Month',
            yaxis_title='Number of Signals',
            barmode='group',
            template='plotly_white',
            height=400
        )

        return fig

    def save_chart(self, fig: go.Figure, filename: str, format: str = 'html'):
        """
        차트 저장

        Args:
            fig: Plotly Figure 객체
            filename: 저장할 파일명
            format: 파일 형식 ('html', 'png', 'pdf')
        """
        if format == 'html':
            fig.write_html(filename)
            logger.info(f"Chart saved as HTML: {filename}")
        elif format == 'png':
            fig.write_image(filename)
            logger.info(f"Chart saved as PNG: {filename}")
        elif format == 'pdf':
            fig.write_image(filename)
            logger.info(f"Chart saved as PDF: {filename}")
        else:
            logger.error(f"Unsupported format: {format}")

    def create_matplotlib_chart(
        self,
        df: pd.DataFrame,
        ticker: str,
        buy_signals: Optional[pd.DataFrame] = None,
        sell_signals: Optional[pd.DataFrame] = None
    ) -> plt.Figure:
        """
        Matplotlib을 사용한 정적 차트 생성

        Args:
            df: 주가 데이터
            ticker: 종목 코드
            buy_signals: 매수 시그널
            sell_signals: 매도 시그널

        Returns:
            Matplotlib Figure 객체
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                       gridspec_kw={'height_ratios': [3, 1]})

        # 가격 차트
        ax1.plot(df.index, df['Close'], label='Close', color='black', linewidth=1)

        # 이동평균선
        if 'SMA20' in df.columns:
            ax1.plot(df.index, df['SMA20'], label='SMA20',
                    color=self.default_colors['sma20'], linewidth=0.8)
        if 'SMA50' in df.columns:
            ax1.plot(df.index, df['SMA50'], label='SMA50',
                    color=self.default_colors['sma50'], linewidth=0.8)
        if 'SMA200' in df.columns:
            ax1.plot(df.index, df['SMA200'], label='SMA200',
                    color=self.default_colors['sma200'], linewidth=1)

        # 매수/매도 시그널
        if buy_signals is not None and not buy_signals.empty:
            ax1.scatter(buy_signals.index,
                       buy_signals['Price'] if 'Price' in buy_signals.columns else buy_signals['Close'],
                       color=self.default_colors['buy'], marker='^', s=100,
                       label='Buy', zorder=5)

        if sell_signals is not None and not sell_signals.empty:
            ax1.scatter(sell_signals.index,
                       sell_signals['Price'] if 'Price' in sell_signals.columns else sell_signals['Close'],
                       color=self.default_colors['sell'], marker='v', s=100,
                       label='Sell', zorder=5)

        ax1.set_title(f'{ticker} - Stock Price with Signals')
        ax1.set_ylabel('Price')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # 거래량 차트
        colors = ['g' if row['Close'] >= row['Open'] else 'r'
                 for idx, row in df.iterrows()]
        ax2.bar(df.index, df['Volume'], color=colors, alpha=0.5)
        ax2.set_ylabel('Volume')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)

        # X축 날짜 형식
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))

        plt.tight_layout()
        return fig