"""
Reporting Layer
보고서 및 시각화 레이어

Report Agent가 관리하는 모든 시각화 및 보고서 생성 기능
- 주식 차트 시각화
- 백테스트 결과 대시보드
- 실시간 거래 모니터링
- 시그널 타임라인 시각화
"""

# Try to import the full report agent, fall back to simple version
try:
    from .report_agent import ReportAgent
except ImportError:
    from .simple_report_agent import ReportAgent

# Export only ReportAgent as the main interface
__all__ = ['ReportAgent']