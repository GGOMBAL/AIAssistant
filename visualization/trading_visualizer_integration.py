"""
Trading System Visualizer Integration
기존 트레이딩 시스템과 시각화 모듈 통합

Features:
- MongoDB 데이터 직접 연동
- 실제 백테스트 결과 시각화
- 실시간 시그널 차트 업데이트
- 포트폴리오 성과 추적
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from visualization.stock_chart_visualizer import StockChartVisualizer
from visualization.backtest_visualizer import BacktestVisualizer
from visualization.mongodb_data_loader import MongoDBDataLoader

logger = logging.getLogger(__name__)

class TradingVisualizerIntegration:
    """
    트레이딩 시스템 시각화 통합 클래스

    MongoDB에서 직접 데이터를 로드하여 시각화합니다.
    """

    def __init__(self, db_address: str = "MONGODB_LOCAL"):
        """
        초기화

        Args:
            db_address: MongoDB 주소 설정 키
        """
        self.stock_visualizer = StockChartVisualizer()
        self.backtest_visualizer = BacktestVisualizer()
        self.mongo_loader = MongoDBDataLoader(db_address=db_address)
        self.output_dir = Path("visualization_output")
        self.output_dir.mkdir(exist_ok=True)

        logger.info(f"Trading Visualizer Integration initialized with MongoDB: {db_address}")

    def visualize_stock_with_signals(
        self,
        ticker: str,
        df_daily: Optional[pd.DataFrame] = None,
        df_signals: Optional[pd.DataFrame] = None,
        market: str = "NASDAQ",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        load_from_db: bool = True,
        save: bool = True
    ) -> Dict:
        """
        개별 주식 차트와 매매 시그널 시각화

        Args:
            ticker: 종목 코드
            df_daily: 일간 데이터 (Optional, load_from_db=False일 때 필수)
            df_signals: 시그널 데이터 (Optional)
            market: 시장 (NASDAQ, NYSE, KOSPI, KOSDAQ, HSI)
            start_date: 시작일
            end_date: 종료일
            load_from_db: MongoDB에서 데이터 로드 여부
            save: 파일 저장 여부

        Returns:
            생성된 차트 정보
        """
        try:
            # MongoDB에서 데이터 로드
            if load_from_db:
                logger.info(f"Loading {ticker} data from MongoDB ({market})")
                df_daily = self.mongo_loader.load_stock_data(
                    ticker=ticker,
                    market=market,
                    data_type="daily",
                    start_date=start_date,
                    end_date=end_date
                )

                if df_daily.empty:
                    logger.warning(f"No data found for {ticker} in MongoDB")
                    return {'status': 'error', 'error': f'No data found for {ticker}'}

                # 시그널 데이터 로드 (있다면)
                if df_signals is None:
                    df_signals_raw = self.mongo_loader.load_trading_signals(
                        market=market,
                        date=end_date if end_date else datetime.now().strftime('%Y-%m-%d')
                    )

                    # 해당 종목 시그널만 필터링
                    if not df_signals_raw.empty and 'Ticker' in df_signals_raw.columns:
                        df_signals = df_signals_raw[df_signals_raw['Ticker'] == ticker]

            elif df_daily is None:
                return {'status': 'error', 'error': 'df_daily is required when load_from_db=False'}

            # 데이터 준비 (MongoDB 데이터는 이미 처리됨)
            if not load_from_db:
                df = self._prepare_stock_data(df_daily, start_date, end_date)
            else:
                df = df_daily

            # 시그널 분리
            buy_signals, sell_signals = self._extract_signals(df_signals)

            # 차트 생성
            fig = self.stock_visualizer.create_candlestick_chart(
                df=df,
                ticker=ticker,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                show_volume=True,
                show_sma=True,
                interactive=True
            )

            # 저장
            chart_info = {}
            if save and fig:
                filename = f"{self.output_dir}/{ticker}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                self.stock_visualizer.save_chart(fig, filename)
                chart_info['chart_file'] = filename
                logger.info(f"Stock chart saved: {filename}")

            # 시그널 분포 차트
            if buy_signals is not None and sell_signals is not None:
                signal_fig = self.stock_visualizer.create_signal_distribution_chart(
                    buy_signals, sell_signals, ticker
                )

                if save and signal_fig:
                    signal_filename = f"{self.output_dir}/{ticker}_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    self.stock_visualizer.save_chart(signal_fig, signal_filename)
                    chart_info['signal_chart'] = signal_filename

            return {
                'status': 'success',
                'ticker': ticker,
                'charts': chart_info,
                'buy_signals': len(buy_signals) if buy_signals is not None else 0,
                'sell_signals': len(sell_signals) if sell_signals is not None else 0
            }

        except Exception as e:
            logger.error(f"Error visualizing stock {ticker}: {e}")
            return {'status': 'error', 'error': str(e)}

    def visualize_backtest_results(
        self,
        backtest_output: Dict,
        benchmark: Optional[pd.Series] = None,
        save: bool = True
    ) -> Dict:
        """
        백테스트 결과 시각화

        Args:
            backtest_output: Service Layer 백테스트 출력
            benchmark: 벤치마크 데이터
            save: 파일 저장 여부

        Returns:
            생성된 차트 정보
        """
        try:
            # 백테스트 결과 포맷 변환
            formatted_results = self._format_backtest_results(backtest_output)

            # 성과 대시보드 생성
            dashboard = self.backtest_visualizer.create_performance_dashboard(
                formatted_results, benchmark
            )

            chart_info = {}
            if save and dashboard:
                dashboard_file = f"{self.output_dir}/backtest_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                dashboard.write_html(dashboard_file)
                chart_info['dashboard'] = dashboard_file
                logger.info(f"Backtest dashboard saved: {dashboard_file}")

            # 누적 수익률 차트
            if 'returns' in formatted_results:
                cum_returns_fig = self.backtest_visualizer.create_cumulative_returns_chart(
                    formatted_results['returns'],
                    benchmark,
                    title="Portfolio vs Benchmark"
                )

                if save and cum_returns_fig:
                    cum_file = f"{self.output_dir}/cumulative_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    cum_returns_fig.write_html(cum_file)
                    chart_info['cumulative_returns'] = cum_file

            # 드로우다운 차트
            if 'portfolio_value' in formatted_results:
                drawdown_fig = self.backtest_visualizer.create_drawdown_chart(
                    formatted_results['portfolio_value']
                )

                if save and drawdown_fig:
                    dd_file = f"{self.output_dir}/drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    drawdown_fig.write_html(dd_file)
                    chart_info['drawdown'] = dd_file

            # 거래 분석 차트
            if 'trades_df' in formatted_results:
                trade_fig = self.backtest_visualizer.create_trade_analysis_chart(
                    formatted_results['trades_df']
                )

                if save and trade_fig:
                    trade_file = f"{self.output_dir}/trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    trade_fig.write_html(trade_file)
                    chart_info['trade_analysis'] = trade_file

            # 성과 지표 테이블
            if 'metrics' in formatted_results:
                metrics_fig = self.backtest_visualizer.create_performance_metrics_table(
                    formatted_results['metrics']
                )

                if save and metrics_fig:
                    metrics_file = f"{self.output_dir}/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    metrics_fig.write_html(metrics_file)
                    chart_info['metrics'] = metrics_file

            return {
                'status': 'success',
                'charts': chart_info,
                'metrics': formatted_results.get('metrics', {})
            }

        except Exception as e:
            logger.error(f"Error visualizing backtest results: {e}")
            return {'status': 'error', 'error': str(e)}

    def visualize_portfolio_performance(
        self,
        portfolio_data: Dict,
        market: str = "US",
        save: bool = True
    ) -> Dict:
        """
        포트폴리오 성과 시각화

        Args:
            portfolio_data: 포트폴리오 데이터
            market: 시장 구분
            save: 파일 저장 여부

        Returns:
            생성된 차트 정보
        """
        try:
            # 포트폴리오 데이터 준비
            portfolio_df = self._prepare_portfolio_data(portfolio_data)

            # 차트 생성
            charts = {}

            # 1. 포트폴리오 구성 파이 차트
            if 'holdings' in portfolio_data:
                holdings_fig = self._create_holdings_chart(portfolio_data['holdings'])
                if save and holdings_fig:
                    holdings_file = f"{self.output_dir}/portfolio_holdings_{market}_{datetime.now().strftime('%Y%m%d')}.html"
                    holdings_fig.write_html(holdings_file)
                    charts['holdings'] = holdings_file

            # 2. 섹터별 분포
            if 'sector_allocation' in portfolio_data:
                sector_fig = self._create_sector_chart(portfolio_data['sector_allocation'])
                if save and sector_fig:
                    sector_file = f"{self.output_dir}/sector_allocation_{market}_{datetime.now().strftime('%Y%m%d')}.html"
                    sector_fig.write_html(sector_file)
                    charts['sectors'] = sector_file

            return {
                'status': 'success',
                'market': market,
                'charts': charts
            }

        except Exception as e:
            logger.error(f"Error visualizing portfolio: {e}")
            return {'status': 'error', 'error': str(e)}

    def _prepare_stock_data(
        self,
        df_daily: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Indicator Layer 출력을 시각화용 데이터로 변환

        Args:
            df_daily: 일간 데이터 (Indicator Layer 형식)
            start_date: 시작일
            end_date: 종료일

        Returns:
            시각화용 DataFrame
        """
        # 컬럼명 매핑
        column_mapping = {
            'Dopen': 'Open',
            'Dhigh': 'High',
            'Dlow': 'Low',
            'Dclose': 'Close',
            'Dvolume': 'Volume'
        }

        df = df_daily.copy()

        # 컬럼명 변경
        df.rename(columns=column_mapping, inplace=True)

        # 날짜 필터링
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        return df

    def _extract_signals(
        self,
        df_signals: Optional[pd.DataFrame]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Strategy Layer 시그널을 매수/매도로 분리

        Args:
            df_signals: 시그널 데이터

        Returns:
            buy_signals, sell_signals
        """
        if df_signals is None or df_signals.empty:
            return None, None

        buy_signals = None
        sell_signals = None

        if 'BuySig' in df_signals.columns:
            buy_mask = df_signals['BuySig'] == 1
            if buy_mask.any():
                buy_signals = df_signals[buy_mask][['close']].copy()
                buy_signals.columns = ['Price']
                if 'Type' in df_signals.columns:
                    buy_signals['Signal_Type'] = df_signals.loc[buy_mask, 'Type']

        if 'SellSig' in df_signals.columns:
            sell_mask = df_signals['SellSig'] == 1
            if sell_mask.any():
                sell_signals = df_signals[sell_mask][['close']].copy()
                sell_signals.columns = ['Price']
                if 'Type' in df_signals.columns:
                    sell_signals['Signal_Type'] = df_signals.loc[sell_mask, 'Type']

        return buy_signals, sell_signals

    def _format_backtest_results(self, backtest_output: Dict) -> Dict:
        """
        Service Layer 백테스트 출력을 시각화 형식으로 변환

        Args:
            backtest_output: 백테스트 출력

        Returns:
            포맷된 결과
        """
        formatted = {}

        # 포트폴리오 가치
        if 'portfolio_value' in backtest_output:
            formatted['portfolio_value'] = pd.Series(backtest_output['portfolio_value'])

        # 수익률
        if 'daily_returns' in backtest_output:
            formatted['returns'] = pd.Series(backtest_output['daily_returns'])

        # 월별 수익률
        if 'monthly_returns' in backtest_output:
            formatted['monthly_returns'] = pd.Series(backtest_output['monthly_returns'])

        # 드로우다운
        if 'drawdown' in backtest_output:
            formatted['drawdown'] = pd.Series(backtest_output['drawdown'])

        # 거래 데이터
        if 'trades' in backtest_output:
            formatted['trades'] = backtest_output['trades']
            if 'trade_history' in backtest_output:
                formatted['trades_df'] = pd.DataFrame(backtest_output['trade_history'])

        # 성과 지표
        if 'performance_metrics' in backtest_output:
            formatted['metrics'] = backtest_output['performance_metrics']

        return formatted

    def _prepare_portfolio_data(self, portfolio_data: Dict) -> pd.DataFrame:
        """포트폴리오 데이터 준비"""
        # 구현 필요
        return pd.DataFrame()

    def _create_holdings_chart(self, holdings: Dict):
        """포트폴리오 보유 종목 차트"""
        import plotly.graph_objects as go

        labels = list(holdings.keys())
        values = list(holdings.values())

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                textposition='inside',
                textinfo='label+percent'
            )
        ])

        fig.update_layout(
            title="Portfolio Holdings",
            height=500,
            template='plotly_white'
        )

        return fig

    def visualize_multiple_stocks_from_db(
        self,
        tickers: List[str],
        market: str = "NASDAQ",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save: bool = True
    ) -> Dict:
        """
        여러 종목을 MongoDB에서 로드하여 시각화

        Args:
            tickers: 종목 코드 리스트
            market: 시장
            start_date: 시작일
            end_date: 종료일
            save: 파일 저장 여부

        Returns:
            시각화 결과 정보
        """
        results = {}

        # 여러 종목 데이터 동시 로드
        stocks_data = self.mongo_loader.load_multiple_stocks(
            tickers=tickers,
            market=market,
            data_type="daily",
            start_date=start_date,
            end_date=end_date
        )

        for ticker, df in stocks_data.items():
            # 각 종목별 차트 생성
            result = self.visualize_stock_with_signals(
                ticker=ticker,
                df_daily=df,
                market=market,
                load_from_db=False,  # 이미 로드했으므로
                save=save
            )
            results[ticker] = result

        return {
            'status': 'success',
            'market': market,
            'total_stocks': len(tickers),
            'processed_stocks': len(results),
            'results': results
        }

    def visualize_backtest_from_db(
        self,
        backtest_id: Optional[str] = None,
        strategy_name: Optional[str] = None,
        save: bool = True
    ) -> Dict:
        """
        MongoDB에서 백테스트 결과를 로드하여 시각화

        Args:
            backtest_id: 백테스트 ID
            strategy_name: 전략 이름
            save: 파일 저장 여부

        Returns:
            시각화 결과 정보
        """
        # MongoDB에서 백테스트 결과 로드
        backtest_data = self.mongo_loader.load_backtest_results(
            backtest_id=backtest_id,
            strategy_name=strategy_name
        )

        if not backtest_data:
            return {'status': 'error', 'error': 'No backtest results found'}

        # 시각화 실행
        return self.visualize_backtest_results(
            backtest_output=backtest_data,
            save=save
        )

    def get_available_tickers(self, market: str = "NASDAQ") -> List[str]:
        """
        MongoDB에서 사용 가능한 종목 리스트 조회

        Args:
            market: 시장

        Returns:
            종목 코드 리스트
        """
        return self.mongo_loader.get_available_tickers(market)

    def get_database_info(self) -> Dict:
        """
        MongoDB 데이터베이스 정보 조회

        Returns:
            데이터베이스 통계 정보
        """
        return self.mongo_loader.get_database_info()

    def test_mongodb_connection(self) -> bool:
        """
        MongoDB 연결 테스트

        Returns:
            연결 성공 여부
        """
        return self.mongo_loader.test_connection()

    def close(self):
        """리소스 정리"""
        if hasattr(self, 'mongo_loader'):
            self.mongo_loader.close()

    def _create_sector_chart(self, sector_allocation: Dict):
        """섹터별 분포 차트"""
        import plotly.graph_objects as go

        labels = list(sector_allocation.keys())
        values = list(sector_allocation.values())

        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color='lightblue'
            )
        ])

        fig.update_layout(
            title="Sector Allocation",
            xaxis_title="Sector",
            yaxis_title="Allocation (%)",
            height=400,
            template='plotly_white'
        )

        return fig