"""
Trading Visualization Module
주식 트레이딩 시각화 모듈

이 모듈은 다음 기능을 제공합니다:
- 주식 차트 시각화 (캔들스틱, 매수/매도 시그널)
- 백테스트 결과 시각화 (성과 대시보드, 드로우다운 분석)
- 포트폴리오 성과 시각화
- 기존 트레이딩 시스템과의 통합
"""

from .stock_chart_visualizer import StockChartVisualizer
from .backtest_visualizer import BacktestVisualizer
from .trading_visualizer_integration import TradingVisualizerIntegration

__version__ = "1.0.0"
__author__ = "AI Trading System"

__all__ = [
    'StockChartVisualizer',
    'BacktestVisualizer',
    'TradingVisualizerIntegration'
]

# 모듈 정보
MODULE_INFO = {
    'name': 'Trading Visualization Module',
    'version': __version__,
    'description': 'Comprehensive visualization tools for stock trading and backtesting',
    'features': [
        'Interactive stock charts with Plotly',
        'Buy/Sell signal visualization',
        'Backtest performance dashboard',
        'Portfolio analysis charts',
        'MongoDB data integration',
        'HTML/PNG/PDF export support'
    ],
    'dependencies': [
        'pandas',
        'numpy',
        'plotly',
        'matplotlib'
    ]
}

def get_module_info():
    """모듈 정보 반환"""
    return MODULE_INFO

def quick_start():
    """빠른 시작 가이드 출력"""
    print("=" * 60)
    print("Trading Visualization Module - Quick Start")
    print("=" * 60)
    print("\n1. Stock Chart Visualization:")
    print("   from visualization import StockChartVisualizer")
    print("   visualizer = StockChartVisualizer()")
    print("   fig = visualizer.create_candlestick_chart(df, ticker)")
    print("\n2. Backtest Results:")
    print("   from visualization import BacktestVisualizer")
    print("   backtest_viz = BacktestVisualizer()")
    print("   dashboard = backtest_viz.create_performance_dashboard(results)")
    print("\n3. System Integration:")
    print("   from visualization import TradingVisualizerIntegration")
    print("   integration = TradingVisualizerIntegration()")
    print("   integration.visualize_stock_with_signals(ticker, df_daily, df_signals)")
    print("\nFor detailed examples, see Test/Demo/demo_visualization.py")
    print("=" * 60)