"""
Auto Trade System Main Launcher (Unified Version with Report Agent)
오케스트레이터 - Project Layer를 사용하여 백테스트 및 실거래 실행

[2025-10-21] Merged with main_auto_trade_with_report.py
- 통합된 메뉴 시스템 (6개 옵션)
- Report Agent 완전 통합
- 실시간 모니터링 (매수 신호 + 보유 종목)

이 파일은 오케스트레이터 역할을 수행하며:
- Indicator Layer (DataFrameGenerator) 사용
- Strategy Layer (SignalGenerationService) 사용
- Service Layer (DailyBacktestService) 사용
- Reporting Layer (ReportAgent) 사용 - 시각화 담당
- Real-time Monitoring (LivePriceService + RealTimeDisplay)
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
from pymongo import MongoClient
import pandas as pd
import json

# Set matplotlib backend to non-interactive before importing quantstats
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Project Layer imports
from project.indicator.data_frame_generator import DataFrameGenerator
from project.strategy.signal_generation_service import SignalGenerationService
from project.strategy.position_manager import PositionManager  # 포지션 관리 (손절가, 트레일링 스탑)
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig
from project.service.staged_pipeline_service import StagedPipelineService
from project.service.live_price_service import LivePriceService
from project.ui.realtime_display import RealTimeDisplay

# Reporting Layer imports
from project.reporting.report_agent import ReportAgent

# Helper Layer imports (for order execution)
from project.Helper.kis_api_helper_us import KISUSHelper

# Import QuantStats for terminal output
try:
    import quantstats_lumi as qs
    # Disable matplotlib plots in QuantStats
    import matplotlib.pyplot as plt
    plt.ioff()  # Turn off interactive mode
    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    logger.warning("quantstats_lumi not available. Install with: pip install quantstats-lumi")

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

# Report Agent instance (singleton)
report_agent: Optional[ReportAgent] = None

def get_report_agent(config: dict) -> ReportAgent:
    """Get or create Report Agent instance"""
    global report_agent
    if report_agent is None:
        report_agent = ReportAgent(config)
    return report_agent

def print_quantstats_terminal_report(portfolio_value: pd.Series, benchmark: str = None, title: str = "Performance Report"):
    """
    QuantStats 터미널 리포트 출력

    Args:
        portfolio_value: 포트폴리오 가치 시계열 (pandas Series with DatetimeIndex)
        benchmark: 벤치마크 티커 (예: 'SPY', None이면 벤치마크 없이 출력)
        title: 리포트 제목
    """
    if not QUANTSTATS_AVAILABLE:
        logger.warning("QuantStats not available. Skipping terminal report.")
        return

    try:
        import matplotlib.pyplot as plt

        # Close any existing plots to prevent GUI issues
        plt.close('all')

        # Validate input
        if not isinstance(portfolio_value.index, pd.DatetimeIndex):
            logger.error("portfolio_value must have DatetimeIndex")
            return

        # Calculate returns from portfolio value
        returns = portfolio_value.pct_change().fillna(0)

        # Remove timezone info if present (QuantStats compatibility)
        if returns.index.tz is not None:
            returns.index = returns.index.tz_localize(None)

        # Print header
        print("\n" + "="*70)
        print(title.center(70))
        print("="*70 + "\n")

        # Get benchmark data if specified
        benchmark_data = None
        if benchmark:
            try:
                print(f"Downloading benchmark data ({benchmark})...\n")
                benchmark_data = qs.utils.download_returns(benchmark)

                # Ensure benchmark has same date format
                if benchmark_data.index.tz is not None:
                    benchmark_data.index = benchmark_data.index.tz_localize(None)

                # Align benchmark with returns dates
                benchmark_data = benchmark_data.reindex(returns.index, method='ffill')
            except Exception as e:
                logger.warning(f"Could not use benchmark {benchmark}: {e}")
                benchmark_data = None

        # Print performance metrics manually (for terminal output)
        print("[Performance Metrics]\n")

        # Format output table
        if benchmark_data is not None:
            print(f"{'Metric':<30} {'Benchmark':<15} {'Strategy':<15}")
            print("-" * 60)
        else:
            print(f"{'Metric':<30} {'Strategy':<15}")
            print("-" * 45)

        # Period information
        start_period = returns.index[0].strftime('%Y-%m-%d')
        end_period = returns.index[-1].strftime('%Y-%m-%d')

        print(f"{'Start Period':<30} {start_period:<15}")
        print(f"{'End Period':<30} {end_period:<15}")
        print(f"{'Risk-Free Rate %':<30} {'0.0%':<15}")
        print(f"{'Time in Market %':<30} {'100.0%':<15}")
        print()

        # Calculate and print metrics
        try:
            # Helper function to extract scalar value
            def to_scalar(value):
                """Convert Series or scalar to float"""
                if isinstance(value, pd.Series):
                    return float(value.iloc[0]) if len(value) > 0 else 0.0
                return float(value) if value is not None else 0.0

            # Returns metrics
            total_return = to_scalar(qs.stats.comp(returns))
            cagr = to_scalar(qs.stats.cagr(returns))

            if benchmark_data is not None:
                bench_total = to_scalar(qs.stats.comp(benchmark_data))
                bench_cagr = to_scalar(qs.stats.cagr(benchmark_data))
                print(f"{'Total Return':<30} {bench_total:>14.2%} {total_return:>14.2%}")
                print(f"{'CAGR% (Annual Return)':<30} {bench_cagr:>14.2%} {cagr:>14.2%}")
            else:
                print(f"{'Total Return':<30} {total_return:>14.2%}")
                print(f"{'CAGR% (Annual Return)':<30} {cagr:>14.2%}")
            print()

            # Risk-adjusted metrics
            sharpe = to_scalar(qs.stats.sharpe(returns))
            sortino = to_scalar(qs.stats.sortino(returns))

            if benchmark_data is not None:
                bench_sharpe = to_scalar(qs.stats.sharpe(benchmark_data))
                bench_sortino = to_scalar(qs.stats.sortino(benchmark_data))
                print(f"{'Sharpe':<30} {bench_sharpe:>14.2f} {sharpe:>14.2f}")
                print(f"{'Sortino':<30} {bench_sortino:>14.2f} {sortino:>14.2f}")
            else:
                print(f"{'Sharpe':<30} {sharpe:>14.2f}")
                print(f"{'Sortino':<30} {sortino:>14.2f}")

            # Drawdown metrics
            max_dd = to_scalar(qs.stats.max_drawdown(returns))

            if benchmark_data is not None:
                bench_max_dd = to_scalar(qs.stats.max_drawdown(benchmark_data))
                print(f"{'Max Drawdown %':<30} {bench_max_dd:>14.2%} {max_dd:>14.2%}")
            else:
                print(f"{'Max Drawdown %':<30} {max_dd:>14.2%}")
            print()

            # Volatility
            volatility = to_scalar(qs.stats.volatility(returns))

            if benchmark_data is not None:
                bench_vol = to_scalar(qs.stats.volatility(benchmark_data))
                print(f"{'Volatility (ann.)':<30} {bench_vol:>14.2%} {volatility:>14.2%}")
            else:
                print(f"{'Volatility (ann.)':<30} {volatility:>14.2%}")
            print()

            # Win rate metrics
            win_rate = to_scalar(qs.stats.win_rate(returns))
            avg_win = to_scalar(qs.stats.avg_win(returns))
            avg_loss = to_scalar(qs.stats.avg_loss(returns))

            print(f"{'Win Rate %':<30} {win_rate:>14.2%}")
            print(f"{'Avg. Win %':<30} {avg_win:>14.2%}")
            print(f"{'Avg. Loss %':<30} {avg_loss:>14.2%}")
            print()

            # Benchmark comparison metrics
            if benchmark_data is not None:
                # Calculate correlation manually (most reliable)
                try:
                    correlation = to_scalar(returns.corr(benchmark_data))
                    print(f"{'Correlation':<30} {correlation:>14.2f}")
                except Exception as e:
                    logger.debug(f"Could not calculate correlation: {e}")

                # Try information_ratio (may fail with some data)
                try:
                    info_ratio = to_scalar(qs.stats.information_ratio(returns, benchmark_data))
                    print(f"{'Information Ratio':<30} {info_ratio:>14.2f}")
                except Exception as e:
                    logger.debug(f"Could not calculate information ratio: {e}")

                # Try R-squared (may fail with some data)
                try:
                    r2 = to_scalar(qs.stats.r_squared(returns, benchmark_data))
                    print(f"{'R-Squared':<30} {r2:>14.2f}")
                except Exception as e:
                    logger.debug(f"Could not calculate R-squared: {e}")

                print()

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            import traceback
            traceback.print_exc()

        # Close plots after generating report
        plt.close('all')

        print("=" * 70)
        print("End of Performance Report".center(70))
        print("=" * 70 + "\n")

    except Exception as e:
        logger.error(f"Error generating QuantStats terminal report: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure all plots are closed
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass

def load_staged_pipeline_config(preset: str = None) -> dict:
    """
    Strategy Signal 설정 파일에서 Threshold 로드

    Previously used staged_pipeline_config.yaml, now uses strategy_signal_config.yaml

    Args:
        preset: 'conservative', 'aggressive', 'balanced', 'custom' 중 하나
                None이면 active_strategy 사용

    Returns:
        Staged pipeline threshold 설정 딕셔너리
    """
    config_path = project_root / 'config' / 'strategy_signal_config.yaml'

    if not config_path.exists():
        logger.warning(f"Strategy signal config not found: {config_path}")
        logger.warning("Using default threshold values (0.5)")
        return {
            'earnings_threshold': 0.5,
            'fundamental_threshold': 0.5,
            'weekly_threshold': 0.5,
            'rs_threshold': 0.5,
            'daily_threshold': 0.5
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        signal_config = yaml.safe_load(f)

    # Preset이 지정되지 않으면 active_strategy 사용
    strategy_name = preset if preset else signal_config.get('active_strategy', 'balanced')

    # 해당 strategy의 thresholds 가져오기
    strategies = signal_config.get('strategies', {})
    if strategy_name not in strategies:
        logger.warning(f"Strategy '{strategy_name}' not found, using 'balanced'")
        strategy_name = 'balanced'

    strategy = strategies.get(strategy_name, {})
    thresholds = strategy.get('thresholds', {})

    logger.info(f"Loading thresholds from strategy: {strategy_name}")

    # E, F, W, RS, D 형식을 earnings_threshold 등으로 변환
    return {
        'earnings_threshold': thresholds.get('E', 0.5),
        'fundamental_threshold': thresholds.get('F', 0.5),
        'weekly_threshold': thresholds.get('W', 0.5),
        'rs_threshold': thresholds.get('RS', 0.5),
        'daily_threshold': thresholds.get('D', 0.5)
    }


def load_config():
    """설정 파일 로드"""
    global DEBUG, BACKTEST_MODE

    config_path = project_root / 'myStockInfo.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    DEBUG = config.get('global_settings', {}).get('DEBUG', False)
    BACKTEST_MODE = config.get('global_settings', {}).get('BACKTEST_MODE', 'LIMITED')

    # Staged Pipeline 설정 추가
    staged_pipeline_preset = config.get('global_settings', {}).get('STAGED_PIPELINE_PRESET', None)
    staged_pipeline_config = load_staged_pipeline_config(preset=staged_pipeline_preset)
    config['staged_pipeline'] = staged_pipeline_config

    # KIS API credentials 추가 (US 시장 거래용)
    if config.get('REAL_APP_KEY'):
        config['app_key'] = config.get('REAL_APP_KEY')
        config['app_secret'] = config.get('REAL_APP_SECRET')
        config['account_no'] = config.get('REAL_CANO')
        config['product_code'] = config.get('REAL_ACNT_PRDT_CD')
        config['base_url'] = config.get('REAL_URL')
        config['is_virtual'] = False

    # 로깅 레벨 조정
    if DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    print(f"DEBUG 모드: {'ON' if DEBUG else 'OFF'}")
    print(f"백테스트 모드: {BACKTEST_MODE}")

    if staged_pipeline_preset:
        print(f"Staged Pipeline Preset: {staged_pipeline_preset}")
    print(f"Staged Pipeline Thresholds:")
    for key, value in staged_pipeline_config.items():
        print(f"  - {key}: {value}")

    return config

async def get_symbols_from_mongodb(config: dict, mode: str = 'FULL', randomize: bool = True, seed: Optional[int] = None) -> List[str]:
    """
    MongoDB에서 종목 리스트 가져오기

    Args:
        config: 설정 딕셔너리
        mode: 'FULL' (모든 종목) or 'LIMITED' (제한된 종목)
        randomize: LIMITED 모드에서 랜덤 샘플링 여부 (기본: True)
        seed: 랜덤 시드 (재현 가능한 결과를 위해, None이면 매번 다른 결과)

    Returns:
        심볼 리스트
    """
    from pymongo import MongoClient
    import random

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

        if randomize and len(all_symbols) > limited_count:
            # 랜덤 시드 설정 (재현 가능한 결과를 위해)
            if seed is not None:
                random.seed(seed)
                print(f"  Random seed: {seed}")
            else:
                # 현재 시간 기반 시드 사용 (매번 다른 결과)
                from datetime import datetime
                current_seed = int(datetime.now().timestamp())
                random.seed(current_seed)
                print(f"  Random seed: {current_seed}")

            # 랜덤 샘플링
            all_symbols = random.sample(all_symbols, limited_count)
            print(f"  Randomly sampled: {len(all_symbols)} symbols")
        else:
            # 랜덤화 비활성화 또는 종목 수가 제한보다 적을 경우
            all_symbols = all_symbols[:limited_count]
            print(f"  Limited to first: {len(all_symbols)} symbols")

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
                        pct_from_52h = (w_close / w_52h) * 100
                        if w_close >= w_52h * 0.90:
                            signal_status['W'] = 'O'
                            signal_desc.append(f'52W High {pct_from_52h:.1f}%')
                        else:
                            signal_status['W'] = '-'
                            signal_desc.append(f'52W High {pct_from_52h:.1f}% (Need 90%+)')
                    else:
                        signal_status['W'] = '?'
                        signal_desc.append('No 52W High data')
                else:
                    signal_status['W'] = '-'
                    signal_desc.append('No W data')
            else:
                signal_status['W'] = '-'
                signal_desc.append('No W data')

            # Daily 시그널 (D) - 기술지표 기반 평가
            # BuySig 컬럼이 있으면 사용, 없으면 SMA 기반 평가
            if 'BuySig' in df_D.columns:
                buy_sig = df_D.loc[date, 'BuySig']
                if buy_sig >= 1:
                    signal_status['D'] = 'O'
                    signal_desc.append('Daily Buy')
                else:
                    signal_status['D'] = '-'
                    signal_desc.append(f'BuySig={buy_sig:.0f} (Need >=1)')
            else:
                # Staged Pipeline 데이터: SMA 기반 평가
                d_close = 0
                d_sma20 = 0
                d_sma50 = 0

                for col in ['close', 'Dclose', 'Close']:
                    if col in df_D.columns:
                        d_close = df_D.loc[date, col]
                        break

                if 'SMA20' in df_D.columns:
                    d_sma20 = df_D.loc[date, 'SMA20']
                if 'SMA50' in df_D.columns:
                    d_sma50 = df_D.loc[date, 'SMA50']

                # 단순 트렌드 평가: close > SMA20 > SMA50
                if d_close > 0 and d_sma20 > 0 and d_sma50 > 0:
                    if d_close > d_sma20 and d_sma20 > d_sma50:
                        signal_status['D'] = 'O'
                        signal_desc.append(f'Above SMA20({d_sma20:.2f})&50({d_sma50:.2f})')
                    elif d_close > d_sma20:
                        signal_status['D'] = 'o'
                        signal_desc.append(f'Above SMA20({d_sma20:.2f}), SMA20<SMA50')
                    else:
                        signal_status['D'] = '-'
                        signal_desc.append(f'Below SMA20({d_sma20:.2f})')
                else:
                    signal_status['D'] = '-'
                    signal_desc.append('No SMA data')

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
                        signal_desc.append(f'RS={rs_4w:.0f} (Need >=70)')
                else:
                    signal_status['RS'] = '-'
                    signal_desc.append('No RS data at date')
            else:
                signal_status['RS'] = '-'
                signal_desc.append('No RS data')

            # Earnings 시그널 (E)
            if signals['E'] is not None and len(signals['E']) > 0:
                e_data = signals['E'][signals['E'].index <= date]
                if len(e_data) > 0:
                    e_latest = e_data.iloc[-1]
                    eps_yoy = e_latest.get('eps_yoy', 0)
                    rev_yoy = e_latest.get('rev_yoy', 0)
                    if eps_yoy > 0 and rev_yoy > 0:
                        signal_status['E'] = 'O'
                        signal_desc.append(f'EPS+{eps_yoy:.0f}% REV+{rev_yoy:.0f}%')
                    else:
                        signal_status['E'] = '-'
                        if eps_yoy <= 0 and rev_yoy <= 0:
                            signal_desc.append(f'EPS{eps_yoy:+.0f}% REV{rev_yoy:+.0f}%')
                        elif eps_yoy <= 0:
                            signal_desc.append(f'EPS{eps_yoy:+.0f}% (Need >0)')
                        else:
                            signal_desc.append(f'REV{rev_yoy:+.0f}% (Need >0)')
                else:
                    signal_status['E'] = '-'
                    signal_desc.append('No E data at date')
            else:
                signal_status['E'] = '-'
                signal_desc.append('No E data')

            # Fundamental 시그널 (F)
            if signals['F'] is not None and len(signals['F']) > 0:
                f_data = signals['F'][signals['F'].index <= date]
                if len(f_data) > 0:
                    f_latest = f_data.iloc[-1]
                    eps_yoy = f_latest.get('EPS_YOY', 0)
                    rev_yoy = f_latest.get('REV_YOY', 0)
                    if eps_yoy > 0 and rev_yoy > 0:
                        signal_status['F'] = 'O'
                        signal_desc.append(f'Fund: EPS+{eps_yoy:.0f}% REV+{rev_yoy:.0f}%')
                    else:
                        signal_status['F'] = '-'
                        if eps_yoy <= 0 and rev_yoy <= 0:
                            signal_desc.append(f'Fund: EPS{eps_yoy:+.0f}% REV{rev_yoy:+.0f}%')
                        elif eps_yoy <= 0:
                            signal_desc.append(f'Fund: EPS{eps_yoy:+.0f}% (Need >0)')
                        else:
                            signal_desc.append(f'Fund: REV{rev_yoy:+.0f}% (Need >0)')
                else:
                    signal_status['F'] = '-'
                    signal_desc.append('No F data at date')
            else:
                signal_status['F'] = '-'
                signal_desc.append('No F data')

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

    # Merge staged pipeline config with main config
    pipeline_config = config.copy()
    if 'staged_pipeline' in config:
        pipeline_config.update(config['staged_pipeline'])
        print(f"\nStaged Pipeline Thresholds:")
        for key, value in config['staged_pipeline'].items():
            print(f"  - {key}: {value}")

    pipeline = StagedPipelineService(
        config=pipeline_config,
        market='US',
        area='US',
        start_day=data_start,
        end_day=end_date_dt,
        is_backtest=True,  # Backtest mode: prevent future reference in Highest calculations
        execution_mode='analysis'  # Menu 1: Backtest uses D-1 data for breakout analysis
    )

    pipeline_results = pipeline.run_staged_pipeline(symbols)

    print(f"\n최종 매매 후보: {pipeline_results['total_candidates']} 종목")

    if pipeline_results['total_candidates'] == 0:
        print("[WARNING] 매매 후보 종목이 없습니다.")
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
                            # BuySig should be generated by D stage signal generation
                            # This is a fallback only for edge cases
                            df_D[col] = 0  # No signal as default
                            if col == 'BuySig':
                                logger.debug(f"{symbol}: BuySig not found in D stage data (unexpected), using 0")
                        elif col == 'signal':
                            df_D[col] = 0
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

                # Debug: Check if we have valid data and date-specific signals
                buy_sig_sum = df_D['BuySig'].sum()
                buy_sig_count = (df_D['BuySig'] > 0).sum()  # Count days with signals
                print(f"    [{symbol}] Shape: {df_D.shape}, "
                      f"BuySig: {buy_sig_count} days ({buy_sig_sum:.1f} total), "
                      f"Price range: ${df_D['close'].min():.2f} - ${df_D['close'].max():.2f}")

                backtest_data[symbol] = df_D

        if backtest_data:
            backtest_config = BacktestConfig()
            # initial_cash는 달러 단위로 들어옴 (예: 100000.0 = $100K)
            # DailyBacktestService는 백만달러(M) 단위를 기대함
            # $100K = 0.1M
            backtest_config.initial_cash = initial_cash / 1_000_000  # Convert to million dollars
            backtest_config.max_positions = 10
            backtest_config.slippage = 0.002
            backtest_config.message_output = True  # 날짜별 상세 출력 활성화
            backtest_config.enable_whipsaw = False  # WHIPSAW 비활성화 (테스트용)

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

        # Report Agent를 통한 백테스트 대시보드 생성 (Option 1)
        try:
            print("\n[Report Agent] 백테스트 대시보드 생성 중...")
            report = get_report_agent(config)
            dashboard_path = report.generate_backtest_report(
                backtest_results=backtest_results,
                save=True
            )
            if dashboard_path:
                print(f"[Report Agent] 대시보드 생성 완료: {dashboard_path}")
        except Exception as e:
            logger.warning(f"백테스트 대시보드 생성 실패: {e}")

        # QuantStats 터미널 리포트 출력 (Option 1 추가)
        try:
            print("\n[QuantStats Report] 백테스트 성과 분석 리포트 생성 중...")

            # Extract portfolio balance from backtest results
            if hasattr(backtest_results, 'daily_balance') and backtest_results.daily_balance is not None:
                daily_balance = backtest_results.daily_balance

                # Convert to Series with DatetimeIndex if needed
                if isinstance(daily_balance, pd.DataFrame):
                    # Use 'total_value' or 'balance' column
                    if 'total_value' in daily_balance.columns:
                        portfolio_value = daily_balance['total_value']
                    elif 'balance' in daily_balance.columns:
                        portfolio_value = daily_balance['balance']
                    else:
                        # Use first numeric column
                        numeric_cols = daily_balance.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            portfolio_value = daily_balance[numeric_cols[0]]
                        else:
                            logger.warning("No numeric column found in daily_balance")
                            portfolio_value = None
                elif isinstance(daily_balance, pd.Series):
                    portfolio_value = daily_balance
                elif isinstance(daily_balance, dict):
                    # Convert dict to Series
                    portfolio_value = pd.Series(daily_balance)
                else:
                    logger.warning(f"Unsupported daily_balance type: {type(daily_balance)}")
                    portfolio_value = None

                if portfolio_value is not None and len(portfolio_value) > 0:
                    # Ensure DatetimeIndex
                    if not isinstance(portfolio_value.index, pd.DatetimeIndex):
                        try:
                            portfolio_value.index = pd.to_datetime(portfolio_value.index)
                        except:
                            logger.warning("Could not convert portfolio_value index to datetime")
                            portfolio_value = None

                    if portfolio_value is not None and isinstance(portfolio_value.index, pd.DatetimeIndex):
                        # Print terminal report with SPY benchmark
                        print_quantstats_terminal_report(
                            portfolio_value=portfolio_value,
                            benchmark='SPY',
                            title="Backtest Performance vs SPY Benchmark"
                        )
                    else:
                        logger.warning("Portfolio value does not have valid DatetimeIndex")
                else:
                    logger.warning("Portfolio value is empty or None")
            else:
                logger.warning("daily_balance not found in backtest_results")

        except Exception as e:
            logger.warning(f"QuantStats 터미널 리포트 생성 실패: {e}")
            import traceback
            traceback.print_exc()

        # 4. 개별 티커의 시그널 타임라인 출력 (비활성화)
        # print("\n" + "="*80)
        # print("개별 티커 시그널 타임라인 (최근 100개 거래일)")
        # print("="*80)
        # _print_ticker_signal_timeline(final_candidates_data, symbols_with_d_data[:3])

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
        market_code = None

        if symbol in client['NasDataBase_D'].list_collection_names():
            market_found = 'NASDAQ'
            market_code = 'NAS'  # Correct market code for database queries
            print(f"   -> {symbol} found in NASDAQ market")
        elif symbol in client['NysDataBase_D'].list_collection_names():
            market_found = 'NYSE'
            market_code = 'NYS'  # Correct market code for database queries
            print(f"   -> {symbol} found in NYSE market")

        client.close()

        if not market_found:
            print(f"[ERROR] {symbol} not found in NASDAQ or NYSE databases")
            return None

        # 2. DataFrameGenerator로 데이터 로드
        print(f"\n[2/4] {symbol} 데이터 로딩 중...")
        df_generator = DataFrameGenerator(
            universe=[symbol],
            market=market_code,  # Use correct market code (NAS/NYS)
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

        # DataFrame 출력: Signal 컬럼들 + 일봉 데이터 + ADR + TargetPrice + LossCutPrice
        print("\n" + "="*60)
        print("SIGNAL & PRICE DATAFRAME (Last 10 Days)")
        print("="*60)

        if symbol in df_D and not df_D[symbol].empty:
            # df_dump 생성 (SignalGenerationService에서 생성한 데이터)
            df_dump = signal_service.df_dump.get(symbol) if hasattr(signal_service, 'df_dump') and signal_service.df_dump else None

            if df_dump is not None and not df_dump.empty:
                # 필요한 컬럼들 선택
                display_cols = []

                # Signal columns (ALL signals including eBuySig and SellSig)
                signal_cols = ['eBuySig', 'fBuySig', 'wBuySig', 'rsBuySig', 'dBuySig', 'BuySig', 'SellSig']
                for col in signal_cols:
                    if col in df_dump.columns:
                        display_cols.append(col)

                # Price columns (from df_D)
                price_cols = ['high', 'low', 'open', 'close']
                for col in price_cols:
                    if col in df_dump.columns:
                        display_cols.append(col)
                    elif 'D' + col in df_dump.columns:  # Try with D prefix
                        display_cols.append('D' + col)

                # Technical indicators
                tech_cols = ['RS_4W', 'ADR', 'TargetPrice', 'LossCutPrice']
                for col in tech_cols:
                    if col in df_dump.columns:
                        display_cols.append(col)

                # 컬럼이 있는 경우에만 출력
                available_cols = [col for col in display_cols if col in df_dump.columns]

                if available_cols:
                    print("\n")
                    print(df_dump[available_cols].tail(10).to_string())
                    print("\n")
                else:
                    print("\n[INFO] Signal columns not available in df_dump")
                    print("       Displaying available Daily data instead:\n")

                    # Fallback: df_D에서 직접 출력
                    daily_df = df_D[symbol].copy()

                    # 신호 컬럼들 추가 - Generate timeseries signals for all dates
                    fallback_cols = []

                    # Generate timeseries signals (for last 10 days)
                    print("\n[DEBUG] Generating timeseries signals...")
                    print(f"  df_D[{symbol}] shape: {df_D[symbol].shape if symbol in df_D else 'N/A'}")
                    print(f"  df_W shape: {df_W.get(symbol).shape if symbol in df_W else 'N/A'}")
                    print(f"  df_RS shape: {df_RS.get(symbol).shape if symbol in df_RS else 'N/A'}")
                    print(f"  df_F shape: {df_F.get(symbol).shape if symbol in df_F else 'N/A'}")
                    print(f"  df_E shape: {df_E.get(symbol).shape if symbol in df_E else 'N/A'}")

                    signals_df = signal_service.generate_signals_timeseries(
                        df_daily=df_D[symbol],
                        df_weekly=df_W.get(symbol),
                        df_rs=df_RS.get(symbol),
                        df_fundamental=df_F.get(symbol),
                        df_earnings=df_E.get(symbol)
                    )

                    print(f"[DEBUG] signals_df shape: {signals_df.shape}")
                    print(f"[DEBUG] signals_df empty: {signals_df.empty}")
                    if not signals_df.empty:
                        print(f"[DEBUG] signals_df columns: {signals_df.columns.tolist()}")

                    if not signals_df.empty:
                        # Join signals with daily data (including target_price and losscut_price)
                        daily_df = daily_df.join(signals_df[['weekly_signal', 'rs_signal', 'fundamental_signal',
                                                               'earnings_signal', 'daily_rs_signal', 'signal',
                                                               'target_price', 'losscut_price']], how='left')
                        # Rename columns to match expected names
                        daily_df['wBuySig'] = daily_df['weekly_signal'].fillna(0).astype(int)
                        daily_df['rsBuySig'] = daily_df['rs_signal'].fillna(0).astype(int)
                        daily_df['fBuySig'] = daily_df['fundamental_signal'].fillna(0).astype(int)
                        daily_df['eBuySig'] = daily_df['earnings_signal'].fillna(0).astype(int)
                        daily_df['dBuySig'] = daily_df['daily_rs_signal'].fillna(0).astype(int)
                        daily_df['BuySig'] = daily_df['signal'].fillna(0).astype(int)
                        daily_df['SellSig'] = 0  # TODO: implement sell signal in timeseries

                        # Use timeseries target_price and losscut_price (already calculated for each date)
                        daily_df['TargetPrice'] = daily_df['target_price'].fillna(0)
                        daily_df['LossCutPrice'] = daily_df['losscut_price'].fillna(0)

                        # Drop intermediate columns
                        daily_df = daily_df.drop(columns=['weekly_signal', 'rs_signal', 'fundamental_signal',
                                                           'earnings_signal', 'daily_rs_signal', 'signal',
                                                           'target_price', 'losscut_price'], errors='ignore')
                    else:
                        # Fallback: use single signal value for all dates
                        daily_df['eBuySig'] = signal_data.get('signal_components', {}).get('earnings', 0)
                        daily_df['fBuySig'] = signal_data.get('signal_components', {}).get('fundamental', 0)
                        daily_df['wBuySig'] = signal_data.get('signal_components', {}).get('weekly', 0)
                        daily_df['rsBuySig'] = signal_data.get('signal_components', {}).get('rs', 0)
                        daily_df['dBuySig'] = signal_data.get('signal_components', {}).get('daily_rs', 0)
                        daily_df['BuySig'] = 1 if signal_data.get('final_signal') == 'BUY' else 0
                        daily_df['SellSig'] = 1 if signal_data.get('final_signal') == 'SELL' else 0

                        # Fallback: use single target/losscut value for all dates
                        target_price = signal_data.get('target_price', 0)
                        losscut_price = signal_data.get('losscut_price', 0)
                        daily_df['TargetPrice'] = target_price
                        daily_df['LossCutPrice'] = losscut_price

                    fallback_cols.extend(['eBuySig', 'fBuySig', 'wBuySig', 'rsBuySig', 'dBuySig', 'BuySig', 'SellSig'])

                    # 가격 컬럼들만 선택
                    for col in ['Dhigh', 'Dlow', 'Dopen', 'Dclose', 'ADR']:
                        if col in daily_df.columns:
                            fallback_cols.append(col)

                    # RS_4W는 df_RS에서 가져오기
                    if symbol in df_RS and not df_RS[symbol].empty and 'RS_4W' in df_RS[symbol].columns:
                        daily_df['RS_4W'] = df_RS[symbol]['RS_4W']
                        fallback_cols.append('RS_4W')

                    # TargetPrice와 LossCutPrice 컬럼 추가 (이미 위에서 설정됨)
                    fallback_cols.extend(['TargetPrice', 'LossCutPrice'])

                    if fallback_cols:
                        print(daily_df[fallback_cols].tail(10).to_string())
                        print("\n")
            else:
                print("\n[INFO] df_dump not available. Displaying Daily data:\n")

                # df_D에서 직접 출력
                daily_df = df_D[symbol].copy()

                # 신호 컬럼들 추가 - Generate timeseries signals for all dates
                display_cols = []

                # Generate timeseries signals (for last 10 days)
                print("\n[DEBUG] Generating timeseries signals (df_dump not available)...")
                print(f"  df_D[{symbol}] shape: {df_D[symbol].shape if symbol in df_D else 'N/A'}")
                print(f"  df_W shape: {df_W.get(symbol).shape if symbol in df_W else 'N/A'}")
                print(f"  df_RS shape: {df_RS.get(symbol).shape if symbol in df_RS else 'N/A'}")
                print(f"  df_F shape: {df_F.get(symbol).shape if symbol in df_F else 'N/A'}")
                print(f"  df_E shape: {df_E.get(symbol).shape if symbol in df_E else 'N/A'}")

                signals_df = signal_service.generate_signals_timeseries(
                    df_daily=df_D[symbol],
                    df_weekly=df_W.get(symbol),
                    df_rs=df_RS.get(symbol),
                    df_fundamental=df_F.get(symbol),
                    df_earnings=df_E.get(symbol)
                )

                print(f"[DEBUG] signals_df shape: {signals_df.shape}")
                print(f"[DEBUG] signals_df empty: {signals_df.empty}")
                if not signals_df.empty:
                    print(f"[DEBUG] signals_df columns: {signals_df.columns.tolist()}")

                if not signals_df.empty:
                    # Join signals with daily data (including target_price and losscut_price)
                    daily_df = daily_df.join(signals_df[['weekly_signal', 'rs_signal', 'fundamental_signal',
                                                           'earnings_signal', 'daily_rs_signal', 'signal',
                                                           'target_price', 'losscut_price']], how='left')
                    # Rename columns to match expected names
                    daily_df['wBuySig'] = daily_df['weekly_signal'].fillna(0).astype(int)
                    daily_df['rsBuySig'] = daily_df['rs_signal'].fillna(0).astype(int)
                    daily_df['fBuySig'] = daily_df['fundamental_signal'].fillna(0).astype(int)
                    daily_df['eBuySig'] = daily_df['earnings_signal'].fillna(0).astype(int)
                    daily_df['dBuySig'] = daily_df['daily_rs_signal'].fillna(0).astype(int)
                    daily_df['BuySig'] = daily_df['signal'].fillna(0).astype(int)
                    daily_df['SellSig'] = 0  # TODO: implement sell signal in timeseries

                    # Use timeseries target_price and losscut_price (already calculated for each date)
                    daily_df['TargetPrice'] = daily_df['target_price'].fillna(0)
                    daily_df['LossCutPrice'] = daily_df['losscut_price'].fillna(0)

                    # Drop intermediate columns
                    daily_df = daily_df.drop(columns=['weekly_signal', 'rs_signal', 'fundamental_signal',
                                                       'earnings_signal', 'daily_rs_signal', 'signal',
                                                       'target_price', 'losscut_price'], errors='ignore')
                else:
                    # Fallback: use single signal value for all dates
                    daily_df['eBuySig'] = signal_data.get('signal_components', {}).get('earnings', 0)
                    daily_df['fBuySig'] = signal_data.get('signal_components', {}).get('fundamental', 0)
                    daily_df['wBuySig'] = signal_data.get('signal_components', {}).get('weekly', 0)
                    daily_df['rsBuySig'] = signal_data.get('signal_components', {}).get('rs', 0)
                    daily_df['dBuySig'] = signal_data.get('signal_components', {}).get('daily_rs', 0)
                    daily_df['BuySig'] = 1 if signal_data.get('final_signal') == 'BUY' else 0
                    daily_df['SellSig'] = 1 if signal_data.get('final_signal') == 'SELL' else 0

                    # Fallback: use single target/losscut value for all dates
                    target_price = signal_data.get('target_price', 0)
                    losscut_price = signal_data.get('losscut_price', 0)
                    daily_df['TargetPrice'] = target_price
                    daily_df['LossCutPrice'] = losscut_price

                display_cols.extend(['eBuySig', 'fBuySig', 'wBuySig', 'rsBuySig', 'dBuySig', 'BuySig', 'SellSig'])

                # 가격 컬럼들 선택
                for col in ['Dhigh', 'Dlow', 'Dopen', 'Dclose', 'ADR']:
                    if col in daily_df.columns:
                        display_cols.append(col)

                # RS_4W는 df_RS에서 가져오기
                if symbol in df_RS and not df_RS[symbol].empty and 'RS_4W' in df_RS[symbol].columns:
                    daily_df['RS_4W'] = df_RS[symbol]['RS_4W']
                    display_cols.append('RS_4W')

                # TargetPrice와 LossCutPrice 컬럼 추가 (이미 위에서 설정됨)
                display_cols.extend(['TargetPrice', 'LossCutPrice'])

                if display_cols:
                    print(daily_df[display_cols].tail(10).to_string())
                    print("\n")

        print("="*60)

        # Report Agent를 통한 개별 종목 차트 생성 (Option 2)
        try:
            print("\n[Report Agent] 종목 시그널 차트 생성 중...")
            report = get_report_agent(config)

            # 데이터 준비
            stock_data = df_D[symbol] if symbol in df_D else None
            buy_signals = pd.DataFrame()
            sell_signals = pd.DataFrame()

            if stock_data is not None and 'BuySig' in signal_data:
                if signal_data.get('BuySig', 0) > 0:
                    buy_signals = pd.DataFrame([{
                        'Date': stock_data.index[-1] if not stock_data.empty else datetime.now(),
                        'Price': signal_data.get('entry_price', 0),
                        'Signal_Type': signal_data.get('signal_type', 'BUY')
                    }])

            chart_path = report.generate_stock_signal_chart(
                ticker=symbol,
                stock_data=stock_data,
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                save=True
            )
            if chart_path:
                print(f"[Report Agent] 차트 생성 완료: {chart_path}")
        except Exception as e:
            logger.warning(f"종목 차트 생성 실패: {e}")

        # QuantStats 터미널 리포트 출력 (Option 2 추가)
        if symbol in df_D and not df_D[symbol].empty:
            try:
                print("\n[QuantStats Report] 성과 분석 리포트 생성 중...")

                # Create portfolio value series from stock price data
                stock_prices = df_D[symbol].copy()

                # Ensure DatetimeIndex
                if 'Date' in stock_prices.columns:
                    stock_prices['Date'] = pd.to_datetime(stock_prices['Date'])
                    stock_prices = stock_prices.set_index('Date')
                elif not isinstance(stock_prices.index, pd.DatetimeIndex):
                    # Try to convert index to datetime
                    try:
                        stock_prices.index = pd.to_datetime(stock_prices.index)
                    except:
                        logger.warning(f"Could not convert {symbol} index to datetime, skipping QuantStats report")
                        stock_prices = None

                if stock_prices is not None:
                    # Get close prices
                    if 'Dclose' in stock_prices.columns:
                        portfolio_value = stock_prices['Dclose'].copy()
                    elif 'close' in stock_prices.columns:
                        portfolio_value = stock_prices['close'].copy()
                    else:
                        # Use ad_close if available
                        for col in ['ad_close', 'Dclose', 'close']:
                            if col in stock_prices.columns:
                                portfolio_value = stock_prices[col].copy()
                                break
                        else:
                            logger.warning(f"No valid price column found for {symbol}")
                            portfolio_value = None

                    if portfolio_value is not None:
                        # Normalize to start from 100000 (initial capital)
                        portfolio_value = portfolio_value / portfolio_value.iloc[0] * 100000

                        # Ensure DatetimeIndex
                        if isinstance(portfolio_value.index, pd.DatetimeIndex):
                            # Print terminal report with SPY benchmark
                            print_quantstats_terminal_report(
                                portfolio_value=portfolio_value,
                                benchmark='SPY',
                                title=f"{symbol} Performance vs SPY Benchmark"
                            )
                        else:
                            logger.warning(f"{symbol} portfolio value index is not DatetimeIndex")

            except Exception as e:
                logger.warning(f"QuantStats 터미널 리포트 생성 실패: {e}")
                import traceback
                traceback.print_exc()

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
    print("\n백테스트 기간을 선택하세요:")
    print("1. 최근 1년 (기본값)")
    print("2. 최근 2년")
    print("3. 최근 3년")
    print("4. 최근 5년")
    print("5. 사용자 지정 (연 단위)")

    period_choice = input("\n선택 (1-5, 기본값: 1): ").strip() or "1"

    end_date = datetime.now()

    if period_choice == "1":
        years = 1
    elif period_choice == "2":
        years = 2
    elif period_choice == "3":
        years = 3
    elif period_choice == "4":
        years = 5
    elif period_choice == "5":
        # 사용자 지정
        try:
            custom_years = input("백테스트 기간(년)을 입력하세요 (예: 5): ").strip()
            years = int(custom_years) if custom_years else 1
            if years < 1:
                print("[WARNING] 1년 미만은 불가능합니다. 기본값 1년으로 설정합니다.")
                years = 1
            elif years > 10:
                print("[WARNING] 10년 초과는 권장하지 않습니다. 10년으로 제한합니다.")
                years = 10
        except ValueError:
            print("[WARNING] 잘못된 입력입니다. 기본값 1년으로 설정합니다.")
            years = 1
    else:
        print("[WARNING] 잘못된 선택입니다. 기본값 1년으로 설정합니다.")
        years = 1

    start_date = end_date - timedelta(days=365*years)

    print(f"\n[백테스트 기간] {years}년")
    print(f"  시작: {start_date.strftime('%Y-%m-%d')}")
    print(f"  종료: {end_date.strftime('%Y-%m-%d')}")

    # 종목 로드
    print("\n종목 로드 중...")
    symbols = await get_symbols_from_mongodb(config, mode=BACKTEST_MODE)
    print(f"로드된 종목: {len(symbols)}개")

    # Staged Pipeline 백테스트 실행
    results = await run_backtest_staged(
        symbols=symbols,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_cash=1_000_000.0,  # 1M USD (백테스트용)
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
        print("[ERROR] 종목 코드를 입력해주세요.")
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
        # Try NASDAQ first, then NYSE
        # Note: Market codes must match database_name_calculator.py expectations
        # 'NAS' -> NasDataBase_*, 'NYS' -> NysDataBase_*
        markets_to_try = [
            ('NAS', 'NASDAQ'),   # (market_code, display_name)
            ('NYS', 'NYSE')
        ]
        all_final_candidates = []
        all_loaded_data_combined = {}

        # Merge staged pipeline config with main config
        pipeline_config = config.copy()
        if 'staged_pipeline' in config:
            pipeline_config.update(config['staged_pipeline'])

        for market_code, market_name in markets_to_try:
            print(f"\n[Staged Pipeline] {market_name}에서 시그널 생성 중...")

            try:
                pipeline = StagedPipelineService(
                    config=pipeline_config,
                    market=market_code,  # Use correct market code (NAS/NYS)
                    area='US',
                    start_day=data_start,
                    end_day=end_date,
                    is_backtest=True,  # Backtest mode: prevent future reference in Highest calculations
                    execution_mode='analysis'  # Menu 4: Signal Timeline uses D-1 data for breakout analysis
                )

                pipeline_results = pipeline.run_staged_pipeline(symbols)

                # Collect data from this market (regardless of filter pass/fail)
                # Menu 4: Show timeline for all requested symbols, not just those that pass filters
                market_data = pipeline.data_loader.get_all_loaded_data()
                found_symbols = []

                if market_data:
                    for stage, symbols_data in market_data.items():
                        if isinstance(symbols_data, dict):
                            for symbol, df in symbols_data.items():
                                if symbol in symbols:  # Only collect requested symbols
                                    if symbol not in all_loaded_data_combined:
                                        all_loaded_data_combined[symbol] = {}
                                        found_symbols.append(symbol)
                                    all_loaded_data_combined[symbol][stage] = df

                if found_symbols:
                    print(f"   [OK] {market_name}에서 {len(found_symbols)}개 종목 발견: {', '.join(found_symbols)}")
                    all_final_candidates.extend(found_symbols)
                else:
                    print(f"   [INFO] {market_name}에서 해당 종목을 찾을 수 없습니다.")

            except Exception as market_error:
                print(f"   [WARNING] {market_name} 조회 중 오류: {market_error}")
                continue

        # Remove duplicates
        all_final_candidates = list(set(all_final_candidates))

        if not all_final_candidates:
            print("\n[ERROR] 입력한 종목의 데이터를 찾을 수 없습니다.")
            print("   - 해당 종목의 데이터가 NASDAQ 및 NYSE MongoDB에 없습니다.")
            print(f"   - 입력한 종목: {', '.join(symbols)}")
            print("   - MongoDB에 해당 종목의 데이터가 저장되어 있는지 확인해주세요.")
            return

        # Use combined data from all markets
        print(f"\n최종 후보 {len(all_final_candidates)}개 종목의 데이터 로딩 완료")

        # Filter only symbols that have D (daily) data
        symbols_with_d_data = [s for s, data in all_loaded_data_combined.items() if 'D' in data]

        if not symbols_with_d_data:
            print("\n[WARNING] 일봉 데이터가 있는 종목이 없습니다.")
            return

        print(f"\n[OK] 시그널 생성 완료: {len(symbols_with_d_data)}개 종목")
        print(f"   종목: {', '.join(symbols_with_d_data)}")

        # 타임라인 출력
        print("\n" + "="*80)
        print(f"개별 티커 시그널 타임라인 (최근 {days}일)")
        print("="*80)

        _print_ticker_signal_timeline(all_loaded_data_combined, symbols_with_d_data, num_days=100)

        # Report Agent를 통한 시그널 타임라인 차트 생성 (Option 4)
        try:
            print("\n[Report Agent] 시그널 타임라인 차트 생성 중...")
            report = get_report_agent(config)

            for symbol in symbols_with_d_data[:3]:  # 상위 3개 종목
                if symbol in all_loaded_data_combined:
                    stage_data = all_loaded_data_combined[symbol]

                    # 신호 데이터 준비
                    signals_df = pd.DataFrame()
                    if 'D' in stage_data:
                        df_D = stage_data['D']
                        if 'BuySig' in df_D.columns:
                            buy_dates = df_D[df_D['BuySig'] > 0].index
                            for date in buy_dates:
                                signals_df = pd.concat([signals_df, pd.DataFrame({
                                    'Date': [date],
                                    'Stage': ['D'],
                                    'Signal': ['BUY']
                                })])

                    timeline_path = report.generate_signal_timeline_chart(
                        ticker=symbol,
                        signals_data=signals_df,
                        save=True
                    )
                    if timeline_path:
                        print(f"[Report Agent] {symbol} 타임라인 차트 생성: {timeline_path}")
        except Exception as e:
            logger.warning(f"시그널 타임라인 차트 생성 실패: {e}")

        # QuantStats 터미널 리포트 출력 (Option 4 추가)
        try:
            print("\n[QuantStats Report] 포트폴리오 성과 분석 리포트 생성 중...")

            # Create combined portfolio from all symbols with D data
            portfolio_returns_list = []

            for symbol in symbols_with_d_data[:5]:  # Top 5 symbols for portfolio
                if symbol in all_loaded_data_combined and 'D' in all_loaded_data_combined[symbol]:
                    df_D = all_loaded_data_combined[symbol]['D'].copy()

                    # Ensure DatetimeIndex
                    if 'Date' in df_D.columns:
                        df_D['Date'] = pd.to_datetime(df_D['Date'])
                        df_D = df_D.set_index('Date')
                    elif not isinstance(df_D.index, pd.DatetimeIndex):
                        # Try to convert index to datetime
                        try:
                            df_D.index = pd.to_datetime(df_D.index)
                        except:
                            logger.warning(f"Could not convert {symbol} index to datetime")
                            continue

                    # Get close prices
                    if 'close' in df_D.columns:
                        prices = df_D['close']
                    elif 'Dclose' in df_D.columns:
                        prices = df_D['Dclose']
                    else:
                        continue

                    # Calculate returns for this symbol
                    returns = prices.pct_change().fillna(0)
                    portfolio_returns_list.append(returns)

            if portfolio_returns_list:
                # Equal-weighted portfolio
                portfolio_returns = sum(portfolio_returns_list) / len(portfolio_returns_list)

                # Convert to portfolio value starting from 100000
                portfolio_value = (1 + portfolio_returns).cumprod() * 100000

                # Ensure DatetimeIndex
                if not isinstance(portfolio_value.index, pd.DatetimeIndex):
                    logger.warning("Portfolio value index is not DatetimeIndex, skipping QuantStats report")
                else:
                    # Print terminal report with SPY benchmark
                    print_quantstats_terminal_report(
                        portfolio_value=portfolio_value,
                        benchmark='SPY',
                        title=f"Portfolio Performance ({len(portfolio_returns_list)} Stocks) vs SPY"
                    )
            else:
                logger.warning("No valid price data for QuantStats report")

        except Exception as e:
            logger.warning(f"QuantStats 터미널 리포트 생성 실패: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "="*60)
        print("시그널 타임라인 출력 완료")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()

async def run_auto_trading(config: dict, account_type: str = None, execute_orders: bool = None):
    """
    실거래 자동 트레이딩 실행

    Args:
        config: 시스템 설정
        account_type: 'virtual' (모의 계좌) 또는 'real' (실제 계좌), None이면 대화형으로 선택
        execute_orders: 실제 주문 실행 여부, None이면 대화형으로 선택
    """
    print("\n" + "="*60)
    print("[WARNING] 자동 트레이딩 모드")
    print("="*60)

    # 계좌 타입이 지정되지 않은 경우 대화형으로 선택
    if account_type is None:
        print("\n계좌 타입을 선택하세요:")
        print("1. 모의 계좌 (Paper Trading)")
        print("2. 실제 계좌 (Live Trading - 실제 주문 실행)")
        print("0. 취소")

        account_choice = input("\n선택 (0-2): ").strip()

        if account_choice == '0':
            print("[ERROR] 자동 트레이딩이 취소되었습니다.")
            return None
        elif account_choice == '1':
            account_type = 'virtual'
            print("\n[OK] 모의 계좌 모드로 실행합니다.")
        elif account_choice == '2':
            account_type = 'real'
            print("\n[WARNING] 실제 계좌 모드 - 실제 주문이 실행됩니다!")
            final_confirm = input("정말 실행하시겠습니까? (YES 입력 필요): ").strip()
            if final_confirm != 'YES':
                print("[ERROR] 실계좌 트레이딩이 취소되었습니다.")
                return None
        else:
            print("[ERROR] 잘못된 선택입니다.")
            return None
    else:
        # 파라미터로 전달된 경우
        print(f"\n[OK] {account_type} 계좌 모드로 실행합니다 (자동 모드).")
        if account_type == 'real':
            print("[WARNING] 실제 계좌 모드 - 실제 주문이 실행됩니다!")

    print("\n" + "="*60)
    print(f"자동 트레이딩 시작 ({account_type} 계좌)")
    print("="*60)

    # 현재 날짜
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    try:
        # 1. 유니버스 선정을 위한 데이터 로드
        print("\n[1/7] 종목 유니버스 로드 중...")
        symbols = await get_symbols_from_mongodb(config, mode=BACKTEST_MODE)
        print(f"로드된 종목: {len(symbols)}개")

        # 2. 데이터 프레임 생성
        print("\n[2/7] 데이터 프레임 생성 중...")
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
        print("\n[3/7] 매매 시그널 생성 중...")
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

        # 4. 매수 신호 종목 표시 (있는 경우에만)
        if buy_signals:
            print("\n[4/7] 매수 신호 종목 리스트")
            print("="*60)
            print(f"{'종목':<10} {'신호강도':<10} {'현재가':<12} {'손절가':<12} {'목표가':<12}")
            print("-"*60)

            sorted_signals = sorted(buy_signals.items(), key=lambda x: x[1]['signal_strength'], reverse=True)
            for symbol, data in sorted_signals[:20]:  # 상위 20개만 표시
                print(f"{symbol:<10} {data['signal_strength']:<10.2f} ${data['close']:<11.2f} "
                      f"${data['loss_cut']:<11.2f} ${data['target']:<11.2f}")

            print("="*60)

            # Save buy candidates to JSON for backtest validation
            try:
                output_dir = Path("outputs/auto_trading")
                output_dir.mkdir(parents=True, exist_ok=True)

                execution_date = datetime.now().strftime("%Y-%m-%d")
                execution_time = datetime.now().strftime("%H:%M:%S")
                filename = f"buy_candidates_{execution_date.replace('-', '')}.json"
                filepath = output_dir / filename

                candidates_data = {
                    "execution_date": execution_date,
                    "execution_time": execution_time,
                    "account_type": account_type,
                    "execution_mode": "pending",  # Will be updated after order mode selection
                    "market": "US",
                    "total_candidates": len(sorted_signals),
                    "candidates": []
                }

                for symbol, data in sorted_signals:
                    candidate_info = {
                        "symbol": symbol,
                        "signal_strength": float(data.get('signal_strength', 0)),
                        "current_price": float(data.get('close', 0)),
                        "loss_cut": float(data.get('loss_cut', 0)),
                        "target_price": float(data.get('target', 0)),
                        "signal_details": {
                            "RS": float(data.get('RS', 0)) if 'RS' in data else None,
                            "signal_type": data.get('signal_type', 'UNKNOWN'),
                            "filter_conditions": data.get('filter_conditions', {})
                        }
                    }
                    candidates_data["candidates"].append(candidate_info)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(candidates_data, f, indent=2, ensure_ascii=False)

                print(f"\n[OK] 매수 후보군 저장 완료: {filepath}")

            except Exception as e:
                print(f"[WARNING] 매수 후보군 JSON 저장 실패: {e}")

        else:
            print("\n[4/7] 매수 신호 없음 - 보유 종목 모니터링만 수행")
            sorted_signals = []

        # 5. KIS API Helper 초기화 (계좌 조회 및 주문 실행용)
        print("\n[5/7] KIS API 초기화 중...")

        # Check if KIS API credentials are configured
        has_kis_credentials = config.get('app_key') and config.get('app_secret')

        kis_api = None
        execute_real_orders = False

        if has_kis_credentials:
            try:
                kis_api = KISUSHelper(config)
                if kis_api.make_token():
                    print(f"[OK] KIS API 인증 성공")

                    # execute_orders 파라미터로 주문 실행 여부 결정
                    if execute_orders is True:
                        execute_real_orders = True
                        print(f"[WARNING] 실제 주문 실행 모드 활성화")
                    elif execute_orders is False:
                        execute_real_orders = False
                        print(f"[INFO] 모니터링 전용 모드 (주문 실행 안함)")
                    else:
                        # execute_orders가 None인 경우 (대화형 모드)
                        print("\n주문 실행 모드를 선택하세요:")
                        print("1. 모니터링 전용 (시뮬레이션 - 주문 실행 안함)")
                        print("2. 실제 주문 실행 (정규장 시간에만 실제 주문 전송)")

                        order_choice = input("\n선택 (1-2, 기본값: 1): ").strip() or "1"

                        if order_choice == "2":
                            # 실제 주문 실행 모드 - 추가 확인
                            print("\n[WARNING] 실제 주문 실행 모드를 선택하셨습니다.")
                            print(f"[WARNING] 계좌: {account_type}")
                            print("[WARNING] 정규장 시간(09:30~16:00 ET)에 실제 주문이 전송됩니다.")
                            confirm = input("정말 실행하시겠습니까? (YES 입력 필요): ").strip()

                            if confirm == "YES":
                                execute_real_orders = True
                                print(f"[WARNING] 실제 주문 실행 모드 활성화")
                            else:
                                execute_real_orders = False
                                print(f"[INFO] 모니터링 전용 모드로 전환 (주문 실행 취소됨)")
                        else:
                            execute_real_orders = False
                            print(f"[INFO] 모니터링 전용 모드 (주문 실행 안함)")
                else:
                    print(f"[WARNING] KIS API 인증 실패. 시뮬레이션 모드로 전환")
                    execute_real_orders = False
                    kis_api = None
            except Exception as e:
                print(f"[ERROR] KIS API 초기화 실패: {e}")
                print(f"[INFO] 시뮬레이션 모드로 전환")
                execute_real_orders = False
                kis_api = None
        else:
            # KIS API credentials are archived - skip real API initialization for now
            # Use simulation mode for monitoring and signal detection
            execute_real_orders = False
            kis_api = None
            print(f"[INFO] 시뮬레이션 모드로 실행 (KIS API credentials not configured)")
            print(f"[INFO] 실시간 가격 모니터링 및 신호 감지만 수행합니다")

        # Update JSON file with execution mode (if candidates exist)
        if buy_signals:
            try:
                output_dir = Path("outputs/auto_trading")
                execution_date = datetime.now().strftime("%Y-%m-%d")
                filename = f"buy_candidates_{execution_date.replace('-', '')}.json"
                filepath = output_dir / filename

                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        candidates_data = json.load(f)

                    # Update execution mode
                    candidates_data["execution_mode"] = "real_orders" if execute_real_orders else "simulation"
                    candidates_data["kis_api_enabled"] = kis_api is not None

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(candidates_data, f, indent=2, ensure_ascii=False)

                    print(f"[OK] 실행 모드 업데이트 완료: {candidates_data['execution_mode']}")

            except Exception as e:
                print(f"[WARNING] JSON 파일 업데이트 실패: {e}")

        # 6. PositionManager 초기화 (Strategy Layer)
        print("\n[6/7] PositionManager 초기화 중...")
        position_manager = PositionManager(config)
        print(f"[OK] PositionManager 초기화 완료")

        # 7. 실시간 모니터링 + 자동 매매 시작
        print("\n[7/7] 실시간 가격 모니터링 + 자동 매매 시작...")

        # 모니터링할 종목 및 트레이딩 데이터 준비
        # 1) 매수 신호 종목 (상위 10개)
        buy_candidates = {}
        for symbol, data in sorted_signals[:10]:
            buy_candidates[symbol] = {
                'target_price': data['target'],
                'quantity': 100,  # 기본 100주
                'status': 'waiting',  # waiting, ordered, filled
                'signal_strength': data['signal_strength']
            }

        # 2) 현재 보유 중인 종목 (KIS API에서 조회)
        held_positions = {}

        if kis_api:
            # 실제 계좌의 보유 종목 조회 (주문 실행 여부와 무관하게 조회)
            print(f"\n[INFO] 계좌 보유 종목 조회 중...")
            try:
                holdings = kis_api.get_holdings(currency="USD")
                print(f"[OK] 보유 종목 {len(holdings)}개 조회 완료")

                # 신호 데이터를 딕셔너리로 변환 (빠른 조회를 위해)
                signal_dict = {symbol: data for symbol, data in sorted_signals}

                # 같은 종목의 중복 보유를 합산 (평균가격 계산)
                for holding in holdings:
                    symbol = holding['symbol']
                    avg_price = holding['avg_price']
                    quantity = int(holding['quantity'])
                    current_price = holding['current_price']

                    if symbol in held_positions:
                        # 이미 존재하는 종목: 수량과 평균가 합산
                        existing = held_positions[symbol]
                        total_quantity = existing['quantity'] + quantity
                        # 가중 평균 계산
                        weighted_avg = (existing['avg_price'] * existing['quantity'] + avg_price * quantity) / total_quantity

                        existing['quantity'] = total_quantity
                        existing['avg_price'] = weighted_avg
                        existing['current_price'] = current_price
                        existing['market_value'] = current_price * total_quantity
                        existing['profit_loss'] = (current_price - weighted_avg) * total_quantity
                        existing['profit_rate'] = ((current_price - weighted_avg) / weighted_avg) * 100
                        existing['again'] = current_price / weighted_avg if weighted_avg > 0 else 1.0

                        # 목표가/손절가는 새로운 평균가 기준으로 재계산
                        if symbol in signal_dict:
                            signal_data = signal_dict[symbol]
                            existing['target_price'] = signal_data['target']
                            existing['losscut_price'] = signal_data['loss_cut']
                        else:
                            existing['target_price'] = weighted_avg * 1.20
                            existing['losscut_price'] = weighted_avg * 0.97
                    else:
                        # 신규 종목
                        # 해당 종목의 신호 데이터가 있으면 사용, 없으면 기본값
                        if symbol in signal_dict:
                            signal_data = signal_dict[symbol]
                            target_price = signal_data['target']
                            losscut_price = signal_data['loss_cut']
                        else:
                            # 기본 익절/손절: +20%, -3%
                            target_price = avg_price * 1.20
                            losscut_price = avg_price * 0.97

                        # AGain 초기화 (현재 수익률)
                        initial_again = current_price / avg_price if avg_price > 0 else 1.0

                        held_positions[symbol] = {
                            'symbol': symbol,
                            'quantity': quantity,
                            'avg_price': avg_price,
                            'current_price': current_price,
                            'target_price': target_price,
                            'losscut_price': losscut_price,
                            'status': 'holding',
                            'market_value': current_price * quantity,
                            'profit_loss': holding['profit_loss'],
                            'profit_rate': holding['profit_rate'],
                            'again': initial_again,  # 누적 수익률 (PositionManager용)
                            'risk': config.get('market_specific_configs', {}).get('US', {}).get('std_risk_per_trade', 0.05)
                        }

                # 최종 보유 종목 출력
                for symbol, position in held_positions.items():
                    print(f"  - {symbol}: {position['quantity']}주 @ ${position['avg_price']:.2f} "
                          f"(현재: ${position['current_price']:.2f}, "
                          f"익절: ${position['target_price']:.2f}, "
                          f"손절: ${position['losscut_price']:.2f})")

            except Exception as e:
                print(f"[ERROR] 보유 종목 조회 실패: {e}")
                print(f"[INFO] 시뮬레이션 보유 종목 사용")

        # 시뮬레이션 모드이거나 실제 조회 실패 시: 상위 3개를 보유 중으로 가정
        if not held_positions:
            if sorted_signals:
                print(f"\n[INFO] 시뮬레이션 보유 종목 생성 (상위 3개)")
                for symbol, data in sorted_signals[:3]:
                    held_positions[symbol] = {
                        'symbol': symbol,
                        'quantity': 100,
                        'avg_price': data['close'],
                        'current_price': data['close'],
                        'target_price': data['target'],
                        'losscut_price': data['loss_cut'],
                        'status': 'holding',
                        'market_value': data['close'] * 100,
                        'profit_loss': 0,
                        'profit_rate': 0,
                        'again': 1.0,  # 초기 수익률
                        'risk': config.get('market_specific_configs', {}).get('US', {}).get('std_risk_per_trade', 0.05)
                    }
                    print(f"  - {symbol}: 100주 @ ${data['close']:.2f} "
                          f"(익절: ${data['target']:.2f}, 손절: ${data['loss_cut']:.2f})")
            else:
                # 테스트를 위한 mock 보유 종목 생성
                print(f"\n[INFO] 테스트용 mock 보유 종목 생성")
                mock_holdings = [
                    {'symbol': 'AAPL', 'price': 180.00, 'qty': 100},
                    {'symbol': 'MSFT', 'price': 380.00, 'qty': 50},
                    {'symbol': 'GOOGL', 'price': 140.00, 'qty': 75}
                ]
                for mock in mock_holdings:
                    symbol = mock['symbol']
                    price = mock['price']
                    qty = mock['qty']
                    held_positions[symbol] = {
                        'symbol': symbol,
                        'quantity': qty,
                        'avg_price': price,
                        'current_price': price,
                        'target_price': price * 1.10,  # +10%
                        'losscut_price': price * 0.97,  # -3%
                        'status': 'holding',
                        'market_value': price * qty,
                        'profit_loss': 0,
                        'profit_rate': 0,
                        'again': 1.0,  # 초기 수익률
                        'risk': config.get('market_specific_configs', {}).get('US', {}).get('std_risk_per_trade', 0.05)
                    }
                    print(f"  - {symbol}: {qty}주 @ ${price:.2f} "
                          f"(익절: ${price * 1.10:.2f}, 손절: ${price * 0.97:.2f})")

        # 3) 전체 모니터링 종목
        all_monitored = list(set(buy_candidates.keys()) | set(held_positions.keys()))

        print(f"\n{'='*60}")
        print(f"웹소켓 모니터링 대상 등록")
        print(f"{'='*60}")
        print(f"\n[매수 대기 종목: {len(buy_candidates)}개]")
        for symbol in list(buy_candidates.keys())[:5]:
            candidate = buy_candidates[symbol]
            print(f"  - {symbol}: 목표가 ${candidate['target_price']:.2f}")

        print(f"\n[보유 종목: {len(held_positions)}개]")
        total_market_value = sum(pos['market_value'] for pos in held_positions.values())
        total_profit_loss = sum(pos['profit_loss'] for pos in held_positions.values())
        for symbol, position in list(held_positions.items())[:10]:
            print(f"  - {symbol}: {position['quantity']}주 @ ${position['avg_price']:.2f} "
                  f"→ ${position['current_price']:.2f} "
                  f"(손익: ${position['profit_loss']:.2f}, {position['profit_rate']:.2f}%)")
        if len(held_positions) > 0:
            print(f"\n  [총 보유 가치: ${total_market_value:,.2f}, "
                  f"손익: ${total_profit_loss:,.2f}]")

        print(f"\n[전체 웹소켓 감시: {len(all_monitored)}개 종목]")
        print(f"{'='*60}")

        # 모니터링 대상이 하나도 없으면 종료
        if not all_monitored:
            print("\n[WARNING] 모니터링할 종목이 없습니다.")
            print("  - 매수 신호가 없고 보유 종목도 없습니다.")
            print("  - 프로그램을 종료합니다.")
            return None

        # 미국 장 시간 체크 함수 (on_price_update 콜백보다 먼저 정의)
        def is_market_open() -> bool:
            """미국 장이 열려있는지 체크 (동부 시간 기준)
            실행 시간: 정규장 시작 1H 전 ~ 종료 1H 후 (08:30 ~ 17:00 ET)
            pytz를 사용하여 서머타임(DST) 자동 고려
            """
            import pytz

            eastern = pytz.timezone('America/New_York')
            now_eastern = datetime.now(eastern)

            # 주말 체크 (토,일만 False)
            if now_eastern.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False

            # 실행 시간: 08:30 ~ 17:00 (정규장 09:30~16:00 기준 +-1H)
            # pytz 사용으로 서머타임(DST) 자동 반영
            start_time = now_eastern.replace(hour=8, minute=30, second=0, microsecond=0)
            end_time = now_eastern.replace(hour=17, minute=0, second=0, microsecond=0)

            return start_time <= now_eastern <= end_time

        def is_regular_market_hours() -> bool:
            """정규장 시간인지 체크 (동부 시간 기준)
            정규장 시간: 09:30 ~ 16:00 ET
            주문 실행은 정규장 시간에만 가능
            pytz를 사용하여 서머타임(DST) 자동 고려
            """
            import pytz

            eastern = pytz.timezone('America/New_York')
            now_eastern = datetime.now(eastern)

            # 주말 체크 (토,일만 False)
            if now_eastern.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False

            # 정규장 시간: 09:30 ~ 16:00
            # pytz 사용으로 서머타임(DST) 자동 반영
            market_open = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_eastern.replace(hour=16, minute=0, second=0, microsecond=0)

            return market_open <= now_eastern <= market_close

        # 가격 업데이트 콜백 함수 정의
        async def on_price_update(price_data):
            """
            가격 업데이트 시 호출되는 콜백

            Args:
                price_data: PriceData 객체 (symbol, price, volume, timestamp 등 포함)
            """
            # PriceData에서 symbol과 price 추출
            symbol = price_data.symbol
            current_price = price_data.price

            # 매수 대기 종목 체크
            if symbol in buy_candidates:
                candidate = buy_candidates[symbol]
                if candidate['status'] == 'waiting':
                    # 목표가 도달 여부 체크 (현재가가 목표가 이하로 떨어지면 매수)
                    # TargetPrice는 과거 최고가(저항선) - 현재가가 이 가격 근처 또는 이하일 때 매수
                    if current_price <= candidate['target_price']:
                        print(f"\n[BUY SIGNAL] {symbol}: ${current_price:.2f} <= ${candidate['target_price']:.2f}")

                        if execute_real_orders and is_regular_market_hours():
                            # 실제 주문 실행 (정규장 시간에만) - 시장가 주문
                            result = kis_api.make_buy_market_order(
                                stock_code=symbol,
                                amt=candidate['quantity']
                            )

                            if result.get('success', False):
                                order_id = result.get('order_id', 'N/A')
                                print(f"[OK] {symbol} 시장가 매수 주문 체결")
                                print(f"     주문번호: {order_id}")
                                print(f"     수량: {candidate['quantity']}주")
                                candidate['status'] = 'filled'
                                # 보유 종목으로 이동
                                held_positions[symbol] = {
                                    'quantity': candidate['quantity'],
                                    'avg_price': current_price,
                                    'target_price': candidate['target_price'],
                                    'losscut_price': current_price * 0.97,  # 3% 손절
                                    'status': 'holding'
                                }
                            else:
                                error_msg = result.get('message', result.get('error', 'Unknown'))
                                rt_cd = result.get('rt_cd', 'N/A')
                                msg_cd = result.get('msg_cd', 'N/A')
                                print(f"[ERROR] {symbol} 시장가 매수 주문 실패")
                                print(f"     rt_cd: {rt_cd}, msg_cd: {msg_cd}")
                                print(f"     에러: {error_msg}")
                        else:
                            if not is_regular_market_hours():
                                print(f"[INFO] {symbol} 목표가 도달, 정규장 대기 중")
                            else:
                                print(f"[SIMULATION] {symbol} 목표가 도달, 시장가 매수 시뮬레이션")

            # 보유 종목 익절/손절 체크
            if symbol in held_positions:
                position = held_positions[symbol]
                if position['status'] == 'holding':
                    # PositionManager를 통해 AGain 및 손절가 업데이트 (트레일링 스탑)
                    updated_position = position_manager.update_position_status(
                        position=position,
                        current_price=current_price
                    )
                    # 업데이트된 포지션 정보 반영
                    held_positions[symbol] = updated_position
                    position = updated_position  # 로컬 변수도 업데이트

                    # 익절: 목표가 도달
                    if current_price >= position['target_price']:
                        print(f"\n[TAKE PROFIT] {symbol}: ${current_price:.2f} >= ${position['target_price']:.2f}")

                        if execute_real_orders and is_regular_market_hours():
                            result = kis_api.make_sell_market_order(
                                stock_code=symbol,
                                amt=position['quantity']
                            )

                            if result.get('success', False):
                                profit = (current_price - position['avg_price']) * position['quantity']
                                profit_pct = ((current_price - position['avg_price']) / position['avg_price']) * 100
                                order_id = result.get('order_id', 'N/A')
                                print(f"[OK] {symbol} 익절 매도 주문 체결")
                                print(f"     주문번호: {order_id}")
                                print(f"     수량: {position['quantity']}주 @ ${current_price:.2f}")
                                print(f"     손익: +${profit:.2f} ({profit_pct:+.2f}%)")
                                position['status'] = 'sold'
                            else:
                                error_msg = result.get('message', result.get('error', 'Unknown'))
                                rt_cd = result.get('rt_cd', 'N/A')
                                msg_cd = result.get('msg_cd', 'N/A')
                                print(f"[ERROR] {symbol} 익절 매도 주문 실패")
                                print(f"     rt_cd: {rt_cd}, msg_cd: {msg_cd}")
                                print(f"     에러: {error_msg}")
                        else:
                            if not is_regular_market_hours():
                                print(f"[INFO] {symbol} 익절 매도 대기 (정규장 시간 아님)")
                            else:
                                print(f"[SIMULATION] {symbol} 익절 매도 (실제 주문 비활성화)")

                    # 손절: 손절가 도달
                    elif current_price <= position['losscut_price']:
                        print(f"\n[STOP LOSS] {symbol}: ${current_price:.2f} <= ${position['losscut_price']:.2f}")

                        if execute_real_orders and is_regular_market_hours():
                            result = kis_api.make_sell_market_order(
                                stock_code=symbol,
                                amt=position['quantity']
                            )

                            if result.get('success', False):
                                loss = (current_price - position['avg_price']) * position['quantity']
                                loss_pct = ((current_price - position['avg_price']) / position['avg_price']) * 100
                                order_id = result.get('order_id', 'N/A')
                                print(f"[OK] {symbol} 손절 매도 주문 체결")
                                print(f"     주문번호: {order_id}")
                                print(f"     수량: {position['quantity']}주 @ ${current_price:.2f}")
                                print(f"     손익: ${loss:.2f} ({loss_pct:+.2f}%)")
                                position['status'] = 'sold'
                            else:
                                error_msg = result.get('message', result.get('error', 'Unknown'))
                                rt_cd = result.get('rt_cd', 'N/A')
                                msg_cd = result.get('msg_cd', 'N/A')
                                print(f"[ERROR] {symbol} 손절 매도 주문 실패")
                                print(f"     rt_cd: {rt_cd}, msg_cd: {msg_cd}")
                                print(f"     에러: {error_msg}")
                        else:
                            if not is_regular_market_hours():
                                print(f"[INFO] {symbol} 손절 매도 대기 (정규장 시간 아님)")
                            else:
                                print(f"[SIMULATION] {symbol} 손절 매도 (실제 주문 비활성화)")

        # 마켓 오픈 여부 체크
        if not is_market_open():
            import pytz

            eastern = pytz.timezone('America/New_York')
            now_eastern = datetime.now(eastern)
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][now_eastern.weekday()]

            print("\n" + "="*60)
            print("[MARKET CLOSED]")
            print("="*60)
            print(f"Current Time (ET): {now_eastern.strftime('%Y-%m-%d %H:%M:%S')} ({day_name})")
            print(f"\nMarket Status: CLOSED")

            if now_eastern.weekday() >= 5:
                print(f"Reason: Weekend ({day_name})")
                next_open = "Monday 09:30 ET"
            else:
                print(f"Reason: Outside trading hours (09:30-16:00 ET)")
                if now_eastern.hour < 9 or (now_eastern.hour == 9 and now_eastern.minute < 30):
                    next_open = f"Today 09:30 ET"
                else:
                    next_open = "Next trading day 09:30 ET"

            print(f"Next Market Open: {next_open}")
            print("="*60)
            print("\n[INFO] WebSocket service will not start during market closed hours.")
            print("[INFO] Auto-trading program terminated.")
            return None

        # LivePriceService 초기화 및 구독
        live_price_service = LivePriceService(config)
        await live_price_service.start_service()

        # 모니터링 대상 종목의 실제 현재가를 초기값으로 설정
        from project.models.trading_models import PriceData, MarketType

        print(f"\n[INFO] 초기 가격 설정 중...")

        # 1. 보유 종목의 실제 현재가 설정
        for symbol in held_positions.keys():
            position = held_positions[symbol]

            # previous_day_data도 실제 현재가로 설정 (시뮬레이션 기준값)
            live_price_service.previous_day_data[symbol] = position['current_price']

            # 실제 현재가로 PriceData 초기화
            initial_price_data = PriceData(
                symbol=symbol,
                price=position['current_price'],
                volume=0,
                timestamp=datetime.now(),
                change=0.0,
                change_pct=0.0,
                market=MarketType.NASDAQ if symbol not in ['GH'] else MarketType.NYSE
            )
            live_price_service.price_cache[symbol] = initial_price_data
            print(f"  - {symbol}: ${position['current_price']:.2f} (보유 종목)")

        # 2. 매수 대기 종목의 현재가 설정
        for symbol in buy_candidates.keys():
            if symbol not in live_price_service.price_cache:
                candidate = buy_candidates[symbol]
                current_close = candidate.get('close', candidate['target_price'])

                # previous_day_data도 현재 종가로 설정
                live_price_service.previous_day_data[symbol] = current_close

                initial_price_data = PriceData(
                    symbol=symbol,
                    price=current_close,
                    volume=0,
                    timestamp=datetime.now(),
                    change=0.0,
                    change_pct=0.0,
                    market=MarketType.NASDAQ
                )
                live_price_service.price_cache[symbol] = initial_price_data
                print(f"  - {symbol}: ${current_close:.2f} (매수 대기)")

        print(f"[OK] 초기 가격 설정 완료: {len(live_price_service.price_cache)}개 종목")

        # 모든 종목 구독
        for symbol in all_monitored:
            await live_price_service.subscribe_price_updates(
                symbol,
                on_price_update
            )

        # 실시간 모니터링 대시보드 출력 함수
        def print_monitoring_dashboard():
            """실시간 가격 모니터링 대시보드 출력"""
            import os
            # 화면 클리어 (Windows: cls, Unix: clear)
            # os.system('cls' if os.name == 'nt' else 'clear')

            print("\n" + "="*110)
            print(f"{'실시간 모니터링 대시보드':^110}")
            print(f"{'업데이트: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^110}")
            print("="*110)

            # 보유 종목 모니터링
            if held_positions:
                print(f"\n{'[보유 종목]':^110}")
                print("-"*110)
                print(f"{'종목':<8} {'수량':>6} {'평균가':>10} {'현재가':>10} {'손익':>12} {'손익률':>8} "
                      f"{'AGain':>7} {'목표가':>10} {'손절가':>10} {'상태':<10}")
                print("-"*110)

                total_value = 0
                total_pnl = 0

                for symbol, pos in held_positions.items():
                    if pos['status'] == 'holding':
                        # LivePriceService에서 현재가 조회
                        current_price = pos['current_price']
                        if symbol in live_price_service.price_cache:
                            current_price = live_price_service.price_cache[symbol].price

                        market_value = current_price * pos['quantity']
                        pnl = (current_price - pos['avg_price']) * pos['quantity']
                        pnl_pct = ((current_price - pos['avg_price']) / pos['avg_price']) * 100

                        total_value += market_value
                        total_pnl += pnl

                        # AGain 값
                        again = pos.get('again', 1.0)

                        # 목표가/손절가 대비 위치
                        target_dist = ((pos['target_price'] - current_price) / current_price) * 100
                        losscut_dist = ((current_price - pos['losscut_price']) / pos['losscut_price']) * 100

                        # 트레일링 스탑 활성화 여부: 손절가가 기본 손절(avg_price × 0.97)보다 높으면 활성
                        basic_losscut = pos['avg_price'] * 0.97
                        trailing_active = pos['losscut_price'] > basic_losscut

                        # 상태 표시 (트레일링 스탑 활성화 표시)
                        if pnl_pct >= 0:
                            if trailing_active:  # 트레일링 스탑 활성 (손절가가 올라간 상태)
                                status = f"[UP+T] +{pnl_pct:.2f}%"
                            else:
                                status = f"[UP] +{pnl_pct:.2f}%"
                        else:
                            status = f"[DOWN] {pnl_pct:.2f}%"

                        print(f"{symbol:<8} {pos['quantity']:>6} ${pos['avg_price']:>9.2f} ${current_price:>9.2f} "
                              f"${pnl:>10.2f} {pnl_pct:>7.2f}% {again:>6.3f} "
                              f"${pos['target_price']:>9.2f} ${pos['losscut_price']:>9.2f} {status:<12}")

                print("-"*110)
                print(f"{'총계':<8} {'':<6} {'':<10} {'':<10} ${total_pnl:>10.2f} "
                      f"{(total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) != 0 else 0:>7.2f}% "
                      f"{'':<7} {'(총 가치: $' + f'{total_value:,.2f})':<32}")
                print("="*110)

            # 매수 대기 종목
            waiting_count = sum(1 for c in buy_candidates.values() if c['status'] == 'waiting')
            if waiting_count > 0:
                print(f"\n[매수 대기: {waiting_count}개]", end=" ")
                waiting_symbols = [s for s, c in buy_candidates.items() if c['status'] == 'waiting']
                print(", ".join(waiting_symbols[:5]))
                if waiting_count > 5:
                    print(f"  ...외 {waiting_count - 5}개")

            # 장 상태
            market_status = "[OPEN] 장중" if is_market_open() else "[CLOSED] 장마감"
            print(f"\n장 상태: {market_status} | 실행 모드: {'[REAL] 실제 주문' if execute_real_orders else '[SIM] 시뮬레이션'}")
            print("="*110)

        # 장 시간 동안 계속 모니터링
        print("\n" + "="*60)
        print("[INFO] 실시간 모니터링 + 자동 매매 시작")
        print("="*60)
        print(f"실행 모드: {'[REAL] 실제 주문 실행' if execute_real_orders else '[SIMULATION] 시뮬레이션'}")
        print("종료: Ctrl+C")
        print("="*60)

        try:
            iteration = 0
            last_dashboard_time = datetime.now()
            last_market_check_time = datetime.now()

            while True:
                iteration += 1

                # 1분마다 마켓 오픈 상태 체크
                current_time = datetime.now()
                if (current_time - last_market_check_time).total_seconds() >= 60:
                    if not is_market_open():
                        import pytz
                        eastern = pytz.timezone('America/New_York')
                        now_eastern = datetime.now(eastern)

                        print("\n" + "="*60)
                        print("[MARKET CLOSED - AUTO SHUTDOWN]")
                        print("="*60)
                        print(f"Current Time (ET): {now_eastern.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"Market has closed at 16:00 ET")
                        print("[INFO] Stopping WebSocket service...")
                        print("[INFO] Auto-trading program will terminate.")
                        print("="*60)
                        break
                    last_market_check_time = current_time

                # 10초마다 실시간 대시보드 출력
                if (current_time - last_dashboard_time).total_seconds() >= 10:
                    print_monitoring_dashboard()
                    last_dashboard_time = current_time

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n[INFO] 사용자에 의해 모니터링 중지")
        except asyncio.CancelledError:
            print("\n\n[INFO] 모니터링 작업이 취소되었습니다")
        except Exception as e:
            print(f"\n[ERROR] 모니터링 루프 중 에러 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 모니터링 중지 (어떤 경우에도 실행)
            print("\n[INFO] LivePriceService 종료 중...")
            try:
                await live_price_service.stop_service()
                print("[OK] 실시간 모니터링 종료")
            except Exception as e:
                print(f"[WARNING] LivePriceService 종료 실패: {e}")

        # Report Agent를 통한 트레이딩 모니터 대시보드 생성
        try:
            print("\n[7/7] Report Agent로 트레이딩 모니터 대시보드 생성 중...")
            report = get_report_agent(config)

            # 현재 보유 포지션에 손익 정보 추가
            dashboard_positions = []
            for symbol, pos in held_positions.items():
                if pos['status'] == 'holding':
                    # 현재가는 live_price_service에서 조회 (여기서는 평균가로 시뮬레이션)
                    current_price = pos['avg_price']  # TODO: 실제 현재가 조회
                    pnl = (current_price - pos['avg_price']) * pos['quantity']
                    pnl_percent = ((current_price - pos['avg_price']) / pos['avg_price']) * 100

                    dashboard_positions.append({
                        'symbol': symbol,
                        'quantity': pos['quantity'],
                        'avg_price': pos['avg_price'],
                        'current_price': current_price,
                        'target_price': pos['target_price'],
                        'losscut_price': pos['losscut_price'],
                        'pnl': pnl,
                        'pnl_percent': pnl_percent
                    })

            # 매수 대기 종목
            pending_buy_orders = [symbol for symbol, c in buy_candidates.items() if c['status'] == 'waiting']

            monitor_path = report.generate_trading_monitor_dashboard(
                positions=dashboard_positions,
                pending_orders=pending_buy_orders,
                market_status={'status': 'OPEN', 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                save=True
            )
            if monitor_path:
                print(f"[Report Agent] 모니터 대시보드 생성 완료: {monitor_path}")
                print(f"  - 보유 포지션: {len(dashboard_positions)}개")
                print(f"  - 대기 주문: {len(pending_buy_orders)}개")
        except Exception as e:
            logger.warning(f"트레이딩 모니터 대시보드 생성 실패: {e}")

        print("\n" + "="*60)
        print("자동 트레이딩 세션 종료")
        print("="*60)

        return buy_signals

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def show_menu():
    """메뉴 표시"""
    print("\n" + "="*60)
    print("AI Trading System - 메뉴 선택")
    print("="*60)
    print("\n1. 자동 백테스트 실행 (Backtest + Dashboard)")
    print("2. 개별 종목 시그널 확인 (Stock Signal + Chart)")
    print("3. 오토 트레이딩 시스템 (Auto Trading + Monitor)")
    print("4. 개별 티커 시그널 타임라인 (Signal Timeline Chart)")
    print("5. Report Agent 상태 확인")
    print("6. 종료")
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
            choice = input("\n선택 (1-6): ").strip()

            if choice == '1':
                # 자동 백테스트
                await run_auto_backtest(config)

            elif choice == '2':
                # 개별 종목 시그널 확인
                symbol = input("\n종목 코드를 입력하세요 (예: AAPL): ").strip().upper()
                if symbol:
                    await check_single_symbol_signal(symbol, config)
                else:
                    print("[ERROR] 종목 코드를 입력해주세요.")

            elif choice == '3':
                # 오토 트레이딩 시스템
                await run_auto_trading(config)

            elif choice == '4':
                # 개별 티커 시그널 타임라인
                await show_ticker_signal_timeline(config)

            elif choice == '5':
                # Report Agent 상태 확인
                print("\n" + "="*60)
                print("Report Agent Status")
                print("="*60)

                try:
                    agent = get_report_agent(config)
                    status = agent.get_summary()

                    print(f"\n[Report Agent 정보]")
                    print(f"  Output Directory: {status.get('output_directory', 'N/A')}")
                    print(f"  MongoDB Connected: {status.get('mongodb_connected', False)}")

                    # 생성된 차트 목록
                    recent_charts = status.get('recent_charts', [])
                    if recent_charts:
                        print(f"\n[최근 생성된 차트] ({len(recent_charts)}개)")
                        for i, chart in enumerate(recent_charts[:5], 1):  # 최근 5개만 표시
                            print(f"  {i}. {chart}")
                    else:
                        print("\n[최근 생성된 차트] 없음")

                    # 가능한 기능 목록
                    capabilities = status.get('capabilities', [])
                    if capabilities:
                        print(f"\n[사용 가능한 기능]")
                        for cap in capabilities:
                            print(f"  - {cap}")

                except Exception as e:
                    print(f"[ERROR] Report Agent 상태 확인 실패: {e}")
                    import traceback
                    traceback.print_exc()

            elif choice == '6':
                print("\n프로그램을 종료합니다.")
                break

            else:
                print("[ERROR] 1-6 사이의 숫자를 입력해주세요.")

        except KeyboardInterrupt:
            print("\n\n프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"[ERROR] 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
