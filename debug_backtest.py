#!/usr/bin/env python3
"""
백테스트 Balance 계산 문제 디버깅
"""

import asyncio
import yaml
from datetime import datetime, timedelta
from project.service.staged_pipeline_service import StagedPipelineService
from project.service.daily_backtest_service import DailyBacktestService, BacktestConfig
import pandas as pd

async def debug_backtest():
    """백테스트 실행 및 디버그"""

    # 설정 로드
    with open('myStockInfo.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 날짜 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3개월
    data_start = start_date - timedelta(days=365*3)

    # 소수의 종목으로 테스트
    test_symbols = ['AAPL', 'MSFT', 'NVDA']

    print("=" * 80)
    print("백테스트 Balance 계산 디버그")
    print("=" * 80)
    print(f"\n테스트 종목: {test_symbols}")
    print(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # Staged Pipeline 실행
    print("\n[1단계] Staged Pipeline 실행...")
    pipeline = StagedPipelineService(
        config=config,
        market='NASDAQ',
        area='US',
        start_day=data_start,
        end_day=end_date
    )

    pipeline_results = pipeline.run_staged_pipeline(test_symbols)

    if pipeline_results['total_candidates'] == 0:
        print("\n매매 후보가 없습니다.")
        return

    final_candidates = pipeline_results.get('final_candidates', [])
    print(f"\n최종 후보: {len(final_candidates)}개 - {final_candidates}")

    # 데이터 준비
    print("\n[2단계] 백테스트 데이터 준비...")
    all_loaded_data = pipeline.data_loader.get_all_loaded_data()

    final_candidates_data = {}
    if all_loaded_data:
        for stage, symbols_data in all_loaded_data.items():
            if isinstance(symbols_data, dict):
                for symbol, df in symbols_data.items():
                    if symbol not in final_candidates_data:
                        final_candidates_data[symbol] = {}
                    final_candidates_data[symbol][stage] = df

    # 백테스트 데이터 변환
    backtest_data = {}
    for symbol in final_candidates:
        if symbol not in final_candidates_data:
            continue

        stage_data = final_candidates_data[symbol]
        if 'D' not in stage_data:
            continue

        df_D = stage_data['D'].copy()

        # Date 인덱스 설정
        if 'Date' in df_D.columns:
            df_D['Date'] = pd.to_datetime(df_D['Date'])
            df_D = df_D.set_index('Date')
            df_D = df_D.sort_index()

        # 컬럼명 매핑
        if 'Dopen' in df_D.columns:
            df_D['open'] = df_D['Dopen']
        if 'Dhigh' in df_D.columns:
            df_D['high'] = df_D['Dhigh']
        if 'Dlow' in df_D.columns:
            df_D['low'] = df_D['Dlow']
        if 'Dclose' in df_D.columns:
            df_D['close'] = df_D['Dclose']

        # 매수 신호 설정
        df_D['BuySig'] = 1
        df_D['SellSig'] = 0
        df_D['signal'] = 1
        df_D['Type'] = 'Staged'
        df_D['TargetPrice'] = df_D['close'] * 1.20
        df_D['LossCutPrice'] = df_D['close'] * 0.95

        if 'ADR' not in df_D.columns:
            df_D['ADR'] = 5.0

        print(f"\n[{symbol}]")
        print(f"  Shape: {df_D.shape}")
        print(f"  Date range: {df_D.index[0]} ~ {df_D.index[-1]}")
        print(f"  Close 가격 범위: ${df_D['close'].min():.2f} ~ ${df_D['close'].max():.2f}")
        print(f"  샘플 데이터 (최근 3일):")
        print(df_D[['close', 'BuySig', 'TargetPrice', 'LossCutPrice']].tail(3))

        backtest_data[symbol] = df_D

    if not backtest_data:
        print("\n백테스트 데이터가 없습니다.")
        return

    # 백테스트 설정
    print("\n[3단계] 백테스트 설정...")
    initial_cash_usd = 100000.0  # $100K
    initial_cash_m = initial_cash_usd / 1_000_000  # 0.1M

    print(f"\n초기 자본:")
    print(f"  USD: ${initial_cash_usd:,.0f}")
    print(f"  Million USD: ${initial_cash_m:.2f}M")

    backtest_config = BacktestConfig()
    backtest_config.initial_cash = initial_cash_m
    backtest_config.max_positions = 3
    backtest_config.slippage = 0.002
    backtest_config.message_output = True  # 모든 거래 출력

    print(f"\n백테스트 설정:")
    print(f"  initial_cash: {backtest_config.initial_cash}")
    print(f"  max_positions: {backtest_config.max_positions}")
    print(f"  slippage: {backtest_config.slippage}")

    # 백테스트 실행
    print("\n[4단계] 백테스트 실행...")
    print("=" * 80)

    backtest_service = DailyBacktestService(backtest_config)

    backtest_results = backtest_service.run_backtest(
        universe=list(backtest_data.keys()),
        df_data=backtest_data,
        market='US',
        area='US'
    )

    # 결과 출력
    print("\n" + "=" * 80)
    print("백테스트 결과")
    print("=" * 80)

    metrics = backtest_results.performance_metrics

    print(f"\n[성과 지표]")
    print(f"  총 수익률: {metrics.get('total_return', 0):.2%}")
    print(f"  최종 자산: ${metrics.get('final_value', 0):.2f}M = ${metrics.get('final_value', 0)*1_000_000:,.0f}")
    print(f"  최대 손실: {metrics.get('max_drawdown', 0):.2%}")

    print(f"\n[거래 통계]")
    print(f"  총 거래 수: {metrics.get('total_trades', 0)}")
    print(f"  승리 횟수: {metrics.get('win_count', 0)}")
    print(f"  손실 횟수: {metrics.get('loss_count', 0)}")
    print(f"  승률: {metrics.get('win_rate', 0):.2%}")

    if backtest_results.trades:
        print(f"\n[거래 내역 샘플 (처음 5개)]")
        for trade in backtest_results.trades[:5]:
            print(f"  {trade.timestamp.strftime('%Y-%m-%d')}: {trade.trade_type.value} {trade.ticker} "
                  f"@ ${trade.price:.2f}, PnL: ${trade.pnl:.2f}")

if __name__ == "__main__":
    asyncio.run(debug_backtest())
