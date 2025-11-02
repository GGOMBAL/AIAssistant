"""
Backtest Result Visualizer
백테스트 결과 시각화 모듈

Features:
- 포트폴리오 가치 곡선
- 수익률 차트
- 드로우다운 분석
- 성과 지표 대시보드
- 거래 분석
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class BacktestVisualizer:
    """
    백테스트 결과 시각화 클래스

    백테스트 성과를 다양한 차트로 시각화합니다.
    """

    def __init__(self):
        """초기화"""
        self.colors = {
            'portfolio': '#2E86AB',
            'benchmark': '#A23B72',
            'positive': '#00C853',
            'negative': '#D32F2F',
            'drawdown': '#FF6D00'
        }

    def create_performance_dashboard(
        self,
        backtest_results: Dict,
        benchmark_data: Optional[pd.DataFrame] = None
    ) -> go.Figure:
        """
        백테스트 성과 대시보드 생성

        Args:
            backtest_results: 백테스트 결과 딕셔너리
            benchmark_data: 벤치마크 데이터 (Optional)

        Returns:
            Plotly Figure 객체
        """
        # 서브플롯 생성 (2x2)
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Portfolio Value',
                'Monthly Returns',
                'Drawdown',
                'Trade Analysis'
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.12,
            specs=[[{"secondary_y": False}, {"type": "bar"}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )

        # 1. 포트폴리오 가치 곡선
        portfolio_value = backtest_results.get('portfolio_value', pd.Series())
        if not portfolio_value.empty:
            fig.add_trace(
                go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    name='Portfolio Value',
                    line=dict(color=self.colors['portfolio'], width=2)
                ),
                row=1, col=1
            )

            # 벤치마크 추가
            if benchmark_data is not None:
                fig.add_trace(
                    go.Scatter(
                        x=benchmark_data.index,
                        y=benchmark_data.values,
                        name='Benchmark',
                        line=dict(color=self.colors['benchmark'], width=1, dash='dash')
                    ),
                    row=1, col=1
                )

        # 2. 월별 수익률
        monthly_returns = backtest_results.get('monthly_returns', pd.Series())
        if not monthly_returns.empty:
            colors = [self.colors['positive'] if r >= 0 else self.colors['negative']
                     for r in monthly_returns.values]

            fig.add_trace(
                go.Bar(
                    x=monthly_returns.index,
                    y=monthly_returns.values * 100,  # 퍼센트로 변환
                    name='Monthly Returns',
                    marker_color=colors,
                    showlegend=False
                ),
                row=1, col=2
            )

        # 3. 드로우다운
        drawdown = backtest_results.get('drawdown', pd.Series())
        if not drawdown.empty:
            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,  # 퍼센트로 변환
                    name='Drawdown',
                    fill='tozeroy',
                    fillcolor='rgba(255, 109, 0, 0.3)',
                    line=dict(color=self.colors['drawdown'], width=1)
                ),
                row=2, col=1
            )

        # 4. 거래 분석 (파이 차트)
        trades = backtest_results.get('trades', {})
        if trades:
            labels = ['Winning Trades', 'Losing Trades']
            values = [trades.get('winning_trades', 0), trades.get('losing_trades', 0)]
            colors = [self.colors['positive'], self.colors['negative']]

            fig.add_trace(
                go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors),
                    hole=0.3,
                    name='Trade Analysis'
                ),
                row=2, col=2
            )

        # 레이아웃 설정
        fig.update_layout(
            title_text='Backtest Performance Dashboard',
            height=800,
            showlegend=True,
            template='plotly_white'
        )

        # 축 레이블 설정
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)

        fig.update_xaxes(title_text="Month", row=1, col=2)
        fig.update_yaxes(title_text="Return (%)", row=1, col=2)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        return fig

    def create_cumulative_returns_chart(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        title: str = "Cumulative Returns"
    ) -> go.Figure:
        """
        누적 수익률 차트 생성

        Args:
            returns: 일별 수익률
            benchmark_returns: 벤치마크 수익률
            title: 차트 제목

        Returns:
            Plotly Figure 객체
        """
        # 누적 수익률 계산
        cum_returns = (1 + returns).cumprod() - 1

        fig = go.Figure()

        # 포트폴리오 누적 수익률
        fig.add_trace(
            go.Scatter(
                x=cum_returns.index,
                y=cum_returns.values * 100,
                name='Portfolio',
                line=dict(color=self.colors['portfolio'], width=2),
                hovertemplate='Date: %{x}<br>Return: %{y:.2f}%<extra></extra>'
            )
        )

        # 벤치마크 누적 수익률
        if benchmark_returns is not None:
            cum_benchmark = (1 + benchmark_returns).cumprod() - 1
            fig.add_trace(
                go.Scatter(
                    x=cum_benchmark.index,
                    y=cum_benchmark.values * 100,
                    name='Benchmark',
                    line=dict(color=self.colors['benchmark'], width=2, dash='dash'),
                    hovertemplate='Date: %{x}<br>Return: %{y:.2f}%<extra></extra>'
                )
            )

        # 레이아웃
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Cumulative Return (%)',
            template='plotly_white',
            hovermode='x unified',
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # 0% 라인 추가
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)

        return fig

    def create_drawdown_chart(
        self,
        portfolio_value: pd.Series,
        title: str = "Portfolio Drawdown"
    ) -> go.Figure:
        """
        드로우다운 차트 생성

        Args:
            portfolio_value: 포트폴리오 가치
            title: 차트 제목

        Returns:
            Plotly Figure 객체
        """
        # 드로우다운 계산
        cummax = portfolio_value.cummax()
        drawdown = (portfolio_value - cummax) / cummax

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=('Portfolio Value', 'Drawdown %')
        )

        # 포트폴리오 가치
        fig.add_trace(
            go.Scatter(
                x=portfolio_value.index,
                y=portfolio_value.values,
                name='Portfolio Value',
                line=dict(color=self.colors['portfolio'], width=1.5)
            ),
            row=1, col=1
        )

        # 최고점
        fig.add_trace(
            go.Scatter(
                x=cummax.index,
                y=cummax.values,
                name='Peak Value',
                line=dict(color='gray', width=1, dash='dot')
            ),
            row=1, col=1
        )

        # 드로우다운
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown.values * 100,
                name='Drawdown',
                fill='tozeroy',
                fillcolor='rgba(255, 109, 0, 0.3)',
                line=dict(color=self.colors['drawdown'], width=1)
            ),
            row=2, col=1
        )

        # 레이아웃
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=True
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        return fig

    def create_trade_analysis_chart(
        self,
        trades_df: pd.DataFrame,
        title: str = "Trade Analysis"
    ) -> go.Figure:
        """
        거래 분석 차트

        Args:
            trades_df: 거래 데이터 (columns: Date, Symbol, Side, Price, Quantity, PnL)
            title: 차트 제목

        Returns:
            Plotly Figure 객체
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'P&L Distribution',
                'Win Rate by Month',
                'Trade Frequency',
                'Top Performers'
            ),
            specs=[[{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # 1. P&L 분포
        if 'PnL' in trades_df.columns:
            fig.add_trace(
                go.Histogram(
                    x=trades_df['PnL'],
                    name='P&L Distribution',
                    marker_color=self.colors['portfolio'],
                    nbinsx=30
                ),
                row=1, col=1
            )

        # 2. 월별 승률
        if 'Date' in trades_df.columns and 'PnL' in trades_df.columns:
            trades_df['Month'] = pd.to_datetime(trades_df['Date']).dt.to_period('M')
            monthly_stats = trades_df.groupby('Month').agg({
                'PnL': lambda x: (x > 0).sum() / len(x) * 100
            })

            fig.add_trace(
                go.Bar(
                    x=monthly_stats.index.astype(str),
                    y=monthly_stats['PnL'],
                    name='Win Rate',
                    marker_color=self.colors['positive']
                ),
                row=1, col=2
            )

        # 3. 거래 빈도
        if 'Symbol' in trades_df.columns:
            trade_freq = trades_df['Symbol'].value_counts().head(10)

            fig.add_trace(
                go.Bar(
                    x=trade_freq.index,
                    y=trade_freq.values,
                    name='Trade Frequency',
                    marker_color=self.colors['portfolio']
                ),
                row=2, col=1
            )

        # 4. 상위 수익 종목
        if 'Symbol' in trades_df.columns and 'PnL' in trades_df.columns:
            symbol_pnl = trades_df.groupby('Symbol')['PnL'].sum().sort_values(ascending=True).tail(10)

            fig.add_trace(
                go.Bar(
                    x=symbol_pnl.values,
                    y=symbol_pnl.index,
                    name='Top Performers',
                    orientation='h',
                    marker_color=[self.colors['positive'] if x > 0 else self.colors['negative']
                                 for x in symbol_pnl.values]
                ),
                row=2, col=2
            )

        # 레이아웃
        fig.update_layout(
            title=title,
            height=800,
            template='plotly_white',
            showlegend=False
        )

        # 축 레이블
        fig.update_xaxes(title_text="P&L ($)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)

        fig.update_xaxes(title_text="Month", row=1, col=2)
        fig.update_yaxes(title_text="Win Rate (%)", row=1, col=2)

        fig.update_xaxes(title_text="Symbol", row=2, col=1)
        fig.update_yaxes(title_text="Number of Trades", row=2, col=1)

        fig.update_xaxes(title_text="Total P&L ($)", row=2, col=2)
        fig.update_yaxes(title_text="Symbol", row=2, col=2)

        return fig

    def create_performance_metrics_table(
        self,
        metrics: Dict,
        title: str = "Performance Metrics"
    ) -> go.Figure:
        """
        성과 지표 테이블 생성

        Args:
            metrics: 성과 지표 딕셔너리
            title: 테이블 제목

        Returns:
            Plotly Figure 객체
        """
        # 지표 포맷팅
        formatted_metrics = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if 'rate' in key.lower() or 'ratio' in key.lower():
                    formatted_value = f"{value:.2%}"
                else:
                    formatted_value = f"{value:,.2f}"
            else:
                formatted_value = str(value)

            formatted_metrics.append([key.replace('_', ' ').title(), formatted_value])

        fig = go.Figure(data=[
            go.Table(
                header=dict(
                    values=['Metric', 'Value'],
                    fill_color='paleturquoise',
                    align='left',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=list(zip(*formatted_metrics)),
                    fill_color='lavender',
                    align='left',
                    font=dict(size=11)
                )
            )
        ])

        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white'
        )

        return fig

    def save_all_charts(
        self,
        backtest_results: Dict,
        output_dir: str = "backtest_results"
    ):
        """
        모든 차트를 파일로 저장

        Args:
            backtest_results: 백테스트 결과
            output_dir: 출력 디렉토리
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        # 대시보드 저장
        dashboard = self.create_performance_dashboard(backtest_results)
        dashboard.write_html(f"{output_dir}/dashboard.html")

        # 누적 수익률 저장
        if 'returns' in backtest_results:
            cum_returns = self.create_cumulative_returns_chart(backtest_results['returns'])
            cum_returns.write_html(f"{output_dir}/cumulative_returns.html")

        # 드로우다운 저장
        if 'portfolio_value' in backtest_results:
            drawdown = self.create_drawdown_chart(backtest_results['portfolio_value'])
            drawdown.write_html(f"{output_dir}/drawdown.html")

        logger.info(f"All charts saved to {output_dir}/")