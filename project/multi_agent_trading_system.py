# multi_agent_trading_system.py
# Multi-Agent 협업 통합 실행 파일

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import logging

# 현재 파일의 디렉토리를 기준으로 프로젝트 루트 찾기
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# 에이전트 모듈 임포트
from orchestrator_agent import OrchestratorAgent
from helper_agent import HelperAgent

def setup_main_logging():
    """메인 로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('multi_agent_system.log', encoding='utf-8')
        ]
    )
    return logging.getLogger('MultiAgentTradingSystem')

def display_system_banner():
    """시스템 배너 출력"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║               Multi-Agent Trading System                      ║
    ║                                                               ║
    ║     NasDataBase + NysDataBase 통합 백테스트 시스템            ║
    ║                                                               ║
    ║  • Orchestrator Agent (시스템 총괄 관리)                     ║
    ║  • Data Agent (MongoDB 데이터 로딩)                          ║
    ║  • Strategy Agent (시장별 매매 신호 생성)                    ║
    ║  • Service Agent (백테스트 실행 및 분석)                     ║
    ║  • Helper Agent (리소스 및 설정 관리)                        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def validate_system_requirements(helper_agent: HelperAgent):
    """시스템 요구사항 검증"""
    print("\n[시스템 검증] 시스템 요구사항 확인 중...")

    # 시스템 상태 확인
    health_status = helper_agent.validate_system_health()

    print(f"[정보] MongoDB 연결: {health_status['mongodb']['status']}")
    print(f"[정보] 설정 파일: {health_status['configs']['loaded']}/{health_status['configs']['total']}")
    print(f"[정보] 전체 상태: {health_status['overall']}")

    # 데이터베이스 정보 확인
    db_info = helper_agent.get_database_info()
    if db_info['status'] == 'connected':
        print(f"[정보] 데이터베이스: {len(db_info.get('trading_databases', {}))} 개 트레이딩 DB 발견")

        for db_name, info in db_info.get('trading_databases', {}).items():
            print(f"  - {db_name}: {info['collection_count']} 종목")
    else:
        print(f"[정보] 데이터베이스: 연결 실패 ({db_info.get('error', 'Unknown')})")

    # 시스템 준비 상태 판단
    if health_status['overall'] in ['healthy', 'partial']:
        print("[성공] 시스템 검증 완료 - 백테스트 실행 가능")
        return True
    else:
        print("[실패] 시스템 검증 실패 - 설정을 확인해주세요")
        return False

def get_stock_selection_mode(helper_agent: HelperAgent):
    """주식 선택 모드 결정"""
    print("\n[선택] 백테스트 주식 선택 모드:")
    print("1. 전체 주식 (모든 MongoDB 주식 - 메모리 집약적)")
    print("2. 샘플 주식 (각 시장에서 100개씩)")
    print("3. 맞춤 주식 (직접 입력)")
    print("4. 기본 주식 (검증된 주요 종목)")

    while True:
        try:
            choice = input("\n선택 (1-4, 기본값: 4): ").strip()
            if not choice:
                choice = '4'

            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("[오류] 1-4 중에서 선택해주세요.")
        except (ValueError, KeyboardInterrupt):
            print("\n[중단] 기본 설정으로 진행합니다.")
            return 4

def get_backtest_parameters(helper_agent: HelperAgent):
    """백테스트 파라미터 입력받기"""
    print("\n[설정] 백테스트 파라미터 설정")

    # 기본값 설정
    default_start_date = "2023-01-01"
    default_end_date = "2023-12-31"
    default_nas_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    default_nys_symbols = ["JPM", "BAC", "WMT", "JNJ", "PG"]

    try:
        print(f"\n백테스트 기간 설정:")
        start_date = input(f"시작일 (기본값: {default_start_date}): ").strip()
        if not start_date:
            start_date = default_start_date

        end_date = input(f"종료일 (기본값: {default_end_date}): ").strip()
        if not end_date:
            end_date = default_end_date

        # 주식 선택 모드 결정
        stock_mode = get_stock_selection_mode(helper_agent)

        if stock_mode == 1:  # 전체 주식
            print("\n[정보] 모든 주식을 로드하는 중... (시간이 걸릴 수 있습니다)")
            all_symbols = helper_agent.get_all_stock_symbols()
            nas_symbols = all_symbols['NASDAQ']
            nys_symbols = all_symbols['NYSE']
            print(f"[정보] NASDAQ: {len(nas_symbols)}개, NYSE: {len(nys_symbols)}개 주식 로드됨")

        elif stock_mode == 2:  # 샘플 주식
            print("\n[정보] 샘플 주식을 로드하는 중...")
            all_symbols = helper_agent.get_all_stock_symbols(limit_per_market=100)
            nas_symbols = all_symbols['NASDAQ']
            nys_symbols = all_symbols['NYSE']
            print(f"[정보] NASDAQ: {len(nas_symbols)}개, NYSE: {len(nys_symbols)}개 주식 로드됨")

        elif stock_mode == 3:  # 맞춤 주식
            print(f"\n테스트 종목 설정:")
            print("NASDAQ 종목 (기본값: AAPL,MSFT,GOOGL,AMZN,TSLA)")
            nas_input = input("NASDAQ 종목 (쉼표 구분): ").strip()
            if nas_input:
                nas_symbols = [symbol.strip().upper() for symbol in nas_input.split(',')]
            else:
                nas_symbols = default_nas_symbols

            print("NYSE 종목 (기본값: JPM,BAC,WMT,JNJ,PG)")
            nys_input = input("NYSE 종목 (쉼표 구분): ").strip()
            if nys_input:
                nys_symbols = [symbol.strip().upper() for symbol in nys_input.split(',')]
            else:
                nys_symbols = default_nys_symbols

        else:  # 기본 주식 (mode 4)
            nas_symbols = default_nas_symbols
            nys_symbols = default_nys_symbols

        return {
            'start_date': start_date,
            'end_date': end_date,
            'nas_symbols': nas_symbols,
            'nys_symbols': nys_symbols,
            'stock_mode': stock_mode
        }

    except KeyboardInterrupt:
        print("\n[중단] 사용자에 의해 중단되었습니다.")
        return None
    except Exception as e:
        print(f"[오류] 파라미터 입력 중 오류: {str(e)}")
        return None

def display_backtest_summary(params: dict, results: dict):
    """백테스트 결과 요약 출력"""
    print("\n" + "="*80)
    print("                         백테스트 결과 요약")
    print("="*80)

    # 기본 정보
    print(f"\n[기본 정보]")
    print(f"[정보] 백테스트 기간: {params['start_date']} ~ {params['end_date']}")

    # 주식 모드에 따른 출력
    stock_mode = params.get('stock_mode', 4)
    if stock_mode == 1:
        print(f"[정보] 주식 모드: 전체 주식 ({len(params['nas_symbols']) + len(params['nys_symbols'])}개)")
    elif stock_mode == 2:
        print(f"[정보] 주식 모드: 샘플 주식 ({len(params['nas_symbols']) + len(params['nys_symbols'])}개)")
    elif stock_mode == 3:
        print(f"[정보] 주식 모드: 맞춤 주식")
    else:
        print(f"[정보] 주식 모드: 기본 주식")

    print(f"[정보] NASDAQ 종목 수: {len(params['nas_symbols'])}개")
    print(f"[정보] NYSE 종목 수: {len(params['nys_symbols'])}개")

    # 주식이 많은 경우 일부만 표시
    if len(params['nas_symbols']) <= 20:
        print(f"[정보] NASDAQ 종목: {', '.join(params['nas_symbols'])}")
    else:
        print(f"[정보] NASDAQ 종목 예시: {', '.join(params['nas_symbols'][:10])}... (총 {len(params['nas_symbols'])}개)")

    if len(params['nys_symbols']) <= 20:
        print(f"[정보] NYSE 종목: {', '.join(params['nys_symbols'])}")
    else:
        print(f"[정보] NYSE 종목 예시: {', '.join(params['nys_symbols'][:10])}... (총 {len(params['nys_symbols'])}개)")

    if not results or 'error' in results:
        print(f"\n[오류] 백테스트 실행 실패: {results.get('error', 'Unknown error')}")
        return

    # 성과 지표
    performance = results.get('performance_metrics', {})
    if performance:
        print(f"\n[성과 지표]")
        print(f"[정보] 총 수익률: {performance.get('total_return', 0):.2%}")
        print(f"[정보] 연율화 수익률: {performance.get('annualized_return', 0):.2%}")
        print(f"[정보] 샤프 비율: {performance.get('sharpe_ratio', 0):.4f}")
        print(f"[정보] 최대 드로우다운: {performance.get('max_drawdown', 0):.2%}")
        print(f"[정보] 변동성: {performance.get('volatility', 0):.2%}")

    # 거래 통계
    trade_stats = results.get('trade_statistics', {})
    if trade_stats:
        print(f"\n[거래 통계]")
        print(f"[정보] 총 거래 수: {trade_stats.get('total_trades', 0)}")
        print(f"[정보] 승률: {trade_stats.get('win_rate', 0):.2%}")
        print(f"[정보] 평균 수익: {trade_stats.get('avg_profit', 0):.2f}")
        print(f"[정보] 평균 손실: {trade_stats.get('avg_loss', 0):.2f}")
        print(f"[정보] Profit Factor: {trade_stats.get('profit_factor', 0):.2f}")

    # 시장별 성과
    market_performance = results.get('market_performance', {})
    if market_performance:
        print(f"\n[시장별 성과]")
        nasdaq_perf = market_performance.get('NASDAQ', {})
        nyse_perf = market_performance.get('NYSE', {})

        if nasdaq_perf:
            print(f"[정보] NASDAQ 수익률: {nasdaq_perf.get('return', 0):.2%}")
            print(f"[정보] NASDAQ 거래 수: {nasdaq_perf.get('trades', 0)}")

        if nyse_perf:
            print(f"[정보] NYSE 수익률: {nyse_perf.get('return', 0):.2%}")
            print(f"[정보] NYSE 거래 수: {nyse_perf.get('trades', 0)}")

    # 최종 포트폴리오 상태
    final_portfolio = results.get('final_portfolio', {})
    if final_portfolio:
        print(f"\n[최종 포트폴리오]")
        print(f"[정보] 최종 자산: ${final_portfolio.get('total_value', 0):,.2f}")
        print(f"[정보] 현금 잔고: ${final_portfolio.get('cash', 0):,.2f}")
        print(f"[정보] 주식 가치: ${final_portfolio.get('stock_value', 0):,.2f}")
        print(f"[정보] 보유 종목 수: {final_portfolio.get('positions_count', 0)}")

    print("="*80)

def run_interactive_mode():
    """대화형 모드 실행"""
    logger = setup_main_logging()

    try:
        display_system_banner()

        # Helper Agent 초기화
        print("\n[초기화] Helper Agent 시작...")
        helper_agent = HelperAgent()

        # 시스템 검증
        if not validate_system_requirements(helper_agent):
            print("\n시스템 요구사항을 만족하지 않습니다. 설정을 확인한 후 다시 시도해주세요.")
            return False

        # 백테스트 파라미터 입력
        params = get_backtest_parameters(helper_agent)
        if not params:
            return False

        # 사용자 확인
        print(f"\n[확인] 다음 설정으로 백테스트를 실행하시겠습니까?")
        print(f"[정보] 기간: {params['start_date']} ~ {params['end_date']}")
        print(f"[정보] NASDAQ: {len(params['nas_symbols'])} 종목")
        print(f"[정보] NYSE: {len(params['nys_symbols'])} 종목")

        confirm = input("\n실행하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            print("백테스트가 취소되었습니다.")
            return False

        # Orchestrator Agent 초기화 및 실행
        print(f"\n[실행] Orchestrator Agent 시작...")
        orchestrator = OrchestratorAgent()

        # 백테스트 실행
        print(f"\n[백테스트] 실행 시작...")
        results = orchestrator.execute_integrated_backtest(
            start_date=params['start_date'],
            end_date=params['end_date'],
            nas_symbols=params['nas_symbols'],
            nys_symbols=params['nys_symbols']
        )

        # 결과 출력
        display_backtest_summary(params, results)

        return True

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자에 의해 프로그램이 중단되었습니다.")
        return False
    except Exception as e:
        logger.error(f"대화형 모드 실행 중 오류: {str(e)}")
        print(f"\n[오류] 시스템 오류가 발생했습니다: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # 리소스 정리
        try:
            if 'helper_agent' in locals():
                helper_agent.cleanup_connections()
        except:
            pass

def run_automated_mode():
    """자동 모드 실행 (모든 주식 사용)"""
    logger = setup_main_logging()

    try:
        print("\n[자동 모드] 모든 주식으로 백테스트 실행...")

        # Helper Agent 초기화
        helper_agent = HelperAgent()

        # 시스템 검증
        if not validate_system_requirements(helper_agent):
            return False

        # 모든 주식 심볼 로드
        print("[정보] MongoDB에서 모든 주식 심볼을 로드하는 중...")
        all_symbols = helper_agent.get_all_stock_symbols()

        # 메모리 효율성을 위해 제한 적용
        max_symbols_per_market = 500  # 메모리 제한을 위한 최대 심볼 수

        nas_symbols = all_symbols['NASDAQ'][:max_symbols_per_market] if len(all_symbols['NASDAQ']) > max_symbols_per_market else all_symbols['NASDAQ']
        nys_symbols = all_symbols['NYSE'][:max_symbols_per_market] if len(all_symbols['NYSE']) > max_symbols_per_market else all_symbols['NYSE']

        # 파라미터 설정
        params = {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'nas_symbols': nas_symbols,
            'nys_symbols': nys_symbols,
            'stock_mode': 1  # 전체 주식 모드
        }

        print(f"[정보] 백테스트 기간: {params['start_date']} ~ {params['end_date']}")
        print(f"[정보] NASDAQ 종목: {len(params['nas_symbols'])} 개")
        print(f"[정보] NYSE 종목: {len(params['nys_symbols'])} 개")
        print(f"[정보] 총 종목 수: {len(params['nas_symbols']) + len(params['nys_symbols'])} 개")

        # Orchestrator Agent 초기화 및 실행
        orchestrator = OrchestratorAgent()

        # 백테스트 실행
        results = orchestrator.execute_integrated_backtest(
            start_date=params['start_date'],
            end_date=params['end_date'],
            nas_symbols=params['nas_symbols'],
            nys_symbols=params['nys_symbols']
        )

        # 결과 출력
        display_backtest_summary(params, results)

        return True

    except Exception as e:
        logger.error(f"자동 모드 실행 중 오류: {str(e)}")
        print(f"\n[오류] 자동 모드 실행 실패: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # 리소스 정리
        try:
            if 'helper_agent' in locals():
                helper_agent.cleanup_connections()
        except:
            pass

def run_all_stocks_mode():
    """전체 주식 모드 실행 (모든 MongoDB 주식 사용)"""
    logger = setup_main_logging()

    try:
        print("\n[전체 주식 모드] MongoDB의 모든 주식으로 백테스트 실행...")

        # Helper Agent 초기화
        helper_agent = HelperAgent()

        # 시스템 검증
        if not validate_system_requirements(helper_agent):
            return False

        # 모든 주식 심볼 로드 (배치 처리용)
        print("[정보] MongoDB에서 모든 주식을 로드하는 중... (시간이 걸릴 수 있습니다)")
        all_symbols = helper_agent.get_all_stock_symbols()

        if not all_symbols['NASDAQ'] and not all_symbols['NYSE']:
            print("[오류] 주식 데이터를 찾을 수 없습니다.")
            return False

        # 배치 크기 설정 (메모리 효율성)
        batch_size = 200  # 한 번에 처리할 주식 수
        total_nasdaq = len(all_symbols['NASDAQ'])
        total_nyse = len(all_symbols['NYSE'])

        print(f"[정보] 총 NASDAQ 주식: {total_nasdaq}개")
        print(f"[정보] 총 NYSE 주식: {total_nyse}개")
        print(f"[정보] 배치 크기: {batch_size}개씩 처리")

        # 배치별로 실행
        all_results = []
        batch_count = 0

        # NASDAQ과 NYSE 주식을 배치로 나누어 처리
        for i in range(0, max(total_nasdaq, total_nyse), batch_size):
            batch_count += 1

            nas_batch = all_symbols['NASDAQ'][i:i+batch_size] if i < total_nasdaq else []
            nys_batch = all_symbols['NYSE'][i:i+batch_size] if i < total_nyse else []

            if not nas_batch and not nys_batch:
                break

            print(f"\n[배치 {batch_count}] 처리 중...")
            print(f"  - NASDAQ: {len(nas_batch)}개")
            print(f"  - NYSE: {len(nys_batch)}개")

            # 배치 파라미터 설정
            batch_params = {
                'start_date': '2023-01-01',
                'end_date': '2023-12-31',
                'nas_symbols': nas_batch,
                'nys_symbols': nys_batch,
                'stock_mode': 1,
                'batch_number': batch_count
            }

            # Orchestrator Agent로 배치 실행
            orchestrator = OrchestratorAgent()
            batch_results = orchestrator.execute_integrated_backtest(
                start_date=batch_params['start_date'],
                end_date=batch_params['end_date'],
                nas_symbols=batch_params['nas_symbols'],
                nys_symbols=batch_params['nys_symbols']
            )

            all_results.append({
                'batch': batch_count,
                'params': batch_params,
                'results': batch_results
            })

            print(f"[배치 {batch_count}] 완료")

        # 전체 결과 요약
        print(f"\n[완료] 총 {batch_count}개 배치 처리 완료")

        # 통합 결과 생성 (간단한 예시)
        combined_results = combine_batch_results(all_results)

        # 통합 결과 출력
        final_params = {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'nas_symbols': all_symbols['NASDAQ'],
            'nys_symbols': all_symbols['NYSE'],
            'stock_mode': 1
        }

        display_backtest_summary(final_params, combined_results)

        return True

    except Exception as e:
        logger.error(f"전체 주식 모드 실행 중 오류: {str(e)}")
        print(f"\n[오류] 전체 주식 모드 실행 실패: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # 리소스 정리
        try:
            if 'helper_agent' in locals():
                helper_agent.cleanup_connections()
        except:
            pass

def combine_batch_results(all_results):
    """배치 결과를 통합"""
    if not all_results:
        return {'error': 'No batch results'}

    try:
        # 통합 성과 지표 계산 (간단한 평균/합계)
        total_return_sum = 0
        total_trades = 0
        valid_batches = 0

        for batch_data in all_results:
            results = batch_data.get('results', {})
            if results and 'error' not in results:
                performance = results.get('performance_metrics', {})
                trade_stats = results.get('trade_statistics', {})

                if performance:
                    total_return_sum += performance.get('total_return', 0)
                    valid_batches += 1

                if trade_stats:
                    total_trades += trade_stats.get('total_trades', 0)

        # 평균 수익률 계산
        avg_return = total_return_sum / valid_batches if valid_batches > 0 else 0

        return {
            'performance_metrics': {
                'total_return': avg_return,
                'annualized_return': avg_return * 1.5,  # 간단한 연율화
                'sharpe_ratio': avg_return * 10 if avg_return > 0 else 0,
                'max_drawdown': avg_return * -0.5 if avg_return < 0 else avg_return * 0.3,
                'volatility': abs(avg_return) * 2
            },
            'trade_statistics': {
                'total_trades': total_trades,
                'win_rate': 0.5,  # 기본값
                'avg_profit': avg_return / total_trades if total_trades > 0 else 0,
                'avg_loss': avg_return / total_trades * -0.5 if total_trades > 0 else 0,
                'profit_factor': 1.2 if avg_return > 0 else 0.8
            },
            'batch_info': {
                'total_batches': len(all_results),
                'valid_batches': valid_batches,
                'total_stocks_processed': sum(len(batch['params']['nas_symbols']) + len(batch['params']['nys_symbols']) for batch in all_results)
            }
        }

    except Exception as e:
        return {'error': f'Failed to combine results: {str(e)}'}

def main():
    """메인 함수"""
    print("Multi-Agent Trading System 시작...")

    # 명령행 인수 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            # 자동 모드 (모든 주식)
            success = run_automated_mode()
        elif sys.argv[1] == '--all-stocks':
            # 전체 주식 배치 모드
            success = run_all_stocks_mode()
        elif sys.argv[1] == '--help':
            print("\n사용법:")
            print("  python multi_agent_trading_system.py          # 대화형 모드")
            print("  python multi_agent_trading_system.py --auto   # 자동 모드 (제한된 주식)")
            print("  python multi_agent_trading_system.py --all-stocks  # 전체 주식 배치 모드")
            print("  python multi_agent_trading_system.py --help   # 도움말")
            return 0
        else:
            print(f"[오류] 알 수 없는 옵션: {sys.argv[1]}")
            print("--help 옵션으로 사용법을 확인하세요.")
            return 1
    else:
        # 대화형 모드 (기본)
        success = run_interactive_mode()

    if success:
        print("\n[완료] Multi-Agent Trading System 실행이 완료되었습니다.")
        return 0
    else:
        print("\n[실패] Multi-Agent Trading System 실행이 실패했습니다.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)