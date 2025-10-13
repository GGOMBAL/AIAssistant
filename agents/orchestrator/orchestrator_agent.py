"""
Orchestrator Agent - Multi-Agent Trading System

모든 서브 에이전트들을 관리하고 협업을 조정하는 메인 오케스트레이터
NasDataBase와 NysDataBase를 통합하여 백테스트 실행

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
import yaml
from typing import Dict, List, Any, Optional
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.dirname(project_root))


class OrchestratorAgent:
    """
    오케스트레이터 에이전트

    모든 서브 에이전트들의 작업을 조정하고 전체 워크플로우를 관리
    """

    def __init__(self, config_path: Optional[str] = None):
        """오케스트레이터 초기화"""
        self.execution_log = []
        self.agents = {}
        self.config = self._load_config(config_path)

        # 서브 에이전트들 초기화
        self._initialize_agents()

        self._log("[오케스트레이터] Multi-Agent Trading System 초기화 완료")
        self._log(f"[오케스트레이터] 활성 에이전트: {list(self.agents.keys())}")

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """설정 파일 로드"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(project_root), 'myStockInfo.yaml')

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='UTF-8') as f:
                    config = yaml.load(f, Loader=yaml.FullLoader)
                self._log("[오케스트레이터] 설정 파일 로드 완료")
                return config
            else:
                self._log("[오케스트레이터] 설정 파일 없음 - 기본 설정 사용")
                return self._get_default_config()
        except Exception as e:
            self._log(f"[오케스트레이터] 설정 파일 로드 실패: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            'MONGODB_LOCAL': 'localhost',
            'MONGODB_PORT': 27017,
            'MONGODB_ID': 'admin',
            'MONGODB_PW': 'wlsaud07',
            'backtest_config': {
                'initial_cash': 100000000,  # 1억원
                'commission_rate': 0.002,   # 0.2% 수수료
                'slippage': 0.001,         # 0.1% 슬리피지
                'max_stocks_per_market': 5,  # 시장별 최대 종목 수
            }
        }

    def _initialize_agents(self):
        """서브 에이전트들 초기화"""
        try:
            # Data Agent 초기화
            from data_agent import DataAgent
            self.agents['data'] = DataAgent(self.config)
            self._log("[오케스트레이터] Data Agent 초기화 완료")

            # Strategy Agent 초기화
            from strategy_agent import StrategyAgent
            self.agents['strategy'] = StrategyAgent(self.config)
            self._log("[오케스트레이터] Strategy Agent 초기화 완료")

            # Service Agent 초기화
            from service_agent import ServiceAgent
            self.agents['service'] = ServiceAgent(self.config)
            self._log("[오케스트레이터] Service Agent 초기화 완료")

            # Helper Agent 초기화
            from helper_agent import HelperAgent
            self.agents['helper'] = HelperAgent()
            self._log("[오케스트레이터] Helper Agent 초기화 완료")

            # RUN Agent 초기화
            from run_agent import RunAgent
            self.agents['run'] = RunAgent()
            self._log("[오케스트레이터] RUN Agent 초기화 완료")

        except ImportError as e:
            self._log(f"[오케스트레이터] 에이전트 초기화 실패: {e}")
            self._log("[오케스트레이터] 기본 에이전트로 대체 실행")

    def execute_integrated_backtest(self,
                                   start_date: str = "2023-01-01",
                                   end_date: str = "2023-12-31",
                                   nas_symbols: Optional[List[str]] = None,
                                   nys_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        통합 백테스트 실행

        Args:
            start_date: 백테스트 시작일
            end_date: 백테스트 종료일
            nas_symbols: NASDAQ 종목 리스트 (None이면 자동 선택)
            nys_symbols: NYSE 종목 리스트 (None이면 자동 선택)

        Returns:
            백테스트 결과
        """
        overall_start_time = time.time()

        try:
            self._log("="*80)
            self._log("[오케스트레이터] Multi-Agent 통합 백테스트 시작")
            self._log(f"[오케스트레이터] 기간: {start_date} ~ {end_date}")
            self._log("="*80)

            # Phase 1: Data Agent - 데이터 수집 및 준비
            self._log("\n[Phase 1] Data Agent 작업 시작")
            market_data = self._delegate_to_data_agent(start_date, end_date, nas_symbols, nys_symbols)

            if not market_data:
                self._log("[오케스트레이터] 데이터 로드 실패 - 백테스트 중단")
                return None

            # Phase 2: Strategy Agent - 매매 신호 생성
            self._log("\n[Phase 2] Strategy Agent 작업 시작")
            signals = self._delegate_to_strategy_agent(market_data)

            # Phase 3: Service Agent - 백테스트 실행
            self._log("\n[Phase 3] Service Agent 작업 시작")
            backtest_results = self._delegate_to_service_agent(market_data, signals, start_date, end_date)

            # Phase 4: 결과 통합 및 분석
            self._log("\n[Phase 4] 오케스트레이터 결과 통합")
            final_results = self._consolidate_results(backtest_results, market_data, signals)

            total_time = time.time() - overall_start_time
            self._log(f"\n[오케스트레이터] 전체 실행 시간: {total_time:.2f}초")
            self._log("[오케스트레이터] Multi-Agent 통합 백테스트 완료!")

            return final_results

        except Exception as e:
            self._log(f"[오케스트레이터] 백테스트 실행 실패: {e}")
            return None

    def _delegate_to_data_agent(self, start_date: str, end_date: str,
                               nas_symbols: Optional[List[str]],
                               nys_symbols: Optional[List[str]]) -> Dict[str, pd.DataFrame]:
        """Data Agent에게 데이터 로드 작업 위임"""

        if 'data' in self.agents:
            self._log("[오케스트레이터] Data Agent에게 데이터 로드 작업 위임")

            # Data Agent 프롬프트 생성
            data_prompt = f"""
            Data Agent 작업 지시:

            1. NasDataBase_D와 NysDataBase_D에서 데이터 로드
            2. 기간: {start_date} ~ {end_date}
            3. NASDAQ 종목: {nas_symbols if nas_symbols else '자동 선택 (5개)'}
            4. NYSE 종목: {nys_symbols if nys_symbols else '자동 선택 (5개)'}
            5. 기술지표 계산 포함
            6. 표준화된 OHLCV 포맷으로 반환

            요구사항:
            - MongoDB 연결 및 데이터 검증
            - 결측치 처리 및 데이터 품질 확인
            - 이동평균, RSI, 볼린저밴드, MACD 등 기술지표 추가
            """

            return self.agents['data'].execute_data_loading(
                start_date=start_date,
                end_date=end_date,
                nas_symbols=nas_symbols,
                nys_symbols=nys_symbols,
                prompt=data_prompt
            )
        else:
            # Fallback: 직접 데이터 로드
            self._log("[오케스트레이터] Data Agent 없음 - 직접 데이터 로드")
            return self._fallback_data_loading(start_date, end_date, nas_symbols, nys_symbols)

    def _delegate_to_strategy_agent(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Strategy Agent에게 신호 생성 작업 위임"""

        if 'strategy' in self.agents:
            self._log("[오케스트레이터] Strategy Agent에게 신호 생성 작업 위임")

            # Strategy Agent 프롬프트 생성
            strategy_prompt = f"""
            Strategy Agent 작업 지시:

            1. 시장별 차별화된 전략 적용
               - NASDAQ: 기술주 특성 고려한 성장주 전략
               - NYSE: 대형주 특성 고려한 가치주 전략

            2. 신호 생성 규칙:
               - 골든크로스/데드크로스 (MA5/MA20)
               - RSI 필터링 (30-70 범위)
               - 볼린저밴드 돌파 신호
               - MACD 확인 신호

            3. 리스크 관리:
               - 시장별 포지션 크기 조절
               - 상관관계 고려한 포트폴리오 분산
               - 시장 변동성 기반 포지션 조정

            4. 종목 수: NASDAQ {len([k for k in market_data.keys() if 'NAS' in k])}개, NYSE {len([k for k in market_data.keys() if 'NYS' in k])}개
            """

            return self.agents['strategy'].generate_trading_signals(
                market_data=market_data,
                prompt=strategy_prompt
            )
        else:
            # Fallback: 직접 신호 생성
            self._log("[오케스트레이터] Strategy Agent 없음 - 직접 신호 생성")
            return self._fallback_signal_generation(market_data)

    def _delegate_to_service_agent(self, market_data: Dict[str, pd.DataFrame],
                                  signals: Dict[str, Any],
                                  start_date: str, end_date: str) -> Dict[str, Any]:
        """Service Agent에게 백테스트 실행 위임"""

        if 'service' in self.agents:
            self._log("[오케스트레이터] Service Agent에게 백테스트 실행 위임")

            # Service Agent 프롬프트 생성
            service_prompt = f"""
            Service Agent 작업 지시:

            1. 통합 백테스트 엔진 실행
               - 시장별 구분된 포트폴리오 관리
               - 실시간 리스크 모니터링
               - 동적 포지션 크기 조절

            2. 실행 파라미터:
               - 초기 자본: {self.config.get('backtest_config', {}).get('initial_cash', 100000000):,}원
               - 수수료: {self.config.get('backtest_config', {}).get('commission_rate', 0.002):.1%}
               - 슬리피지: {self.config.get('backtest_config', {}).get('slippage', 0.001):.1%}

            3. 성과 측정:
               - 시장별 수익률 분석
               - 리스크 조정 수익률 계산
               - 최대 낙폭 및 샤프 비율
               - 거래 통계 및 승률

            4. 기간: {start_date} ~ {end_date}
            """

            return self.agents['service'].execute_backtest(
                market_data=market_data,
                signals=signals,
                start_date=start_date,
                end_date=end_date,
                prompt=service_prompt
            )
        else:
            # Fallback: 직접 백테스트 실행
            self._log("[오케스트레이터] Service Agent 없음 - 직접 백테스트 실행")
            return self._fallback_backtest_execution(market_data, signals)

    def _consolidate_results(self, backtest_results: Dict[str, Any],
                           market_data: Dict[str, pd.DataFrame],
                           signals: Dict[str, Any]) -> Dict[str, Any]:
        """결과 통합 및 최종 분석"""

        self._log("[오케스트레이터] 결과 통합 및 분석 중...")

        # 시장별 결과 분리
        nas_results = {}
        nys_results = {}

        for ticker, data in market_data.items():
            if any(nas_market in ticker for nas_market in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']):
                nas_results[ticker] = data
            else:
                nys_results[ticker] = data

        # 통합 성과 분석
        consolidated_results = {
            'overall_performance': backtest_results,
            'market_breakdown': {
                'NASDAQ': {
                    'symbols': list(nas_results.keys()),
                    'symbol_count': len(nas_results)
                },
                'NYSE': {
                    'symbols': list(nys_results.keys()),
                    'symbol_count': len(nys_results)
                }
            },
            'execution_summary': {
                'total_symbols': len(market_data),
                'total_signals': sum(len(s.get('buy_signals', [])) + len(s.get('sell_signals', []))
                                   for s in signals.values() if isinstance(s, dict)),
                'data_quality': self._assess_data_quality(market_data),
                'signal_quality': self._assess_signal_quality(signals)
            }
        }

        # 최종 리포트 생성
        self._generate_final_report(consolidated_results)

        return consolidated_results

    def _assess_data_quality(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """데이터 품질 평가"""
        quality_metrics = {
            'total_symbols': len(market_data),
            'avg_data_points': np.mean([len(df) for df in market_data.values()]),
            'missing_data_ratio': 0,
            'date_range_coverage': 100
        }

        # 결측치 비율 계산
        total_missing = sum(df.isnull().sum().sum() for df in market_data.values())
        total_points = sum(df.size for df in market_data.values())
        quality_metrics['missing_data_ratio'] = (total_missing / total_points * 100) if total_points > 0 else 0

        return quality_metrics

    def _assess_signal_quality(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """신호 품질 평가"""
        if not signals:
            return {'total_signals': 0, 'signal_distribution': {}}

        total_buy_signals = sum(len(s.get('buy_signals', [])) for s in signals.values() if isinstance(s, dict))
        total_sell_signals = sum(len(s.get('sell_signals', [])) for s in signals.values() if isinstance(s, dict))

        return {
            'total_signals': total_buy_signals + total_sell_signals,
            'buy_signals': total_buy_signals,
            'sell_signals': total_sell_signals,
            'signal_balance': abs(total_buy_signals - total_sell_signals) / max(total_buy_signals + total_sell_signals, 1)
        }

    def _generate_final_report(self, results: Dict[str, Any]):
        """최종 리포트 생성"""
        self._log("\n" + "="*80)
        self._log("[오케스트레이터] Multi-Agent 백테스트 최종 리포트")
        self._log("="*80)

        # 시장별 요약
        market_breakdown = results['market_breakdown']
        self._log(f"[시장 구성] NASDAQ: {market_breakdown['NASDAQ']['symbol_count']}개 종목")
        self._log(f"[시장 구성] NYSE: {market_breakdown['NYSE']['symbol_count']}개 종목")

        # 실행 요약
        exec_summary = results['execution_summary']
        self._log(f"[실행 통계] 총 종목: {exec_summary['total_symbols']}개")
        self._log(f"[실행 통계] 총 신호: {exec_summary['total_signals']}개")

        # 데이터 품질
        data_quality = exec_summary['data_quality']
        self._log(f"[데이터 품질] 평균 데이터 포인트: {data_quality['avg_data_points']:.0f}개")
        self._log(f"[데이터 품질] 결측치 비율: {data_quality['missing_data_ratio']:.2f}%")

    # Fallback 메서드들 (에이전트 없을 때 사용)
    def _fallback_data_loading(self, start_date: str, end_date: str,
                              nas_symbols: Optional[List[str]],
                              nys_symbols: Optional[List[str]]) -> Dict[str, pd.DataFrame]:
        """데이터 로드 fallback"""
        from mongodb_integrated_backtest import MongoDBIntegratedBacktest

        backtest_system = MongoDBIntegratedBacktest()

        # 기본 종목 설정
        if not nas_symbols:
            nas_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        if not nys_symbols:
            nys_symbols = ['JNJ', 'PG', 'KO', 'DIS', 'WMT']  # NYSE 대표 종목들

        universe = nas_symbols + nys_symbols

        # MongoDB 연결 및 데이터 로드 시도
        if backtest_system._connect_mongodb():
            return backtest_system._load_mongodb_data(universe, start_date, end_date)
        else:
            return backtest_system._load_yfinance_fallback(universe, start_date, end_date)

    def _fallback_signal_generation(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """신호 생성 fallback"""
        from mongodb_integrated_backtest import MongoDBIntegratedBacktest

        backtest_system = MongoDBIntegratedBacktest()
        return backtest_system._generate_signals(market_data)

    def _fallback_backtest_execution(self, market_data: Dict[str, pd.DataFrame],
                                   signals: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 실행 fallback"""
        from mongodb_integrated_backtest import MongoDBIntegratedBacktest

        backtest_system = MongoDBIntegratedBacktest()
        return backtest_system._run_simple_backtest(market_data, signals)

    def _log(self, message: str):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)

    def get_execution_log(self) -> List[str]:
        """실행 로그 반환"""
        return self.execution_log.copy()

    def get_agent_status(self) -> Dict[str, bool]:
        """에이전트 상태 반환"""
        return {name: agent is not None for name, agent in self.agents.items()}


def main():
    """메인 실행 함수"""
    try:
        print("[시작] Multi-Agent 통합 백테스트 시스템 시작")

        # 오케스트레이터 초기화
        orchestrator = OrchestratorAgent()

        # 통합 백테스트 실행
        results = orchestrator.execute_integrated_backtest(
            start_date="2023-01-01",
            end_date="2023-12-31",
            nas_symbols=None,  # 자동 선택
            nys_symbols=None   # 자동 선택
        )

        if results:
            print("\n[성공] Multi-Agent 통합 백테스트 완료")

            # 에이전트 상태 출력
            agent_status = orchestrator.get_agent_status()
            print(f"[에이전트 상태] {agent_status}")

        else:
            print("\n[실패] 백테스트 실행 실패")

    except Exception as e:
        print(f"\n[실패] 메인 실행 실패: {e}")


if __name__ == "__main__":
    main()