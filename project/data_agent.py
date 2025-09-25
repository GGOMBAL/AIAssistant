"""
Data Agent - Multi-Agent Trading System

데이터 수집, 처리, 기술지표 계산을 담당하는 전문 에이전트
NasDataBase_D와 NysDataBase_D를 통합하여 처리

버전: 1.0
작성일: 2025-09-22
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import pymongo
import yaml
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

try:
    from simple_technical_indicators import SimpleTechnicalIndicators
except ImportError:
    print("[Data Agent] 기술지표 모듈을 찾을 수 없습니다.")


class DataAgent:
    """
    Data Agent

    MongoDB에서 NasDataBase_D와 NysDataBase_D 데이터를 로드하고
    기술지표를 계산하여 표준화된 형태로 제공
    """

    def __init__(self, config: Dict[str, Any]):
        """Data Agent 초기화"""
        self.config = config
        self.execution_log = []
        self.mongodb_client = None
        self.indicators = SimpleTechnicalIndicators()

        self._log("[Data Agent] 초기화 완료")

    def execute_data_loading(self,
                            start_date: str,
                            end_date: str,
                            nas_symbols: Optional[List[str]] = None,
                            nys_symbols: Optional[List[str]] = None,
                            prompt: str = "") -> Dict[str, pd.DataFrame]:
        """
        데이터 로딩 실행

        Args:
            start_date: 시작일
            end_date: 종료일
            nas_symbols: NASDAQ 종목 리스트
            nys_symbols: NYSE 종목 리스트
            prompt: 오케스트레이터로부터의 작업 지시

        Returns:
            로드된 시장 데이터
        """
        start_time = time.time()

        try:
            self._log("[Data Agent] 데이터 로딩 작업 시작")
            self._log(f"[Data Agent] 작업 지시 수신: {len(prompt)} 문자")

            # MongoDB 연결
            if not self._connect_mongodb():
                self._log("[Data Agent] MongoDB 연결 실패 - 대체 데이터 소스 시도")
                return self._load_fallback_data(start_date, end_date, nas_symbols, nys_symbols)

            # 종목 선택
            final_nas_symbols = self._select_nas_symbols(nas_symbols)
            final_nys_symbols = self._select_nys_symbols(nys_symbols)

            self._log(f"[Data Agent] 선택된 NASDAQ 종목: {final_nas_symbols}")
            self._log(f"[Data Agent] 선택된 NYSE 종목: {final_nys_symbols}")

            # 데이터 로드
            market_data = {}

            # NASDAQ 데이터 로드
            nas_data = self._load_market_data('NasDataBase_D', final_nas_symbols, start_date, end_date)
            market_data.update(nas_data)

            # NYSE 데이터 로드
            nys_data = self._load_market_data('NysDataBase_D', final_nys_symbols, start_date, end_date)
            market_data.update(nys_data)

            # 기술지표 계산
            processed_data = self._calculate_technical_indicators(market_data)

            # 데이터 품질 검증
            validated_data = self._validate_data_quality(processed_data)

            execution_time = time.time() - start_time
            self._log(f"[Data Agent] 데이터 로딩 완료 - 실행시간: {execution_time:.2f}초")
            self._log(f"[Data Agent] 총 {len(validated_data)}개 종목 데이터 준비 완료")

            return validated_data

        except Exception as e:
            self._log(f"[Data Agent] 데이터 로딩 실패: {e}")
            return {}
        finally:
            if self.mongodb_client:
                self.mongodb_client.close()

    def _connect_mongodb(self) -> bool:
        """MongoDB 연결"""
        try:
            mongodb_host = self.config.get('MONGODB_LOCAL', 'localhost')
            mongodb_port = self.config.get('MONGODB_PORT', 27017)
            mongodb_id = self.config.get('MONGODB_ID', 'admin')
            mongodb_pw = self.config.get('MONGODB_PW', 'wlsaud07')

            self.mongodb_client = pymongo.MongoClient(
                host=mongodb_host,
                port=mongodb_port,
                username=mongodb_id,
                password=mongodb_pw,
                serverSelectionTimeoutMS=10000
            )

            # 연결 테스트
            database_names = self.mongodb_client.list_database_names()

            # 필요한 데이터베이스 확인
            required_dbs = ['NasDataBase_D', 'NysDataBase_D']
            available_dbs = [db for db in required_dbs if db in database_names]

            self._log(f"[Data Agent] MongoDB 연결 성공 - 사용 가능 DB: {available_dbs}")

            return len(available_dbs) > 0

        except Exception as e:
            self._log(f"[Data Agent] MongoDB 연결 실패: {e}")
            return False

    def _select_nas_symbols(self, nas_symbols: Optional[List[str]]) -> List[str]:
        """NASDAQ 종목 선택"""
        if nas_symbols:
            return nas_symbols

        # 기본 NASDAQ 종목들
        preferred_nas = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']

        try:
            if 'NasDataBase_D' in self.mongodb_client.list_database_names():
                db = self.mongodb_client['NasDataBase_D']
                available_collections = db.list_collection_names()

                # 선호 종목 중 사용 가능한 것들
                available_preferred = [symbol for symbol in preferred_nas if symbol in available_collections]

                if len(available_preferred) >= 5:
                    return available_preferred[:5]
                else:
                    # 부족하면 다른 종목도 추가
                    additional = [col for col in available_collections
                                if col not in preferred_nas and col.isupper() and len(col) <= 5]
                    return available_preferred + additional[:5-len(available_preferred)]

        except Exception as e:
            self._log(f"[Data Agent] NASDAQ 종목 선택 실패: {e}")

        return preferred_nas[:5]

    def _select_nys_symbols(self, nys_symbols: Optional[List[str]]) -> List[str]:
        """NYSE 종목 선택"""
        if nys_symbols:
            return nys_symbols

        # 기본 NYSE 종목들 (NASDAQ과 겹치지 않는)
        preferred_nys = ['JNJ', 'PG', 'KO', 'DIS', 'WMT', 'V', 'JPM', 'UNH', 'HD', 'MA']

        try:
            if 'NysDataBase_D' in self.mongodb_client.list_database_names():
                db = self.mongodb_client['NysDataBase_D']
                available_collections = db.list_collection_names()

                # 선호 종목 중 사용 가능한 것들
                available_preferred = [symbol for symbol in preferred_nys if symbol in available_collections]

                if len(available_preferred) >= 5:
                    return available_preferred[:5]
                else:
                    # 부족하면 다른 종목도 추가
                    additional = [col for col in available_collections
                                if col not in preferred_nys and col.isupper() and len(col) <= 5]
                    return available_preferred + additional[:5-len(available_preferred)]

        except Exception as e:
            self._log(f"[Data Agent] NYSE 종목 선택 실패: {e}")

        return preferred_nys[:5]

    def _load_market_data(self, database_name: str, symbols: List[str],
                         start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """특정 시장의 데이터 로드"""
        market_data = {}

        try:
            if database_name in self.mongodb_client.list_database_names():
                db = self.mongodb_client[database_name]
                market_type = "NASDAQ" if "Nas" in database_name else "NYSE"

                self._log(f"[Data Agent] {market_type} 데이터 로드 시작 ({len(symbols)}개 종목)")

                # 날짜 변환
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")

                for symbol in symbols:
                    try:
                        if symbol in db.list_collection_names():
                            collection = db[symbol]

                            # 날짜 범위 쿼리
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
                                df['Date'] = pd.to_datetime(df['Date'])
                                df.set_index('Date', inplace=True)

                                # OHLCV 컬럼 표준화
                                required_columns = ['open', 'high', 'low', 'close', 'volume']
                                available_columns = [col for col in required_columns if col in df.columns]

                                if available_columns:
                                    df = df[available_columns]

                                    # 컬럼명 표준화
                                    column_mapping = {
                                        'open': 'Open',
                                        'high': 'High',
                                        'low': 'Low',
                                        'close': 'Close',
                                        'volume': 'Volume'
                                    }
                                    df = df.rename(columns=column_mapping)

                                    # 시장 정보 추가
                                    df['Market'] = market_type

                                    market_data[f"{symbol}_{market_type}"] = df
                                    self._log(f"[Data Agent] {symbol} ({market_type}): {len(df)}일 데이터 로드")

                            else:
                                self._log(f"[Data Agent] {symbol} ({market_type}): 기간 내 데이터 없음")
                        else:
                            self._log(f"[Data Agent] {symbol} ({market_type}): 컬렉션 없음")

                    except Exception as e:
                        self._log(f"[Data Agent] {symbol} ({market_type}) 로드 실패: {e}")

            else:
                self._log(f"[Data Agent] {database_name} 데이터베이스 없음")

        except Exception as e:
            self._log(f"[Data Agent] {database_name} 데이터 로드 실패: {e}")

        return market_data

    def _calculate_technical_indicators(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """기술지표 계산"""
        self._log(f"[Data Agent] 기술지표 계산 시작 ({len(market_data)}개 종목)")

        processed_data = {}

        for symbol, df in market_data.items():
            try:
                self._log(f"[Data Agent] {symbol} 기술지표 계산 중...")

                # 데이터 복사
                processed_df = df.copy()

                # 기본 기술지표 추가
                processed_df = self.indicators.add_moving_averages(processed_df, [5, 10, 20, 50, 200])
                processed_df = self.indicators.add_rsi(processed_df, period=14)
                processed_df = self.indicators.add_bollinger_bands(processed_df, period=20, std_dev=2)
                processed_df = self.indicators.add_macd(processed_df, fast=12, slow=26, signal=9)
                processed_df = self.indicators.add_stochastic(processed_df, k_period=14, d_period=3)
                processed_df = self.indicators.add_atr(processed_df, period=14)
                processed_df = self.indicators.add_volume_indicators(processed_df)
                processed_df = self.indicators.add_price_change(processed_df)

                # 시장별 특수 지표 추가
                if 'NASDAQ' in symbol:
                    # NASDAQ 특화 지표 (성장주 특성)
                    processed_df['Price_Momentum'] = processed_df['Close'].pct_change(20)  # 20일 모멘텀
                    processed_df['Volume_Surge'] = processed_df['Volume'] / processed_df['Volume'].rolling(10).mean()
                elif 'NYSE' in symbol:
                    # NYSE 특화 지표 (가치주 특성)
                    processed_df['Price_Stability'] = processed_df['Close'].rolling(20).std() / processed_df['Close']
                    processed_df['Dividend_Yield_Proxy'] = 1 / processed_df['Close']  # 간접적 배당수익률

                processed_data[symbol] = processed_df
                self._log(f"[Data Agent] {symbol} 기술지표 계산 완료 ({len(processed_df.columns)}개 컬럼)")

            except Exception as e:
                self._log(f"[Data Agent] {symbol} 기술지표 계산 실패: {e}")
                processed_data[symbol] = df  # 원본 데이터라도 포함

        self._log(f"[Data Agent] 기술지표 계산 완료")
        return processed_data

    def _validate_data_quality(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """데이터 품질 검증"""
        self._log("[Data Agent] 데이터 품질 검증 시작")

        validated_data = {}

        for symbol, df in data.items():
            try:
                # 기본 검증
                if df.empty:
                    self._log(f"[Data Agent] {symbol}: 빈 데이터프레임 - 제외")
                    continue

                # 최소 데이터 포인트 확인 (30일 이상)
                if len(df) < 30:
                    self._log(f"[Data Agent] {symbol}: 데이터 부족 ({len(df)}일) - 제외")
                    continue

                # 필수 컬럼 확인
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    self._log(f"[Data Agent] {symbol}: 필수 컬럼 누락 {missing_columns} - 제외")
                    continue

                # 결측치 처리
                missing_ratio = df[required_columns].isnull().sum().sum() / (len(df) * len(required_columns))
                if missing_ratio > 0.1:  # 10% 이상 결측치
                    self._log(f"[Data Agent] {symbol}: 결측치 과다 ({missing_ratio:.1%}) - 제외")
                    continue

                # 이상치 확인 (가격이 0 이하이거나 극단값)
                price_issues = (df['Close'] <= 0).sum()
                if price_issues > 0:
                    self._log(f"[Data Agent] {symbol}: 가격 이상치 {price_issues}개 발견 - 수정")
                    df = df[df['Close'] > 0]

                # 볼륨 이상치 확인
                volume_issues = (df['Volume'] < 0).sum()
                if volume_issues > 0:
                    self._log(f"[Data Agent] {symbol}: 볼륨 이상치 {volume_issues}개 발견 - 수정")
                    df['Volume'] = df['Volume'].clip(lower=0)

                # 최종 검증 통과
                validated_data[symbol] = df
                self._log(f"[Data Agent] {symbol}: 품질 검증 통과 ({len(df)}일, {len(df.columns)}개 컬럼)")

            except Exception as e:
                self._log(f"[Data Agent] {symbol} 품질 검증 실패: {e}")

        self._log(f"[Data Agent] 데이터 품질 검증 완료: {len(validated_data)}/{len(data)} 종목 통과")
        return validated_data

    def _load_fallback_data(self, start_date: str, end_date: str,
                           nas_symbols: Optional[List[str]],
                           nys_symbols: Optional[List[str]]) -> Dict[str, pd.DataFrame]:
        """대체 데이터 로드 (Yahoo Finance 등)"""
        self._log("[Data Agent] 대체 데이터 소스 사용")

        try:
            # 기존 시스템 사용
            from mongodb_integrated_backtest import MongoDBIntegratedBacktest
            backtest_system = MongoDBIntegratedBacktest()

            if not nas_symbols:
                nas_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            if not nys_symbols:
                nys_symbols = ['JNJ', 'PG', 'KO', 'DIS', 'WMT']

            universe = nas_symbols + nys_symbols
            return backtest_system._load_yfinance_fallback(universe, start_date, end_date)

        except Exception as e:
            self._log(f"[Data Agent] 대체 데이터 로드 실패: {e}")
            return {}

    def get_data_summary(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """데이터 요약 정보 반환"""
        if not data:
            return {}

        summary = {
            'total_symbols': len(data),
            'nasdaq_symbols': len([k for k in data.keys() if 'NASDAQ' in k]),
            'nyse_symbols': len([k for k in data.keys() if 'NYSE' in k]),
            'avg_data_points': np.mean([len(df) for df in data.values()]),
            'date_range': {
                'start': min(df.index.min() for df in data.values()),
                'end': max(df.index.max() for df in data.values())
            },
            'total_indicators': np.mean([len(df.columns) for df in data.values()])
        }

        return summary

    def _log(self, message: str):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)

    def get_execution_log(self) -> List[str]:
        """실행 로그 반환"""
        return self.execution_log.copy()