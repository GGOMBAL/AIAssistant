"""
Interface Compatible Backtest Service
표준 인터페이스 규약을 준수하는 백테스트 서비스
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json

logger = logging.getLogger(__name__)


class InterfaceCompatibleBacktest:
    """
    표준 인터페이스를 준수하는 백테스트 서비스
    INTERFACE_SPECIFICATION.md의 규약을 따름
    """

    def __init__(self):
        """백테스트 서비스 초기화"""
        self.indicator_data = {}
        self.strategy_output = {}
        self.universe = []

    def load_indicator_data(self,
                           df_D: Dict[str, Dict] = None,
                           df_W: Dict[str, Dict] = None,
                           df_RS: Dict[str, Dict] = None,
                           df_E: Dict[str, Dict] = None,
                           df_F: Dict[str, Dict] = None) -> None:
        """
        Indicator Layer에서 Strategy Layer로 전달되는 표준 인터페이스 데이터 로드

        Args:
            df_D: 일간 데이터 (Daily indicators)
            df_W: 주간 데이터 (Weekly indicators)
            df_RS: 상대강도 데이터 (Relative Strength)
            df_E: 실적 데이터 (Earnings)
            df_F: 펀더멘털 데이터 (Fundamental)

        각 데이터는 다음 구조를 따름:
        {
            "TICKER": {
                "columns": [...],
                "index": [...],
                "data": [[...], ...]
            }
        }
        """

        self.indicator_data = {
            'df_D': df_D or {},
            'df_W': df_W or {},
            'df_RS': df_RS or {},
            'df_E': df_E or {},
            'df_F': df_F or {}
        }

        # 모든 티커 수집
        tickers = set()
        for df_name, df_dict in self.indicator_data.items():
            if df_dict:
                tickers.update(df_dict.keys())

        self.all_tickers = sorted(list(tickers))
        logger.info(f"[INTERFACE] Loaded indicator data for {len(self.all_tickers)} tickers")

    def load_strategy_output(self, df_dump: Dict[str, Dict], universe: Dict[str, Any]) -> None:
        """
        Strategy Layer 출력 인터페이스 데이터 로드

        Args:
            df_dump: 매매 후보 종목 데이터
                {
                    "TICKER": {
                        "columns": ["open", "high", "low", "close", "ADR",
                                   "LossCutPrice", "TargetPrice", "BuySig", "SellSig", ...],
                        "index": [...],
                        "data": [[...], ...]
                    }
                }
            universe: 선정된 종목 리스트
                {
                    "Universe": ["TICKER1", "TICKER2", ...],
                    "count": 58
                }
        """

        self.strategy_output = df_dump or {}
        self.universe = universe.get('Universe', []) if universe else []

        logger.info(f"[INTERFACE] Loaded strategy output: {len(self.strategy_output)} candidates, Universe: {len(self.universe)} stocks")

    def convert_to_dataframe(self, interface_data: Dict[str, Dict]) -> Dict[str, pd.DataFrame]:
        """
        표준 인터페이스 데이터를 DataFrame으로 변환

        Args:
            interface_data: 표준 인터페이스 형식의 데이터

        Returns:
            Dict[str, pd.DataFrame]: 티커별 DataFrame
        """

        df_dict = {}

        for ticker, data in interface_data.items():
            if not data or 'columns' not in data or 'index' not in data or 'data' not in data:
                logger.warning(f"[INTERFACE] Invalid data structure for {ticker}")
                continue

            try:
                # DataFrame 생성
                df = pd.DataFrame(
                    data=data['data'],
                    index=pd.to_datetime(data['index']),
                    columns=data['columns']
                )

                df_dict[ticker] = df

            except Exception as e:
                logger.error(f"[INTERFACE] Failed to convert {ticker} to DataFrame: {e}")

        return df_dict

    def convert_from_dataframe(self, df_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        DataFrame을 표준 인터페이스 형식으로 변환

        Args:
            df_dict: 티커별 DataFrame 딕셔너리

        Returns:
            Dict[str, Dict]: 표준 인터페이스 형식 데이터
        """

        interface_data = {}

        for ticker, df in df_dict.items():
            if df is None or df.empty:
                continue

            try:
                # 인덱스를 ISO 8601 형식 문자열로 변환
                if isinstance(df.index, pd.DatetimeIndex):
                    index_list = [dt.strftime('%Y-%m-%dT%H:%M:%S.000') for dt in df.index]
                else:
                    index_list = df.index.tolist()

                # 데이터를 중첩 리스트로 변환
                data_list = df.values.tolist()

                interface_data[ticker] = {
                    "columns": df.columns.tolist(),
                    "index": index_list,
                    "data": data_list
                }

            except Exception as e:
                logger.error(f"[INTERFACE] Failed to convert DataFrame for {ticker}: {e}")

        return interface_data

    def run_backtest(self,
                    start_date: str,
                    end_date: str,
                    initial_cash: float = 100000,
                    max_positions: int = 10,
                    risk_per_trade: float = 0.03) -> Dict[str, Any]:
        """
        표준 인터페이스 데이터로 백테스트 실행

        Args:
            start_date: 백테스트 시작일 (YYYY-MM-DD)
            end_date: 백테스트 종료일 (YYYY-MM-DD)
            initial_cash: 초기 자금
            max_positions: 최대 보유 종목 수
            risk_per_trade: 거래당 리스크 비율

        Returns:
            백테스트 결과
        """

        logger.info(f"[BACKTEST] Starting interface-compatible backtest")
        logger.info(f"[BACKTEST] Period: {start_date} to {end_date}")
        logger.info(f"[BACKTEST] Initial cash: ${initial_cash:,.0f}")

        # Strategy output을 DataFrame으로 변환
        df_candidates = self.convert_to_dataframe(self.strategy_output)

        if not df_candidates:
            logger.warning("[BACKTEST] No candidate stocks found")
            return self._empty_results(initial_cash)

        # ReferCompatibleBacktest 사용하여 실제 백테스트 실행
        from project.service.refer_compatible_backtest import ReferCompatibleBacktest

        # Universe 사용 (strategy layer output)
        universe_to_use = self.universe if self.universe else list(df_candidates.keys())

        # 백테스트 서비스 초기화
        backtest_service = ReferCompatibleBacktest(
            Universe=universe_to_use,
            Market='US',
            Area='US',
            df=df_candidates,
            risk=risk_per_trade,
            MaxStockCnt=max_positions,
            TimeFrame='D'
        )

        # 백테스트 실행
        try:
            result_df = backtest_service.trade_stocks(initial_cash=initial_cash)

            if result_df is None or result_df.empty:
                logger.warning("[BACKTEST] No trading results generated")
                return self._empty_results(initial_cash)

            # 결과 분석
            results = self._analyze_results(result_df, initial_cash, start_date, end_date)

            logger.info(f"[BACKTEST] Completed: Return={results['total_return']:.2f}%, Trades={results['total_trades']}")

            return results

        except Exception as e:
            logger.error(f"[BACKTEST] Error during execution: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return self._empty_results(initial_cash)

    def _analyze_results(self, result_df: pd.DataFrame, initial_cash: float,
                        start_date: str, end_date: str) -> Dict[str, Any]:
        """백테스트 결과 분석"""

        # 마지막 날짜의 계좌 정보 추출
        last_idx = -1
        final_balance = result_df.loc[result_df.index[last_idx], ('Account', 'Balance')]
        final_cash = result_df.loc[result_df.index[last_idx], ('Account', 'Cash')]
        final_stocks = result_df.loc[result_df.index[last_idx], ('Account', 'Stocks')]
        win_count = result_df.loc[result_df.index[last_idx], ('Account', 'WinCnt')]
        loss_count = result_df.loc[result_df.index[last_idx], ('Account', 'LossCnt')]

        # 계산
        total_return = ((final_balance - initial_cash) / initial_cash * 100) if initial_cash > 0 else 0
        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

        return {
            'period': f"{start_date} ~ {end_date}",
            'initial_cash': initial_cash,
            'final_balance': float(final_balance) if not pd.isna(final_balance) else initial_cash,
            'final_cash': float(final_cash) if not pd.isna(final_cash) else initial_cash,
            'final_stocks': float(final_stocks) if not pd.isna(final_stocks) else 0,
            'total_return': total_return,
            'total_trades': int(total_trades),
            'winning_trades': int(win_count),
            'losing_trades': int(loss_count),
            'win_rate': win_rate,
            'result_dataframe': result_df,
            'universe_count': len(self.universe),
            'candidate_count': len(self.strategy_output)
        }

    def _empty_results(self, initial_cash: float) -> Dict[str, Any]:
        """빈 결과 반환"""
        return {
            'period': '',
            'initial_cash': initial_cash,
            'final_balance': initial_cash,
            'final_cash': initial_cash,
            'final_stocks': 0,
            'total_return': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'result_dataframe': pd.DataFrame(),
            'universe_count': 0,
            'candidate_count': 0
        }

    def validate_interfaces(self) -> Dict[str, List[str]]:
        """
        로드된 데이터의 인터페이스 규약 준수 여부 검증

        Returns:
            검증 결과 (경고 및 오류 메시지)
        """

        validation_results = {
            'errors': [],
            'warnings': []
        }

        # 필수 컬럼 정의 (INTERFACE_SPECIFICATION.md 기준)
        required_columns = {
            'df_D': ['Dclose', 'ADR', 'SMA20', 'SMA50', 'SMA200'],
            'df_W': ['Wclose', '52_H', '52_L'],
            'df_RS': ['RS_4W', 'RS_12W', 'Sector', 'Industry'],
            'df_dump': ['open', 'close', 'ADR', 'LossCutPrice', 'TargetPrice',
                       'BuySig', 'SellSig', 'signal']
        }

        # Indicator 데이터 검증
        for df_name, required_cols in required_columns.items():
            if df_name == 'df_dump':
                continue

            df_data = self.indicator_data.get(df_name, {})
            if not df_data:
                validation_results['warnings'].append(f"{df_name} is empty or not loaded")
                continue

            # 샘플 티커로 검증
            sample_ticker = list(df_data.keys())[0] if df_data else None
            if sample_ticker:
                ticker_data = df_data[sample_ticker]
                if 'columns' in ticker_data:
                    missing_cols = set(required_cols) - set(ticker_data['columns'])
                    if missing_cols:
                        validation_results['errors'].append(
                            f"{df_name}[{sample_ticker}] missing required columns: {missing_cols}"
                        )

        # Strategy output 검증
        if self.strategy_output:
            sample_ticker = list(self.strategy_output.keys())[0]
            ticker_data = self.strategy_output[sample_ticker]
            if 'columns' in ticker_data:
                missing_cols = set(required_columns['df_dump']) - set(ticker_data['columns'])
                if missing_cols:
                    validation_results['errors'].append(
                        f"df_dump[{sample_ticker}] missing required columns: {missing_cols}"
                    )

        # Universe 검증
        if not self.universe:
            validation_results['warnings'].append("Universe is empty")

        return validation_results


# 사용 예제
def example_usage():
    """표준 인터페이스를 사용한 백테스트 예제"""

    # 1. 백테스트 서비스 초기화
    backtest = InterfaceCompatibleBacktest()

    # 2. Indicator Layer 데이터 로드 (표준 인터페이스 형식)
    # 실제로는 JSON 파일이나 MongoDB에서 로드
    df_D = {
        "AAPL": {
            "columns": ["Dclose", "ADR", "SMA20", "SMA50", "SMA200"],
            "index": ["2023-01-01T00:00:00.000", "2023-01-02T00:00:00.000"],
            "data": [[150.0, 3.5, 148.0, 147.0, 145.0],
                    [152.0, 3.6, 149.0, 147.5, 145.5]]
        }
    }

    backtest.load_indicator_data(df_D=df_D)

    # 3. Strategy Layer 출력 로드
    df_dump = {
        "AAPL": {
            "columns": ["open", "close", "ADR", "LossCutPrice", "TargetPrice",
                       "BuySig", "SellSig", "signal"],
            "index": ["2023-01-01T00:00:00.000", "2023-01-02T00:00:00.000"],
            "data": [[149.0, 150.0, 3.5, 145.0, 160.0, 1, 0, 1],
                    [151.0, 152.0, 3.6, 147.0, 162.0, 0, 0, 0]]
        }
    }

    universe = {
        "Universe": ["AAPL"],
        "count": 1
    }

    backtest.load_strategy_output(df_dump, universe)

    # 4. 인터페이스 검증
    validation = backtest.validate_interfaces()
    if validation['errors']:
        print("Interface validation errors:", validation['errors'])

    # 5. 백테스트 실행
    results = backtest.run_backtest(
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_cash=100000,
        max_positions=10
    )

    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Win Rate: {results['win_rate']:.1f}%")

    return results


if __name__ == "__main__":
    example_usage()