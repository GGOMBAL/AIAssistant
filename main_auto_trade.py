"""
Auto Trade System Main Launcher (Refactored)
오케스트레이터 - Project Layer를 사용하여 백테스트 및 실거래 실행

이 파일은 오케스트레이터 역할만 수행하며:
- Indicator Layer (DataFrameGenerator) 사용
- Strategy Layer (SignalGenerationService) 사용
- Service Layer (DailyBacktestService) 사용
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import yaml
from pymongo import MongoClient
import pandas as pd

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Project Layer imports
from project.indicator.data_frame_generator import DataFrameGenerator
from project.strategy.signal_generation_service import SignalGenerationService
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig
from project.service.staged_pipeline_service import StagedPipelineService

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trade.log'),
        logging.StreamHandler()
    ]
)

logging.getLogger('pymongo').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Global configuration
DEBUG = False
BACKTEST_MODE = 'LIMITED'

def load_config():
    """설정 파일 로드"""
    global DEBUG, BACKTEST_MODE

    config_path = project_root / 'myStockInfo.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    DEBUG = config.get('global_settings', {}).get('DEBUG', False)
    BACKTEST_MODE = config.get('global_settings', {}).get('BACKTEST_MODE', 'LIMITED')

    # 로깅 레벨 조정
    if DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    print(f"DEBUG 모드: {'ON' if DEBUG else 'OFF'}")
    print(f"백테스트 모드: {BACKTEST_MODE}")

    return config

async def get_symbols_from_mongodb(config: dict, mode: str = 'FULL') -> List[str]:
    """
    MongoDB에서 종목 리스트 가져오기

    Args:
        config: 설정 딕셔너리
        mode: 'FULL' (모든 종목) or 'LIMITED' (제한된 종목)

    Returns:
        심볼 리스트
    """
    from pymongo import MongoClient

    mongodb_config = {
        'host': config.get('MONGODB_LOCAL', 'localhost'),
        'port': config.get('MONGODB_PORT', 27017),
        'username': config.get('MONGODB_ID', 'admin'),
        'password': config.get('MONGODB_PW', 'wlsaud07')
    }

    client = MongoClient(
        f"mongodb://{mongodb_config['username']}:{mongodb_config['password']}@"
        f"{mongodb_config['host']}:{mongodb_config['port']}/"
    )

    # NASDAQ + NYSE 종목 (컬렉션 이름 = 심볼)
    print(f"\nLoading symbols in {mode} mode...")
    nasdaq_collections = client['NasDataBase_D'].list_collection_names()
    nyse_collections = client['NysDataBase_D'].list_collection_names()

    # 컬렉션 이름 = 심볼 (A prefix 없음)
    # 빈 문자열과 시스템 컬렉션 제외
    nasdaq_symbols = [col for col in nasdaq_collections if col and not col.startswith('_')]
    nyse_symbols = [col for col in nyse_collections if col and not col.startswith('_')]

    all_symbols = list(set(nasdaq_symbols + nyse_symbols))

    print(f"  NASDAQ: {len(nasdaq_symbols)} symbols")
    print(f"  NYSE: {len(nyse_symbols)} symbols")
    print(f"  Total unique: {len(all_symbols)} symbols")

    client.close()

    if mode == 'LIMITED':
        limited_count = 500
        all_symbols = all_symbols[:limited_count]
        print(f"  Limited to: {len(all_symbols)} symbols")

    return all_symbols

def _print_ticker_signal_timeline(candidates_data: Dict, symbols: List[str], num_days: int = 100):
    """
    개별 티커의 W/D/RS/E/F 시그널을 타임라인 형태로 출력

    Args:
        candidates_data: {symbol: {stage: DataFrame}} 형태의 데이터
        symbols: 출력할 심볼 리스트
        num_days: 출력할 날짜 수 (기본 100개)
    """
    import pandas as pd
    import numpy as np

    for symbol in symbols:
        if symbol not in candidates_data:
            continue

        stage_data = candidates_data[symbol]

        # D 데이터가 있는 경우에만 처리
        if 'D' not in stage_data:
            continue

        df_D = stage_data['D'].copy()

        # 인덱스를 datetime으로 변환 (필요한 경우)
        if not isinstance(df_D.index, pd.DatetimeIndex):
            # 'Date' 컬럼이 있으면 인덱스로 설정
            if 'Date' in df_D.columns:
                df_D['Date'] = pd.to_datetime(df_D['Date'])
                df_D = df_D.set_index('Date')
            # 인덱스가 정수면 그냥 건너뛰기
            elif isinstance(df_D.index[0], (int, np.integer)):
                print(f"\n[{symbol}] 시그널 타임라인 - 날짜 정보 없음 (인덱스가 정수)")
                continue
            else:
                df_D.index = pd.to_datetime(df_D.index)

        # 최근 num_days 개만 추출
        if len(df_D) > num_days:
            df_D = df_D.iloc[-num_days:]

        print(f"\n[{symbol}] 시그널 타임라인")
        print(f"기간: {df_D.index[0].strftime('%Y-%m-%d')} ~ {df_D.index[-1].strftime('%Y-%m-%d')}")

        # 디버그: 사용 가능한 컬럼 출력
        print(f"D 컬럼: {list(df_D.columns)[:10]}...")
        if stage_data.get('W') is not None:
            print(f"W 컬럼: {list(stage_data.get('W').columns)[:10]}...")

        print("-" * 120)

        # 각 스테이지별 데이터 확인 및 인덱스 변환
        signals = {}
        for stage_name, stage_df in [('W', stage_data.get('W')),
                                       ('D', df_D),
                                       ('RS', stage_data.get('RS')),
                                       ('E', stage_data.get('E')),
                                       ('F', stage_data.get('F'))]:
            if stage_df is not None and len(stage_df) > 0:
                # 인덱스를 datetime으로 변환
                if not isinstance(stage_df.index, pd.DatetimeIndex):
                    stage_df = stage_df.copy()
                    if 'Date' in stage_df.columns:
                        stage_df['Date'] = pd.to_datetime(stage_df['Date'])
                        stage_df = stage_df.set_index('Date')
                    elif not isinstance(stage_df.index[0], (int, np.integer)):
                        stage_df.index = pd.to_datetime(stage_df.index)
                signals[stage_name] = stage_df
            else:
                signals[stage_name] = None

        # 타임라인 헤더
        print(f"{'Date':<12} {'Close':>8} | {'W':^5} {'D':^5} {'RS':^5} {'E':^5} {'F':^5} | Description")
        print("-" * 120)

        # 날짜별로 시그널 출력
        for idx, date in enumerate(df_D.index):
            # Close 가격 가져오기 (여러 컬럼명 시도)
            close_price = 0
            for col in ['close', 'Dclose', 'Close']:
                if col in df_D.columns:
                    close_price = df_D.loc[date, col]
                    break

            # 각 시그널 확인
            signal_status = {}
            signal_desc = []

            # Weekly 시그널 (W)
            if signals['W'] is not None and len(signals['W']) > 0:
                # 주봉은 날짜가 일치하거나 가장 가까운 과거 데이터 사용
                w_data = signals['W'][signals['W'].index <= date]
                if len(w_data) > 0:
                    w_latest = w_data.iloc[-1]

                    # close 컬럼 찾기
                    w_close = 0
                    for col in ['close', 'Wclose', 'Close']:
                        if col in w_data.columns:
                            w_close = w_latest.get(col, 0)
                            break

                    # 52주 최고가 컬럼 찾기
                    w_52h = 0
                    for col in ['52_H', '52_high', 'high_52w']:
                        if col in w_data.columns:
                            w_52h = w_latest.get(col, 0)
                            break

                    # 52주 최고가 근처 체크
                    if w_52h > 0 and w_close > 0:
                        if w_close >= w_52h * 0.90:
                            signal_status['W'] = 'O'
                            signal_desc.append('52W High 90%+')
                        else:
                            signal_status['W'] = '-'
                    else:
                        signal_status['W'] = '?'
                else:
                    signal_status['W'] = '-'
            else:
                signal_status['W'] = '-'

            # Daily 시그널 (D) - BuySig 체크
            if 'BuySig' in df_D.columns:
                buy_sig = df_D.loc[date, 'BuySig']
                if buy_sig >= 1:
                    signal_status['D'] = 'O'
                    signal_desc.append('Daily Buy')
                else:
                    signal_status['D'] = '-'
            else:
                signal_status['D'] = '?'

            # RS 시그널
            if signals['RS'] is not None and len(signals['RS']) > 0:
                rs_data = signals['RS'][signals['RS'].index <= date]
                if len(rs_data) > 0:
                    rs_latest = rs_data.iloc[-1]
                    rs_4w = rs_latest.get('RS_4W', 0)
                    if rs_4w >= 90:
                        signal_status['RS'] = 'O'
                        signal_desc.append(f'RS={rs_4w:.0f}')
                    elif rs_4w >= 70:
                        signal_status['RS'] = 'o'
                        signal_desc.append(f'RS={rs_4w:.0f}')
                    else:
                        signal_status['RS'] = '-'
                else:
                    signal_status['RS'] = '-'
            else:
                signal_status['RS'] = '-'

            # Earnings 시그널 (E)
            if signals['E'] is not None and len(signals['E']) > 0:
                e_data = signals['E'][signals['E'].index <= date]
                if len(e_data) > 0:
                    e_latest = e_data.iloc[-1]
                    eps_yoy = e_latest.get('eps_yoy', 0)
                    rev_yoy = e_latest.get('rev_yoy', 0)
                    if eps_yoy > 0 and rev_yoy > 0:
                        signal_status['E'] = 'O'
                        signal_desc.append(f'EPS+{eps_yoy:.0f}%')
                    else:
                        signal_status['E'] = '-'
                else:
                    signal_status['E'] = '-'
            else:
                signal_status['E'] = '-'

            # Fundamental 시그널 (F)
            if signals['F'] is not None and len(signals['F']) > 0:
                f_data = signals['F'][signals['F'].index <= date]
                if len(f_data) > 0:
                    f_latest = f_data.iloc[-1]
                    eps_yoy = f_latest.get('EPS_YOY', 0)
                    rev_yoy = f_latest.get('REV_YOY', 0)
                    if eps_yoy > 0 and rev_yoy > 0:
                        signal_status['F'] = 'O'
                        signal_desc.append(f'Fund+')
                    else:
                        signal_status['F'] = '-'
                else:
                    signal_status['F'] = '-'
            else:
                signal_status['F'] = '-'

            # 10일마다 또는 시그널이 있는 경우 출력
            has_signal = any(v in ['O', 'o'] for v in signal_status.values())
            if idx % 10 == 0 or has_signal:
                # 날짜 문자열 생성 (datetime 또는 정수 처리)
                if isinstance(date, pd.Timestamp):
                    date_str = date.strftime('%Y-%m-%d')
                elif isinstance(date, (int, np.integer)):
                    date_str = f"Index_{date}"
                else:
                    date_str = str(date)

                desc_str = ', '.join(signal_desc) if signal_desc else '-'

                print(f"{date_str:<12} ${close_price:>7.2f} | "
                      f"{signal_status.get('W', '-'):^5} "
                      f"{signal_status.get('D', '-'):^5} "
                      f"{signal_status.get('RS', '-'):^5} "
                      f"{signal_status.get('E', '-'):^5} "
                      f"{signal_status.get('F', '-'):^5} | "
                      f"{desc_str}")

        # 범례
        print("\n[범례] O=시그널 발생, o=약한 시그널, -=시그널 없음, ?=데이터 없음")
        print("-" * 120)


async def run_backtest_staged(
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_cash: float,
    config: dict
) -> dict:
    """
    Staged Pipeline을 사용한 백테스트 실행

    Flow (E → F → W → RS → D):
    1. E 데이터 로드 → E 시그널 생성 → 필터링
    2. F 데이터 로드 (E 통과 종목만) → F 시그널 생성 → 필터링
    3. W 데이터 로드 (F 통과 종목만) → W 시그널 생성 → 필터링
    4. RS 데이터 로드 (W 통과 종목만) → RS 시그널 생성 → 필터링
    5. D 데이터 로드 (RS 통과 종목만) → D 시그널 생성 → 최종 후보
    6. DailyBacktestService로 백테스트 실행
    """

    print("="*60)
    print("Staged Pipeline 백테스트 실행")
    print("="*60)

    start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
    data_start = start_date_dt - timedelta(days=365*3)

    # Run staged pipeline
    print("\n[Staged Pipeline] 단계별 필터링 시작...")
    pipeline = StagedPipelineService(
        config=config,
        market='US',
        area='US',
        start_day=data_start,
        end_day=end_date_dt
    )

    pipeline_results = pipeline.run_staged_pipeline(symbols)

    print(f"\n최종 매매 후보: {pipeline_results['total_candidates']} 종목")

    if pipeline_results['total_candidates'] == 0:
        print("⚠️  매매 후보 종목이 없습니다.")
        return {
            'status': 'no_candidates',
            'pipeline_results': pipeline_results
        }

    # Get final candidates from pipeline results
    final_candidates = pipeline_results.get('final_candidates', [])

    if not final_candidates:
        print("[WARNING] 최종 후보 데이터가 없습니다.")
        return {
            'status': 'no_final_data',
            'pipeline_results': pipeline_results
        }

    # Load all data for final candidates
    print(f"\n최종 후보 {len(final_candidates)}개 종목의 데이터 로딩 중...")
    all_loaded_data = pipeline.data_loader.get_all_loaded_data()

    # Convert data structure from {stage: {symbol: df}} to {symbol: {stage: df}}
    final_candidates_data = {}
    if all_loaded_data:
        # Invert the data structure
        for stage, symbols_data in all_loaded_data.items():
            if isinstance(symbols_data, dict):
                for symbol, df in symbols_data.items():
                    if symbol not in final_candidates_data:
                        final_candidates_data[symbol] = {}
                    final_candidates_data[symbol][stage] = df

    # Filter only symbols that have D (daily) data
    symbols_with_d_data = [s for s, data in final_candidates_data.items() if 'D' in data]
    print(f"\n백테스트 데이터 준비:")
    print(f"  - 로드된 전체 종목: {len(final_candidates_data)}개")
    print(f"  - 일봉 데이터 보유: {len(symbols_with_d_data)}개")
    print(f"  - 백테스트 대상: {symbols_with_d_data}")

    # Run backtest with final candidates
    print("\n" + "="*60)
    print("백테스트 실행 중...")
    print("="*60)

    if final_candidates_data and symbols_with_d_data:
        # 백테스트용 데이터 포맷 변환
        # {symbol: {stage: DataFrame}} → {symbol: DataFrame}
        backtest_data = {}
        for symbol in symbols_with_d_data:  # Only process symbols with D data
            stage_data = final_candidates_data[symbol]
            # D (Daily) 데이터를 메인으로 사용
            if 'D' in stage_data:
                df_D = stage_data['D'].copy()

                # Set Date column as index if it exists
                if 'Date' in df_D.columns:
                    df_D['Date'] = pd.to_datetime(df_D['Date'])
                    df_D = df_D.set_index('Date')
                    df_D = df_D.sort_index()

                # 백테스트에 필요한 컬럼 확인 및 추가
                required_cols = ['open', 'high', 'low', 'close', 'ADR', 'LossCutPrice',
                                'TargetPrice', 'BuySig', 'SellSig', 'signal', 'Type']

                # 컬럼명 매핑 (있는 경우)
                if 'Dopen' in df_D.columns:
                    df_D['open'] = df_D['Dopen']
                if 'Dhigh' in df_D.columns:
                    df_D['high'] = df_D['Dhigh']
                if 'Dlow' in df_D.columns:
                    df_D['low'] = df_D['Dlow']
                if 'Dclose' in df_D.columns:
                    df_D['close'] = df_D['Dclose']

                # 기본값 설정 (누락된 컬럼)
                for col in required_cols:
                    if col not in df_D.columns:
                        if col in ['BuySig', 'SellSig']:
                            df_D[col] = 1  # 모든 종목에 매수 신호 (이미 필터링 통과)
                        elif col == 'signal':
                            df_D[col] = 1
                        elif col == 'Type':
                            df_D[col] = 'Staged'
                        elif col == 'TargetPrice':
                            # Target price = current close * 1.20 (20% profit target)
                            df_D[col] = df_D['close'] * 1.20
                        elif col == 'LossCutPrice':
                            # Loss cut price = current close * 0.95 (5% stop loss)
                            df_D[col] = df_D['close'] * 0.95
                        elif col == 'ADR':
                            # Default ADR if not present
                            df_D[col] = 5.0
                        else:
                            df_D[col] = 0

                # Debug: Check if we have valid data
                print(f"    [{symbol}] Shape: {df_D.shape}, BuySig sum: {df_D['BuySig'].sum()}, "
                      f"Price range: {df_D['close'].min():.2f} - {df_D['close'].max():.2f}")

                backtest_data[symbol] = df_D

        if backtest_data:
            backtest_config = BacktestConfig()
            # initial_cash는 달러 단위로 들어옴 (예: 100000.0 = $100K)
            # DailyBacktestService는 백만달러(M) 단위를 기대함
            # $100K = 0.1M
            backtest_config.initial_cash = initial_cash / 1_000_000  # Convert to million dollars
            backtest_config.max_positions = 10
            backtest_config.slippage = 0.002
            backtest_config.message_output = True  # 날짜별 Balance 출력 활성화

            print(f"\n백테스트 설정:")
            print(f"  - 초기 자본: ${initial_cash:,.0f} = ${backtest_config.initial_cash:.2f}M")
            print(f"  - 최대 보유 종목: {backtest_config.max_positions}개")
            print(f"  - 슬리피지: {backtest_config.slippage*100:.2f}%")

            backtest_service = DailyBacktestService(backtest_config)

            print(f"\n백테스트 실행 파라미터:")
            print(f"  - Universe: {list(backtest_data.keys())}")
            print(f"  - 데이터 shape 확인:")
            for symbol in list(backtest_data.keys())[:3]:  # First 3 symbols
                df = backtest_data[symbol]
                print(f"      {symbol}: {df.shape}, Index: {type(df.index).__name__}, "
                      f"Has BuySig: {'BuySig' in df.columns}, BuySig sum: {df['BuySig'].sum() if 'BuySig' in df.columns else 'N/A'}")

            # 백테스트 실행
            backtest_results = backtest_service.run_backtest(
                universe=list(backtest_data.keys()),
                df_data=backtest_data,
                market='US',
                area='US'
            )
        else:
            print("[WARNING] 백테스트 데이터 준비 실패")
            return {
                'status': 'data_format_error',
                'pipeline_results': pipeline_results
            }

        # 결과 출력
        print("\n" + "="*80)
        print("백테스트 최종 결과")
        print("="*80)

        metrics = backtest_results.performance_metrics

        print(f"\n[성과 지표]")
        print(f"  총 수익률: {metrics.get('total_return', 0):.2%}")
        print(f"  최종 자산: ${metrics.get('final_value', 0):.2f}M")
        print(f"  최대 손실: {metrics.get('max_drawdown', 0):.2%}")

        print(f"\n[거래 통계]")
        print(f"  총 거래 수: {metrics.get('total_trades', 0)}")
        print(f"  승리 횟수: {metrics.get('win_count', 0):.1f}")
        print(f"  손실 횟수: {metrics.get('loss_count', 0):.1f}")
        print(f"  승률: {metrics.get('win_rate', 0):.2%}")

        print(f"\n[포트폴리오 통계]")
        print(f"  평균 현금 비율: {metrics.get('avg_cash_ratio', 0):.2f}%")
        print(f"  최대 보유 종목 수: {metrics.get('max_positions', 0)}")

        print(f"\n[실행 정보]")
        print(f"  실행 시간: {backtest_results.execution_time:.2f}초")

        # 4. 개별 티커의 시그널 타임라인 출력 (최근 100개 날짜)
        print("\n" + "="*80)
        print("개별 티커 시그널 타임라인 (최근 100개 거래일)")
        print("="*80)
        _print_ticker_signal_timeline(final_candidates_data, symbols_with_d_data[:3])

        return {
            'status': 'completed',
            'pipeline_results': pipeline_results,
            'candidates_data': final_candidates_data,
            'backtest_results': backtest_results
        }
    else:
        print("[WARNING] 최종 후보 데이터가 없습니다.")
        return {
            'status': 'no_data',
            'pipeline_results': pipeline_results
        }

async def run_backtest_with_project_layers(
    symbols: List[str],
    start_date: str,
    end_date: str,
    initial_cash: float,
    config: dict
) -> dict:
    """
    Project Layer를 사용한 백테스트 실행 (기존 방식)

    Flow:
    1. DataFrameGenerator로 데이터 로드 및 지표 계산
    2. SignalGenerationService로 시그널 생성
    3. DailyBacktestService로 백테스트 실행
    """

    print("="*60)
    print("Project Layer를 사용한 백테스트 실행 (기존 방식)")
    print("="*60)

    # 1. Indicator Layer: 데이터 로드 및 지표 계산
    print("\n[Step 1] Indicator Layer - 데이터 로드 중...")

    start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

    # 3년 lookback으로 데이터 로드
    data_start = start_date_dt - timedelta(days=365*3)

    data_generator = DataFrameGenerator(
        universe=symbols,
        market='US',
        area='US',
        start_day=data_start,
        end_day=end_date_dt
    )

    # 모든 데이터 프레임 생성
    print("  - 데이터 로딩 시작...")
    data_generator.load_data_from_database()

    print(f"  - Daily 데이터: {len(data_generator.df_D)} 종목")
    print(f"  - Weekly 데이터: {len(data_generator.df_W)} 종목")
    print(f"  - RS 데이터: {len(data_generator.df_RS)} 종목")
    print(f"  - Fundamental 데이터: {len(data_generator.df_F)} 종목")

    # 2. Strategy Layer: 시그널 생성
    print("\n[Step 2] Strategy Layer - 시그널 생성 중...")

    signal_service = SignalGenerationService(area='US', trading_mode=False)

    signals_by_symbol = {}

    for symbol in symbols[:10]:  # 테스트용 10개만
        if symbol not in data_generator.df_D:
            continue

        df_daily = data_generator.df_D.get(symbol)
        df_weekly = data_generator.df_W.get(symbol)
        df_rs = data_generator.df_RS.get(symbol)
        df_fundamental = data_generator.df_F.get(symbol)
        df_earnings = data_generator.df_E.get(symbol)

        # 종합 시그널 생성
        signal_result = signal_service.generate_comprehensive_signals(
            df_daily=df_daily,
            df_weekly=df_weekly,
            df_rs=df_rs,
            df_fundamental=df_fundamental,
            df_earnings=df_earnings
        )

        signals_by_symbol[symbol] = signal_result

        if signal_result['signal_strength'] > 0:
            print(f"  - {symbol}: 신호 강도 {signal_result['signal_strength']:.2f}")

    # 3. Service Layer: 백테스트 실행
    print("\n[Step 3] Service Layer - 백테스트 실행 중...")

    backtest_config = BacktestConfig()
    backtest_config.initial_cash = initial_cash / 100_000_000  # Convert to 억원
    backtest_config.max_positions = 10
    backtest_config.slippage = 0.002
    backtest_config.message_output = DEBUG

    backtest_service = DailyBacktestService(backtest_config)

    # 백테스트용 데이터 준비 (시그널이 포함된 데이터)
    # TODO: 실제로는 Strategy Layer의 결과를 백테스트 서비스에 전달

    results = {
        'signals_generated': len(signals_by_symbol),
        'symbols_analyzed': len(symbols),
        'start_date': start_date,
        'end_date': end_date,
        'initial_cash': initial_cash,
        'status': 'completed'
    }

    print("\n[완료] 백테스트 실행 완료")
    print(f"  - 분석 종목: {results['symbols_analyzed']}개")
    print(f"  - 시그널 생성: {results['signals_generated']}개")

    return results

async def check_single_symbol_signal(symbol: str, config: dict):
    """개별 종목의 매매 시그널 확인 (NASDAQ + NYSE 검색)"""
    print("\n" + "="*60)
    print(f"종목 시그널 분석: {symbol}")
    print("="*60)

    # 날짜 설정 (최근 3년)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)

    try:
        # 1. MongoDB에서 종목이 어느 마켓에 있는지 확인
        print(f"\n[1/4] {symbol} 마켓 확인 중...")

        mongodb_config = {
            'host': config.get('MONGODB_LOCAL', 'localhost'),
            'port': config.get('MONGODB_PORT', 27017),
            'username': config.get('MONGODB_ID', 'admin'),
            'password': config.get('MONGODB_PW', 'wlsaud07')
        }

        client = MongoClient(
            f"mongodb://{mongodb_config['username']}:{mongodb_config['password']}@"
            f"{mongodb_config['host']}:{mongodb_config['port']}/"
        )

        # NASDAQ과 NYSE에서 종목 검색
        market_found = None

        if symbol in client['NasDataBase_D'].list_collection_names():
            market_found = 'NASDAQ'
            print(f"   -> {symbol} found in NASDAQ market")
        elif symbol in client['NysDataBase_D'].list_collection_names():
            market_found = 'NYSE'
            print(f"   -> {symbol} found in NYSE market")

        client.close()

        if not market_found:
            print(f"[ERROR] {symbol} not found in NASDAQ or NYSE databases")
            return None

        # 2. DataFrameGenerator로 데이터 로드
        print(f"\n[2/4] {symbol} 데이터 로딩 중...")
        df_generator = DataFrameGenerator(
            universe=[symbol],
            market='US',
            area='US',
            start_day=start_date,
            end_day=end_date
        )

        df_generator.load_data_from_database()
        symbol_data = df_generator.get_dataframes()

        # 심볼별 데이터 추출
        df_W = symbol_data.get('df_W', {})
        df_D = symbol_data.get('df_D', {})

        if not df_W or symbol not in df_W or not df_D or symbol not in df_D:
            print(f"[ERROR] {symbol} data loading failed")
            return None

        # 3. SignalGenerationService로 시그널 생성
        print(f"\n[3/4] {symbol} 시그널 생성 중...")
        signal_service = SignalGenerationService(config)

        # 심볼별 데이터 추출
        df_RS = symbol_data.get('df_RS', {})
        df_E = symbol_data.get('df_E', {})
        df_F = symbol_data.get('df_F', {})

        # 시그널 생성
        signal_data = signal_service.generate_comprehensive_signals(
            df_weekly=df_W.get(symbol),
            df_rs=df_RS.get(symbol),
            df_fundamental=df_F.get(symbol),
            df_earnings=df_E.get(symbol),
            df_daily=df_D.get(symbol)
        )

        if not signal_data:
            print(f"[ERROR] {symbol} signal generation failed")
            return None

        # 4. 최신 시그널 정보 출력
        print(f"\n[4/4] {symbol} 시그널 분석 완료\n")

        # 가격 정보는 df_D에서 직접 가져오기
        latest_price_data = df_D[symbol].iloc[-1] if symbol in df_D and not df_D[symbol].empty else None

        print("="*60)
        print(f"Symbol: {symbol}")
        print(f"Market: {market_found}")
        print("="*60)

        if latest_price_data is not None:
            print("\n[Price Information]")
            print(f"  Current Price: ${latest_price_data.get('ad_close', 0):.2f}")
            print(f"  Date: {latest_price_data.get('Date', 'N/A')}")

        print("\n[Trading Signal]")
        final_signal = str(signal_data.get('final_signal', 'HOLD'))
        signal_strength = signal_data.get('signal_strength', 0)
        confidence = signal_data.get('confidence', 0)

        if 'BUY' in final_signal:
            print(f"  [BUY] Signal detected!")
            print(f"  Signal Strength: {signal_strength:.2f}")
            print(f"  Confidence: {confidence:.2%}")
            print(f"  Stop Loss: ${signal_data.get('losscut_price', 0):.2f}")
            print(f"  Target Price: ${signal_data.get('target_price', 0):.2f}")
        elif 'SELL' in final_signal:
            print(f"  [SELL] Signal detected!")
            print(f"  Signal Strength: {signal_strength:.2f}")
        else:
            print(f"  [HOLD] No signal")
            print(f"  Signal Strength: {signal_strength:.2f}")
            print(f"  Confidence: {confidence:.2%}")

        print("\n[Signal Components]")
        components = signal_data.get('signal_components', {})
        print(f"  Weekly: {components.get('weekly', 0)}")
        print(f"  RS: {components.get('rs', 0)}")
        print(f"  Fundamental: {components.get('fundamental', 0)}")
        print(f"  Earnings: {components.get('earnings', 0)}")
        print(f"  Daily RS: {components.get('daily_rs', 0)}")

        # DataFrame Summary (Latest Values) 출력 추가
        print("\n" + "="*60)
        print("DATAFRAME SUMMARY - LATEST VALUES")
        print("="*60)

        # Daily (D) DataFrame
        if symbol in df_D and not df_D[symbol].empty:
            print("\nDaily Data (D):")
            print("-"*60)
            latest_d = df_D[symbol].iloc[-1]
            d_cols = ['Date', 'Dopen', 'Dhigh', 'Dlow', 'Dclose', 'volume', 'ADR', 'SMA20', 'SMA50', 'SMA200']
            for col in d_cols:
                if col in latest_d.index:
                    val = latest_d[col]
                    if pd.notna(val):
                        if col == 'Date':
                            print(f"  {col:<20}: {val}")
                        elif col == 'volume':
                            print(f"  {col:<20}: {val:,.0f}")
                        else:
                            print(f"  {col:<20}: {val:.4f}")

        # Weekly (W) DataFrame
        if symbol in df_W and not df_W[symbol].empty:
            print("\nWeekly Data (W):")
            print("-"*60)
            latest_w = df_W[symbol].iloc[-1]
            w_cols = ['Date', 'Wopen', 'Whigh', 'Wlow', 'Wclose', 'volume', '52_H', '52_L', '1Year_H', '1Year_L']
            for col in w_cols:
                if col in latest_w.index:
                    val = latest_w[col]
                    if pd.notna(val):
                        if col == 'Date':
                            print(f"  {col:<20}: {val}")
                        elif col == 'volume':
                            print(f"  {col:<20}: {val:,.0f}")
                        else:
                            print(f"  {col:<20}: {val:.4f}")

        # RS DataFrame
        if symbol in df_RS and not df_RS[symbol].empty:
            print("\nRelative Strength (RS) Data:")
            print("-"*60)
            latest_rs = df_RS[symbol].iloc[-1]
            rs_cols = ['Date', 'RS_4W', 'RS_12W', 'Sector', 'Industry', 'Sector_RS_4W', 'Sector_RS_12W', 'Industry_RS_4W', 'Industry_RS_12W']
            for col in rs_cols:
                if col in latest_rs.index:
                    val = latest_rs[col]
                    if pd.notna(val):
                        if col in ['Date', 'Sector', 'Industry']:
                            print(f"  {col:<20}: {val}")
                        else:
                            print(f"  {col:<20}: {val:.4f}")

        # Earnings (E) DataFrame
        if symbol in df_E and not df_E[symbol].empty:
            print("\nEarnings (E) Data:")
            print("-"*60)
            latest_e = df_E[symbol].iloc[-1]
            e_cols = ['Date', 'EarningDate', 'eps', 'eps_yoy', 'eps_qoq', 'revenue', 'rev_yoy', 'rev_qoq']
            for col in e_cols:
                if col in latest_e.index:
                    val = latest_e[col]
                    if pd.notna(val):
                        if col in ['Date', 'EarningDate']:
                            print(f"  {col:<20}: {val}")
                        else:
                            print(f"  {col:<20}: {val:.4f}")

        # Fundamental (F) DataFrame
        if symbol in df_F and not df_F[symbol].empty:
            print("\nFundamental (F) Data:")
            print("-"*60)
            latest_f = df_F[symbol].iloc[-1]
            f_cols = ['Date', 'netIncome', 'totalRevenue', 'grossProfit', 'operatingIncome', 'totalAssets',
                     'totalShareholderEquity', 'EPS', 'EPS_YOY', 'EPS_QOQ', 'REV_YOY', 'REV_QOQ']
            for col in f_cols:
                if col in latest_f.index:
                    val = latest_f[col]
                    if pd.notna(val):
                        if col == 'Date':
                            print(f"  {col:<20}: {val}")
                        elif col in ['netIncome', 'totalRevenue', 'grossProfit', 'operatingIncome', 'totalAssets', 'totalShareholderEquity']:
                            print(f"  {col:<20}: {val:,.0f}")
                        else:
                            print(f"  {col:<20}: {val:.4f}")

        # Strategy Layer 최종 아웃풋 출력
        print("\n" + "="*60)
        print("STRATEGY LAYER OUTPUT - FINAL SIGNAL DATA")
        print("="*60)

        # 1. Core Signal Information
        print("\n[1/6] Core Signal Information")
        print("-"*60)
        print(f"  Final Signal: {signal_data.get('final_signal', 'N/A')}")
        print(f"  Signal Strength: {signal_data.get('signal_strength', 0):.4f}")
        print(f"  Confidence: {signal_data.get('confidence', 0):.4f}")
        print(f"  Signal Type: {signal_data.get('signal_type', 'N/A')}")

        # 2. Price Targets
        print("\n[2/6] Price Targets & Risk Management")
        print("-"*60)
        print(f"  Entry Price: ${signal_data.get('entry_price', 0):.2f}")
        print(f"  Target Price: ${signal_data.get('target_price', 0):.2f}")
        print(f"  Stop Loss: ${signal_data.get('losscut_price', 0):.2f}")
        print(f"  Risk/Reward Ratio: {signal_data.get('risk_reward_ratio', 0):.2f}")

        # 3. Signal Components Breakdown
        print("\n[3/6] Signal Components Breakdown")
        print("-"*60)
        components = signal_data.get('signal_components', {})
        print(f"  Weekly Signal: {components.get('weekly', 0):.4f}")
        print(f"  RS Signal: {components.get('rs', 0):.4f}")
        print(f"  Fundamental Signal: {components.get('fundamental', 0):.4f}")
        print(f"  Earnings Signal: {components.get('earnings', 0):.4f}")
        print(f"  Daily RS Signal: {components.get('daily_rs', 0):.4f}")
        print(f"  Total Score: {sum(components.values()):.4f}")

        # 4. Technical Indicators (from raw dataframes)
        print("\n[4/6] Technical Indicators")
        print("-"*60)

        # Get values from Daily dataframe
        adr_val = df_D[symbol].iloc[-1].get('ADR', 0) if symbol in df_D and not df_D[symbol].empty and 'ADR' in df_D[symbol].columns else 0
        # Get values from RS dataframe
        rs_4w = df_RS[symbol].iloc[-1].get('RS_4W', 0) if symbol in df_RS and not df_RS[symbol].empty and 'RS_4W' in df_RS[symbol].columns else 0
        rs_12w = df_RS[symbol].iloc[-1].get('RS_12W', 0) if symbol in df_RS and not df_RS[symbol].empty and 'RS_12W' in df_RS[symbol].columns else 0
        # Get values from Weekly dataframe
        high_52w = df_W[symbol].iloc[-1].get('52_H', 0) if symbol in df_W and not df_W[symbol].empty and '52_H' in df_W[symbol].columns else 0
        low_52w = df_W[symbol].iloc[-1].get('52_L', 0) if symbol in df_W and not df_W[symbol].empty and '52_L' in df_W[symbol].columns else 0
        wclose = df_W[symbol].iloc[-1].get('Wclose', 0) if symbol in df_W and not df_W[symbol].empty and 'Wclose' in df_W[symbol].columns else 0
        dist_52h = ((high_52w - wclose) / high_52w * 100) if high_52w > 0 else 0

        print(f"  ADR (Average Daily Range): {adr_val:.2f}%")
        print(f"  RS 4-Week: {rs_4w:.4f}")
        print(f"  RS 12-Week: {rs_12w:.4f}")
        print(f"  52-Week High: ${high_52w:.2f}")
        print(f"  52-Week Low: ${low_52w:.2f}")
        print(f"  Distance from 52W High: {dist_52h:.2f}%")

        # 5. Fundamental Metrics (from raw dataframes)
        print("\n[5/6] Fundamental Metrics")
        print("-"*60)

        # Get values from RS dataframe
        sector = df_RS[symbol].iloc[-1].get('Sector', 'N/A') if symbol in df_RS and not df_RS[symbol].empty and 'Sector' in df_RS[symbol].columns else 'N/A'
        industry = df_RS[symbol].iloc[-1].get('Industry', 'N/A') if symbol in df_RS and not df_RS[symbol].empty and 'Industry' in df_RS[symbol].columns else 'N/A'
        # Get values from Fundamental dataframe
        eps_yoy = df_F[symbol].iloc[-1].get('EPS_YOY', 0) if symbol in df_F and not df_F[symbol].empty and 'EPS_YOY' in df_F[symbol].columns else 0
        rev_yoy = df_F[symbol].iloc[-1].get('REV_YOY', 0) if symbol in df_F and not df_F[symbol].empty and 'REV_YOY' in df_F[symbol].columns else 0

        print(f"  Sector: {sector}")
        print(f"  Industry: {industry}")
        print(f"  EPS YoY Growth: {eps_yoy:.2f}%")
        print(f"  Revenue YoY Growth: {rev_yoy:.2f}%")
        print(f"  ROE: N/A (not calculated)")
        print(f"  PBR: N/A (not calculated)")
        print(f"  PSR: N/A (not calculated)")

        # 6. Additional Signal Details
        print("\n[6/6] Additional Signal Details")
        print("-"*60)
        print(f"  Signal Generation Time: {signal_data.get('timestamp', 'N/A')}")
        print(f"  Data Quality Score: {signal_data.get('data_quality', 1.0):.2f}")
        print(f"  Backtest Performance: {signal_data.get('backtest_win_rate', 0):.2f}%")

        # Signal Validation
        validations = signal_data.get('validations', {})
        if validations:
            print(f"\n  Signal Validations:")
            for key, value in validations.items():
                status = "[PASS]" if value else "[FAIL]"
                print(f"    {status} {key}")

        # Strategy Notes
        if 'strategy_notes' in signal_data:
            print(f"\n  Strategy Notes:")
            for note in signal_data.get('strategy_notes', []):
                print(f"    - {note}")

        print("\n" + "="*60)
        print("END OF STRATEGY LAYER OUTPUT")
        print("="*60)

        return signal_data

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

async def run_auto_backtest(config: dict):
    """자동 백테스트 실행 (Staged Pipeline 사용)"""
    print("\n" + "="*60)
    print("자동 백테스트 모드 (Staged Pipeline)")
    print("="*60)

    # 백테스트 기간 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    print(f"\n백테스트 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # 종목 로드
    print("\n종목 로드 중...")
    symbols = await get_symbols_from_mongodb(config, mode=BACKTEST_MODE)
    print(f"로드된 종목: {len(symbols)}개")

    # Staged Pipeline 백테스트 실행
    results = await run_backtest_staged(
        symbols=symbols,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_cash=100000.0,
        config=config
    )

    print("\n" + "="*60)
    print("백테스트 완료")
    print("="*60)

    return results

async def show_ticker_signal_timeline(config: dict):
    """
    개별 티커의 W/D/RS/E/F 시그널을 타임라인 형태로 출력
    사용자가 선택한 종목들에 대해 시그널 생성 및 타임라인 출력
    """
    print("\n" + "="*60)
    print("개별 티커 시그널 타임라인")
    print("="*60)

    # 종목 입력
    print("\n분석할 종목 코드를 입력하세요 (쉼표로 구분, 예: AAPL,MSFT,GOOGL):")
    symbols_input = input("종목 코드: ").strip().upper()

    if not symbols_input:
        print("❌ 종목 코드를 입력해주세요.")
        return

    symbols = [s.strip() for s in symbols_input.split(',')]
    print(f"\n선택된 종목: {', '.join(symbols)}")

    # 분석 기간 입력
    print("\n분석 기간을 선택하세요:")
    print("1. 최근 3개월")
    print("2. 최근 6개월")
    print("3. 최근 1년")
    print("4. 최근 2년")

    period_choice = input("\n선택 (1-4, 기본값: 1): ").strip() or "1"

    period_days = {
        "1": 90,
        "2": 180,
        "3": 365,
        "4": 730
    }

    days = period_days.get(period_choice, 90)

    # 날짜 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    data_start = start_date - timedelta(days=365*3)  # 3년 lookback

    print(f"\n분석 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    try:
        # Staged Pipeline 실행
        print("\n[Staged Pipeline] 시그널 생성 중...")
        pipeline = StagedPipelineService(
            config=config,
            market='US',
            area='US',
            start_day=data_start,
            end_day=end_date
        )

        pipeline_results = pipeline.run_staged_pipeline(symbols)

        # Get final candidates from pipeline
        final_candidates = pipeline_results.get('final_candidates', [])

        if not final_candidates:
            print("\n[WARNING] 시그널을 통과한 종목이 없습니다.")
            print("   - 해당 종목의 데이터가 MongoDB에 없거나")
            print("   - 필터 조건을 통과하지 못했을 수 있습니다.")
            return

        # Load all data for final candidates
        print(f"\n최종 후보 {len(final_candidates)}개 종목의 데이터 로딩 중...")
        all_loaded_data = pipeline.data_loader.get_all_loaded_data()

        # Convert data structure from {stage: {symbol: df}} to {symbol: {stage: df}}
        final_candidates_data = {}
        if all_loaded_data:
            for stage, symbols_data in all_loaded_data.items():
                if isinstance(symbols_data, dict):
                    for symbol, df in symbols_data.items():
                        if symbol not in final_candidates_data:
                            final_candidates_data[symbol] = {}
                        final_candidates_data[symbol][stage] = df

        # Filter only symbols that have D (daily) data
        symbols_with_d_data = [s for s, data in final_candidates_data.items() if 'D' in data]

        if not symbols_with_d_data:
            print("\n[WARNING] 일봉 데이터가 있는 종목이 없습니다.")
            return

        print(f"\n✅ 시그널 생성 완료: {len(symbols_with_d_data)}개 종목")
        print(f"   종목: {', '.join(symbols_with_d_data)}")

        # 타임라인 출력
        print("\n" + "="*80)
        print(f"개별 티커 시그널 타임라인 (최근 {days}일)")
        print("="*80)

        _print_ticker_signal_timeline(final_candidates_data, symbols_with_d_data, num_days=100)

        print("\n" + "="*60)
        print("시그널 타임라인 출력 완료")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

async def run_auto_trading(config: dict):
    """실거래 자동 트레이딩 실행"""
    print("\n" + "="*60)
    print("⚠️  자동 트레이딩 모드")
    print("="*60)

    # 계좌 타입 선택 (단일 프롬프트)
    print("\n계좌 타입을 선택하세요:")
    print("1. 모의 계좌 (Paper Trading)")
    print("2. 실제 계좌 (Live Trading - 실제 주문 실행)")
    print("0. 취소")

    account_choice = input("\n선택 (0-2): ").strip()

    if account_choice == '0':
        print("❌ 자동 트레이딩이 취소되었습니다.")
        return None
    elif account_choice == '1':
        account_type = 'virtual'
        print("\n✅ 모의 계좌 모드로 실행합니다.")
    elif account_choice == '2':
        account_type = 'real'
        print("\n⚠️  실제 계좌 모드 - 실제 주문이 실행됩니다!")
        final_confirm = input("정말 실행하시겠습니까? (YES 입력 필요): ").strip()
        if final_confirm != 'YES':
            print("❌ 실계좌 트레이딩이 취소되었습니다.")
            return None
    else:
        print("❌ 잘못된 선택입니다.")
        return None

    print("\n" + "="*60)
    print(f"자동 트레이딩 시작 ({account_type} 계좌)")
    print("="*60)

    # 현재 날짜
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    try:
        # 1. 유니버스 선정을 위한 데이터 로드
        print("\n[1/4] 종목 유니버스 로드 중...")
        symbols = await get_symbols_from_mongodb(config, mode=BACKTEST_MODE)
        print(f"로드된 종목: {len(symbols)}개")

        # 2. 데이터 프레임 생성
        print("\n[2/4] 데이터 프레임 생성 중...")
        df_generator = DataFrameGenerator(
            universe=symbols,
            market='US',
            area='US',
            start_day=start_date,
            end_day=end_date
        )

        # 데이터 로드
        df_generator.load_data_from_database()
        all_data = df_generator.get_dataframes()

        # 심볼별 데이터 추출
        df_W = all_data.get('df_W', {})
        df_RS = all_data.get('df_RS', {})
        df_D = all_data.get('df_D', {})
        df_E = all_data.get('df_E', {})
        df_F = all_data.get('df_F', {})

        # 실제 데이터가 있는 심볼들 확인
        available_symbols = list(set(df_W.keys()) & set(df_D.keys()))
        print(f"데이터 생성 완료: {len(available_symbols)}개 종목")

        # 3. 매매 시그널 생성
        print("\n[3/4] 매매 시그널 생성 중...")
        signal_service = SignalGenerationService(config)

        # 각 종목별로 시그널 생성
        signals = {}
        for symbol in available_symbols:
            try:
                signal_data = signal_service.generate_comprehensive_signals(
                    df_weekly=df_W.get(symbol),
                    df_rs=df_RS.get(symbol),
                    df_fundamental=df_F.get(symbol),
                    df_earnings=df_E.get(symbol),
                    df_daily=df_D.get(symbol)
                )

                # 모든 시그널 저장 (매수/매도/관망 모두)
                if signal_data:
                    import pandas as pd
                    signals[symbol] = pd.DataFrame([signal_data])

            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue

        # 매수 신호가 있는 종목 필터링
        buy_signals = {}
        for symbol, df in signals.items():
            if not df.empty:
                latest = df.iloc[-1]
                if latest.get('BuySig', 0) > 0:
                    buy_signals[symbol] = {
                        'signal_strength': latest.get('signal', 0),
                        'close': latest.get('close', 0),
                        'loss_cut': latest.get('LossCutPrice', 0),
                        'target': latest.get('TargetPrice', 0),
                        'adr': latest.get('ADR', 0)
                    }

        print(f"매수 신호 종목: {len(buy_signals)}개")

        if not buy_signals:
            print("\n⚪ 현재 매수 신호가 있는 종목이 없습니다.")
            return None

        # 4. 매수 신호 종목 표시
        print("\n[4/4] 매수 신호 종목 리스트")
        print("="*60)
        print(f"{'종목':<10} {'신호강도':<10} {'현재가':<12} {'손절가':<12} {'목표가':<12}")
        print("-"*60)

        sorted_signals = sorted(buy_signals.items(), key=lambda x: x[1]['signal_strength'], reverse=True)
        for symbol, data in sorted_signals[:20]:  # 상위 20개만 표시
            print(f"{symbol:<10} {data['signal_strength']:<10.2f} ${data['close']:<11.2f} "
                  f"${data['loss_cut']:<11.2f} ${data['target']:<11.2f}")

        print("="*60)

        # 주문 실행 정보
        print("\n💡 주문 실행 정보:")
        print("   ⚠️  실제 주문 실행 기능은 아직 구현되지 않았습니다.")
        print("   📌 주문 실행을 위해서는 KIS API 연동이 필요합니다.")
        print("\n   TODO: 실제 주문 실행 로직 구현")
        print("   - KIS API를 통한 주문 전송")
        print("   - 포지션 관리")
        print("   - 손절/익절 자동 주문")

        print("\n" + "="*60)
        print("자동 트레이딩 세션 종료")
        print("="*60)

        return buy_signals

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_menu():
    """메뉴 표시"""
    print("\n" + "="*60)
    print("AI Trading System - 메뉴 선택")
    print("="*60)
    print("\n1. 자동 백테스트 실행 (전체 종목)")
    print("2. 개별 종목 시그널 확인")
    print("3. 오토 트레이딩 시스템 (실거래)")
    print("4. 개별 티커 시그널 타임라인 (W/D/RS/E/F)")
    print("5. 종료")
    print("\n" + "="*60)

async def main():
    """메인 실행 함수"""

    print("="*60)
    print("AI Trading System (Refactored with Project Layers)")
    print("="*60)

    # 설정 로드
    config = load_config()

    while True:
        show_menu()

        try:
            choice = input("\n선택 (1-5): ").strip()

            if choice == '1':
                # 자동 백테스트
                await run_auto_backtest(config)

            elif choice == '2':
                # 개별 종목 시그널 확인
                symbol = input("\n종목 코드를 입력하세요 (예: AAPL): ").strip().upper()
                if symbol:
                    await check_single_symbol_signal(symbol, config)
                else:
                    print("❌ 종목 코드를 입력해주세요.")

            elif choice == '3':
                # 오토 트레이딩 시스템
                await run_auto_trading(config)

            elif choice == '4':
                # 개별 티커 시그널 타임라인
                await show_ticker_signal_timeline(config)

            elif choice == '5':
                print("\n프로그램을 종료합니다.")
                break

            else:
                print("❌ 1-5 사이의 숫자를 입력해주세요.")

        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
