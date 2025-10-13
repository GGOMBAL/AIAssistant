"""
Interactive Orchestrator with RUN_AGENT (Peer-level)
클로드 창에서 사용자 입력을 받아 Orchestrator가 모든 Agent에게 작업 할당

Architecture (Peer-level Agents):
    User Input
        ↓
    Orchestrator (작업 분배 및 조정)
        ↓
    ├── HELPER_AGENT (API 통합)
    ├── DATABASE_AGENT (MongoDB 관리)
    ├── STRATEGY_AGENT (시그널 생성)
    ├── SERVICE_AGENT (백테스트 실행)
    └── RUN_AGENT (파일 실행, 프로세스 관리) ← 동등 레벨

사용 방법:
    python interactive_orchestrator.py

Version: 2.1
Created: 2025-10-09
Updated: 2025-10-10 - RUN_AGENT를 Peer-level Agent로 재설계
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import yaml

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from orchestrator.user_input_handler import UserInputHandler
from orchestrator.main_orchestrator import MainOrchestrator
from run_agent import RunAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('interactive_orchestrator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('InteractiveOrchestrator')

class InteractiveOrchestrator:
    """
    대화형 Orchestrator with Peer-level Agents

    Architecture:
    1. Orchestrator: 사용자 입력 분석 및 작업 분배
    2. UserInputHandler: 프롬프트 생성 및 Agent 실행
    3. Peer-level Agents: 실제 작업 수행
       - Helper Agent: API 통합
       - Database Agent: MongoDB 관리
       - Strategy Agent: 시그널 생성
       - Service Agent: 백테스트 실행
       - RUN Agent: 파일 실행 및 프로세스 관리

    사용자 입력 처리:
    1. 입력 분석
    2. 적절한 Agent(s) 선택
    3. 프롬프트 자동 생성
    4. Agent에게 작업 할당
    5. 결과 통합 및 반환
    """

    def __init__(self, config_path: str = "myStockInfo.yaml"):
        self.config_path = PROJECT_ROOT / config_path
        self.config = self._load_config()

        # RUN_AGENT 초기화 (Peer-level Agent)
        self.run_agent = RunAgent(config_path)
        logger.info("🚀 RUN_AGENT 초기화 완료 (Peer-level Agent)")

        # Orchestrator 초기화 (API 키 필요)
        # 현재는 시뮬레이션 모드로 실행
        self.orchestrator = None  # MainOrchestrator(api_key) 필요 시

        # UserInputHandler 초기화 (run_agent 전달)
        self.input_handler = UserInputHandler(
            orchestrator=self.orchestrator,
            run_agent=self.run_agent
        )

        logger.info("✅ Interactive Orchestrator 초기화 완료")

    def _load_config(self) -> dict:
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 설정 파일 로드: {self.config_path}")
            return config
        except Exception as e:
            logger.warning(f"⚠️  설정 파일 로드 실패: {e}")
            return {}

    async def process_request(self, user_input: str) -> dict:
        """
        사용자 요청 처리

        Args:
            user_input: 사용자의 자연어 입력

        Returns:
            처리 결과
        """
        print("\n" + "=" * 80)
        print("[Orchestrator] 요청을 분석하고 Sub-Agent에게 작업을 할당합니다...")
        print("=" * 80)

        # UserInputHandler를 통해 처리
        result = await self.input_handler.process_user_input(user_input)

        # 결과 출력
        self._display_result(result)

        return result

    def _display_result(self, result: dict):
        """결과를 보기 좋게 출력"""

        print("\n" + "=" * 80)
        print("[실행 결과]")
        print("=" * 80)

        print(f"\n[SUCCESS] 성공한 Agent: {', '.join(result['successful_agents'])}")

        if result['failed_agents']:
            print(f"[FAILED] 실패한 Agent: {', '.join(result['failed_agents'])}")

        print(f"\n[요약]")
        print(result['summary'])

        # 상세 결과
        print(f"\n[상세 결과]")
        for agent, agent_result in result['results'].items():
            status_icon = "[OK]" if agent_result.get('status') == 'success' else "[FAIL]"
            print(f"\n{status_icon} {agent}:")

            # Agent의 응답 출력
            if 'response' in agent_result:
                response = agent_result['response']

                # 코드 블록이 포함된 긴 응답은 요약
                if len(response) > 500:
                    if '```' in response:
                        print(f"  Response: [Code output - see logs for details]")
                    else:
                        # 처음 300자만 표시
                        response_summary = response[:300].replace('\n', ' ').strip() + "..."
                        print(f"  Response: {response_summary}")
                else:
                    # 짧은 응답은 전체 표시 (줄바꿈은 제거)
                    response_clean = response.replace('\n', ' ').strip()
                    print(f"  Response: {response_clean}")

            # Agent별 특수한 형식의 결과가 있다면 추가로 출력
            if agent == 'strategy_agent' and 'signals' in agent_result:
                for signal in agent_result['signals'][:3]:  # 최대 3개만
                    print(f"  - {signal['symbol']}: {signal['signal']} "
                          f"(신뢰도: {signal['confidence']*100:.0f}%)")

            elif agent == 'service_agent' and 'backtest_result' in agent_result:
                bt = agent_result['backtest_result']
                print(f"  - 수익률: {bt.get('total_return', 0)*100:.2f}%")
                print(f"  - 샤프 비율: {bt.get('sharpe_ratio', 0):.2f}")
                print(f"  - 승률: {bt.get('win_rate', 0)*100:.1f}%")

            elif agent == 'database_agent' and 'data' in agent_result:
                data = agent_result['data']
                if 'total_symbols' in data:
                    print(f"  - 종목 수: {data['total_symbols']}")

        print("\n" + "=" * 80)

    def get_run_agent_status(self) -> dict:
        """RUN_AGENT 상태 조회"""
        if self.run_agent:
            return {
                'running_processes': self.run_agent.get_running_processes(),
                'execution_history_count': len(self.run_agent.execution_history),
                'work_directory': str(self.run_agent.work_dir)
            }
        return {}

    async def interactive_mode(self):
        """대화형 모드"""

        print("\n" + "=" * 80)
        print(" " * 20 + "Interactive Orchestrator v2.1")
        print(" " * 15 + "Multi-Agent System (Peer-level Architecture)")
        print("=" * 80)

        print("\n사용 가능한 명령어:")
        print("  - 자연어 입력: 원하는 작업을 자연어로 입력하세요")
        print("  - 'status': RUN_AGENT 상태 확인")
        print("  - 'exit' 또는 'quit': 종료")
        print("  - 'help': 도움말")

        print("\n예시:")
        print("  - 'NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘'")
        print("  - 'AAPL, MSFT에 대한 매매 시그널 생성해줘'")
        print("  - 'MongoDB에서 최근 데이터 가져와줘'")
        print("  - 'run_backtest_auto.py 파일 실행해줘' (RUN_AGENT 사용)")

        print("\n" + "=" * 80)

        while True:
            try:
                # 사용자 입력 받기
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # 종료 명령
                if user_input.lower() in ['exit', 'quit', '종료']:
                    print("\n[EXIT] Orchestrator를 종료합니다. 감사합니다!")
                    break

                # RUN_AGENT 상태 확인
                if user_input.lower() in ['status', '상태']:
                    self._display_run_agent_status()
                    continue

                # 히스토리 명령
                if user_input.lower() in ['history', '히스토리']:
                    self._display_history()
                    continue

                # 도움말
                if user_input.lower() in ['help', '도움말']:
                    self._display_help()
                    continue

                # 일반 요청 처리
                await self.process_request(user_input)

            except KeyboardInterrupt:
                print("\n\n[EXIT] Orchestrator를 종료합니다.")
                break

            except Exception as e:
                logger.error(f"[ERROR] 오류 발생: {e}")
                print(f"\n[ERROR] 오류: {e}")

    def _display_run_agent_status(self):
        """RUN_AGENT 상태 출력"""
        status = self.get_run_agent_status()

        print("\n" + "=" * 80)
        print("[RUN_AGENT 상태]")
        print("=" * 80)

        print(f"\n작업 디렉토리: {status.get('work_directory', 'N/A')}")
        print(f"실행 히스토리 수: {status.get('execution_history_count', 0)}")

        running_procs = status.get('running_processes', {})
        if running_procs:
            print(f"\n실행 중인 프로세스: {len(running_procs)}")
            for proc_id, proc_info in running_procs.items():
                print(f"  - {proc_id}: {proc_info}")
        else:
            print(f"\n실행 중인 프로세스: 없음")

        # 최근 실행 히스토리
        if self.run_agent and self.run_agent.execution_history:
            recent = self.run_agent.get_execution_history(limit=5)
            print(f"\n최근 실행 히스토리 (최대 5개):")
            for i, exec_info in enumerate(recent, 1):
                status_icon = "[OK]" if exec_info['status'] == 'success' else "[FAIL]"
                print(f"{i}. {status_icon} {exec_info['file_path']}")
                print(f"   시간: {exec_info.get('duration', 0):.2f}초")
                print(f"   반환 코드: {exec_info.get('return_code', -1)}")

        print("\n" + "=" * 80)

    def _display_history(self):
        """대화 히스토리 출력"""
        history = self.input_handler.get_conversation_history()

        if not history:
            print("\n[HISTORY] 대화 히스토리가 없습니다.")
            return

        print("\n" + "=" * 80)
        print("[대화 히스토리]")
        print("=" * 80)

        for i, conv in enumerate(history, 1):
            print(f"\n{i}. [{conv['timestamp']}]")
            print(f"   입력: {conv['user_input']}")
            print(f"   실행: {', '.join(conv['results']['agents_executed'])}")
            print(f"   결과: {conv['results']['summary'].strip()}")

    def _display_help(self):
        """도움말 출력"""
        print("\n" + "=" * 80)
        print("[도움말]")
        print("=" * 80)

        print("\nInteractive Orchestrator v2.1 사용법:")
        print("\n[아키텍처] Peer-level Multi-Agent System")
        print("  - Helper, Database, Strategy, Service, RUN Agent가 동등한 레벨")

        print("\n명령어:")
        print("  - status 또는 상태: RUN_AGENT 상태 확인")
        print("  - history 또는 히스토리: 대화 히스토리 보기")
        print("  - help 또는 도움말: 이 도움말 표시")
        print("  - exit 또는 quit 또는 종료: 프로그램 종료")

        print("\n1. 백테스트 실행:")
        print("   예: 'NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘'")
        print("   - database_agent: MongoDB에서 과거 데이터 로드")
        print("   - strategy_agent: 과거 데이터 기반 시그널 생성")
        print("   - service_agent: 시그널 기반 백테스트 실행")

        print("\n2. 시그널 생성:")
        print("   예: 'AAPL, MSFT에 대한 매매 시그널 생성해줘'")
        print("   - database_agent: 종목 데이터 로드")
        print("   - strategy_agent: BUY/SELL/HOLD 시그널 생성")

        print("\n3. 데이터 수집:")
        print("   예: 'MongoDB에서 최신 데이터 가져와줘'")
        print("   - helper_agent: 외부 API에서 데이터 수집")
        print("   - database_agent: MongoDB에 데이터 저장")

        print("\n4. 파일 실행 (RUN_AGENT):")
        print("   예: 'run_backtest_auto.py 파일 실행해줘'")
        print("   - run_agent: Python 파일 실행 및 모니터링")
        print("   - 백테스트 스크립트 자동 실행")

        print("\n5. 성과 분석:")
        print("   예: '포트폴리오 성과 분석해줘'")
        print("   - database_agent: 성과 데이터 로드")
        print("   - service_agent: 분석 리포트 생성")

        print("\n" + "=" * 80)


async def main():
    """메인 실행 함수"""

    import argparse

    parser = argparse.ArgumentParser(description='Interactive Orchestrator v2.1')
    parser.add_argument(
        '--config',
        default='myStockInfo.yaml',
        help='설정 파일 경로 (기본: myStockInfo.yaml)'
    )

    args = parser.parse_args()

    # InteractiveOrchestrator 생성 (RUN_AGENT 항상 포함)
    orchestrator = InteractiveOrchestrator(config_path=args.config)

    # 대화형 모드 실행
    await orchestrator.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
