"""
RUN AGENT - Multi-Agent System Main Controller
최상위 실행 Agent로 모든 Agent들을 관리하고 조율합니다.

Architecture:
    RUN AGENT (이 파일)
        ↓
    Orchestrator (작업 분배 및 조정)
        ↓
    ├── HELPER_AGENT
    ├── DATABASE_AGENT
    ├── STRATEGY_AGENT
    └── SERVICE_AGENT

Version: 1.0
Created: 2025-10-09
"""

import asyncio
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# 프로젝트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

# Agent Router imports
from project.router.helper_agent_router import HelperAgentRouter
from project.router.data_agent_router import DataAgentRouter
from project.router.strategy_agent_router import StrategyAgentRouter
from project.router.service_agent_router import ServiceAgentRouter

# Orchestrator import
from orchestrator.main_orchestrator import MainOrchestrator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('run_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('RUN_AGENT')

class AgentType(Enum):
    """Agent 타입 정의"""
    HELPER = "helper"
    DATABASE = "database"
    STRATEGY = "strategy"
    SERVICE = "service"

class ExecutionMode(Enum):
    """실행 모드"""
    BACKTEST = "backtest"
    TRADING = "trading"
    ANALYSIS = "analysis"

@dataclass
class AgentStatus:
    """Agent 상태"""
    name: str
    type: AgentType
    status: str  # 'ready', 'running', 'completed', 'error'
    last_update: datetime
    message: str = ""

class RunAgent:
    """
    RUN AGENT - 최상위 실행 관리자

    역할:
    1. 전체 Agent 라이프사이클 관리
    2. Orchestrator와 협업하여 작업 조율
    3. Agent 간 통신 및 데이터 흐름 제어
    4. 시스템 상태 모니터링 및 에러 처리
    """

    def __init__(self, config_path: str = "myStockInfo.yaml"):
        """RUN AGENT 초기화"""
        self.config_path = PROJECT_ROOT / config_path
        self.config = self._load_config()

        # Agent 상태 추적
        self.agent_statuses: Dict[str, AgentStatus] = {}

        # Agent Router 초기화
        self.helper_router = None
        self.database_router = None
        self.strategy_router = None
        self.service_router = None

        # Orchestrator 초기화
        self.orchestrator = None

        # 실행 모드
        self.execution_mode = ExecutionMode.BACKTEST

        logger.info("🚀 RUN AGENT 초기화 완료")

    def _load_config(self) -> dict:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 설정 파일 로드: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ 설정 파일 로드 실패: {e}")
            raise

    async def initialize_agents(self):
        """모든 Agent 초기화"""
        logger.info("=" * 60)
        logger.info("Agent 초기화 시작")
        logger.info("=" * 60)

        try:
            # 1. Helper Agent Router 초기화
            logger.info("1. Helper Agent 초기화 중...")
            self.helper_router = HelperAgentRouter()
            self._update_agent_status("helper", AgentType.HELPER, "ready", "Helper Agent 준비 완료")

            # 2. Database Agent Router 초기화
            logger.info("2. Database Agent 초기화 중...")
            self.database_router = DataAgentRouter()
            self._update_agent_status("database", AgentType.DATABASE, "ready", "Database Agent 준비 완료")

            # 3. Strategy Agent Router 초기화
            logger.info("3. Strategy Agent 초기화 중...")
            self.strategy_router = StrategyAgentRouter()
            self._update_agent_status("strategy", AgentType.STRATEGY, "ready", "Strategy Agent 준비 완료")

            # 4. Service Agent Router 초기화
            logger.info("4. Service Agent 초기화 중...")
            self.service_router = ServiceAgentRouter()
            self._update_agent_status("service", AgentType.SERVICE, "ready", "Service Agent 준비 완료")

            # 5. Orchestrator 초기화
            logger.info("5. Orchestrator 초기화 중...")
            self.orchestrator = MainOrchestrator(self.config)

            logger.info("✅ 모든 Agent 초기화 완료")
            self._print_agent_status()

        except Exception as e:
            logger.error(f"❌ Agent 초기화 실패: {e}")
            raise

    def _update_agent_status(self, name: str, agent_type: AgentType, status: str, message: str = ""):
        """Agent 상태 업데이트"""
        self.agent_statuses[name] = AgentStatus(
            name=name,
            type=agent_type,
            status=status,
            last_update=datetime.now(),
            message=message
        )

    def _print_agent_status(self):
        """Agent 상태 출력"""
        logger.info("\n" + "=" * 60)
        logger.info("Agent 상태 현황")
        logger.info("=" * 60)

        for name, status in self.agent_statuses.items():
            status_icon = "✅" if status.status == "ready" else "⏳"
            logger.info(f"{status_icon} {name.upper()}: {status.status} - {status.message}")

        logger.info("=" * 60 + "\n")

    async def run_backtest(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_cash: float = 100000.0
    ) -> Dict[str, Any]:
        """
        백테스트 실행

        Flow:
        1. RUN AGENT → Orchestrator에게 백테스트 작업 요청
        2. Orchestrator → 각 Agent에게 작업 분배
        3. Database Agent → 데이터 로드
        4. Strategy Agent → 시그널 생성
        5. Service Agent → 백테스트 실행
        6. RUN AGENT ← 결과 수집 및 반환
        """
        self.execution_mode = ExecutionMode.BACKTEST

        logger.info("=" * 60)
        logger.info(f"백테스트 실행: {start_date} ~ {end_date}")
        logger.info(f"종목 수: {len(symbols)}, 초기 자금: ${initial_cash:,.0f}")
        logger.info("=" * 60)

        try:
            # 1. Database Agent - 데이터 로드
            self._update_agent_status("database", AgentType.DATABASE, "running", "데이터 로드 중...")
            logger.info("\n[Step 1] Database Agent - 데이터 로드")

            # TODO: Database Agent Router를 통한 데이터 로드
            data_result = await self._load_data_via_database_agent(symbols, start_date, end_date)

            self._update_agent_status("database", AgentType.DATABASE, "completed", f"{len(data_result)} 종목 로드 완료")
            logger.info(f"✅ 데이터 로드 완료: {len(data_result)} 종목")

            # 2. Strategy Agent - 시그널 생성
            self._update_agent_status("strategy", AgentType.STRATEGY, "running", "시그널 생성 중...")
            logger.info("\n[Step 2] Strategy Agent - 시그널 생성")

            # TODO: Strategy Agent Router를 통한 시그널 생성
            signals_result = await self._generate_signals_via_strategy_agent(data_result)

            self._update_agent_status("strategy", AgentType.STRATEGY, "completed", f"{len(signals_result)} 시그널 생성 완료")
            logger.info(f"✅ 시그널 생성 완료: {len(signals_result)} 시그널")

            # 3. Service Agent - 백테스트 실행
            self._update_agent_status("service", AgentType.SERVICE, "running", "백테스트 실행 중...")
            logger.info("\n[Step 3] Service Agent - 백테스트 실행")

            # TODO: Service Agent Router를 통한 백테스트 실행
            backtest_result = await self._run_backtest_via_service_agent(signals_result, initial_cash)

            self._update_agent_status("service", AgentType.SERVICE, "completed", "백테스트 완료")
            logger.info("✅ 백테스트 실행 완료")

            # 4. 결과 집계
            final_result = {
                'execution_mode': self.execution_mode.value,
                'period': {'start': start_date, 'end': end_date},
                'symbols_count': len(symbols),
                'data_loaded': len(data_result),
                'signals_generated': len(signals_result),
                'backtest_result': backtest_result,
                'agent_statuses': {name: status.status for name, status in self.agent_statuses.items()},
                'timestamp': datetime.now().isoformat()
            }

            logger.info("\n" + "=" * 60)
            logger.info("백테스트 완료")
            logger.info("=" * 60)
            self._print_result_summary(final_result)

            return final_result

        except Exception as e:
            logger.error(f"❌ 백테스트 실행 중 오류: {e}")
            raise

    async def _load_data_via_database_agent(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Database Agent를 통한 데이터 로드"""
        # TODO: 실제 Database Agent Router 호출
        logger.info(f"  - 데이터 로드 요청: {len(symbols)} 종목")

        # 임시 구현
        await asyncio.sleep(0.5)

        return {symbol: {"status": "loaded"} for symbol in symbols[:100]}

    async def _generate_signals_via_strategy_agent(
        self,
        data_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Strategy Agent를 통한 시그널 생성"""
        # TODO: 실제 Strategy Agent Router 호출
        logger.info(f"  - 시그널 생성 요청: {len(data_result)} 종목")

        # 임시 구현
        await asyncio.sleep(0.5)

        return {symbol: {"signal": "buy", "strength": 0.8} for symbol in list(data_result.keys())[:20]}

    async def _run_backtest_via_service_agent(
        self,
        signals_result: Dict[str, Any],
        initial_cash: float
    ) -> Dict[str, Any]:
        """Service Agent를 통한 백테스트 실행"""
        # TODO: 실제 Service Agent Router 호출
        logger.info(f"  - 백테스트 실행: {len(signals_result)} 시그널, ${initial_cash:,.0f}")

        # 임시 구현
        await asyncio.sleep(0.5)

        return {
            'total_return': 0.15,
            'sharpe_ratio': 1.23,
            'max_drawdown': 0.08,
            'trades': 45,
            'win_rate': 0.58
        }

    def _print_result_summary(self, result: Dict[str, Any]):
        """결과 요약 출력"""
        logger.info(f"실행 모드: {result['execution_mode']}")
        logger.info(f"기간: {result['period']['start']} ~ {result['period']['end']}")
        logger.info(f"종목 수: {result['symbols_count']}")
        logger.info(f"데이터 로드: {result['data_loaded']} 종목")
        logger.info(f"시그널 생성: {result['signals_generated']} 시그널")

        if 'backtest_result' in result:
            bt = result['backtest_result']
            logger.info(f"\n백테스트 결과:")
            logger.info(f"  - 총 수익률: {bt.get('total_return', 0)*100:.2f}%")
            logger.info(f"  - 샤프 비율: {bt.get('sharpe_ratio', 0):.2f}")
            logger.info(f"  - 최대 낙폭: {bt.get('max_drawdown', 0)*100:.2f}%")
            logger.info(f"  - 총 거래: {bt.get('trades', 0)}회")
            logger.info(f"  - 승률: {bt.get('win_rate', 0)*100:.1f}%")

    async def run_live_trading(self):
        """실시간 거래 실행"""
        self.execution_mode = ExecutionMode.TRADING

        logger.info("=" * 60)
        logger.info("실시간 거래 모드")
        logger.info("=" * 60)

        # TODO: 실시간 거래 로직 구현
        logger.warning("⚠️  실시간 거래는 아직 구현되지 않았습니다.")

    async def shutdown(self):
        """모든 Agent 종료"""
        logger.info("\n" + "=" * 60)
        logger.info("Agent 종료 중...")
        logger.info("=" * 60)

        # Agent 상태 업데이트
        for name in self.agent_statuses.keys():
            agent_type = self.agent_statuses[name].type
            self._update_agent_status(name, agent_type, "shutdown", "정상 종료")

        logger.info("✅ 모든 Agent 종료 완료")
        self._print_agent_status()

async def main():
    """메인 실행 함수"""

    print("=" * 80)
    print(" " * 25 + "RUN AGENT v1.0")
    print(" " * 15 + "Multi-Agent Trading System Controller")
    print("=" * 80)

    # RUN AGENT 생성
    run_agent = RunAgent()

    try:
        # 1. Agent 초기화
        await run_agent.initialize_agents()

        # 2. 백테스트 실행 (예시)
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # MongoDB에서 종목 로드 (임시로 하드코딩)
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

        result = await run_agent.run_backtest(
            symbols=test_symbols,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_cash=100000.0
        )

        # 3. Agent 종료
        await run_agent.shutdown()

        print("\n" + "=" * 80)
        print(" " * 30 + "실행 완료")
        print("=" * 80)

        return result

    except Exception as e:
        logger.error(f"❌ 실행 중 오류 발생: {e}")
        await run_agent.shutdown()
        raise

if __name__ == "__main__":
    asyncio.run(main())
