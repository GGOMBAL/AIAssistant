"""
Report Agent
보고서 및 시각화 관리 에이전트

Report Agent는 Reporting Layer의 모든 기능을 관리합니다:
- 백테스트 결과 시각화 (옵션 1)
- 개별 종목 시그널 차트 (옵션 2)
- 오토 트레이딩 모니터링 (옵션 3)
- 시그널 타임라인 시각화 (옵션 4)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Visualization imports
from visualization.trading_visualizer_integration import TradingVisualizerIntegration
from visualization.stock_chart_visualizer import StockChartVisualizer
from visualization.backtest_visualizer import BacktestVisualizer

logger = logging.getLogger(__name__)

class ReportAgent:
    """
    Report Agent - Reporting Layer 관리자

    모든 시각화 및 보고서 생성을 담당합니다.
    """

    def __init__(self, config: Optional[Dict] = None, db_address: Optional[str] = None):
        """
        초기화

        Args:
            config: Configuration dictionary (from myStockInfo.yaml)
            db_address: MongoDB 서버 주소 (예: "MONGODB_LOCAL", "MONGODB_NAS")
        """
        # db_address 파라미터 우선 사용
        if db_address is not None:
            _db_address = db_address
            self.config = config or {}
        # config가 문자열이면 db_address로 처리 (하위 호환성)
        elif isinstance(config, str):
            _db_address = config
            self.config = {}
        # config가 딕셔너리면 config에서 추출
        elif isinstance(config, dict):
            _db_address = config.get('db_address', "MONGODB_LOCAL")
            self.config = config
        # 기본값
        else:
            _db_address = "MONGODB_LOCAL"
            self.config = {}

        self.visualizer = TradingVisualizerIntegration(db_address=_db_address)
        self.stock_chart = StockChartVisualizer()
        self.backtest_viz = BacktestVisualizer()
        self.output_dir = Path("project/reporting/outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Report Agent] Initialized with MongoDB: {_db_address}")

    def generate_backtest_report(
        self,
        backtest_results: Any,
        pipeline_results: Optional[Dict] = None,
        benchmark_data: Optional[pd.DataFrame] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        백테스트 결과 보고서 생성 (Option 1 연동)

        Args:
            backtest_results: 백테스트 실행 결과
            pipeline_results: 파이프라인 실행 결과 (optional)
            benchmark_data: 벤치마크 데이터 (optional)
            save: 파일 저장 여부

        Returns:
            Dictionary with 'status', 'charts', and 'metrics'
        """
        try:
            logger.info("[Report Agent] Generating backtest report...")

            # 백테스트 결과 포맷 변환
            formatted_results = self._format_backtest_results(backtest_results)

            # 1. 성과 대시보드 생성
            dashboard = self.backtest_viz.create_performance_dashboard(formatted_results)

            charts_saved = {}
            if save and dashboard:
                dashboard_file = self.output_dir / f"backtest_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                dashboard.write_html(str(dashboard_file))
                charts_saved['dashboard'] = str(dashboard_file)
                logger.info(f"[Report Agent] Dashboard saved: {dashboard_file}")

            # 2. 누적 수익률 차트
            if 'returns' in formatted_results:
                cum_returns = self.backtest_viz.create_cumulative_returns_chart(
                    formatted_results['returns'],
                    title="Backtest Cumulative Returns"
                )

                if save and cum_returns:
                    cum_file = self.output_dir / f"cumulative_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    cum_returns.write_html(str(cum_file))
                    charts_saved['cumulative_returns'] = str(cum_file)

            # 3. 드로우다운 분석
            if 'portfolio_value' in formatted_results:
                drawdown = self.backtest_viz.create_drawdown_chart(
                    formatted_results['portfolio_value'],
                    title="Portfolio Drawdown Analysis"
                )

                if save and drawdown:
                    dd_file = self.output_dir / f"drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    drawdown.write_html(str(dd_file))
                    charts_saved['drawdown'] = str(dd_file)

            # 4. 거래 분석
            if 'trades_df' in formatted_results:
                trade_analysis = self.backtest_viz.create_trade_analysis_chart(
                    formatted_results['trades_df'],
                    title="Trade Analysis"
                )

                if save and trade_analysis:
                    trade_file = self.output_dir / f"trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    trade_analysis.write_html(str(trade_file))
                    charts_saved['trade_analysis'] = str(trade_file)

            # 5. 성과 지표 테이블
            if 'metrics' in formatted_results:
                metrics_table = self.backtest_viz.create_performance_metrics_table(
                    formatted_results['metrics'],
                    title="Backtest Performance Metrics"
                )

                if save and metrics_table:
                    metrics_file = self.output_dir / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    metrics_table.write_html(str(metrics_file))
                    charts_saved['metrics'] = str(metrics_file)

            logger.info(f"[Report Agent] Backtest report complete - {len(charts_saved)} files generated")

            # Return result dictionary
            return {
                'status': 'success',
                'charts': charts_saved,
                'metrics': formatted_results.get('metrics', {})
            }

        except Exception as e:
            logger.error(f"[Report Agent] Error generating backtest report: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'charts': {},
                'metrics': {},
                'error': str(e)
            }

    def generate_stock_signal_chart(
        self,
        symbol: Optional[str] = None,
        ticker: Optional[str] = None,
        signal_data: Optional[Dict] = None,
        df_data: Optional[Dict] = None,
        stock_data: Optional[pd.DataFrame] = None,
        buy_signals: Optional[pd.DataFrame] = None,
        sell_signals: Optional[pd.DataFrame] = None,
        load_from_db: bool = True,
        save: bool = True
    ) -> Optional[str]:
        """
        개별 종목 시그널 차트 생성 (Option 2 연동)

        Args:
            symbol: 종목 코드 (ticker와 동일, 호환성)
            ticker: 종목 코드 (symbol과 동일, 호환성)
            signal_data: SignalGenerationService 출력
            df_data: DataFrameGenerator 출력
            stock_data: 주가 데이터 (df_data 대신 사용 가능)
            buy_signals: 매수 신호 (signal_data 대신 사용 가능)
            sell_signals: 매도 신호 (signal_data 대신 사용 가능)
            load_from_db: MongoDB에서 데이터 로드 여부
            save: 파일 저장 여부

        Returns:
            차트 생성 결과
        """
        try:
            # symbol과 ticker 중 하나라도 있으면 사용
            _symbol = symbol or ticker
            if not _symbol:
                logger.error("[Report Agent] No symbol/ticker provided")
                return None

            logger.info(f"[Report Agent] Generating signal chart for {_symbol}...")

            # Use simple plotly implementation directly
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Extract stock_data from df_data if available
            if stock_data is None and df_data:
                # df_data는 {symbol: {'D': df, 'W': df, ...}} 형태
                symbol_data = df_data.get(_symbol, {})
                stock_data = symbol_data.get('D')  # Daily data 사용

            # If no data provided, try to use stock_chart_visualizer
            if stock_data is None:
                try:
                    # Try using the visualization module
                    result = self.stock_chart.create_candlestick_chart(
                        df=pd.DataFrame(),  # Empty df will trigger MongoDB load
                        ticker=_symbol,
                        buy_signals=buy_signals,
                        sell_signals=sell_signals,
                        show_volume=True,
                        show_sma=True
                    )
                    if result:
                        chart_path = self.output_dir / f"{_symbol}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        result.write_html(str(chart_path))
                        logger.info(f"[Report Agent] Stock chart saved: {chart_path}")
                        return str(chart_path)
                except Exception as viz_error:
                    logger.warning(f"Visualization module failed: {viz_error}")
                    return None
            else:
                # Create chart directly with provided data
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f'{_symbol} Price', 'Volume')
                )

                # Prepare data
                if not isinstance(stock_data.index, pd.DatetimeIndex):
                    if 'Date' in stock_data.columns:
                        stock_data = stock_data.set_index('Date')
                    stock_data.index = pd.to_datetime(stock_data.index)

                # Find column names
                open_col = next((col for col in ['open', 'Dopen', 'Open'] if col in stock_data.columns), None)
                high_col = next((col for col in ['high', 'Dhigh', 'High'] if col in stock_data.columns), None)
                low_col = next((col for col in ['low', 'Dlow', 'Low'] if col in stock_data.columns), None)
                close_col = next((col for col in ['close', 'Dclose', 'Close', 'ad_close'] if col in stock_data.columns), None)
                volume_col = next((col for col in ['volume', 'Dvolume', 'Volume'] if col in stock_data.columns), None)

                # Add candlestick if we have the data
                if all([open_col, high_col, low_col, close_col]):
                    fig.add_trace(
                        go.Candlestick(
                            x=stock_data.index,
                            open=stock_data[open_col],
                            high=stock_data[high_col],
                            low=stock_data[low_col],
                            close=stock_data[close_col],
                            name='Price'
                        ),
                        row=1, col=1
                    )

                    # Add volume if available
                    if volume_col:
                        colors = ['green' if stock_data[close_col].iloc[i] >= stock_data[open_col].iloc[i] else 'red'
                                 for i in range(len(stock_data))]
                        fig.add_trace(
                            go.Bar(x=stock_data.index, y=stock_data[volume_col],
                                  name='Volume', marker_color=colors, showlegend=False),
                            row=2, col=1
                        )

                    # Add buy signals
                    if buy_signals is not None and not buy_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=buy_signals.index if isinstance(buy_signals.index, pd.DatetimeIndex) else buy_signals.get('Date', []),
                                y=buy_signals.get('Price', [stock_data[close_col].mean()] * len(buy_signals)),
                                mode='markers',
                                name='Buy Signal',
                                marker=dict(symbol='triangle-up', size=12, color='green')
                            ),
                            row=1, col=1
                        )

                    # Add sell signals
                    if sell_signals is not None and not sell_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=sell_signals.index if isinstance(sell_signals.index, pd.DatetimeIndex) else sell_signals.get('Date', []),
                                y=sell_signals.get('Price', [stock_data[close_col].mean()] * len(sell_signals)),
                                mode='markers',
                                name='Sell Signal',
                                marker=dict(symbol='triangle-down', size=12, color='red')
                            ),
                            row=1, col=1
                        )

                    # Update layout
                    fig.update_layout(
                        title=f'{_symbol} - Stock Chart with Signals',
                        height=800,
                        showlegend=True,
                        xaxis_rangeslider_visible=False
                    )
                    fig.update_xaxes(title_text="Date", row=2, col=1)
                    fig.update_yaxes(title_text="Price", row=1, col=1)
                    fig.update_yaxes(title_text="Volume", row=2, col=1)

                    # Save chart
                    if save:
                        chart_path = self.output_dir / f"{_symbol}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                        fig.write_html(str(chart_path))
                        logger.info(f"[Report Agent] Stock chart saved: {chart_path}")
                        return str(chart_path)
                else:
                    logger.warning(f"Missing required columns for {_symbol}")
                    return None

        except Exception as e:
            logger.error(f"[Report Agent] Error generating stock signal chart: {e}")
            return None

    def generate_trading_monitor_dashboard(
        self,
        buy_signals: Optional[Dict] = None,
        portfolio_status: Optional[Dict] = None,
        positions: Optional[List[Dict]] = None,
        pending_orders: Optional[List[str]] = None,
        market_status: Optional[Dict[str, Any]] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        오토 트레이딩 모니터링 대시보드 생성 (Option 3 연동)

        Args:
            buy_signals: 매수 신호 종목 딕셔너리 (optional)
            portfolio_status: 포트폴리오 상태 정보 (optional)
            positions: 현재 포지션 리스트 (optional)
            pending_orders: 대기중인 주문 리스트 (optional)
            market_status: 시장 상태 (optional)
            save: 파일 저장 여부

        Returns:
            Dictionary with 'status', 'charts', and 'info'
        """
        try:
            logger.info("[Report Agent] Generating trading monitor dashboard...")

            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Initialize default values
            buy_signals = buy_signals or {}
            portfolio_status = portfolio_status or {}
            positions = positions or []
            pending_orders = pending_orders or []
            market_status = market_status or {'status': 'UNKNOWN', 'time': datetime.now().strftime('%Y-%m-%d %H:%M')}

            charts_saved = {}

            # 1. Buy Signals Table
            if buy_signals:
                # Create buy signals visualization
                symbols = list(buy_signals.keys())
                signal_strengths = [buy_signals[s].get('signal_strength', 0) for s in symbols]

                fig_signals = go.Figure(data=[
                    go.Bar(
                        x=symbols,
                        y=signal_strengths,
                        text=[f"{s:.2f}" for s in signal_strengths],
                        textposition='auto',
                        marker_color='lightblue'
                    )
                ])

                fig_signals.update_layout(
                    title=f"Buy Signals - {len(symbols)} candidates",
                    xaxis_title="Symbol",
                    yaxis_title="Signal Strength",
                    height=400
                )

                if save:
                    signals_file = self.output_dir / f"buy_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    fig_signals.write_html(str(signals_file))
                    charts_saved['buy_signals'] = str(signals_file)
                    logger.info(f"[Report Agent] Buy signals chart saved: {signals_file}")

            # 2. Portfolio Status
            if portfolio_status:
                fig_portfolio = go.Figure()

                fig_portfolio.add_trace(go.Indicator(
                    mode="number",
                    value=portfolio_status.get('cash_ratio', 0),
                    title={'text': f"Cash Ratio (%) - {portfolio_status.get('account_type', 'UNKNOWN')}"},
                    number={'suffix': '%'},
                    domain={'x': [0, 0.5], 'y': [0, 1]}
                ))

                fig_portfolio.add_trace(go.Indicator(
                    mode="number",
                    value=portfolio_status.get('positions', 0),
                    title={'text': "Active Positions"},
                    domain={'x': [0.5, 1], 'y': [0, 1]}
                ))

                fig_portfolio.update_layout(
                    title="Portfolio Status",
                    height=300
                )

                if save:
                    portfolio_file = self.output_dir / f"portfolio_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    fig_portfolio.write_html(str(portfolio_file))
                    charts_saved['portfolio_status'] = str(portfolio_file)
                    logger.info(f"[Report Agent] Portfolio status saved: {portfolio_file}")

            # 3. Market Status (if positions exist)
            if positions:
                # Create positions dashboard
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        'Current Positions P&L',
                        'Position Distribution',
                        'Market Status',
                        'Position Details'
                    ),
                    specs=[
                        [{"type": "bar"}, {"type": "pie"}],
                        [{"type": "indicator"}, {"type": "table"}]
                    ]
                )

                symbols_pos = [p.get('symbol', '') for p in positions]
                pnl_values = [p.get('pnl', 0) for p in positions]
                colors = ['green' if pnl > 0 else 'red' for pnl in pnl_values]

                fig.add_trace(
                    go.Bar(x=symbols_pos, y=pnl_values, name='P&L',
                          marker_color=colors),
                    row=1, col=1
                )

                position_values = [abs(p.get('current_price', 0) * p.get('quantity', 0)) for p in positions]

                fig.add_trace(
                    go.Pie(labels=symbols_pos,
                          values=position_values,
                          hole=0.3),
                    row=1, col=2
                )

                fig.add_trace(
                    go.Indicator(
                        mode="number",
                        value=len(positions),
                        title={'text': f"Active Positions - {market_status.get('status', 'CLOSED')}"},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ),
                    row=2, col=1
                )

                table_data = []
                table_data.append(['Market', market_status.get('status', 'CLOSED')])
                table_data.append(['Time', market_status.get('time', 'N/A')])
                table_data.append(['Positions', str(len(positions))])

                fig.add_trace(
                    go.Table(
                        header=dict(
                            values=['Item', 'Value'],
                            fill_color='lightgray',
                            align='left'
                        ),
                        cells=dict(
                            values=list(zip(*table_data)) if table_data else [[], []],
                            fill_color='white',
                            align='left'
                        )
                    ),
                    row=2, col=2
                )

                fig.update_layout(
                    title_text=f"Trading Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    height=800,
                    showlegend=False
                )

                if save:
                    dashboard_file = self.output_dir / f"trading_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    fig.write_html(str(dashboard_file))
                    charts_saved['monitor_dashboard'] = str(dashboard_file)
                    logger.info(f"[Report Agent] Trading monitor saved: {dashboard_file}")

            logger.info(f"[Report Agent] Monitor dashboard complete - {len(charts_saved)} charts generated")

            return {
                'status': 'success',
                'charts': charts_saved,
                'info': {
                    'buy_signals_count': len(buy_signals),
                    'positions_count': len(positions),
                    'cash_ratio': portfolio_status.get('cash_ratio', 0) if portfolio_status else 0
                }
            }

        except Exception as e:
            logger.error(f"[Report Agent] Error generating trading monitor: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'charts': {},
                'info': {},
                'error': str(e)
            }

    def generate_signal_timeline_chart(
        self,
        ticker: str,
        signals_data: pd.DataFrame,
        save: bool = True
    ) -> Optional[str]:
        """
        시그널 타임라인 차트 생성 (Option 4 연동)

        Args:
            ticker: 종목 코드
            signals_data: 시그널 데이터 DataFrame
            save: 파일 저장 여부

        Returns:
            차트 파일 경로 또는 None
        """
        try:
            logger.info(f"[Report Agent] Generating signal timeline for {ticker}...")

            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            # Create simple timeline chart
            fig = go.Figure()

            # If signals_data is provided and not empty
            if signals_data is not None and not signals_data.empty:
                # Ensure Date column exists
                if 'Date' in signals_data.columns:
                    x_data = signals_data['Date']
                elif signals_data.index.name == 'Date':
                    x_data = signals_data.index
                else:
                    x_data = list(range(len(signals_data)))

                # Add scatter plot for signals
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=[1] * len(signals_data),
                        mode='markers',
                        marker=dict(size=10, color='green'),
                        name='Signals'
                    )
                )

            # Update layout
            fig.update_layout(
                title=f'{ticker} - Signal Timeline',
                xaxis_title='Date',
                yaxis_title='Signal',
                height=400,
                showlegend=True
            )

            # Save the chart
            if save:
                timeline_file = self.output_dir / f"{ticker}_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                fig.write_html(str(timeline_file))
                logger.info(f"[Report Agent] Signal timeline saved: {timeline_file}")
                return str(timeline_file)

            return None

        except Exception as e:
            logger.error(f"[Report Agent] Error generating signal timeline: {e}")
            return None

    def _format_backtest_results(self, backtest_results: Any) -> Dict:
        """백테스트 결과를 시각화 형식으로 변환"""
        formatted = {}

        # BacktestResults 객체에서 데이터 추출
        if hasattr(backtest_results, 'portfolio_values'):
            formatted['portfolio_value'] = pd.Series(backtest_results.portfolio_values)

        if hasattr(backtest_results, 'daily_returns'):
            formatted['returns'] = pd.Series(backtest_results.daily_returns)

        if hasattr(backtest_results, 'drawdowns'):
            formatted['drawdown'] = pd.Series(backtest_results.drawdowns)

        if hasattr(backtest_results, 'trade_history'):
            formatted['trades_df'] = pd.DataFrame(backtest_results.trade_history)

        if hasattr(backtest_results, 'performance_metrics'):
            formatted['metrics'] = backtest_results.performance_metrics

        # 거래 통계
        if hasattr(backtest_results, 'total_trades'):
            formatted['trades'] = {
                'total_trades': backtest_results.total_trades,
                'winning_trades': getattr(backtest_results, 'winning_trades', 0),
                'losing_trades': getattr(backtest_results, 'losing_trades', 0)
            }

        return formatted

    def _convert_signal_to_dataframe(self, signal_data: Dict, df_base: pd.DataFrame) -> pd.DataFrame:
        """시그널 데이터를 DataFrame으로 변환"""
        df = df_base.copy()

        # 시그널 정보 추가
        df['BuySig'] = 1 if 'BUY' in str(signal_data.get('final_signal', '')) else 0
        df['SellSig'] = 1 if 'SELL' in str(signal_data.get('final_signal', '')) else 0
        df['Signal_Type'] = signal_data.get('signal_type', '')
        df['Signal_Strength'] = signal_data.get('signal_strength', 0)

        return df

    def _create_signal_component_chart(self, symbol: str, signal_data: Dict):
        """시그널 컴포넌트 차트 생성"""
        import plotly.graph_objects as go

        components = signal_data.get('signal_components', {})
        if not components:
            return None

        fig = go.Figure(data=[
            go.Bar(
                x=list(components.keys()),
                y=list(components.values()),
                marker_color=['green' if v > 0 else 'red' for v in components.values()]
            )
        ])

        fig.update_layout(
            title=f'{symbol} - Signal Components',
            xaxis_title='Component',
            yaxis_title='Signal Value',
            height=400
        )

        return fig

    def _create_pipeline_summary(self, pipeline_results: Dict) -> str:
        """파이프라인 결과 요약 생성"""
        summary = []
        summary.append("=" * 60)
        summary.append("Pipeline Execution Summary")
        summary.append("=" * 60)
        summary.append(f"\nTotal Candidates: {pipeline_results.get('total_candidates', 0)}")

        # Stage별 결과
        for stage in ['E', 'F', 'W', 'RS', 'D']:
            stage_result = pipeline_results.get(f'stage_{stage}', {})
            if stage_result:
                summary.append(f"\nStage {stage}:")
                summary.append(f"  - Input: {stage_result.get('input_count', 0)}")
                summary.append(f"  - Passed: {stage_result.get('passed_count', 0)}")
                summary.append(f"  - Filtered: {stage_result.get('filtered_count', 0)}")

        # 최종 후보
        final_candidates = pipeline_results.get('final_candidates', [])
        if final_candidates:
            summary.append(f"\nFinal Candidates ({len(final_candidates)}):")
            for candidate in final_candidates[:10]:  # 상위 10개
                summary.append(f"  - {candidate}")

        return "\n".join(summary)

    def get_summary(self) -> Dict:
        """Report Agent 상태 요약"""
        return {
            'agent': 'ReportAgent',
            'status': 'active',
            'output_directory': str(self.output_dir),
            'services': [
                'Backtest Report Generation',
                'Stock Signal Charts',
                'Trading Monitor Dashboard',
                'Signal Timeline Visualization'
            ],
            'mongodb_connected': self.visualizer.test_mongodb_connection()
        }