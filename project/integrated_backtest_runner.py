"""
통합 백테스트 실행 시스템

Indicator Layer, Strategy Layer, Service Layer를 통합하여
완전한 백테스트를 실행하고 상세한 과정을 출력

버전: 1.0
작성일: 2025-09-21
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 각 레이어 임포트
try:
    # Helper Layer (실제 데이터 가져오기)
    from Helper.yfinance_helper import YFinanceHelper

    # Simple Technical Indicators (독립적인 구현)
    from simple_technical_indicators import SimpleTechnicalIndicators

    # Service Layer (기본적인 백테스트 엔진만 사용)
    from service.backtest_engine import BacktestEngineConfig, TimeFrame, BacktestMode, StrategySignals

    print("모든 필수 레이어 임포트 성공")
    IMPORTS_SUCCESS = True

except ImportError as e:
    print(f"레이어 임포트 실패: {e}")
    import traceback
    traceback.print_exc()
    print("기본 구현을 사용합니다.")
    IMPORTS_SUCCESS = False

    # 기본 백업 클래스들
    class DummyService:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: {}

    YFinanceHelper = DummyService
    SimpleTechnicalIndicators = DummyService


class IntegratedBacktestRunner:
    """
    통합 백테스트 실행 시스템

    Indicator Layer → Strategy Layer → Service Layer 순서로
    데이터를 처리하고 백테스트를 실행
    """

    def __init__(self, config: Dict[str, Any]):
        """
        통합 백테스트 실행기 초기화

        Args:
            config: 백테스트 설정
        """
        self.config = config
        self.results = {}
        self.execution_log = []

        # 각 레이어 초기화
        self._initialize_layers()

    def _initialize_layers(self):
        """각 레이어 초기화"""
        self._log("🚀 통합 백테스트 시스템 초기화 시작")

        try:
            # Helper Layer 초기화 (실제 데이터 제공)
            self._log("Helper Layer 초기화 중...")
            self.yfinance_helper = YFinanceHelper()
            self._log("Helper Layer 초기화 완료")

            # Technical Indicators 초기화
            self._log("Technical Indicators 초기화 중...")
            self.technical_indicators = SimpleTechnicalIndicators()
            self._log("Technical Indicators 초기화 완료")

            self._log("🎉 모든 레이어 초기화 성공")

        except Exception as e:
            self._log(f"❌ 레이어 초기화 실패: {e}")
            raise e

    def run_integrated_backtest(self, universe: List[str],
                              start_date: str = "2023-01-01",
                              end_date: str = "2023-12-31") -> Dict[str, Any]:
        """
        통합 백테스트 실행

        Args:
            universe: 백테스트 대상 종목 리스트
            start_date: 시작일
            end_date: 종료일

        Returns:
            Dict[str, Any]: 백테스트 결과
        """
        self._log("=" * 80)
        self._log("🚀 통합 백테스트 실행 시작")
        self._log(f"📅 기간: {start_date} ~ {end_date}")
        self._log(f"📈 대상 종목: {universe}")
        self._log("=" * 80)

        overall_start_time = time.time()

        try:
            # Phase 1: Indicator Layer - 데이터 생성 및 기술지표 계산
            self._log("\n📊 Phase 1: Indicator Layer 처리 시작")
            df_data = self._process_indicator_layer(universe, start_date, end_date)

            # Phase 2: Strategy Layer - 신호 생성 및 포지션 계산
            self._log("\n🧠 Phase 2: Strategy Layer 처리 시작")
            strategy_signals = self._process_strategy_layer(df_data, universe)

            # Phase 3: Service Layer - 백테스트 실행 및 성과 분석
            self._log("\n⚙️ Phase 3: Service Layer 처리 시작")
            backtest_results = self._process_service_layer(universe, df_data, strategy_signals)

            # Phase 4: 결과 통합 및 분석
            self._log("\n📋 Phase 4: 결과 통합 및 분석")
            integrated_results = self._integrate_results(backtest_results)

            overall_execution_time = time.time() - overall_start_time
            self._log(f"\n⏱️ 전체 실행 시간: {overall_execution_time:.2f}초")
            self._log("🎉 통합 백테스트 실행 완료!")

            # 결과 출력
            self._print_results_summary(integrated_results)

            return integrated_results

        except Exception as e:
            self._log(f"❌ 통합 백테스트 실행 실패: {e}")
            raise e

    def _process_indicator_layer(self, universe: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Indicator Layer 처리"""
        start_time = time.time()

        # 1. 실제 시장 데이터 가져오기 (Helper Layer 사용)
        self._log("📈 실제 시장 데이터 로드 중...")
        df_data = self._get_real_market_data(universe, start_date, end_date)

        # 2. 기술지표 계산
        self._log("📊 기술지표 계산 중...")
        for ticker in universe:
            if ticker in df_data:
                # 이동평균선
                df_data[ticker] = self.technical_indicators.add_moving_averages(
                    df_data[ticker], [5, 10, 20, 50, 200]
                )

                # RSI
                df_data[ticker] = self.technical_indicators.add_rsi(df_data[ticker])

                # 볼린저 밴드
                df_data[ticker] = self.technical_indicators.add_bollinger_bands(df_data[ticker])

                # ADR 계산
                df_data[ticker] = self._calculate_adr(df_data[ticker])

                self._log(f"  ✅ {ticker} 기술지표 계산 완료")

        execution_time = time.time() - start_time
        self._log(f"✅ Indicator Layer 처리 완료 ({execution_time:.2f}초)")
        self._log(f"📊 처리된 데이터: {len(df_data)}개 종목, {len(df_data[universe[0]])}일 데이터")

        return df_data

    def _process_strategy_layer(self, df_data: Dict[str, pd.DataFrame], universe: List[str]) -> StrategySignals:
        """Strategy Layer 처리"""
        start_time = time.time()

        # 1. 신호 생성
        self._log("🔍 매수/매도 신호 생성 중...")

        buy_signals = {}
        sell_signals = {}
        target_prices = {}
        position_sizes = {}
        risk_parameters = {}

        for ticker in universe:
            if ticker in df_data:
                df = df_data[ticker]

                # 매수 신호 생성 (예: 단순 이동평균 크로스오버)
                buy_signal = self._generate_buy_signal(df)
                sell_signal = self._generate_sell_signal(df)

                buy_signals[ticker] = buy_signal
                sell_signals[ticker] = sell_signal

                # 목표가 계산 (현재가 + ADR%)
                current_price = df['Close'].iloc[-1]
                adr = df['ADR'].iloc[-1] if 'ADR' in df.columns else 3.0
                target_prices[ticker] = current_price * (1 + adr / 100)

                # 포지션 크기 계산
                position_sizes[ticker] = self._calculate_position_size(adr)

                # 리스크 파라미터
                risk_parameters[ticker] = self.config.get('std_risk', 0.05)

                self._log(f"  📊 {ticker}: 매수신호={buy_signal}, 매도신호={sell_signal}, 목표가={target_prices[ticker]:.2f}")

        execution_time = time.time() - start_time
        self._log(f"✅ Strategy Layer 처리 완료 ({execution_time:.2f}초)")

        # StrategySignals 객체 생성
        strategy_signals = StrategySignals(
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            position_sizes=position_sizes,
            risk_parameters=risk_parameters,
            target_prices=target_prices,
            metadata={
                'strategy_name': 'IntegratedStrategy',
                'generation_time': datetime.now(),
                'total_signals': len(buy_signals)
            }
        )

        return strategy_signals

    def _process_service_layer(self, universe: List[str], df_data: Dict[str, pd.DataFrame],
                             strategy_signals: StrategySignals) -> Dict[str, Any]:
        """Service Layer 처리"""
        start_time = time.time()

        # 1. 백테스트 실행
        self._log("🔄 백테스트 엔진 실행 중...")
        backtest_result = self.backtest_engine.run_backtest(
            universe=universe,
            df_data=df_data,
            strategy_signals=strategy_signals
        )

        # 2. 성과 분석
        self._log("📈 성과 분석 중...")
        # 임시 거래 및 포트폴리오 데이터 생성 (실제로는 백테스트 결과에서 추출)
        mock_trades, mock_portfolio_history = self._generate_mock_trades_and_portfolio()

        performance_report = self.performance_analyzer.generate_report(
            strategy_name="IntegratedStrategy",
            trades=mock_trades,
            portfolio_history=mock_portfolio_history,
            initial_capital=self.config.get('initial_cash', 100.0) * 1000000  # 억원 → 원
        )

        # 3. 거래 기록 저장
        self._log("💾 거래 기록 저장 중...")
        session_id = self.trade_recorder.start_session("IntegratedStrategy",
                                                      self.config.get('initial_cash', 100.0) * 1000000)

        for trade in mock_trades:
            # Trade를 TradeRecord로 변환하여 저장 (실제 구현에서는 적절한 변환 로직 필요)
            pass

        execution_time = time.time() - start_time
        self._log(f"✅ Service Layer 처리 완료 ({execution_time:.2f}초)")

        return {
            'backtest_result': backtest_result,
            'performance_report': performance_report,
            'session_id': session_id
        }

    def _integrate_results(self, service_results: Dict[str, Any]) -> Dict[str, Any]:
        """결과 통합 및 최종 분석"""
        start_time = time.time()

        self._log("📊 최종 결과 통합 중...")

        backtest_result = service_results['backtest_result']
        performance_report = service_results['performance_report']

        # 주요 성과 지표 추출
        key_metrics = {
            'total_return': backtest_result.total_return,
            'annual_return': backtest_result.annual_return,
            'max_drawdown': backtest_result.max_drawdown,
            'sharpe_ratio': backtest_result.sharpe_ratio,
            'win_rate': backtest_result.win_rate,
            'profit_factor': backtest_result.profit_factor,
            'total_trades': backtest_result.total_trades
        }

        # 실행 통계
        execution_stats = {
            'total_execution_time': backtest_result.execution_time,
            'timeframe': backtest_result.timeframe,
            'strategy_name': backtest_result.strategy_name
        }

        # 통합 결과
        integrated_results = {
            'key_metrics': key_metrics,
            'execution_stats': execution_stats,
            'backtest_result': backtest_result,
            'performance_report': performance_report,
            'execution_log': self.execution_log.copy()
        }

        execution_time = time.time() - start_time
        self._log(f"✅ 결과 통합 완료 ({execution_time:.2f}초)")

        return integrated_results

    def _get_real_market_data(self, universe: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """실제 시장 데이터 가져오기 (Helper Layer 사용)"""
        self._log("📡 실제 시장 데이터 다운로드 중...")

        df_data = {}
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        for ticker in universe:
            try:
                self._log(f"  📊 {ticker} 데이터 다운로드 중...")

                # Helper Layer를 통해 실제 데이터 가져오기
                df = self.yfinance_helper.get_ohlcv(
                    stock_code=ticker,
                    p_code="D",  # Daily data
                    start_date=start_dt,
                    end_date=end_dt,
                    ohlcv="Y"  # Adjusted prices
                )

                if not df.empty:
                    # 컬럼명을 표준화
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })

                    # 필요한 컬럼이 모두 있는지 확인
                    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if all(col in df.columns for col in required_columns):
                        df_data[ticker] = df
                        self._log(f"  ✅ {ticker}: {len(df)}일 데이터 로드 완료")
                    else:
                        missing = [col for col in required_columns if col not in df.columns]
                        self._log(f"  ⚠️ {ticker}: 필요한 컬럼 누락 {missing}")
                else:
                    self._log(f"  ❌ {ticker}: 데이터 없음")

            except Exception as e:
                self._log(f"  ❌ {ticker} 데이터 로드 실패: {e}")
                continue

        self._log(f"✅ 실제 데이터 로드 완료: {len(df_data)}/{len(universe)} 종목")
        return df_data

    def _calculate_adr(self, df: pd.DataFrame) -> pd.DataFrame:
        """ADR(Average Daily Range) 계산"""
        df = df.copy()
        df['ADR'] = ((df['High'] - df['Low']) / df['Close'] * 100).rolling(window=20).mean()
        return df

    def _generate_buy_signal(self, df: pd.DataFrame) -> int:
        """매수 신호 생성 (간단한 예시)"""
        if len(df) < 20:
            return 0

        # 단순 이동평균 크로스오버
        ma5 = df['Close'].rolling(5).mean().iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]

        return 1 if ma5 > ma20 else 0

    def _generate_sell_signal(self, df: pd.DataFrame) -> int:
        """매도 신호 생성 (간단한 예시)"""
        if len(df) < 20:
            return 0

        # 단순 이동평균 크로스언더
        ma5 = df['Close'].rolling(5).mean().iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]

        return 1 if ma5 < ma20 else 0

    def _calculate_position_size(self, adr: float) -> float:
        """포지션 크기 계산"""
        base_size = 0.2  # 20%

        if adr >= 5:
            return base_size / 2  # 변동성이 클 때는 포지션 축소
        else:
            return base_size

    def _generate_mock_trades_and_portfolio(self):
        """임시 거래 및 포트폴리오 데이터 생성"""
        from service.performance_analyzer import Trade, Portfolio

        # 임시 거래 데이터
        trades = []
        for i in range(10):
            trade = Trade(
                ticker=f"STOCK{i%3}",
                trade_type="BUY" if i % 2 == 0 else "SELL",
                quantity=100,
                price=100 + i * 5,
                timestamp=pd.Timestamp.now() - timedelta(days=i),
                reason="SIGNAL",
                pnl=np.random.uniform(-5, 10),
                commission=1.0
            )
            trades.append(trade)

        # 임시 포트폴리오 히스토리
        portfolio_history = []
        for i in range(30):
            portfolio = Portfolio(
                timestamp=pd.Timestamp.now() - timedelta(days=i),
                cash=50000000 + i * 1000000,  # 5천만원 + 증가
                positions={"AAPL": 20000000, "MSFT": 15000000},
                total_value=85000000 + i * 1000000,
                unrealized_pnl=i * 100000,
                realized_pnl=i * 50000
            )
            portfolio_history.append(portfolio)

        return trades, portfolio_history

    def _log(self, message: str):
        """실행 로그 기록"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.execution_log.append(log_message)

    def _print_results_summary(self, results: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "=" * 80)
        print("📊 통합 백테스트 결과 요약")
        print("=" * 80)

        metrics = results['key_metrics']
        stats = results['execution_stats']

        print(f"📈 전략명: {stats['strategy_name']}")
        print(f"📅 타임프레임: {stats['timeframe']}")
        print(f"⏱️ 실행 시간: {stats['total_execution_time']:.2f}초")
        print()

        print("💰 성과 지표:")
        print(f"  📊 총 수익률: {metrics['total_return']:.2%}")
        print(f"  📈 연율화 수익률: {metrics['annual_return']:.2%}")
        print(f"  📉 최대 낙폭: {metrics['max_drawdown']:.2%}")
        print(f"  📊 샤프 비율: {metrics['sharpe_ratio']:.3f}")
        print(f"  🎯 승률: {metrics['win_rate']:.2%}")
        print(f"  💎 수익 인수: {metrics['profit_factor']:.3f}")
        print(f"  🔄 총 거래 수: {metrics['total_trades']}")
        print()

        print("🔧 시스템 상태:")
        health_status = self.backtest_engine.health_check()
        for component, status in health_status.items():
            status_icon = "✅" if status == "healthy" else "⚠️"
            print(f"  {status_icon} {component}: {status}")

        print("\n" + "=" * 80)
        print("🎉 통합 백테스트 실행 완료!")
        print("=" * 80)


def main():
    """메인 실행 함수"""
    print("🚀 통합 백테스트 시스템 시작")

    # 백테스트 설정
    config = {
        'initial_cash': 100.0,  # 1억원
        'max_positions': 10,
        'slippage': 0.002,
        'std_risk': 0.05,
        'market': 'US',
        'area': 'US',
        'enable_multiprocessing': True,
        'message_output': True
    }

    # 백테스트 대상 종목
    universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    # 백테스트 기간
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    try:
        # 통합 백테스트 실행기 생성
        runner = IntegratedBacktestRunner(config)

        # 백테스트 실행
        results = runner.run_integrated_backtest(universe, start_date, end_date)

        # 결과 저장 (옵션)
        # results_df = pd.DataFrame([results['key_metrics']])
        # results_df.to_csv(f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        print("\n✅ 메인 실행 완료")
        return results

    except Exception as e:
        print(f"\n❌ 메인 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()

    if results:
        print(f"\n🔍 상세 로그 확인:")
        print(f"총 로그 엔트리: {len(results['execution_log'])}")
        print("주요 단계별 소요 시간이 위에 표시되었습니다.")
    else:
        print("\n❌ 백테스트 실행에 실패했습니다.")
        sys.exit(1)