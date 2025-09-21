"""
Service Layer Performance Analysis and Reporting

백테스트 결과 분석 및 리포팅을 담당하는 서비스
수익률, 리스크, 거래 분석 등 종합적인 성과 지표 제공

버전: 1.0
작성일: 2025-09-21
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


@dataclass
class Trade:
    """개별 거래 정보"""
    ticker: str
    trade_type: str  # 'BUY', 'SELL', 'HALF_SELL', 'WHIPSAW'
    quantity: float
    price: float
    timestamp: pd.Timestamp
    reason: str  # 'SIGNAL', 'LOSSCUT', 'PROFIT_TAKING'
    pnl: float
    commission: float
    duration: Optional[int] = None  # 보유 기간 (일)


@dataclass
class Portfolio:
    """포트폴리오 상태"""
    timestamp: pd.Timestamp
    cash: float
    positions: Dict[str, float]  # {ticker: value}
    total_value: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class ReturnAnalysis:
    """수익률 분석 결과"""
    total_return: float
    annual_return: float
    monthly_returns: pd.Series
    daily_returns: pd.Series
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    recovery_factor: float
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional VaR (95%)


@dataclass
class TradeAnalysis:
    """거래 분석 결과"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    avg_trade: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    expectancy: float
    avg_trade_duration: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    max_adverse_excursion: float
    max_favorable_excursion: float


@dataclass
class RiskAnalysis:
    """리스크 분석 결과"""
    portfolio_beta: float
    correlation_matrix: pd.DataFrame
    sector_exposure: Dict[str, float]
    concentration_risk: float
    position_risk: Dict[str, float]
    rolling_volatility: pd.Series
    downside_deviation: float
    ulcer_index: float
    pain_index: float


@dataclass
class BacktestReport:
    """종합 백테스트 리포트"""
    strategy_name: str
    backtest_period: Tuple[pd.Timestamp, pd.Timestamp]
    initial_capital: float
    final_capital: float
    return_analysis: ReturnAnalysis
    trade_analysis: TradeAnalysis
    risk_analysis: RiskAnalysis
    monthly_performance: pd.DataFrame
    annual_performance: pd.DataFrame
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    rolling_metrics: pd.DataFrame
    sector_performance: Dict[str, Any]
    benchmark_comparison: Optional[Dict[str, Any]] = None


class PerformanceAnalyzer:
    """
    백테스트 성과 분석 및 리포팅 서비스

    다양한 성과 지표를 계산하고 종합 리포트를 생성
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """성과 분석기 초기화"""
        self.risk_free_rate = risk_free_rate

    def analyze_returns(self, trades: List[Trade], portfolio_history: List[Portfolio],
                       initial_capital: float) -> ReturnAnalysis:
        """
        수익률 분석

        Args:
            trades: 거래 기록 리스트
            portfolio_history: 포트폴리오 히스토리
            initial_capital: 초기 자본

        Returns:
            ReturnAnalysis: 수익률 분석 결과
        """
        # 포트폴리오 가치 시계열 생성
        portfolio_values = pd.Series(
            [p.total_value for p in portfolio_history],
            index=[p.timestamp for p in portfolio_history]
        )

        # 일일 수익률 계산
        daily_returns = portfolio_values.pct_change().dropna()

        # 총 수익률
        final_value = portfolio_values.iloc[-1] if len(portfolio_values) > 0 else initial_capital
        total_return = (final_value - initial_capital) / initial_capital

        # 연율화 수익률
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days if len(portfolio_values) > 1 else 1
        annual_return = (1 + total_return) ** (365.25 / days) - 1 if days > 0 else 0

        # 월별 수익률
        monthly_values = portfolio_values.resample('M').last()
        monthly_returns = monthly_values.pct_change().dropna()

        # 변동성 (연율화)
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0

        # 샤프 비율
        excess_returns = daily_returns - self.risk_free_rate / 252
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0

        # 소르티노 비율
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0

        # 최대 낙폭 (MDD) 계산
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()

        # 최대 낙폭 지속 기간
        in_drawdown = drawdown < 0
        drawdown_periods = self._get_consecutive_periods(in_drawdown)
        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0

        # 평균 낙폭
        avg_drawdown = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0

        # 칼마 비율
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0

        # 회복 계수
        recovery_factor = total_return / abs(max_drawdown) if max_drawdown < 0 else 0

        # VaR (95%)
        var_95 = daily_returns.quantile(0.05) if len(daily_returns) > 0 else 0

        # CVaR (95%)
        cvar_95 = daily_returns[daily_returns <= var_95].mean() if len(daily_returns) > 0 else 0

        return ReturnAnalysis(
            total_return=total_return,
            annual_return=annual_return,
            monthly_returns=monthly_returns,
            daily_returns=daily_returns,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            avg_drawdown=avg_drawdown,
            recovery_factor=recovery_factor,
            var_95=var_95,
            cvar_95=cvar_95
        )

    def analyze_trades(self, trades: List[Trade]) -> TradeAnalysis:
        """
        거래 분석

        Args:
            trades: 거래 기록 리스트

        Returns:
            TradeAnalysis: 거래 분석 결과
        """
        if not trades:
            return self._empty_trade_analysis()

        # 매수/매도 쌍을 이용한 개별 거래 분석
        trade_pairs = self._pair_trades(trades)

        winning_trades = [t for t in trade_pairs if t['pnl'] > 0]
        losing_trades = [t for t in trade_pairs if t['pnl'] < 0]

        total_trades = len(trade_pairs)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)

        # 승률
        win_rate = winning_count / total_trades if total_trades > 0 else 0

        # 평균 손익
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        avg_trade = np.mean([t['pnl'] for t in trade_pairs]) if trade_pairs else 0

        # 최대 손익
        largest_win = max([t['pnl'] for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t['pnl'] for t in losing_trades]) if losing_trades else 0

        # 수익 인수 (Profit Factor)
        gross_profit = sum([t['pnl'] for t in winning_trades])
        gross_loss = abs(sum([t['pnl'] for t in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # 기댓값
        expectancy = avg_trade

        # 평균 거래 기간
        durations = [t['duration'] for t in trade_pairs if t['duration'] is not None]
        avg_trade_duration = np.mean(durations) if durations else 0

        # 연속 승/패 계산
        win_loss_sequence = [t['pnl'] > 0 for t in trade_pairs]
        max_consecutive_wins = self._max_consecutive_true(win_loss_sequence)
        max_consecutive_losses = self._max_consecutive_true([not x for x in win_loss_sequence])

        # MAE/MFE (추후 구현)
        max_adverse_excursion = 0
        max_favorable_excursion = 0

        return TradeAnalysis(
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_trade_duration=avg_trade_duration,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            max_adverse_excursion=max_adverse_excursion,
            max_favorable_excursion=max_favorable_excursion
        )

    def analyze_risk(self, portfolio_history: List[Portfolio],
                    trades: List[Trade],
                    benchmark_returns: Optional[pd.Series] = None) -> RiskAnalysis:
        """
        리스크 분석

        Args:
            portfolio_history: 포트폴리오 히스토리
            trades: 거래 기록
            benchmark_returns: 벤치마크 수익률 (선택사항)

        Returns:
            RiskAnalysis: 리스크 분석 결과
        """
        # 포트폴리오 가치 시계열
        portfolio_values = pd.Series(
            [p.total_value for p in portfolio_history],
            index=[p.timestamp for p in portfolio_history]
        )
        daily_returns = portfolio_values.pct_change().dropna()

        # 베타 계산 (벤치마크가 있는 경우)
        portfolio_beta = 1.0
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            aligned_returns = daily_returns.align(benchmark_returns, join='inner')[0]
            aligned_benchmark = daily_returns.align(benchmark_returns, join='inner')[1]
            if len(aligned_returns) > 1:
                portfolio_beta = np.cov(aligned_returns, aligned_benchmark)[0, 1] / np.var(aligned_benchmark)

        # 상관관계 매트릭스 (임시)
        correlation_matrix = pd.DataFrame()

        # 섹터 노출도 (임시)
        sector_exposure = {}

        # 집중도 리스크
        if portfolio_history:
            last_portfolio = portfolio_history[-1]
            total_value = last_portfolio.total_value
            if total_value > 0:
                position_weights = {k: v/total_value for k, v in last_portfolio.positions.items()}
                concentration_risk = max(position_weights.values()) if position_weights else 0
            else:
                concentration_risk = 0
        else:
            concentration_risk = 0

        # 포지션별 리스크
        position_risk = {}

        # 롤링 변동성
        rolling_volatility = daily_returns.rolling(window=30).std() * np.sqrt(252)

        # 하방 편차
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0

        # 울서 지수 (Ulcer Index)
        peak = portfolio_values.expanding().max()
        drawdown = (portfolio_values - peak) / peak
        ulcer_index = np.sqrt((drawdown ** 2).mean()) if len(drawdown) > 0 else 0

        # 고통 지수 (Pain Index)
        pain_index = abs(drawdown).mean() if len(drawdown) > 0 else 0

        return RiskAnalysis(
            portfolio_beta=portfolio_beta,
            correlation_matrix=correlation_matrix,
            sector_exposure=sector_exposure,
            concentration_risk=concentration_risk,
            position_risk=position_risk,
            rolling_volatility=rolling_volatility,
            downside_deviation=downside_deviation,
            ulcer_index=ulcer_index,
            pain_index=pain_index
        )

    def generate_report(self, strategy_name: str, trades: List[Trade],
                       portfolio_history: List[Portfolio], initial_capital: float,
                       benchmark_returns: Optional[pd.Series] = None) -> BacktestReport:
        """
        종합 백테스트 리포트 생성

        Args:
            strategy_name: 전략명
            trades: 거래 기록
            portfolio_history: 포트폴리오 히스토리
            initial_capital: 초기 자본
            benchmark_returns: 벤치마크 수익률

        Returns:
            BacktestReport: 종합 백테스트 리포트
        """
        # 기본 분석 수행
        return_analysis = self.analyze_returns(trades, portfolio_history, initial_capital)
        trade_analysis = self.analyze_trades(trades)
        risk_analysis = self.analyze_risk(portfolio_history, trades, benchmark_returns)

        # 백테스트 기간
        if portfolio_history:
            start_date = portfolio_history[0].timestamp
            end_date = portfolio_history[-1].timestamp
        else:
            start_date = end_date = pd.Timestamp.now()

        backtest_period = (start_date, end_date)

        # 최종 자본
        final_capital = portfolio_history[-1].total_value if portfolio_history else initial_capital

        # 월별/연별 성과 테이블
        monthly_performance = self._create_monthly_performance_table(return_analysis.monthly_returns)
        annual_performance = self._create_annual_performance_table(return_analysis.monthly_returns)

        # 주식 곡선 및 낙폭 곡선
        portfolio_values = pd.Series(
            [p.total_value for p in portfolio_history],
            index=[p.timestamp for p in portfolio_history]
        ) if portfolio_history else pd.Series(dtype=float)

        equity_curve = portfolio_values
        peak = portfolio_values.expanding().max()
        drawdown_curve = (portfolio_values - peak) / peak

        # 롤링 메트릭
        rolling_metrics = self._create_rolling_metrics(return_analysis.daily_returns)

        # 섹터 성과 (임시)
        sector_performance = {}

        # 벤치마크 비교 (선택사항)
        benchmark_comparison = None
        if benchmark_returns is not None:
            benchmark_comparison = self._create_benchmark_comparison(
                return_analysis.daily_returns, benchmark_returns
            )

        return BacktestReport(
            strategy_name=strategy_name,
            backtest_period=backtest_period,
            initial_capital=initial_capital,
            final_capital=final_capital,
            return_analysis=return_analysis,
            trade_analysis=trade_analysis,
            risk_analysis=risk_analysis,
            monthly_performance=monthly_performance,
            annual_performance=annual_performance,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            rolling_metrics=rolling_metrics,
            sector_performance=sector_performance,
            benchmark_comparison=benchmark_comparison
        )

    def _pair_trades(self, trades: List[Trade]) -> List[Dict[str, Any]]:
        """매수/매도 쌍으로 거래를 매칭"""
        positions = {}
        completed_trades = []

        for trade in trades:
            ticker = trade.ticker

            if trade.trade_type == 'BUY':
                if ticker not in positions:
                    positions[ticker] = []
                positions[ticker].append(trade)

            elif trade.trade_type in ['SELL', 'HALF_SELL']:
                if ticker in positions and positions[ticker]:
                    buy_trade = positions[ticker].pop(0)
                    duration = (trade.timestamp - buy_trade.timestamp).days
                    pnl = trade.pnl

                    completed_trades.append({
                        'ticker': ticker,
                        'buy_date': buy_trade.timestamp,
                        'sell_date': trade.timestamp,
                        'buy_price': buy_trade.price,
                        'sell_price': trade.price,
                        'pnl': pnl,
                        'duration': duration,
                        'trade_type': trade.trade_type
                    })

        return completed_trades

    def _get_consecutive_periods(self, boolean_series: pd.Series) -> List[int]:
        """연속 True 구간의 길이들 반환"""
        periods = []
        current_period = 0

        for value in boolean_series:
            if value:
                current_period += 1
            else:
                if current_period > 0:
                    periods.append(current_period)
                    current_period = 0

        if current_period > 0:
            periods.append(current_period)

        return periods

    def _max_consecutive_true(self, boolean_list: List[bool]) -> int:
        """연속 True의 최대 길이"""
        max_count = 0
        current_count = 0

        for value in boolean_list:
            if value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count

    def _empty_trade_analysis(self) -> TradeAnalysis:
        """빈 거래 분석 결과"""
        return TradeAnalysis(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            avg_win=0,
            avg_loss=0,
            avg_trade=0,
            largest_win=0,
            largest_loss=0,
            profit_factor=0,
            expectancy=0,
            avg_trade_duration=0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            max_adverse_excursion=0,
            max_favorable_excursion=0
        )

    def _create_monthly_performance_table(self, monthly_returns: pd.Series) -> pd.DataFrame:
        """월별 성과 테이블 생성"""
        if len(monthly_returns) == 0:
            return pd.DataFrame()

        # 월별 수익률을 연도별로 정리
        monthly_data = []
        for date, ret in monthly_returns.items():
            monthly_data.append({
                'Year': date.year,
                'Month': date.month,
                'Return': ret
            })

        df = pd.DataFrame(monthly_data)
        if df.empty:
            return pd.DataFrame()

        # 피벗 테이블 생성
        pivot_table = df.pivot(index='Year', columns='Month', values='Return')

        # 월 이름으로 컬럼 변경
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        pivot_table.columns = [month_names[i-1] for i in pivot_table.columns]

        return pivot_table.fillna(0)

    def _create_annual_performance_table(self, monthly_returns: pd.Series) -> pd.DataFrame:
        """연별 성과 테이블 생성"""
        if len(monthly_returns) == 0:
            return pd.DataFrame()

        # 연별 수익률 계산
        annual_returns = (1 + monthly_returns).groupby(monthly_returns.index.year).prod() - 1

        annual_data = []
        for year, ret in annual_returns.items():
            annual_data.append({
                'Year': year,
                'Annual Return': ret,
                'Cumulative Return': (1 + annual_returns.loc[:year]).prod() - 1
            })

        return pd.DataFrame(annual_data)

    def _create_rolling_metrics(self, daily_returns: pd.Series, window: int = 252) -> pd.DataFrame:
        """롤링 메트릭 생성"""
        if len(daily_returns) < window:
            return pd.DataFrame()

        rolling_data = []
        for i in range(window, len(daily_returns)):
            period_returns = daily_returns.iloc[i-window:i]

            rolling_data.append({
                'Date': daily_returns.index[i],
                'Rolling Return': (1 + period_returns).prod() - 1,
                'Rolling Volatility': period_returns.std() * np.sqrt(252),
                'Rolling Sharpe': (period_returns.mean() / period_returns.std() * np.sqrt(252)) if period_returns.std() > 0 else 0
            })

        return pd.DataFrame(rolling_data).set_index('Date')

    def _create_benchmark_comparison(self, portfolio_returns: pd.Series,
                                   benchmark_returns: pd.Series) -> Dict[str, Any]:
        """벤치마크 비교 분석"""
        # 날짜 정렬
        aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')

        if len(aligned_portfolio) == 0:
            return {}

        # 비교 메트릭 계산
        portfolio_total = (1 + aligned_portfolio).prod() - 1
        benchmark_total = (1 + aligned_benchmark).prod() - 1
        excess_return = portfolio_total - benchmark_total

        portfolio_vol = aligned_portfolio.std() * np.sqrt(252)
        benchmark_vol = aligned_benchmark.std() * np.sqrt(252)

        correlation = aligned_portfolio.corr(aligned_benchmark)

        # 베타 계산
        if aligned_benchmark.var() > 0:
            beta = aligned_portfolio.cov(aligned_benchmark) / aligned_benchmark.var()
        else:
            beta = 1.0

        # 알파 계산
        alpha = portfolio_total - beta * benchmark_total

        return {
            'portfolio_return': portfolio_total,
            'benchmark_return': benchmark_total,
            'excess_return': excess_return,
            'portfolio_volatility': portfolio_vol,
            'benchmark_volatility': benchmark_vol,
            'correlation': correlation,
            'beta': beta,
            'alpha': alpha
        }