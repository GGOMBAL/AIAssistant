"""
MongoDB Data Loader for Visualization
MongoDB에서 직접 데이터를 로드하여 시각화에 사용

Features:
- MongoDB 직접 연결
- 일간/주간 데이터 로드
- 시그널 데이터 조회
- 백테스트 결과 로드
- 데이터 캐싱
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from project.database.mongodb_operations import MongoDBOperations

logger = logging.getLogger(__name__)

class MongoDBDataLoader:
    """
    MongoDB 데이터 로더 클래스

    시각화를 위한 데이터를 MongoDB에서 직접 로드합니다.
    """

    def __init__(self, db_address: str = "MONGODB_LOCAL"):
        """
        초기화

        Args:
            db_address: MongoDB 주소 설정 키
        """
        self.db = MongoDBOperations(db_address=db_address)
        self.cache = {}  # 데이터 캐싱

        # 데이터베이스 이름 매핑
        self.db_names = {
            'US': {
                'NASDAQ': {
                    'daily': 'NasDataBase_D',
                    'weekly': 'NasDataBase_W',
                    'rs': 'NasDataBase_RS',
                    'fundamental': 'NasDataBase_F',
                    'earnings': 'NasDataBase_E'
                },
                'NYSE': {
                    'daily': 'NysDataBase_D',
                    'weekly': 'NysDataBase_W',
                    'rs': 'NysDataBase_RS',
                    'fundamental': 'NysDataBase_F',
                    'earnings': 'NysDataBase_E'
                }
            },
            'KR': {
                'KOSPI': {
                    'daily': 'KospiDataBase_D',
                    'weekly': 'KospiDataBase_W',
                    'rs': 'KospiDataBase_RS',
                    'fundamental': 'KospiDataBase_F'
                },
                'KOSDAQ': {
                    'daily': 'KosdaqDataBase_D',
                    'weekly': 'KosdaqDataBase_W',
                    'rs': 'KosdaqDataBase_RS',
                    'fundamental': 'KosdaqDataBase_F'
                }
            },
            'HK': {
                'HSI': {
                    'daily': 'HkDataBase_D',
                    'weekly': 'HkDataBase_W',
                    'rs': 'HkDataBase_RS',
                    'fundamental': 'HkDataBase_F'
                }
            }
        }

        logger.info(f"MongoDB Data Loader initialized with {db_address}")

    def load_stock_data(
        self,
        ticker: str,
        market: str = "NASDAQ",
        data_type: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        주식 데이터 로드

        Args:
            ticker: 종목 코드
            market: 시장 (NASDAQ, NYSE, KOSPI, KOSDAQ, HSI)
            data_type: 데이터 타입 (daily, weekly, rs, fundamental, earnings)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            limit: 데이터 제한

        Returns:
            주식 데이터 DataFrame
        """
        try:
            # 캐시 키 생성
            cache_key = f"{ticker}_{market}_{data_type}_{start_date}_{end_date}"
            if cache_key in self.cache:
                logger.info(f"Returning cached data for {ticker}")
                return self.cache[cache_key]

            # 데이터베이스 이름 결정
            region = self._get_region(market)
            if region not in self.db_names:
                logger.error(f"Unknown region for market {market}")
                return pd.DataFrame()

            if market not in self.db_names[region]:
                logger.error(f"Unknown market {market}")
                return pd.DataFrame()

            db_name = self.db_names[region][market].get(data_type)
            if not db_name:
                logger.error(f"No database for {market} {data_type}")
                return pd.DataFrame()

            # Collection 이름 (MongoDB는 'A' prefix 사용)
            collection_name = f"A{ticker}"

            # 쿼리 생성
            query = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter['$gte'] = pd.to_datetime(start_date)
                if end_date:
                    date_filter['$lte'] = pd.to_datetime(end_date)
                if date_filter:
                    query['Date'] = date_filter

            # 데이터 조회
            df = self.db.execute_query(
                db_name=db_name,
                collection_name=collection_name,
                query=query,
                limit=limit
            )

            if df.empty:
                logger.warning(f"No data found for {ticker} in {db_name}")
                return df

            # 데이터 후처리
            df = self._process_stock_data(df, data_type)

            # 캐싱
            self.cache[cache_key] = df

            logger.info(f"Loaded {len(df)} rows for {ticker} from {db_name}")
            return df

        except Exception as e:
            logger.error(f"Error loading stock data for {ticker}: {e}")
            return pd.DataFrame()

    def load_multiple_stocks(
        self,
        tickers: List[str],
        market: str = "NASDAQ",
        data_type: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목 데이터 동시 로드

        Args:
            tickers: 종목 코드 리스트
            market: 시장
            data_type: 데이터 타입
            start_date: 시작일
            end_date: 종료일

        Returns:
            종목별 DataFrame 딕셔너리
        """
        results = {}

        for ticker in tickers:
            df = self.load_stock_data(
                ticker=ticker,
                market=market,
                data_type=data_type,
                start_date=start_date,
                end_date=end_date
            )

            if not df.empty:
                results[ticker] = df

        logger.info(f"Loaded data for {len(results)}/{len(tickers)} stocks")
        return results

    def load_backtest_results(
        self,
        backtest_id: Optional[str] = None,
        strategy_name: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict:
        """
        백테스트 결과 로드

        Args:
            backtest_id: 백테스트 ID
            strategy_name: 전략 이름
            date: 백테스트 날짜

        Returns:
            백테스트 결과 딕셔너리
        """
        try:
            # 백테스트 결과는 별도 컬렉션에 저장
            db_name = "BacktestResults"
            collection_name = "Results"

            # 쿼리 생성
            query = {}
            if backtest_id:
                query['backtest_id'] = backtest_id
            if strategy_name:
                query['strategy_name'] = strategy_name
            if date:
                query['date'] = pd.to_datetime(date)

            # 최신 결과 조회
            df = self.db.execute_query(
                db_name=db_name,
                collection_name=collection_name,
                query=query,
                limit=1
            )

            if df.empty:
                logger.warning("No backtest results found")
                return {}

            # DataFrame을 딕셔너리로 변환
            result = df.iloc[0].to_dict()

            # JSON 문자열 파싱
            for key in ['portfolio_value', 'returns', 'trades']:
                if key in result and isinstance(result[key], str):
                    try:
                        result[key] = json.loads(result[key])
                    except:
                        pass

            return result

        except Exception as e:
            logger.error(f"Error loading backtest results: {e}")
            return {}

    def load_trading_signals(
        self,
        market: str = "NASDAQ",
        date: Optional[str] = None,
        signal_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        매매 시그널 데이터 로드

        Args:
            market: 시장
            date: 시그널 날짜
            signal_type: 시그널 타입 (BUY/SELL)

        Returns:
            시그널 DataFrame
        """
        try:
            # 시그널은 별도 컬렉션에 저장
            db_name = f"{market}_Signals"
            collection_name = "DailySignals"

            # 쿼리 생성
            query = {}
            if date:
                query['Date'] = pd.to_datetime(date)
            if signal_type:
                query['SignalType'] = signal_type

            # 시그널 조회
            df = self.db.execute_query(
                db_name=db_name,
                collection_name=collection_name,
                query=query
            )

            if df.empty:
                logger.info(f"No signals found for {market} on {date}")
                return df

            # 데이터 정리
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error loading trading signals: {e}")
            return pd.DataFrame()

    def load_portfolio_data(
        self,
        portfolio_id: str,
        date: Optional[str] = None
    ) -> Dict:
        """
        포트폴리오 데이터 로드

        Args:
            portfolio_id: 포트폴리오 ID
            date: 조회 날짜

        Returns:
            포트폴리오 데이터 딕셔너리
        """
        try:
            db_name = "Portfolio"
            collection_name = portfolio_id

            # 쿼리 생성
            query = {}
            if date:
                query['Date'] = pd.to_datetime(date)

            # 최신 포트폴리오 데이터 조회
            df = self.db.execute_query(
                db_name=db_name,
                collection_name=collection_name,
                query=query,
                limit=1
            )

            if df.empty:
                logger.warning(f"No portfolio data found for {portfolio_id}")
                return {}

            # DataFrame을 딕셔너리로 변환
            portfolio = df.iloc[0].to_dict()

            # Holdings 파싱
            if 'holdings' in portfolio and isinstance(portfolio['holdings'], str):
                try:
                    portfolio['holdings'] = json.loads(portfolio['holdings'])
                except:
                    pass

            return portfolio

        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            return {}

    def get_available_tickers(self, market: str = "NASDAQ") -> List[str]:
        """
        사용 가능한 종목 리스트 조회

        Args:
            market: 시장

        Returns:
            종목 코드 리스트
        """
        try:
            # 데이터베이스 이름 결정
            region = self._get_region(market)
            db_name = self.db_names[region][market]['daily']

            # Collection 이름 조회
            collections = self.db.get_collection_names(db_name)

            # 'A' prefix 제거
            tickers = [col[1:] for col in collections if col.startswith('A')]

            logger.info(f"Found {len(tickers)} tickers in {market}")
            return sorted(tickers)

        except Exception as e:
            logger.error(f"Error getting available tickers: {e}")
            return []

    def _get_region(self, market: str) -> str:
        """시장에서 지역 추출"""
        market_region_map = {
            'NASDAQ': 'US',
            'NYSE': 'US',
            'KOSPI': 'KR',
            'KOSDAQ': 'KR',
            'HSI': 'HK'
        }
        return market_region_map.get(market, 'US')

    def _process_stock_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        데이터 후처리

        Args:
            df: 원본 DataFrame
            data_type: 데이터 타입

        Returns:
            처리된 DataFrame
        """
        # MongoDB _id 컬럼 제거
        if '_id' in df.columns:
            df = df.drop('_id', axis=1)

        # Date 인덱스 설정
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)

        # 데이터 타입별 컬럼 매핑
        if data_type == 'daily':
            # MongoDB 컬럼명을 시각화용으로 변환
            column_mapping = {
                'ad_open': 'Open',
                'ad_high': 'High',
                'ad_low': 'Low',
                'ad_close': 'Close',
                'volume': 'Volume'
            }

            # 컬럼명 변경
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

            # 기술지표가 있다면 추가
            if 'SMA20' not in df.columns and 'Close' in df.columns:
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['SMA50'] = df['Close'].rolling(window=50).mean()
                df['SMA200'] = df['Close'].rolling(window=200).mean()

        elif data_type == 'weekly':
            column_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

        return df

    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        logger.info("Data cache cleared")

    def get_database_info(self) -> Dict:
        """
        데이터베이스 정보 조회

        Returns:
            데이터베이스 통계 정보
        """
        info = {}

        for region, markets in self.db_names.items():
            info[region] = {}

            for market, databases in markets.items():
                info[region][market] = {}

                for data_type, db_name in databases.items():
                    stats = self.db.get_database_stats(db_name)
                    info[region][market][data_type] = {
                        'database': db_name,
                        'collections': stats.get('collections_count', 0),
                        'size': stats.get('data_size', 0)
                    }

        return info

    def test_connection(self) -> bool:
        """
        MongoDB 연결 테스트

        Returns:
            연결 성공 여부
        """
        result = self.db.test_connection()
        return result.get('connected', False)

    def close(self):
        """연결 종료"""
        self.db.close()
        logger.info("MongoDB Data Loader connection closed")