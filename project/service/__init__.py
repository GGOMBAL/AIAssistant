"""
Service Layer Package

백테스트, 실행, 성과 분석 등 서비스 레이어 모듈들을 관리
Strategy Layer에서 생성된 신호를 바탕으로 실제 거래 실행과 분석을 담당

버전: 1.0
작성일: 2025-09-21

모듈 구성:
- daily_backtest_service: 일봉 백테스트 서비스
- minute_backtest_service: 분봉 백테스트 서비스
- execution_services: 백테스트 실행 함수들
- backtest_engine: 통합 백테스트 엔진
- performance_analyzer: 성과 분석 및 리포팅
- trade_recorder: 거래 기록 관리
"""

try:
    from .daily_backtest_service import (
        DailyBacktestService,
        BacktestConfig
    )
except ImportError:
    pass

try:
    from .minute_backtest_service import (
        MinuteBacktestService
    )
except ImportError:
    pass

try:
    from .execution_services import (
        BacktestExecutionServices,
        ExecutionConfig,
        TradeExecutionResult,
        MinuteEntryResult,
        MarketCondition
    )
except ImportError:
    pass

try:
    from .backtest_engine import (
        BacktestEngine,
        BacktestEngineConfig,
        StrategySignals,
        BacktestResult,
        ComparisonReport,
        OptimizationResult,
        TimeFrame,
        BacktestMode
    )
except ImportError:
    pass

try:
    from .performance_analyzer import (
        PerformanceAnalyzer,
        Trade,
        Portfolio,
        ReturnAnalysis,
        TradeAnalysis,
        RiskAnalysis,
        BacktestReport
    )
except ImportError:
    pass

try:
    from .trade_recorder import (
        TradeRecorder,
        TradeRecord,
        PortfolioSnapshot,
        TradingSession,
        TradeType,
        TradeReason
    )
except ImportError:
    pass

# 서비스 레이어 버전 정보
__version__ = '1.0.0'
__author__ = 'AI Assistant Multi-Agent Trading System'

def get_service_info():
    """서비스 레이어 정보 반환"""
    return {
        'version': __version__,
        'author': __author__,
        'modules': [
            'daily_backtest_service',
            'minute_backtest_service',
            'execution_services',
            'backtest_engine',
            'performance_analyzer',
            'trade_recorder'
        ],
        'description': 'AI Assistant Multi-Agent Trading System Service Layer'
    }