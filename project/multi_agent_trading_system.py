# multi_agent_trading_system.py
# Multi-Agent 협업 통합 실행 파일 (Deprecated)

"""
⚠️  DEPRECATED WARNING ⚠️

이 파일은 더 이상 사용되지 않습니다.
실시간 자동매매 시스템은 main_auto_trade.py를 사용하세요.

이 파일은 백테스트 중심의 멀티 에이전트 시스템을 위해 만들어졌으나,
현재는 main_auto_trade.py의 AutoTradeOrchestrator 기반 시스템으로 통합되었습니다.

사용 방법:
1. 실시간 거래: python main_auto_trade.py
2. 백테스트: project/service/ 디렉토리의 백테스트 엔진 사용

Migration Guide:
- 기존 OrchestratorAgent → AutoTradeOrchestrator
- 기존 에이전트 파일들 → agents/ 디렉토리로 이동
- 설정 파일 → myStockInfo.yaml 및 config/ 디렉토리 사용
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

def main():
    """메인 함수 - 사용 중단 안내"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║                  ⚠️  DEPRECATED NOTICE  ⚠️                     ║
    ║                                                               ║
    ║  이 파일(multi_agent_trading_system.py)은 더 이상 사용되지    ║
    ║  않습니다.                                                    ║
    ║                                                               ║
    ║  실시간 자동매매 시스템을 사용하려면:                         ║
    ║                                                               ║
    ║      python main_auto_trade.py                                ║
    ║                                                               ║
    ║  을 실행하세요.                                               ║
    ║                                                               ║
    ║  새로운 시스템은 다음 기능을 제공합니다:                      ║
    ║  • 실시간 거래 실행                                           ║
    ║  • WebSocket 기반 실시간 데이터                               ║
    ║  • 통합된 리스크 관리                                         ║
    ║  • 실시간 포트폴리오 모니터링                                 ║
    ║  • 체계화된 멀티 에이전트 아키텍처                            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] multi_agent_trading_system.py 실행 중단")
    print("새로운 시스템으로 전환하세요: python main_auto_trade.py")

    return False

if __name__ == "__main__":
    main()