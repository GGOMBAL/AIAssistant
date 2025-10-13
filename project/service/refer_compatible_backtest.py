"""
Refer Compatible Backtest Service
refer/SystemBackTest/BackTest/TestMakTrade_D.py와 완전히 호환되는 백테스트 서비스
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ReferCompatibleBacktest:
    """
    refer의 TestMakTrade_D와 동일한 인터페이스를 가진 백테스트 서비스
    """

    def __init__(self, Universe: List[str], Market: str, Area: str, df: Dict[str, pd.DataFrame],
                 risk: float = 0.03, MaxStockCnt: int = 10, TimeFrame: str = 'D'):
        """
        refer의 TestMakTrade_D.__init__과 동일한 인터페이스

        Args:
            Universe: 종목 리스트
            Market: 시장 (US, KR 등)
            Area: 지역 (US, KR 등)
            df: 각 종목별 DataFrame을 담은 딕셔너리
            risk: 리스크 비율 (기본 3%)
            MaxStockCnt: 최대 보유 종목 수
            TimeFrame: 타임프레임 (일봉='D')
        """

        # 필수 컬럼 필터링 (refer와 동일)
        FILTERED_COL = ['open', 'high', 'low', 'close', 'ADR', 'LossCutPrice', 'TargetPrice',
                       'BuySig', 'SellSig', 'signal', 'Type', 'RS_4W', 'Rev_Yoy_Growth',
                       'Eps_Yoy_Growth', 'Sector', 'Industry']

        # 각 종목 DataFrame 필터링
        for ticker in Universe:
            if ticker in df:
                # 존재하는 컬럼만 필터링
                available_cols = [col for col in FILTERED_COL if col in df[ticker].columns]
                df[ticker] = df[ticker][available_cols]

        # 설정값 저장
        self.MessageOut = False
        self.RebuyingStocks = True
        self.SellWhipsaw = False
        self.MaxStockList = MaxStockCnt
        self.Std_Risk = risk
        self.Init_Risk = 0.03  # 초기 손절 3%
        self.Slippage = 0.002  # 0.2% 슬리피지
        self.Market = Market
        self.Area = Area
        self.df = df
        self.Universe = Universe

        # MultiIndex DataFrame 생성 (refer와 동일)
        df_combined = pd.concat(self.df, axis=1, keys=self.Universe)

        # 컬럼 이름 설정
        if not isinstance(df_combined.columns, pd.MultiIndex):
            df_combined.columns = pd.MultiIndex.from_product(
                [self.Universe, available_cols],
                names=['Ticker', 'Field']
            )
        else:
            df_combined.columns.names = ['Ticker', 'Field']

        # 인덱스 설정
        custom_index = self.df[self.Universe[0]].index if self.Universe else pd.DatetimeIndex([])
        self.assets = [f'ASSET{i}' for i in range(self.MaxStockList)]

        # 결과 DataFrame 생성
        columns = pd.MultiIndex.from_product(
            [self.assets,
             ['Balance', 'Position', 'AGain', 'Duration', 'LossCut', 'AvgPrice', 'Risk']]
        )

        columns = columns.append(
            pd.MultiIndex.from_product(
                [['Account'],
                 ['Stocks', 'Cash', 'Balance', 'Market', 'WinCnt', 'LossCnt', 'GainW', 'GainL', 'Description']]
            )
        )

        result_df = pd.DataFrame(index=custom_index, columns=columns)

        self.df_Comb = df_combined
        self.df_Bal = result_df

        # 색상 코드 (refer와 동일)
        self.CODE = '\033[95m'
        self.NAME = '\033[94m'
        self.COLOR = '\033[91m'
        self.COLOR2 = '\033[92m'
        self.COLOR3 = '\033[93m'
        self.RESET = '\033[0m'

    def trade_stocks(self, initial_cash: float = 100000.0):
        """
        백테스트 실행 (refer의 trade_stocks와 동일한 로직)

        Args:
            initial_cash: 초기 자금

        Returns:
            result_df: 백테스트 결과 DataFrame
        """

        trading_df = self.df_Comb
        result_df = self.df_Bal.copy()

        # 거래일과 종목 리스트
        dates = trading_df.index
        stock_list = pd.Index(self.Universe)

        # NumPy 배열로 변환 (성능 최적화)
        account_values = result_df.loc[:, ('Account', slice(None))].values.astype(float)
        asset_positions = result_df.loc[:, (self.assets, 'Position')].values
        asset_balance = result_df.loc[:, (self.assets, 'Balance')].values.astype(float)
        asset_a_gain = result_df.loc[:, (self.assets, 'AGain')].values.astype(float)
        asset_duration = result_df.loc[:, (self.assets, 'Duration')].values.astype(float)
        asset_losscut = result_df.loc[:, (self.assets, 'LossCut')].values.astype(float)
        asset_avgprice = result_df.loc[:, (self.assets, 'AvgPrice')].values.astype(float)
        asset_risk = result_df.loc[:, (self.assets, 'Risk')].values.astype(float)

        # 초기 설정 (컬럼 순서: Balance, Cash, Stocks, Market, WinCnt, LossCnt, AvgWin, AvgLoss)
        account_values[0, 0] = initial_cash  # Balance (전체 자산)
        account_values[0, 1] = initial_cash  # Cash
        account_values[0, 2] = 0  # Stocks
        account_values[0, 3] = 0  # Market
        account_values[0, 4] = 0  # WinCnt
        account_values[0, 5] = 0  # LossCnt
        account_values[0, 6] = 0  # AvgWin
        account_values[0, 7] = 0  # AvgLoss

        # 모든 asset 배열도 초기화
        for i in range(len(dates)):
            for j in range(self.MaxStockList):
                asset_balance[i, j] = np.nan
                asset_a_gain[i, j] = np.nan
                asset_duration[i, j] = np.nan
                asset_losscut[i, j] = np.nan
                asset_avgprice[i, j] = np.nan
                asset_risk[i, j] = np.nan

        # 진행 상황 표시를 위한 변수
        total_days = len(dates) - 1
        progress_interval = max(1, total_days // 5)  # 5번 진행률 표시

        for i in range(1, len(dates)):
            date = dates[i]

            # 진행 상황 표시 (20%, 40%, 60%, 80%, 100%)
            if (i % progress_interval == 0 or i == total_days) and i > 0:
                current_positions = [pos for pos in asset_positions[i-1] if not pd.isna(pos)]
                position_cnt = len(current_positions)
                balance = account_values[i-1, 0] if account_values[i-1, 0] > 0 else account_values[i-2, 0]  # Balance
                cash = account_values[i-1, 1]  # Cash
                win_cnt = account_values[i-1, 4]  # WinCnt
                loss_cnt = account_values[i-1, 5]  # LossCnt
                cash_ratio = (cash / balance * 100) if balance > 0 else 100
                total_trades = win_cnt + loss_cnt
                win_rate = (win_cnt / total_trades * 100) if total_trades > 0 else 0

                print(f"{date.strftime('%Y-%m-%d')} - Balance: ${balance:,.0f}, "
                      f"Cash: {cash_ratio:.1f}%, "
                      f"Positions: {position_cnt}/{self.MaxStockList}, "
                      f"W/L: {int(win_cnt)}/{int(loss_cnt)} ({win_rate:.1f}%)")

            # 전일 포지션 및 계좌 정보 복사
            asset_positions[i] = asset_positions[i-1]
            asset_balance[i] = asset_balance[i-1]
            asset_a_gain[i] = asset_a_gain[i-1]
            asset_duration[i] = asset_duration[i-1]
            asset_losscut[i] = asset_losscut[i-1]
            asset_avgprice[i] = asset_avgprice[i-1]
            asset_risk[i] = asset_risk[i-1]

            # 전일 계좌 정보 전체 복사
            for k in range(8):  # Account has 8 fields
                account_values[i, k] = account_values[i-1, k]

            # 당일 데이터 추출
            try:
                OPEN = trading_df.loc[date, (slice(None), 'open')].values
                HIGH = trading_df.loc[date, (slice(None), 'high')].values
                LOW = trading_df.loc[date, (slice(None), 'low')].values
                CLOSE = trading_df.loc[date, (slice(None), 'close')].values
                CLOSE_old = trading_df.iloc[i-1][(slice(None), 'close')].values
                BUY_SIGNALS = trading_df.loc[date, (slice(None), 'BuySig')].values
                SELL_SIGNALS = trading_df.loc[date, (slice(None), 'SellSig')].values
                TARGETP = trading_df.loc[date, (slice(None), 'TargetPrice')].values
                ADR = trading_df.loc[date, (slice(None), 'ADR')].values
            except Exception as e:
                logger.warning(f"Data extraction error on {date}: {e}")
                continue

            # 현재 보유 포지션 확인
            current_positions = [pos for pos in asset_positions[i] if not pd.isna(pos)]
            position_cnt = len(current_positions)

            # 1. 매도 처리 (손절 또는 매도 신호)
            for asset_index in range(self.MaxStockList):
                position = asset_positions[i, asset_index]

                if not pd.isna(position):
                    stock_index = stock_list.get_loc(position)

                    # 손절 확인
                    if LOW[stock_index] < asset_losscut[i, asset_index]:
                        # 매도 가격 결정
                        if OPEN[stock_index] < asset_losscut[i, asset_index]:
                            sell_price = OPEN[stock_index]
                        else:
                            sell_price = asset_losscut[i, asset_index]

                        # 수익률 계산
                        if CLOSE_old[stock_index] > 0:
                            gain = (sell_price - CLOSE_old[stock_index]) / CLOSE_old[stock_index]
                        else:
                            gain = -0.999

                        # 매도 실행
                        asset_a_gain_new = asset_a_gain[i, asset_index] * (1 + gain)
                        cash_back = asset_balance[i, asset_index] * asset_a_gain_new * (1 - self.Slippage)

                        # 계좌 업데이트
                        account_values[i, 1] += cash_back  # Cash 증가
                        if asset_a_gain_new > 1:
                            account_values[i, 4] += 1  # Win count
                        else:
                            account_values[i, 5] += 1  # Loss count

                        # 포지션 초기화
                        asset_positions[i, asset_index] = np.nan
                        asset_balance[i, asset_index] = np.nan
                        asset_a_gain[i, asset_index] = np.nan
                        asset_duration[i, asset_index] = np.nan
                        asset_losscut[i, asset_index] = np.nan
                        asset_avgprice[i, asset_index] = np.nan
                        asset_risk[i, asset_index] = np.nan

                        if self.MessageOut:
                            logger.info(f"{date} SELL {position} at {sell_price:.2f} (LossCut)")

                    # 매도 신호 확인
                    elif SELL_SIGNALS[stock_index] == 1:
                        sell_price = OPEN[stock_index]

                        # 수익률 계산
                        if CLOSE_old[stock_index] > 0:
                            gain = (sell_price - CLOSE_old[stock_index]) / CLOSE_old[stock_index]
                        else:
                            gain = -0.999

                        # 매도 실행
                        asset_a_gain_new = asset_a_gain[i, asset_index] * (1 + gain)
                        cash_back = asset_balance[i, asset_index] * asset_a_gain_new * (1 - self.Slippage)

                        # 계좌 업데이트
                        account_values[i, 1] += cash_back
                        if asset_a_gain_new > 1:
                            account_values[i, 4] += 1
                        else:
                            account_values[i, 5] += 1

                        # 포지션 초기화
                        asset_positions[i, asset_index] = np.nan
                        asset_balance[i, asset_index] = np.nan
                        asset_a_gain[i, asset_index] = np.nan
                        asset_duration[i, asset_index] = np.nan
                        asset_losscut[i, asset_index] = np.nan
                        asset_avgprice[i, asset_index] = np.nan
                        asset_risk[i, asset_index] = np.nan

                        if self.MessageOut:
                            logger.info(f"{date} SELL {position} at {sell_price:.2f} (Signal)")

                    else:
                        # 포지션 유지 (업데이트)
                        if CLOSE_old[stock_index] > 0:
                            gain = (CLOSE[stock_index] - CLOSE_old[stock_index]) / CLOSE_old[stock_index]
                        else:
                            gain = 0

                        asset_a_gain[i, asset_index] *= (1 + gain)
                        asset_balance[i, asset_index] *= (1 + gain)
                        asset_duration[i, asset_index] += 1

            # 2. 매수 처리
            current_positions = [pos for pos in asset_positions[i] if not pd.isna(pos)]
            position_cnt = len(current_positions)
            available_slots = self.MaxStockList - position_cnt

            if available_slots > 0:
                # 매수 후보 찾기
                buy_candidates = []
                for j, ticker in enumerate(self.Universe):
                    if BUY_SIGNALS[j] == 1 and ticker not in current_positions:
                        buy_candidates.append((ticker, j))

                # 매수 실행 (가능한 슬롯만큼)
                for ticker, stock_index in buy_candidates[:available_slots]:
                    # 빈 슬롯 찾기
                    for asset_index in range(self.MaxStockList):
                        if pd.isna(asset_positions[i, asset_index]):
                            # 매수 가격 결정
                            if TARGETP[stock_index] >= OPEN[stock_index] and TARGETP[stock_index] <= HIGH[stock_index]:
                                buy_price = TARGETP[stock_index]
                            elif TARGETP[stock_index] < OPEN[stock_index]:
                                buy_price = OPEN[stock_index]
                            else:
                                buy_price = OPEN[stock_index]

                            # 슬리피지 적용
                            buy_price *= (1 + self.Slippage)

                            # 포지션 크기 결정 (총 자산의 20% 또는 10%)
                            position_ratio = 0.1 if ADR[stock_index] >= 5 else 0.2
                            position_size = account_values[i, 2] * position_ratio  # Total balance 기준

                            # 현금이 부족한 경우
                            if position_size > account_values[i, 1]:
                                position_size = account_values[i, 1]

                            if position_size < account_values[i, 2] * 0.01:  # 1% 미만이면 스킵
                                break

                            # 매수 실행
                            account_values[i, 1] -= position_size  # Cash 감소

                            # 첫날 수익률
                            if CLOSE_old[stock_index] > 0:
                                first_gain = (CLOSE[stock_index] - buy_price) / buy_price
                            else:
                                first_gain = 0

                            # 포지션 정보 설정
                            asset_positions[i, asset_index] = ticker
                            asset_balance[i, asset_index] = position_size * (1 + first_gain)
                            asset_a_gain[i, asset_index] = 1 + first_gain
                            asset_duration[i, asset_index] = 1
                            asset_losscut[i, asset_index] = buy_price * (1 - self.Init_Risk)
                            asset_avgprice[i, asset_index] = buy_price
                            asset_risk[i, asset_index] = self.Init_Risk

                            if self.MessageOut:
                                logger.info(f"{date} BUY {ticker} at {buy_price:.2f}")

                            break

            # 3. 계좌 잔액 업데이트
            account_values[i, 0] = np.nansum(asset_balance[i])  # Stock value
            account_values[i, 2] = account_values[i, 0] + account_values[i, 1]  # Total balance

            # 진행 상황 출력
            if i % 50 == 0 or i == len(dates) - 1:
                total_balance = account_values[i, 2] if not pd.isna(account_values[i, 2]) else 0
                cash_ratio = account_values[i, 1] / total_balance * 100 if total_balance > 0 else 0
                win_cnt = int(account_values[i, 4]) if not pd.isna(account_values[i, 4]) else 0
                loss_cnt = int(account_values[i, 5]) if not pd.isna(account_values[i, 5]) else 0
                win_ratio = win_cnt / (win_cnt + loss_cnt) * 100 if (win_cnt + loss_cnt) > 0 else 0

                print(f"{date.strftime('%Y-%m-%d')} - "
                      f"Balance: ${total_balance:,.0f}, "
                      f"Cash: {cash_ratio:.1f}%, "
                      f"Positions: {position_cnt}/{self.MaxStockList}, "
                      f"W/L: {win_cnt}/{loss_cnt} ({win_ratio:.1f}%)")

        # 결과 DataFrame에 값 저장
        result_df.loc[:, ('Account', slice(None))] = account_values
        result_df.loc[:, (self.assets, 'Position')] = asset_positions
        result_df.loc[:, (self.assets, 'Balance')] = asset_balance
        result_df.loc[:, (self.assets, 'AGain')] = asset_a_gain
        result_df.loc[:, (self.assets, 'Duration')] = asset_duration
        result_df.loc[:, (self.assets, 'LossCut')] = asset_losscut
        result_df.loc[:, (self.assets, 'AvgPrice')] = asset_avgprice
        result_df.loc[:, (self.assets, 'Risk')] = asset_risk

        return result_df