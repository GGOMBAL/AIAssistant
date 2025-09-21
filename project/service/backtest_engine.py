"""
Service Layer Unified Backtest Engine

일봉/분봉 백테스트 서비스를 통합 관리하는 메인 엔진
Strategy Layer에서 전달받은 신호를 바탕으로 백테스트 실행

버전: 1.0
작성일: 2025-09-21
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from .daily_backtest_service import DailyBacktestService, BacktestConfig
from .minute_backtest_service import MinuteBacktestService
from .execution_services import BacktestExecutionServices, ExecutionConfig


class TimeFrame(Enum):
    """백테스트 타임프레임"""
    DAILY = "daily"
    MINUTE = "minute"
    HOURLY = "hourly"  # 확장 가능


class BacktestMode(Enum):
    """백테스트 모드"""
    SINGLE = "single"      # 단일 전략
    COMPARISON = "comparison"  # 전략 비교
    OPTIMIZATION = "optimization"  # 파라미터 최적화


@dataclass
class BacktestEngineConfig:
    """백테스트 엔진 설정"""
    timeframe: TimeFrame = TimeFrame.DAILY
    mode: BacktestMode = BacktestMode.SINGLE
    initial_cash: float = 100.0  # 1억원
    max_positions: int = 10
    slippage: float = 0.002
    std_risk: float = 0.05
    market: str = 'US'
    area: str = 'US'
    enable_multiprocessing: bool = True
    max_workers: Optional[int] = None
    message_output: bool = False


@dataclass
class StrategySignals:
    """Strategy Layer에서 전달받는 신호 데이터"""
    buy_signals: Dict[str, Any]
    sell_signals: Dict[str, Any]
    position_sizes: Dict[str, float]
    risk_parameters: Dict[str, float]
    target_prices: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """통합 백테스트 결과"""
    timeframe: str
    strategy_name: str
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    execution_time: float
    trades: List[Dict]
    portfolio_history: List[Dict]
    daily_returns: pd.Series
    equity_curve: pd.Series
    drawdown_series: pd.Series
    detailed_metrics: Dict[str, Any]


@dataclass
class ComparisonReport:
    """전략 비교 리포트"""
    strategies: List[str]
    results: List[BacktestResult]
    comparison_metrics: pd.DataFrame
    ranking: Dict[str, int]
    best_strategy: str
    worst_strategy: str


@dataclass
class OptimizationResult:
    """파라미터 최적화 결과"""
    best_parameters: Dict[str, Any]
    best_result: BacktestResult
    parameter_results: List[Tuple[Dict, BacktestResult]]
    optimization_surface: Optional[pd.DataFrame] = None


class BacktestEngine:
    """
    Service Layer 통합 백테스트 엔진

    일봉/분봉 백테스트 서비스를 통합 관리하고
    Strategy Layer와의 인터페이스를 제공
    """

    def __init__(self, config: BacktestEngineConfig):
        """백테스트 엔진 초기화"""
        self.config = config
        self.timeframe = config.timeframe
        self.mode = config.mode

        # 백테스트 설정 초기화
        self.backtest_config = BacktestConfig(
            initial_cash=config.initial_cash,
            max_positions=config.max_positions,
            slippage=config.slippage,
            std_risk=config.std_risk,
            message_output=config.message_output
        )

        # 실행 서비스 설정 초기화
        self.execution_config = ExecutionConfig(
            std_risk=config.std_risk,
            slippage=config.slippage,
            max_stock_list=config.max_positions,
            message_output=config.message_output
        )

        # 서비스 인스턴스 초기화
        self._initialize_services()

    def _initialize_services(self):
        """백테스트 서비스들 초기화"""
        self.daily_service = DailyBacktestService(self.backtest_config)
        self.minute_service = MinuteBacktestService(self.backtest_config)
        self.execution_service = BacktestExecutionServices(
            self.execution_config,
            self.config.market,
            self.config.area
        )

    def run_backtest(self,
                    universe: List[str],
                    df_data: Dict[str, pd.DataFrame],
                    strategy_signals: StrategySignals,
                    timeframe: Optional[TimeFrame] = None) -> BacktestResult:
        """
        백테스트 실행

        Args:
            universe: 백테스트 대상 종목 리스트
            df_data: 종목별 가격 데이터
            strategy_signals: Strategy Layer에서 생성된 신호
            timeframe: 타임프레임 (지정하지 않으면 설정값 사용)

        Returns:
            BacktestResult: 백테스트 결과
        """
        start_time = time.time()

        if timeframe is None:
            timeframe = self.timeframe

        try:
            if timeframe == TimeFrame.DAILY:
                result = self._run_daily_backtest(universe, df_data, strategy_signals)
            elif timeframe == TimeFrame.MINUTE:
                result = self._run_minute_backtest(universe, df_data, strategy_signals)
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            execution_time = time.time() - start_time

            # 결과에 실행 시간 추가
            result['execution_time'] = execution_time
            result['timeframe'] = timeframe.value

            # BacktestResult 객체로 변환
            return self._convert_to_backtest_result(result, timeframe.value)

        except Exception as e:
            print(f"Error during backtest execution: {e}")
            raise e

    def _run_daily_backtest(self, universe: List[str], df_data: Dict[str, pd.DataFrame],
                           strategy_signals: StrategySignals) -> Dict:
        """일봉 백테스트 실행"""
        return self.daily_service.run_backtest(
            universe=universe,
            df_data=df_data,
            market=self.config.market,
            area=self.config.area
        )

    def _run_minute_backtest(self, universe: List[str], df_data: Dict[str, pd.DataFrame],
                           strategy_signals: StrategySignals) -> Dict:
        """분봉 백테스트 실행"""
        return self.minute_service.run_backtest(
            universe=universe,
            df_data=df_data,
            market=self.config.market,
            area=self.config.area
        )

    def compare_strategies(self, strategies: List[Dict[str, Any]],
                          universe: List[str],
                          df_data: Dict[str, pd.DataFrame]) -> ComparisonReport:
        """
        여러 전략의 백테스트 결과 비교

        Args:
            strategies: 비교할 전략들의 설정 리스트
            universe: 백테스트 대상 종목 리스트
            df_data: 종목별 가격 데이터

        Returns:
            ComparisonReport: 전략 비교 리포트
        """
        results = []
        strategy_names = []

        for i, strategy in enumerate(strategies):
            strategy_name = strategy.get('name', f'Strategy_{i+1}')
            strategy_names.append(strategy_name)

            # 전략별 신호 생성 (실제로는 Strategy Layer에서 받아야 함)
            strategy_signals = self._generate_mock_signals(strategy, universe)

            # 백테스트 실행
            result = self.run_backtest(universe, df_data, strategy_signals)
            result.strategy_name = strategy_name
            results.append(result)

        # 비교 메트릭 생성
        comparison_metrics = self._create_comparison_metrics(results)

        # 랭킹 계산 (샤프 비율 기준)
        ranking = {result.strategy_name: i+1 for i, result in
                  enumerate(sorted(results, key=lambda x: x.sharpe_ratio, reverse=True))}

        best_strategy = min(ranking, key=ranking.get)
        worst_strategy = max(ranking, key=ranking.get)

        return ComparisonReport(
            strategies=strategy_names,
            results=results,
            comparison_metrics=comparison_metrics,
            ranking=ranking,
            best_strategy=best_strategy,
            worst_strategy=worst_strategy
        )

    def optimize_parameters(self, parameter_ranges: Dict[str, List],
                          universe: List[str],
                          df_data: Dict[str, pd.DataFrame],
                          base_strategy: Dict[str, Any],
                          optimization_metric: str = 'sharpe_ratio') -> OptimizationResult:
        """
        파라미터 최적화 (그리드 서치)

        Args:
            parameter_ranges: 최적화할 파라미터 범위 {param_name: [values]}
            universe: 백테스트 대상 종목 리스트
            df_data: 종목별 가격 데이터
            base_strategy: 기본 전략 설정
            optimization_metric: 최적화 기준 메트릭

        Returns:
            OptimizationResult: 최적화 결과
        """
        # 파라미터 조합 생성
        parameter_combinations = self._generate_parameter_combinations(parameter_ranges)

        # 최적화 실행
        if self.config.enable_multiprocessing and len(parameter_combinations) > 1:
            results = self._optimize_parallel(parameter_combinations, universe, df_data,
                                           base_strategy, optimization_metric)
        else:
            results = self._optimize_sequential(parameter_combinations, universe, df_data,
                                             base_strategy, optimization_metric)

        # 최적 결과 선택
        best_result = max(results, key=lambda x: getattr(x[1], optimization_metric))
        best_parameters, best_backtest_result = best_result

        return OptimizationResult(
            best_parameters=best_parameters,
            best_result=best_backtest_result,
            parameter_results=results
        )

    def _optimize_parallel(self, parameter_combinations: List[Dict], universe: List[str],
                          df_data: Dict[str, pd.DataFrame], base_strategy: Dict[str, Any],
                          optimization_metric: str) -> List[Tuple[Dict, BacktestResult]]:
        """병렬 파라미터 최적화"""
        max_workers = self.config.max_workers or mp.cpu_count()

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for params in parameter_combinations:
                future = executor.submit(
                    self._single_optimization_run,
                    params, universe, df_data, base_strategy
                )
                futures.append((params, future))

            results = []
            for params, future in futures:
                try:
                    result = future.result()
                    results.append((params, result))
                except Exception as e:
                    print(f"Error in optimization run with params {params}: {e}")

        return results

    def _optimize_sequential(self, parameter_combinations: List[Dict], universe: List[str],
                           df_data: Dict[str, pd.DataFrame], base_strategy: Dict[str, Any],
                           optimization_metric: str) -> List[Tuple[Dict, BacktestResult]]:
        """순차 파라미터 최적화"""
        results = []

        for params in parameter_combinations:
            try:
                result = self._single_optimization_run(params, universe, df_data, base_strategy)
                results.append((params, result))
            except Exception as e:
                print(f"Error in optimization run with params {params}: {e}")

        return results

    def _single_optimization_run(self, parameters: Dict, universe: List[str],
                               df_data: Dict[str, pd.DataFrame],
                               base_strategy: Dict[str, Any]) -> BacktestResult:
        """단일 최적화 실행"""
        # 파라미터를 적용한 전략 설정 생성
        strategy = base_strategy.copy()
        strategy.update(parameters)

        # 신호 생성
        strategy_signals = self._generate_mock_signals(strategy, universe)

        # 백테스트 실행
        return self.run_backtest(universe, df_data, strategy_signals)

    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List]) -> List[Dict]:
        """파라미터 조합 생성"""
        import itertools

        param_names = list(parameter_ranges.keys())
        param_values = [parameter_ranges[name] for name in param_names]

        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)

        return combinations

    def _generate_mock_signals(self, strategy: Dict[str, Any], universe: List[str]) -> StrategySignals:
        """
        임시 신호 생성 (실제로는 Strategy Layer에서 받아야 함)
        """
        # 임시 구현 - 실제로는 Strategy Layer 인터페이스를 통해 신호를 받아야 함
        return StrategySignals(
            buy_signals={stock: np.random.choice([0, 1]) for stock in universe},
            sell_signals={stock: np.random.choice([0, 1]) for stock in universe},
            position_sizes={stock: 0.1 for stock in universe},
            risk_parameters={stock: 0.05 for stock in universe},
            target_prices={stock: 100.0 for stock in universe},
            metadata={'strategy': strategy}
        )

    def _convert_to_backtest_result(self, result_dict: Dict, timeframe: str) -> BacktestResult:
        """백테스트 결과를 BacktestResult 객체로 변환"""
        # 기본 메트릭 계산
        total_return = result_dict.get('total_return', 0.0)
        annual_return = result_dict.get('annual_return', 0.0)
        max_drawdown = result_dict.get('max_drawdown', 0.0)
        sharpe_ratio = result_dict.get('sharpe_ratio', 0.0)
        win_rate = result_dict.get('win_rate', 0.0)
        profit_factor = result_dict.get('profit_factor', 1.0)
        total_trades = result_dict.get('total_trades', 0)
        execution_time = result_dict.get('execution_time', 0.0)

        # 시계열 데이터 생성
        trades = result_dict.get('trades', [])
        portfolio_history = result_dict.get('portfolio_history', [])

        # 임시 시계열 데이터 (실제로는 백테스트 결과에서 생성)
        daily_returns = pd.Series(dtype=float)
        equity_curve = pd.Series(dtype=float)
        drawdown_series = pd.Series(dtype=float)

        return BacktestResult(
            timeframe=timeframe,
            strategy_name=result_dict.get('strategy_name', 'Default'),
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            execution_time=execution_time,
            trades=trades,
            portfolio_history=portfolio_history,
            daily_returns=daily_returns,
            equity_curve=equity_curve,
            drawdown_series=drawdown_series,
            detailed_metrics=result_dict.get('detailed_metrics', {})
        )

    def _create_comparison_metrics(self, results: List[BacktestResult]) -> pd.DataFrame:
        """전략 비교 메트릭 생성"""
        metrics_data = []

        for result in results:
            metrics_data.append({
                'Strategy': result.strategy_name,
                'Total Return': result.total_return,
                'Annual Return': result.annual_return,
                'Max Drawdown': result.max_drawdown,
                'Sharpe Ratio': result.sharpe_ratio,
                'Win Rate': result.win_rate,
                'Profit Factor': result.profit_factor,
                'Total Trades': result.total_trades,
                'Execution Time': result.execution_time
            })

        return pd.DataFrame(metrics_data)

    def get_supported_timeframes(self) -> List[str]:
        """지원하는 타임프레임 목록 반환"""
        return [tf.value for tf in TimeFrame]

    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            'engine_version': '1.0',
            'supported_timeframes': self.get_supported_timeframes(),
            'config': {
                'timeframe': self.config.timeframe.value,
                'mode': self.config.mode.value,
                'initial_cash': self.config.initial_cash,
                'max_positions': self.config.max_positions,
                'slippage': self.config.slippage,
                'std_risk': self.config.std_risk,
                'market': self.config.market,
                'area': self.config.area,
                'enable_multiprocessing': self.config.enable_multiprocessing
            }
        }

    def health_check(self) -> Dict[str, str]:
        """서비스 상태 체크"""
        status = {
            'engine': 'healthy',
            'daily_service': 'healthy' if self.daily_service else 'unavailable',
            'minute_service': 'healthy' if self.minute_service else 'unavailable',
            'execution_service': 'healthy' if self.execution_service else 'unavailable'
        }

        overall_status = 'healthy' if all(s == 'healthy' for s in status.values()) else 'degraded'
        status['overall'] = overall_status

        return status