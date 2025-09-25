"""
Simple Integrated Backtest System

Indicator Layer, Strategy Layer, Service Layer 통합 백테스트 시스템의 간단한 버전
실제 데이터를 사용하여 기본적인 백테스트를 실행하고 과정을 출력

버전: 1.0
작성일: 2025-09-21
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 필요한 모듈 임포트
try:
    from Helper.yfinance_helper import YFinanceHelper
    from simple_technical_indicators import SimpleTechnicalIndicators
    print("[성공] 모든 필수 모듈 임포트 성공")
except ImportError as e:
    print(f"[실패] 모듈 임포트 실패: {e}")
    print("yfinance를 설치하세요: pip install yfinance")
    sys.exit(1)


class SimpleIntegratedBacktest:
    """
    간단한 통합 백테스트 시스템

    실제 데이터를 사용하여 기본적인 백테스트를 실행
    """

    def __init__(self, config=None):
        """초기화"""
        self.config = config or {
            'initial_cash': 100000000,  # 1억원
            'commission_rate': 0.002,   # 0.2% 수수료
            'slippage': 0.001,         # 0.1% 슬리피지
        }

        self.execution_log = []

        # Helper 및 Indicator 초기화
        self.yfinance_helper = YFinanceHelper()
        self.technical_indicators = SimpleTechnicalIndicators()

        self._log("[성공] Simple Integrated Backtest 시스템 초기화 완료")

    def run_backtest(self, universe, start_date="2023-01-01", end_date="2023-12-31"):
        """통합 백테스트 실행"""
        self._log("=" * 80)
        self._log("[시작] Simple Integrated Backtest 실행 시작")
        self._log(f"[기간] 기간: {start_date} ~ {end_date}")
        self._log(f"[정보] 대상 종목: {universe}")
        self._log("=" * 80)

        overall_start_time = time.time()

        try:
            # Phase 1: 실제 데이터 로드 (Helper Layer)
            self._log("\n[Phase 1] Helper Layer - 실제 데이터 로드")
            market_data = self._load_market_data(universe, start_date, end_date)

            # Phase 2: 기술지표 계산 (Indicator Layer)
            self._log("\n[Phase 2] Indicator Layer - 기술지표 계산")
            processed_data = self._calculate_indicators(market_data)

            # Phase 3: 신호 생성 (Strategy Layer)
            self._log("\n[Phase 3] Strategy Layer - 신호 생성")
            signals = self._generate_signals(processed_data)

            # Phase 4: 백테스트 실행 (Service Layer)
            self._log("\n[Phase 4] Service Layer - 백테스트 실행")
            backtest_results = self._run_simple_backtest(processed_data, signals)

            # Phase 5: 결과 분석 및 출력
            self._log("\n[Phase 5] 결과 분석")
            self._analyze_results(backtest_results)

            total_time = time.time() - overall_start_time
            self._log(f"\n[시간] 전체 실행 시간: {total_time:.2f}초")
            self._log("[완료] Simple Integrated Backtest 완료!")

            return backtest_results

        except Exception as e:
            self._log(f"[실패] 백테스트 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _load_market_data(self, universe, start_date, end_date):
        """실제 시장 데이터 로드"""
        self._log("[다운로드] 실제 시장 데이터 다운로드 중...")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        market_data = {}

        for ticker in universe:
            try:
                self._log(f"  [다운로드] {ticker} 데이터 다운로드 중...")

                df = self.yfinance_helper.get_ohlcv(
                    stock_code=ticker,
                    p_code="D",
                    start_date=start_dt,
                    end_date=end_dt,
                    ohlcv="Y"
                )

                if not df.empty:
                    # 컬럼명 표준화
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })

                    market_data[ticker] = df
                    self._log(f"  [성공] {ticker}: {len(df)}일 데이터 로드 완료")
                else:
                    self._log(f"  [실패] {ticker}: 데이터 없음")

            except Exception as e:
                self._log(f"  [실패] {ticker} 로드 실패: {e}")
                continue

        self._log(f"[성공] 실제 데이터 로드 완료: {len(market_data)}/{len(universe)} 종목")
        return market_data

    def _calculate_indicators(self, market_data):
        """기술지표 계산"""
        self._log("[계산] 기술지표 계산 중...")

        processed_data = {}

        for ticker, df in market_data.items():
            try:
                self._log(f"  [계산] {ticker} 기술지표 계산 중...")

                # 기본 기술지표 계산
                df_with_indicators = self.technical_indicators.add_moving_averages(df, [5, 20, 50])
                df_with_indicators = self.technical_indicators.add_rsi(df_with_indicators)
                df_with_indicators = self.technical_indicators.add_bollinger_bands(df_with_indicators)
                df_with_indicators = self.technical_indicators.calculate_adr(df_with_indicators)

                processed_data[ticker] = df_with_indicators
                self._log(f"  [성공] {ticker} 기술지표 계산 완료")

            except Exception as e:
                self._log(f"  [실패] {ticker} 기술지표 계산 실패: {e}")
                processed_data[ticker] = df

        self._log("[성공] 기술지표 계산 완료")
        return processed_data

    def _generate_signals(self, processed_data):
        """간단한 매매 신호 생성"""
        self._log("[생성] 매매 신호 생성 중...")

        signals = {}

        for ticker, df in processed_data.items():
            try:
                self._log(f"  [생성] {ticker} 신호 생성 중...")

                # 간단한 전략: MA5 > MA20 크로스오버
                buy_signals = []
                sell_signals = []

                for i in range(1, len(df)):
                    if pd.notna(df['MA5'].iloc[i]) and pd.notna(df['MA20'].iloc[i]):
                        # 매수 신호: MA5가 MA20을 상향 돌파
                        if (df['MA5'].iloc[i] > df['MA20'].iloc[i] and
                            df['MA5'].iloc[i-1] <= df['MA20'].iloc[i-1]):
                            buy_signals.append(i)

                        # 매도 신호: MA5가 MA20을 하향 돌파
                        elif (df['MA5'].iloc[i] < df['MA20'].iloc[i] and
                              df['MA5'].iloc[i-1] >= df['MA20'].iloc[i-1]):
                            sell_signals.append(i)

                signals[ticker] = {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'dataframe': df
                }

                self._log(f"  [성공] {ticker}: 매수신호 {len(buy_signals)}개, 매도신호 {len(sell_signals)}개")

            except Exception as e:
                self._log(f"  [실패] {ticker} 신호 생성 실패: {e}")
                signals[ticker] = {'buy_signals': [], 'sell_signals': [], 'dataframe': df}

        self._log("[성공] 매매 신호 생성 완료")
        return signals

    def _run_simple_backtest(self, processed_data, signals):
        """간단한 백테스트 실행"""
        self._log("[실행] 백테스트 실행 중...")

        # 초기 설정
        initial_cash = self.config['initial_cash']
        cash = initial_cash
        positions = {}  # {ticker: {'quantity': 100, 'avg_price': 150.0}}
        trades = []
        portfolio_values = []

        # 전체 거래일 생성
        all_dates = set()
        for ticker, data in signals.items():
            all_dates.update(data['dataframe'].index)

        all_dates = sorted(list(all_dates))

        self._log(f"[기간] 백테스트 기간: {len(all_dates)}일")

        # 일별 백테스트 실행
        for date_idx, date in enumerate(all_dates):
            try:
                day_trades = 0

                # 각 종목에 대해 신호 확인
                for ticker, signal_data in signals.items():
                    df = signal_data['dataframe']

                    if date not in df.index:
                        continue

                    current_idx = df.index.get_loc(date)
                    current_price = df.loc[date, 'Close']

                    # 매수 신호 확인
                    if current_idx in signal_data['buy_signals'] and ticker not in positions:
                        position_size = cash * 0.1  # 10% 포지션

                        if position_size > 10000:  # 최소 1만원
                            quantity = int(position_size / current_price)
                            cost = quantity * current_price * (1 + self.config['commission_rate'] + self.config['slippage'])

                            if cost <= cash:
                                cash -= cost
                                positions[ticker] = {
                                    'quantity': quantity,
                                    'avg_price': current_price,
                                    'entry_date': date
                                }

                                trades.append({
                                    'date': date,
                                    'ticker': ticker,
                                    'action': 'BUY',
                                    'quantity': quantity,
                                    'price': current_price,
                                    'value': cost
                                })
                                day_trades += 1

                    # 매도 신호 확인
                    elif current_idx in signal_data['sell_signals'] and ticker in positions:
                        position = positions[ticker]
                        quantity = position['quantity']
                        proceeds = quantity * current_price * (1 - self.config['commission_rate'] - self.config['slippage'])

                        cash += proceeds

                        pnl = proceeds - (quantity * position['avg_price'])

                        trades.append({
                            'date': date,
                            'ticker': ticker,
                            'action': 'SELL',
                            'quantity': quantity,
                            'price': current_price,
                            'value': proceeds,
                            'pnl': pnl
                        })

                        del positions[ticker]
                        day_trades += 1

                # 포트폴리오 가치 계산
                portfolio_value = cash
                for ticker, position in positions.items():
                    if ticker in processed_data and date in processed_data[ticker].index:
                        current_price = processed_data[ticker].loc[date, 'Close']
                        portfolio_value += position['quantity'] * current_price

                portfolio_values.append({
                    'date': date,
                    'cash': cash,
                    'positions_value': portfolio_value - cash,
                    'total_value': portfolio_value,
                    'return': (portfolio_value - initial_cash) / initial_cash
                })

                if day_trades > 0 or date_idx % 50 == 0:
                    self._log(f"  [진행] {date.strftime('%Y-%m-%d')}: 포트폴리오 가치 {portfolio_value:,.0f}원 (거래 {day_trades}건)")

            except Exception as e:
                self._log(f"  [실패] {date} 백테스트 실패: {e}")
                continue

        # 결과 정리
        results = {
            'initial_cash': initial_cash,
            'final_cash': cash,
            'final_positions': positions,
            'trades': trades,
            'portfolio_values': portfolio_values,
            'total_trades': len(trades)
        }

        self._log("[성공] 백테스트 실행 완료")
        return results

    def _analyze_results(self, results):
        """결과 분석 및 출력"""
        self._log("[분석] 백테스트 결과 분석 중...")

        initial_cash = results['initial_cash']
        portfolio_values = results['portfolio_values']
        trades = results['trades']

        if not portfolio_values:
            self._log("[실패] 분석할 데이터가 없습니다.")
            return

        # 기본 성과 지표
        final_value = portfolio_values[-1]['total_value']
        total_return = (final_value - initial_cash) / initial_cash

        # 거래 분석
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']

        profitable_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) <= 0]

        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0

        # 일별 수익률
        returns = []
        for i in range(1, len(portfolio_values)):
            prev_value = portfolio_values[i-1]['total_value']
            curr_value = portfolio_values[i]['total_value']
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)

        returns = np.array(returns)
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
        sharpe_ratio = (np.mean(returns) * 252 / volatility) if volatility > 0 else 0

        # 최대 낙폭 계산
        peak = initial_cash
        max_drawdown = 0
        for pv in portfolio_values:
            if pv['total_value'] > peak:
                peak = pv['total_value']

            drawdown = (peak - pv['total_value']) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # 결과 출력
        self._log("\n" + "=" * 80)
        self._log("[요약] 백테스트 결과 요약")
        self._log("=" * 80)

        self._log(f"[자본] 초기 자본: {initial_cash:,.0f}원")
        self._log(f"[자본] 최종 자본: {final_value:,.0f}원")
        self._log(f"[수익] 총 수익률: {total_return:.2%}")
        self._log(f"[수익] 연율화 수익률: {total_return * (365/len(portfolio_values)):.2%}")
        self._log(f"[위험] 최대 낙폭: {max_drawdown:.2%}")
        self._log(f"[위험] 변동성: {volatility:.2%}")
        self._log(f"[비율] 샤프 비율: {sharpe_ratio:.3f}")
        self._log(f"[거래] 총 거래 수: {len(trades)}회")
        self._log(f"[거래] 매수 거래: {len(buy_trades)}회")
        self._log(f"[거래] 매도 거래: {len(sell_trades)}회")
        self._log(f"[비율] 승률: {win_rate:.2%}")

        if profitable_trades:
            avg_profit = np.mean([t['pnl'] for t in profitable_trades])
            self._log(f"[수익] 평균 수익: {avg_profit:,.0f}원")

        if losing_trades:
            avg_loss = np.mean([t['pnl'] for t in losing_trades])
            self._log(f"[손실] 평균 손실: {avg_loss:,.0f}원")

        # 상위 거래
        if sell_trades:
            sell_trades_sorted = sorted(sell_trades, key=lambda x: x.get('pnl', 0), reverse=True)
            self._log(f"\n[최고] 최고 수익 거래:")
            for i, trade in enumerate(sell_trades_sorted[:3]):
                pnl = trade.get('pnl', 0)
                self._log(f"  {i+1}. {trade['ticker']} {trade['date'].strftime('%Y-%m-%d')}: {pnl:,.0f}원")

        self._log("\n" + "=" * 80)

    def _log(self, message):
        """로그 출력 및 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)


def main():
    """메인 실행 함수"""
    print("[시작] Simple Integrated Backtest 시작")

    # 백테스트 설정
    config = {
        'initial_cash': 100000000,  # 1억원
        'commission_rate': 0.002,   # 0.2%
        'slippage': 0.001          # 0.1%
    }

    # 테스트 종목
    universe = ["AAPL", "MSFT", "GOOGL"]

    # 백테스트 기간
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    try:
        # 백테스트 실행
        backtest = SimpleIntegratedBacktest(config)
        results = backtest.run_backtest(universe, start_date, end_date)

        if results:
            print("\n[성공] Simple Integrated Backtest 완료")
            return results
        else:
            print("\n[실패] 백테스트 실행 실패")
            return None

    except Exception as e:
        print(f"\n[실패] 메인 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()