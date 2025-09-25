"""
MongoDB 기반 통합 백테스트 시스템

NasDataBase_D, W, F, E 컬렉션에서 실제 데이터를 로드하여
Indicator Layer, Strategy Layer, Service Layer를 통합한 백테스트 실행

버전: 1.0
작성일: 2025-09-22
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
import pymongo
import yaml
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.dirname(project_root))

try:
    from simple_technical_indicators import SimpleTechnicalIndicators
    print("[성공] 기술지표 모듈 임포트 성공")
except ImportError as e:
    print(f"[실패] 기술지표 모듈 임포트 실패: {e}")
    sys.exit(1)


class MongoDBIntegratedBacktest:
    """
    MongoDB 기반 통합 백테스트 시스템

    NasDataBase 컬렉션에서 실제 데이터를 로드하여 백테스트 실행
    """

    def __init__(self, config=None):
        """초기화"""
        self.config = config or {
            'initial_cash': 100000000,  # 1억원
            'commission_rate': 0.002,   # 0.2% 수수료
            'slippage': 0.001,         # 0.1% 슬리피지
        }

        self.execution_log = []
        self.indicators = SimpleTechnicalIndicators()
        self.mongodb_client = None
        self.db = None

        # MongoDB 설정 로드
        self._load_mongodb_config()
        self._log("[성공] MongoDB 통합 백테스트 시스템 초기화 완료")

    def _load_mongodb_config(self):
        """MongoDB 설정 로드"""
        try:
            # myStockInfo.yaml 파일에서 MongoDB 설정 로드
            config_path = os.path.join(os.path.dirname(project_root), 'myStockInfo.yaml')

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='UTF-8') as f:
                    self.stock_info = yaml.load(f, Loader=yaml.FullLoader)
                self._log("[성공] MongoDB 설정 로드 완료")
            else:
                # 기본 설정 사용 (NAS 서버 시도)
                self.stock_info = {
                    'MONGODB_LOCAL': '192.168.55.14',  # NAS 서버 시도
                    'MONGODB_PORT': 27017,
                    'MONGODB_ID': 'admin',
                    'MONGODB_PW': 'wlsaud07'
                }
                self._log("[경고] 기본 MongoDB 설정 사용")

        except Exception as e:
            self._log(f"[실패] MongoDB 설정 로드 실패: {e}")
            raise

    def _connect_mongodb(self):
        """MongoDB 연결"""
        try:
            # 로컬 MongoDB 연결 시도
            mongodb_host = self.stock_info.get('MONGODB_LOCAL', 'localhost')

            self.mongodb_client = pymongo.MongoClient(
                host=mongodb_host,
                port=self.stock_info['MONGODB_PORT'],
                username=self.stock_info['MONGODB_ID'],
                password=self.stock_info['MONGODB_PW'],
                serverSelectionTimeoutMS=10000  # 타임아웃 증가
            )

            self._log(f"[정보] MongoDB 연결 시도: {mongodb_host}:{self.stock_info['MONGODB_PORT']}")

            # 먼저 사용 가능한 데이터베이스 확인
            database_names = self.mongodb_client.list_database_names()
            self._log(f"[정보] 사용 가능한 데이터베이스: {database_names}")

            # NasDataBase_D 데이터베이스 확인
            if 'NasDataBase_D' in database_names:
                self.db = self.mongodb_client['NasDataBase_D']
                collections = self.db.list_collection_names()
                self._log(f"[성공] NasDataBase_D DB 연결 - 종목 수: {len(collections)}")

                # 일부 종목 예시 출력
                sample_tickers = collections[:5]
                self._log(f"[정보] 사용 가능한 종목 예시: {sample_tickers}")
            else:
                self._log("[경고] NasDataBase_D 데이터베이스를 찾을 수 없음 - 대체 데이터 소스 사용")
                return False

            return True

        except Exception as e:
            self._log(f"[실패] MongoDB 연결 실패: {e}")
            return False

    def _get_nasdaq_universe(self, limit=10):
        """NASDAQ 종목 리스트 가져오기"""
        try:
            # NasDataBase_D 데이터베이스에서 사용 가능한 종목들 확인
            if self.db is not None:
                collections = self.db.list_collection_names()

                # 잘 알려진 NASDAQ 종목들 우선 선택
                preferred_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']
                available_preferred = [ticker for ticker in preferred_tickers if ticker in collections]

                if len(available_preferred) >= limit:
                    universe = available_preferred[:limit]
                else:
                    # 선호 종목이 부족하면 다른 종목도 추가
                    additional_needed = limit - len(available_preferred)
                    other_tickers = [ticker for ticker in collections if ticker not in preferred_tickers]
                    universe = available_preferred + other_tickers[:additional_needed]

                self._log(f"[성공] NASDAQ 종목 {len(universe)}개 선택: {universe}")
                return universe
            else:
                # 기본 종목 사용
                default_universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'][:limit]
                self._log(f"[경고] DB 연결 없음 - 기본 종목 사용: {default_universe}")
                return default_universe

        except Exception as e:
            self._log(f"[실패] 종목 리스트 생성 실패: {e}")
            return ['AAPL', 'MSFT', 'GOOGL']

    def _load_mongodb_data(self, universe, start_date, end_date):
        """MongoDB에서 데이터 로드"""
        self._log("[다운로드] MongoDB에서 실제 데이터 로드 중...")

        if not self._connect_mongodb():
            return {}

        market_data = {}

        # 날짜 변환
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = start_date

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = end_date

        for ticker in universe:
            try:
                self._log(f"  [다운로드] {ticker} 데이터 로드 중...")

                # NasDataBase_D 데이터베이스에서 해당 종목 컬렉션 접근
                if ticker in self.db.list_collection_names():
                    collection = self.db[ticker]

                    # 쿼리 조건 (날짜 필터링)
                    query = {
                        "Date": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        }
                    }

                    # 데이터 조회
                    cursor = collection.find(query).sort("Date", 1)
                    data_list = list(cursor)

                    if data_list:
                        df = pd.DataFrame(data_list)

                        # 인덱스 설정
                        df['Date'] = pd.to_datetime(df['Date'])
                        df.set_index('Date', inplace=True)

                        # 필요한 컬럼만 선택 (OHLCV)
                        required_columns = ['open', 'high', 'low', 'close', 'volume']
                        available_columns = [col for col in required_columns if col in df.columns]

                        if available_columns:
                            df = df[available_columns]

                            # 컬럼명 표준화 (대문자로)
                            column_mapping = {
                                'open': 'Open',
                                'high': 'High',
                                'low': 'Low',
                                'close': 'Close',
                                'volume': 'Volume'
                            }
                            df = df.rename(columns=column_mapping)

                            market_data[ticker] = df
                            self._log(f"  [성공] {ticker}: {len(df)}일 데이터 로드 완료")
                        else:
                            self._log(f"  [실패] {ticker}: 필요한 OHLCV 컬럼 없음")
                    else:
                        self._log(f"  [실패] {ticker}: 기간 내 데이터 없음")
                else:
                    self._log(f"  [실패] {ticker}: 컬렉션 없음")

            except Exception as e:
                self._log(f"  [실패] {ticker} 로드 실패: {e}")

        # MongoDB 연결 종료
        if self.mongodb_client:
            self.mongodb_client.close()

        self._log(f"[성공] MongoDB 데이터 로드 완료: {len(market_data)}/{len(universe)} 종목")
        return market_data

    def _load_yfinance_fallback(self, universe, start_date, end_date):
        """Yahoo Finance fallback 데이터 로드"""
        self._log("[대체] Yahoo Finance에서 데이터 로드 중...")

        try:
            # Helper Layer 사용하여 데이터 로드
            sys.path.append(os.path.join(os.path.dirname(project_root), 'Helper'))
            from yfinance_helper import YFinanceHelper

            yfinance_helper = YFinanceHelper()
            market_data = {}

            for ticker in universe:
                try:
                    self._log(f"  [다운로드] {ticker} 데이터 다운로드 중...")

                    # Yahoo Finance에서 데이터 가져오기
                    df = yfinance_helper.get_ohlcv(
                        stock_code=ticker,
                        p_code="D",
                        start_date=start_date,
                        end_date=end_date,
                        market="US",
                        area="US"
                    )

                    if df is not None and not df.empty:
                        # 컬럼명 표준화
                        column_mapping = {
                            'open': 'Open',
                            'high': 'High',
                            'low': 'Low',
                            'close': 'Close',
                            'volume': 'Volume'
                        }

                        for old_col, new_col in column_mapping.items():
                            if old_col in df.columns:
                                df = df.rename(columns={old_col: new_col})

                        # 필요한 컬럼만 선택
                        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        available_columns = [col for col in required_columns if col in df.columns]

                        if available_columns:
                            df = df[available_columns]
                            market_data[ticker] = df
                            self._log(f"  [성공] {ticker}: {len(df)}일 데이터 로드 완료")
                        else:
                            self._log(f"  [실패] {ticker}: 필요한 컬럼 없음")
                    else:
                        self._log(f"  [실패] {ticker}: 데이터 없음")

                except Exception as e:
                    self._log(f"  [실패] {ticker} 로드 실패: {e}")

            self._log(f"[성공] Yahoo Finance 데이터 로드 완료: {len(market_data)}/{len(universe)} 종목")
            return market_data

        except ImportError:
            self._log("[실패] YFinanceHelper 모듈을 찾을 수 없습니다.")
            return {}
        except Exception as e:
            self._log(f"[실패] Yahoo Finance 데이터 로드 실패: {e}")
            return {}

    def _add_indicators(self, market_data):
        """기술지표 추가"""
        self._log("[계산] 기술지표 계산 중...")

        processed_data = {}

        for ticker, df in market_data.items():
            try:
                self._log(f"  [계산] {ticker} 기술지표 계산 중...")

                # 데이터 복사
                processed_df = df.copy()

                # 기술지표 추가
                processed_df = self.indicators.add_moving_averages(processed_df, [5, 10, 20, 50])
                processed_df = self.indicators.add_rsi(processed_df)
                processed_df = self.indicators.add_bollinger_bands(processed_df)
                processed_df = self.indicators.add_macd(processed_df)
                processed_df = self.indicators.add_price_change(processed_df)

                processed_data[ticker] = processed_df
                self._log(f"  [성공] {ticker} 기술지표 계산 완료")

            except Exception as e:
                self._log(f"  [실패] {ticker} 기술지표 계산 실패: {e}")
                processed_data[ticker] = df  # 원본 데이터라도 포함

        self._log("[성공] 기술지표 계산 완료")
        return processed_data

    def _generate_signals(self, processed_data):
        """매매 신호 생성"""
        self._log("[생성] 매매 신호 생성 중...")

        signals = {}

        for ticker, df in processed_data.items():
            try:
                self._log(f"  [생성] {ticker} 신호 생성 중...")

                # 이동평균 크로스오버 전략
                buy_signals = []
                sell_signals = []

                if 'MA5' in df.columns and 'MA20' in df.columns:
                    # 골든 크로스: MA5가 MA20을 상향 돌파
                    golden_cross = (df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1))

                    # 데드 크로스: MA5가 MA20을 하향 돌파
                    dead_cross = (df['MA5'] < df['MA20']) & (df['MA5'].shift(1) >= df['MA20'].shift(1))

                    # RSI 필터 추가 (과매수/과매도 제외)
                    if 'RSI' in df.columns:
                        rsi_filter_buy = (df['RSI'] > 30) & (df['RSI'] < 70)
                        rsi_filter_sell = (df['RSI'] > 30) & (df['RSI'] < 70)

                        golden_cross = golden_cross & rsi_filter_buy
                        dead_cross = dead_cross & rsi_filter_sell

                    # 신호 생성
                    for date in df.index:
                        if golden_cross.loc[date]:
                            buy_signals.append({
                                'date': date,
                                'price': df.loc[date, 'Close'],
                                'signal': 'MA_CROSS_BUY'
                            })
                        elif dead_cross.loc[date]:
                            sell_signals.append({
                                'date': date,
                                'price': df.loc[date, 'Close'],
                                'signal': 'MA_CROSS_SELL'
                            })

                signals[ticker] = {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals
                }

                self._log(f"  [성공] {ticker}: 매수신호 {len(buy_signals)}개, 매도신호 {len(sell_signals)}개")

            except Exception as e:
                self._log(f"  [실패] {ticker} 신호 생성 실패: {e}")
                signals[ticker] = {'buy_signals': [], 'sell_signals': []}

        self._log("[성공] 매매 신호 생성 완료")
        return signals

    def _run_simple_backtest(self, processed_data, signals):
        """간단한 백테스트 실행"""
        self._log("[실행] 백테스트 실행 중...")

        # 모든 날짜 수집
        all_dates = set()
        for df in processed_data.values():
            all_dates.update(df.index)
        all_dates = sorted(list(all_dates))

        self._log(f"[기간] 백테스트 기간: {len(all_dates)}일")

        # 백테스트 상태 초기화
        cash = self.config['initial_cash']
        positions = {}  # {ticker: {'shares': int, 'avg_price': float, 'entry_date': date}}
        portfolio_values = []
        trades = []

        for i, date in enumerate(all_dates):
            try:
                day_trades = 0

                # 각 종목별 신호 처리
                for ticker in processed_data.keys():
                    if date not in processed_data[ticker].index:
                        continue

                    current_price = processed_data[ticker].loc[date, 'Close']

                    # 매도 신호 처리 (보유 중인 경우)
                    if ticker in positions:
                        # 매도 신호 확인
                        for sell_signal in signals[ticker]['sell_signals']:
                            if sell_signal['date'] == date:
                                # 매도 실행
                                position = positions[ticker]
                                sell_amount = position['shares'] * current_price * (1 - self.config['commission_rate'] - self.config['slippage'])

                                pnl = sell_amount - (position['shares'] * position['avg_price'])

                                trades.append({
                                    'ticker': ticker,
                                    'type': 'SELL',
                                    'date': date,
                                    'price': current_price,
                                    'shares': position['shares'],
                                    'amount': sell_amount,
                                    'pnl': pnl,
                                    'entry_date': position['entry_date'],
                                    'hold_days': (date - position['entry_date']).days
                                })

                                cash += sell_amount
                                del positions[ticker]
                                day_trades += 1
                                break

                    # 매수 신호 처리 (미보유인 경우)
                    else:
                        for buy_signal in signals[ticker]['buy_signals']:
                            if buy_signal['date'] == date:
                                # 포지션 크기 결정 (총 자산의 10% 또는 사용 가능 현금의 20% 중 작은 값)
                                portfolio_value = cash + sum([
                                    pos['shares'] * processed_data[t].loc[date, 'Close']
                                    for t, pos in positions.items()
                                    if date in processed_data[t].index
                                ])

                                max_position_value = min(
                                    portfolio_value * 0.1,  # 총 자산의 10%
                                    cash * 0.2  # 현금의 20%
                                )

                                if max_position_value >= current_price * 100:  # 최소 100주
                                    # 매수 실행
                                    cost = current_price * (1 + self.config['commission_rate'] + self.config['slippage'])
                                    shares = int(max_position_value / cost)

                                    if shares > 0:
                                        total_cost = shares * cost

                                        if cash >= total_cost:
                                            positions[ticker] = {
                                                'shares': shares,
                                                'avg_price': cost,
                                                'entry_date': date
                                            }

                                            trades.append({
                                                'ticker': ticker,
                                                'type': 'BUY',
                                                'date': date,
                                                'price': current_price,
                                                'shares': shares,
                                                'amount': total_cost,
                                                'pnl': 0
                                            })

                                            cash -= total_cost
                                            day_trades += 1
                                            break

                # 포트폴리오 가치 계산
                positions_value = 0
                for ticker, position in positions.items():
                    if date in processed_data[ticker].index:
                        current_price = processed_data[ticker].loc[date, 'Close']
                        positions_value += position['shares'] * current_price

                portfolio_value = cash + positions_value
                portfolio_values.append({
                    'date': date,
                    'cash': cash,
                    'positions_value': positions_value,
                    'total_value': portfolio_value,
                    'day_trades': day_trades
                })

                # 진행상황 출력 (일주일에 한번)
                if i % 5 == 0:
                    self._log(f"  [진행] {date.strftime('%Y-%m-%d')}: 포트폴리오 가치 {portfolio_value:,.0f}원 (거래 {day_trades}건)")

            except Exception as e:
                self._log(f"  [실패] {date} 백테스트 실패: {e}")

        self._log("[성공] 백테스트 실행 완료")

        return {
            'portfolio_values': portfolio_values,
            'trades': trades,
            'final_positions': positions
        }

    def _analyze_results(self, backtest_results):
        """백테스트 결과 분석"""
        self._log("[분석] 백테스트 결과 분석 중...")

        portfolio_values = backtest_results['portfolio_values']
        trades = backtest_results['trades']

        if not portfolio_values:
            self._log("[실패] 분석할 데이터가 없습니다.")
            return

        # 기본 통계
        initial_cash = self.config['initial_cash']
        final_value = portfolio_values[-1]['total_value']
        total_return = (final_value - initial_cash) / initial_cash

        # 일별 수익률 계산
        daily_returns = []
        for i in range(1, len(portfolio_values)):
            prev_value = portfolio_values[i-1]['total_value']
            curr_value = portfolio_values[i]['total_value']
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)

        # 위험 지표
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        sharpe_ratio = (np.mean(daily_returns) * 252) / volatility if volatility > 0 else 0

        # 최대 낙폭 계산
        peak = initial_cash
        max_drawdown = 0
        for pv in portfolio_values:
            if pv['total_value'] > peak:
                peak = pv['total_value']
            drawdown = (peak - pv['total_value']) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # 거래 분석
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']

        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) < 0]
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0

        # 결과 출력
        self._log("="*80)
        self._log("[요약] 백테스트 결과 요약")
        self._log("="*80)
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

        if winning_trades:
            avg_profit = np.mean([t['pnl'] for t in winning_trades])
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

    def run_backtest(self, universe=None, start_date="2023-01-01", end_date="2023-12-31"):
        """백테스트 실행"""
        overall_start_time = time.time()

        try:
            self._log("="*80)
            self._log("[시작] MongoDB 기반 통합 백테스트 실행")
            self._log(f"[기간] 기간: {start_date} ~ {end_date}")

            # MongoDB 연결 시도 (실패해도 계속 진행)
            mongodb_connected = self._connect_mongodb()

            if universe is None:
                if mongodb_connected:
                    universe = self._get_nasdaq_universe(limit=5)  # 테스트용으로 5개 종목
                else:
                    universe = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # 기본 종목
                    self._log(f"[기본] MongoDB 연결 실패 - 기본 종목 사용: {universe}")

            self._log(f"[정보] 대상 종목: {universe}")
            self._log("="*80)

            # Phase 1: 데이터 로드 (MongoDB 우선, 실패시 Yahoo Finance)
            self._log("\n[Phase 1] Data Layer - 실제 데이터 로드")
            market_data = self._load_mongodb_data(universe, start_date, end_date)

            if not market_data:
                self._log("[경고] MongoDB 데이터 없음 - Yahoo Finance 사용")
                market_data = self._load_yfinance_fallback(universe, start_date, end_date)

            if not market_data:
                self._log("[실패] 로드된 데이터가 없습니다.")
                return None

            # Phase 2: 기술지표 계산
            self._log("\n[Phase 2] Indicator Layer - 기술지표 계산")
            processed_data = self._add_indicators(market_data)

            # Phase 3: 매매 신호 생성
            self._log("\n[Phase 3] Strategy Layer - 신호 생성")
            signals = self._generate_signals(processed_data)

            # Phase 4: 백테스트 실행
            self._log("\n[Phase 4] Service Layer - 백테스트 실행")
            backtest_results = self._run_simple_backtest(processed_data, signals)

            # Phase 5: 결과 분석
            self._log("\n[Phase 5] 결과 분석")
            self._analyze_results(backtest_results)

            total_time = time.time() - overall_start_time
            self._log(f"\n[시간] 전체 실행 시간: {total_time:.2f}초")
            self._log("[완료] MongoDB 기반 통합 백테스트 완료!")

            return backtest_results

        except Exception as e:
            self._log(f"[실패] 백테스트 실행 실패: {e}")
            return None
        finally:
            if self.mongodb_client:
                self.mongodb_client.close()

    def _log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)


def main():
    """메인 실행 함수"""
    try:
        print("[시작] MongoDB 기반 통합 백테스트 시작")

        # 백테스트 실행
        backtest = MongoDBIntegratedBacktest()

        # NasDataBase 데이터로 백테스트 실행
        universe = None  # None이면 자동으로 NASDAQ 종목 선택
        results = backtest.run_backtest(universe, "2023-01-01", "2023-12-31")

        if results:
            print("\n[성공] MongoDB 기반 통합 백테스트 완료")
        else:
            print("\n[실패] 백테스트 실행 실패")

    except Exception as e:
        print(f"\n[실패] 메인 실행 실패: {e}")


if __name__ == "__main__":
    main()