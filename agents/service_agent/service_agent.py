"""
Service Agent - Multi-Agent Trading System

백테스트 실행, 포트폴리오 관리, 성과 분석을 담당하는 전문 에이전트
시장별 구분된 포트폴리오 관리 및 리스크 제어

버전: 1.0
작성일: 2025-09-22
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)


class ServiceAgent:
    """
    Service Agent

    백테스트 실행, 포트폴리오 관리, 리스크 제어를 담당
    시장별 분리된 포트폴리오 관리 및 통합 성과 분석
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Service Agent 초기화"""
        self.config = config or {}
        self.execution_log = []

        # 백테스트 설정 (안전한 기본값 제공)
        default_backtest_config = {
            'initial_cash': 100000000,  # 1억원
            'commission_rate': 0.002,   # 0.2% 수수료
            'slippage': 0.001,         # 0.1% 슬리피지
            'max_stocks_per_market': 5,  # 시장별 최대 종목 수
        }

        self.backtest_config = self.config.get('backtest_config', default_backtest_config)

        # 리스크 관리 설정
        self.risk_config = {
            'max_position_per_stock': 0.15,  # 종목당 최대 15%
            'max_market_allocation': 0.6,    # 시장당 최대 60%
            'stop_loss_pct': 0.08,          # 8% 손절
            'take_profit_pct': 0.25,        # 25% 익절
            'max_correlation_exposure': 0.5,  # 상관관계 높은 종목 제한
        }

        self._log("[Service Agent] 초기화 완료")
        self._log(f"[Service Agent] 초기 자본: {self.backtest_config['initial_cash']:,}원")
        self._log(f"[Service Agent] 리스크 설정: {self.risk_config}")

    def execute_backtest(self,
                        market_data: Dict[str, pd.DataFrame],
                        signals: Dict[str, Any],
                        start_date: str,
                        end_date: str,
                        prompt: str = "") -> Dict[str, Any]:
        """
        백테스트 실행

        Args:
            market_data: 시장 데이터
            signals: 매매 신호
            start_date: 시작일
            end_date: 종료일
            prompt: 오케스트레이터로부터의 작업 지시

        Returns:
            백테스트 결과
        """
        start_time = time.time()

        try:
            self._log("[Service Agent] 백테스트 실행 작업 시작")
            self._log(f"[Service Agent] 작업 지시 수신: {len(prompt)} 문자")
            self._log(f"[Service Agent] 백테스트 기간: {start_date} ~ {end_date}")

            # 백테스트 환경 초기화
            backtest_env = self._initialize_backtest_environment(market_data, signals)

            # 시장별 포트폴리오 관리
            portfolio_results = self._run_multi_market_backtest(backtest_env, start_date, end_date)

            # 성과 분석
            performance_analysis = self._analyze_performance(portfolio_results, market_data)

            # 리스크 분석
            risk_analysis = self._analyze_risk(portfolio_results, market_data)

            # 거래 통계
            trade_statistics = self._calculate_trade_statistics(portfolio_results)

            # 최종 결과 통합
            final_results = {
                'portfolio_performance': portfolio_results,
                'performance_metrics': performance_analysis,
                'risk_metrics': risk_analysis,
                'trade_statistics': trade_statistics,
                'execution_config': self.backtest_config,
                'risk_config': self.risk_config
            }

            execution_time = time.time() - start_time
            self._log(f"[Service Agent] 백테스트 완료 - 실행시간: {execution_time:.2f}초")

            # 결과 요약 출력
            self._log_performance_summary(final_results)

            return final_results

        except Exception as e:
            self._log(f"[Service Agent] 백테스트 실행 실패: {e}")
            return {}

    def _initialize_backtest_environment(self, market_data: Dict[str, pd.DataFrame],
                                       signals: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 환경 초기화"""
        self._log("[Service Agent] 백테스트 환경 초기화")

        # 시장별 데이터 분리
        nasdaq_data = {k: v for k, v in market_data.items() if 'NASDAQ' in k or
                      any(nasdaq_symbol in k for nasdaq_symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])}
        nyse_data = {k: v for k, v in market_data.items() if k not in nasdaq_data}

        # 시장별 신호 분리
        nasdaq_signals = {k: v for k, v in signals.items() if k in nasdaq_data}
        nyse_signals = {k: v for k, v in signals.items() if k in nyse_data}

        # 전체 거래일 수집
        all_dates = set()
        for df in market_data.values():
            all_dates.update(df.index)
        trading_dates = sorted(list(all_dates))

        env = {
            'nasdaq_data': nasdaq_data,
            'nyse_data': nyse_data,
            'nasdaq_signals': nasdaq_signals,
            'nyse_signals': nyse_signals,
            'trading_dates': trading_dates,
            'initial_cash': self.backtest_config['initial_cash'],
            'nasdaq_cash': self.backtest_config['initial_cash'] * 0.5,  # 50% 할당
            'nyse_cash': self.backtest_config['initial_cash'] * 0.5,    # 50% 할당
            'nasdaq_positions': {},
            'nyse_positions': {},
            'nasdaq_portfolio_values': [],
            'nyse_portfolio_values': [],
            'total_portfolio_values': [],
            'all_trades': [],
        }

        self._log(f"[Service Agent] NASDAQ: {len(nasdaq_data)}개 종목, NYSE: {len(nyse_data)}개 종목")
        self._log(f"[Service Agent] 총 거래일: {len(trading_dates)}일")

        return env

    def _run_multi_market_backtest(self, env: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
        """멀티 마켓 백테스트 실행"""
        self._log("[Service Agent] 멀티 마켓 백테스트 실행 시작")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        for i, date in enumerate(env['trading_dates']):
            if date < start_dt or date > end_dt:
                continue

            try:
                # 일일 백테스트 실행
                self._execute_daily_trading(env, date)

                # 포트폴리오 가치 계산
                self._calculate_daily_portfolio_value(env, date)

                # 리스크 체크 및 조정
                self._daily_risk_management(env, date)

                # 진행상황 로그 (주간)
                if i % 5 == 0:
                    total_value = env['total_portfolio_values'][-1]['total_value'] if env['total_portfolio_values'] else env['initial_cash']
                    self._log(f"[Service Agent] {date.strftime('%Y-%m-%d')}: 포트폴리오 {total_value:,.0f}원")

            except Exception as e:
                self._log(f"[Service Agent] {date} 거래 실행 실패: {e}")

        self._log("[Service Agent] 백테스트 실행 완료")
        return env

    def _execute_daily_trading(self, env: Dict[str, Any], date: datetime):
        """일일 거래 실행"""
        # NASDAQ 거래 실행
        self._execute_market_trading(env, date, 'NASDAQ')

        # NYSE 거래 실행
        self._execute_market_trading(env, date, 'NYSE')

    def _execute_market_trading(self, env: Dict[str, Any], date: datetime, market: str):
        """특정 시장 거래 실행"""
        market_lower = market.lower()
        market_data = env[f'{market_lower}_data']
        market_signals = env[f'{market_lower}_signals']
        market_positions = env[f'{market_lower}_positions']
        market_cash = env[f'{market_lower}_cash']

        # 매도 신호 처리 (먼저 실행)
        for symbol, signal_data in market_signals.items():
            if symbol in market_positions and date in market_data[symbol].index:
                current_price = market_data[symbol].loc[date, 'Close']

                for sell_signal in signal_data.get('sell_signals', []):
                    if sell_signal['date'] == date:
                        # 매도 실행
                        position = market_positions[symbol]
                        sell_amount = self._execute_sell_order(position, current_price, date)

                        if sell_amount > 0:
                            # 현금 업데이트
                            env[f'{market_lower}_cash'] += sell_amount

                            # 거래 기록
                            trade_record = {
                                'date': date,
                                'symbol': symbol,
                                'market': market,
                                'type': 'SELL',
                                'price': current_price,
                                'shares': position['shares'],
                                'amount': sell_amount,
                                'pnl': sell_amount - (position['shares'] * position['avg_price']),
                                'signal': sell_signal.get('signal', 'UNKNOWN'),
                                'confidence': sell_signal.get('confidence', 0.5)
                            }
                            env['all_trades'].append(trade_record)

                            # 포지션 제거
                            del market_positions[symbol]
                            self._log(f"[Service Agent] {symbol} 매도: {current_price:.2f} ({trade_record['pnl']:+,.0f}원)")

        # 매수 신호 처리
        for symbol, signal_data in market_signals.items():
            if symbol not in market_positions and date in market_data[symbol].index:
                current_price = market_data[symbol].loc[date, 'Close']

                for buy_signal in signal_data.get('buy_signals', []):
                    if buy_signal['date'] == date:
                        # 포지션 크기 결정
                        position_size = self._calculate_position_size(
                            env, symbol, current_price, market, signal_data
                        )

                        if position_size > 0 and env[f'{market_lower}_cash'] >= position_size:
                            # 매수 실행
                            shares, actual_cost = self._execute_buy_order(current_price, position_size, date)

                            if shares > 0:
                                # 포지션 추가
                                market_positions[symbol] = {
                                    'shares': shares,
                                    'avg_price': actual_cost / shares,
                                    'entry_date': date,
                                    'entry_price': current_price,
                                    'stop_loss': current_price * (1 - self.risk_config['stop_loss_pct']),
                                    'take_profit': current_price * (1 + self.risk_config['take_profit_pct'])
                                }

                                # 현금 차감
                                env[f'{market_lower}_cash'] -= actual_cost

                                # 거래 기록
                                trade_record = {
                                    'date': date,
                                    'symbol': symbol,
                                    'market': market,
                                    'type': 'BUY',
                                    'price': current_price,
                                    'shares': shares,
                                    'amount': actual_cost,
                                    'pnl': 0,
                                    'signal': buy_signal.get('signal', 'UNKNOWN'),
                                    'confidence': buy_signal.get('confidence', 0.5)
                                }
                                env['all_trades'].append(trade_record)
                                self._log(f"[Service Agent] {symbol} 매수: {current_price:.2f} ({shares}주)")

    def _calculate_position_size(self, env: Dict[str, Any], symbol: str, price: float,
                               market: str, signal_data: Dict[str, Any]) -> float:
        """포지션 크기 계산"""
        market_lower = market.lower()
        available_cash = env[f'{market_lower}_cash']
        total_portfolio_value = env['initial_cash']  # 간단화

        # 기본 포지션 크기 (총 자산의 10%)
        base_position_size = total_portfolio_value * 0.1

        # 시장별 조정
        if market == 'NASDAQ':
            market_multiplier = 0.8  # 변동성이 높으므로 작게
        else:
            market_multiplier = 1.2  # 안정적이므로 크게

        # 신호 확신도 기반 조정
        avg_confidence = np.mean([s.get('confidence', 0.5) for s in signal_data.get('buy_signals', [])])
        confidence_multiplier = 0.5 + avg_confidence  # 0.5 ~ 1.5

        # 포지션 제안 반영
        position_suggestion = signal_data.get('position_suggestion', 1.0)

        # 최종 포지션 크기
        final_position_size = base_position_size * market_multiplier * confidence_multiplier * position_suggestion

        # 제약 조건 적용
        max_position = total_portfolio_value * self.risk_config['max_position_per_stock']
        final_position_size = min(final_position_size, max_position, available_cash * 0.8)

        return max(0, final_position_size)

    def _execute_buy_order(self, price: float, position_size: float, date: datetime) -> Tuple[int, float]:
        """매수 주문 실행"""
        # 슬리피지 및 수수료 적용
        execution_price = price * (1 + self.backtest_config['slippage'])
        shares = int(position_size / execution_price)

        if shares > 0:
            gross_cost = shares * execution_price
            commission = gross_cost * self.backtest_config['commission_rate']
            total_cost = gross_cost + commission
            return shares, total_cost
        else:
            return 0, 0

    def _execute_sell_order(self, position: Dict[str, Any], price: float, date: datetime) -> float:
        """매도 주문 실행"""
        # 슬리피지 및 수수료 적용
        execution_price = price * (1 - self.backtest_config['slippage'])
        gross_proceeds = position['shares'] * execution_price
        commission = gross_proceeds * self.backtest_config['commission_rate']
        net_proceeds = gross_proceeds - commission
        return net_proceeds

    def _calculate_daily_portfolio_value(self, env: Dict[str, Any], date: datetime):
        """일일 포트폴리오 가치 계산"""
        nasdaq_value = env['nasdaq_cash']
        nyse_value = env['nyse_cash']

        # NASDAQ 포지션 가치
        for symbol, position in env['nasdaq_positions'].items():
            if symbol in env['nasdaq_data'] and date in env['nasdaq_data'][symbol].index:
                current_price = env['nasdaq_data'][symbol].loc[date, 'Close']
                nasdaq_value += position['shares'] * current_price

        # NYSE 포지션 가치
        for symbol, position in env['nyse_positions'].items():
            if symbol in env['nyse_data'] and date in env['nyse_data'][symbol].index:
                current_price = env['nyse_data'][symbol].loc[date, 'Close']
                nyse_value += position['shares'] * current_price

        total_value = nasdaq_value + nyse_value

        # 기록 저장
        env['nasdaq_portfolio_values'].append({
            'date': date,
            'cash': env['nasdaq_cash'],
            'positions_value': nasdaq_value - env['nasdaq_cash'],
            'total_value': nasdaq_value
        })

        env['nyse_portfolio_values'].append({
            'date': date,
            'cash': env['nyse_cash'],
            'positions_value': nyse_value - env['nyse_cash'],
            'total_value': nyse_value
        })

        env['total_portfolio_values'].append({
            'date': date,
            'nasdaq_value': nasdaq_value,
            'nyse_value': nyse_value,
            'total_value': total_value,
            'cash_ratio': (env['nasdaq_cash'] + env['nyse_cash']) / total_value
        })

    def _daily_risk_management(self, env: Dict[str, Any], date: datetime):
        """일일 리스크 관리"""
        # 손절/익절 체크
        self._check_stop_loss_take_profit(env, date, 'NASDAQ')
        self._check_stop_loss_take_profit(env, date, 'NYSE')

        # 포트폴리오 리밸런싱 체크 (월 1회)
        if date.day == 1:
            self._rebalance_portfolio(env, date)

    def _check_stop_loss_take_profit(self, env: Dict[str, Any], date: datetime, market: str):
        """손절/익절 체크"""
        market_lower = market.lower()
        market_data = env[f'{market_lower}_data']
        market_positions = env[f'{market_lower}_positions']

        positions_to_close = []

        for symbol, position in market_positions.items():
            if symbol in market_data and date in market_data[symbol].index:
                current_price = market_data[symbol].loc[date, 'Close']

                # 손절 체크
                if current_price <= position['stop_loss']:
                    positions_to_close.append((symbol, 'STOP_LOSS'))

                # 익절 체크
                elif current_price >= position['take_profit']:
                    positions_to_close.append((symbol, 'TAKE_PROFIT'))

        # 포지션 청산
        for symbol, reason in positions_to_close:
            current_price = market_data[symbol].loc[date, 'Close']
            position = market_positions[symbol]
            sell_amount = self._execute_sell_order(position, current_price, date)

            if sell_amount > 0:
                env[f'{market_lower}_cash'] += sell_amount

                trade_record = {
                    'date': date,
                    'symbol': symbol,
                    'market': market,
                    'type': 'SELL',
                    'price': current_price,
                    'shares': position['shares'],
                    'amount': sell_amount,
                    'pnl': sell_amount - (position['shares'] * position['avg_price']),
                    'signal': reason,
                    'confidence': 1.0
                }
                env['all_trades'].append(trade_record)

                del market_positions[symbol]
                self._log(f"[Service Agent] {symbol} {reason}: {current_price:.2f} ({trade_record['pnl']:+,.0f}원)")

    def _rebalance_portfolio(self, env: Dict[str, Any], date: datetime):
        """포트폴리오 리밸런싱"""
        # 현재는 단순 로그만 출력 (향후 고도화 가능)
        total_value = env['total_portfolio_values'][-1]['total_value'] if env['total_portfolio_values'] else env['initial_cash']
        nasdaq_ratio = env['total_portfolio_values'][-1]['nasdaq_value'] / total_value if env['total_portfolio_values'] else 0.5
        nyse_ratio = env['total_portfolio_values'][-1]['nyse_value'] / total_value if env['total_portfolio_values'] else 0.5

        self._log(f"[Service Agent] 포트폴리오 비율 - NASDAQ: {nasdaq_ratio:.1%}, NYSE: {nyse_ratio:.1%}")

    def _analyze_performance(self, portfolio_results: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """성과 분석"""
        self._log("[Service Agent] 성과 분석 시작")

        if not portfolio_results['total_portfolio_values']:
            return {}

        portfolio_values = portfolio_results['total_portfolio_values']
        initial_value = portfolio_results['initial_cash']
        final_value = portfolio_values[-1]['total_value']

        # 기본 수익률 계산
        total_return = (final_value - initial_value) / initial_value
        days = len(portfolio_values)
        annualized_return = (1 + total_return) ** (365 / days) - 1

        # 일별 수익률 계산
        daily_returns = []
        for i in range(1, len(portfolio_values)):
            prev_value = portfolio_values[i-1]['total_value']
            curr_value = portfolio_values[i]['total_value']
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)

        # 리스크 지표
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        sharpe_ratio = (np.mean(daily_returns) * 252) / volatility if volatility > 0 else 0

        # 최대 낙폭
        peak = initial_value
        max_drawdown = 0
        for pv in portfolio_values:
            current_value = pv['total_value']
            if current_value > peak:
                peak = current_value
            drawdown = (peak - current_value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        performance = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_value': final_value,
            'days_traded': days,
            'daily_returns': daily_returns
        }

        return performance

    def _analyze_risk(self, portfolio_results: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """리스크 분석"""
        self._log("[Service Agent] 리스크 분석 시작")

        risk_metrics = {
            'portfolio_concentration': self._calculate_concentration_risk(portfolio_results),
            'market_exposure': self._calculate_market_exposure(portfolio_results),
            'correlation_risk': self._calculate_correlation_risk(market_data),
            'liquidity_risk': self._calculate_liquidity_risk(portfolio_results, market_data)
        }

        return risk_metrics

    def _calculate_concentration_risk(self, portfolio_results: Dict[str, Any]) -> Dict[str, float]:
        """집중도 리스크 계산"""
        # 현재는 간단한 지표만 계산
        nasdaq_positions = len(portfolio_results['nasdaq_positions'])
        nyse_positions = len(portfolio_results['nyse_positions'])
        total_positions = nasdaq_positions + nyse_positions

        return {
            'total_positions': total_positions,
            'nasdaq_concentration': nasdaq_positions / max(total_positions, 1),
            'nyse_concentration': nyse_positions / max(total_positions, 1),
            'diversification_ratio': min(1.0, total_positions / 10)  # 10개 종목 기준
        }

    def _calculate_market_exposure(self, portfolio_results: Dict[str, Any]) -> Dict[str, float]:
        """시장 노출도 계산"""
        if not portfolio_results['total_portfolio_values']:
            return {}

        latest_values = portfolio_results['total_portfolio_values'][-1]
        total_value = latest_values['total_value']

        return {
            'nasdaq_exposure': latest_values['nasdaq_value'] / total_value,
            'nyse_exposure': latest_values['nyse_value'] / total_value,
            'cash_ratio': latest_values['cash_ratio'],
            'equity_exposure': 1 - latest_values['cash_ratio']
        }

    def _calculate_correlation_risk(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """상관관계 리스크 계산"""
        try:
            returns_data = {}
            for symbol, df in market_data.items():
                if 'Daily_Return' in df.columns:
                    returns_data[symbol] = df['Daily_Return'].dropna()

            if len(returns_data) > 1:
                returns_df = pd.DataFrame(returns_data)
                correlation_matrix = returns_df.corr()
                # 대각선 제외한 상관관계 평균
                avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
                return abs(avg_correlation)
            else:
                return 0.0

        except Exception:
            return 0.0

    def _calculate_liquidity_risk(self, portfolio_results: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> float:
        """유동성 리스크 계산"""
        # 거래량 기반 간단한 유동성 지표
        try:
            avg_volume_ratios = []
            for symbol in list(portfolio_results['nasdaq_positions'].keys()) + list(portfolio_results['nyse_positions'].keys()):
                if symbol in market_data and 'Volume_Ratio' in market_data[symbol].columns:
                    avg_ratio = market_data[symbol]['Volume_Ratio'].mean()
                    avg_volume_ratios.append(avg_ratio)

            return np.mean(avg_volume_ratios) if avg_volume_ratios else 1.0

        except Exception:
            return 1.0

    def _calculate_trade_statistics(self, portfolio_results: Dict[str, Any]) -> Dict[str, Any]:
        """거래 통계 계산"""
        trades = portfolio_results['all_trades']

        if not trades:
            return {}

        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']

        # 수익성 거래 분석
        profitable_trades = [t for t in sell_trades if t['pnl'] > 0]
        losing_trades = [t for t in sell_trades if t['pnl'] < 0]

        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0

        statistics = {
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_profit': np.mean([t['pnl'] for t in profitable_trades]) if profitable_trades else 0,
            'avg_loss': np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0,
            'profit_factor': abs(sum(t['pnl'] for t in profitable_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades else float('inf'),
            'avg_confidence': np.mean([t['confidence'] for t in trades]),
            'market_breakdown': {
                'NASDAQ_trades': len([t for t in trades if t['market'] == 'NASDAQ']),
                'NYSE_trades': len([t for t in trades if t['market'] == 'NYSE'])
            }
        }

        return statistics

    def _log_performance_summary(self, results: Dict[str, Any]):
        """성과 요약 로그"""
        performance = results.get('performance_metrics', {})
        trade_stats = results.get('trade_statistics', {})

        self._log("="*80)
        self._log("[Service Agent] 백테스트 성과 요약")
        self._log("="*80)

        if performance:
            self._log(f"[수익성] 총 수익률: {performance['total_return']:.2%}")
            self._log(f"[수익성] 연율화 수익률: {performance['annualized_return']:.2%}")
            self._log(f"[리스크] 변동성: {performance['volatility']:.2%}")
            self._log(f"[리스크] 샤프 비율: {performance['sharpe_ratio']:.3f}")
            self._log(f"[리스크] 최대 낙폭: {performance['max_drawdown']:.2%}")

        if trade_stats:
            self._log(f"[거래] 총 거래 수: {trade_stats['total_trades']}회")
            self._log(f"[거래] 승률: {trade_stats['win_rate']:.2%}")
            self._log(f"[거래] NASDAQ: {trade_stats['market_breakdown']['NASDAQ_trades']}회")
            self._log(f"[거래] NYSE: {trade_stats['market_breakdown']['NYSE_trades']}회")

        self._log("="*80)

    def _log(self, message: str):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)

    def get_execution_log(self) -> List[str]:
        """실행 로그 반환"""
        return self.execution_log.copy()