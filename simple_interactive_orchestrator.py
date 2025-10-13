"""
Simple Interactive Orchestrator
간결한 출력으로 Orchestrator와 Sub-Agent 상호작용만 표시

사용 방법:
    python simple_interactive_orchestrator.py

Version: 1.0
Created: 2025-10-10
"""

import asyncio
import logging
import sys
from pathlib import Path

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from orchestrator.user_input_handler import UserInputHandler

# 로깅 레벨 설정 (INFO 이상만 출력)
logging.basicConfig(
    level=logging.WARNING,  # WARNING 이상만 출력
    format='%(message)s'
)

logger = logging.getLogger('SimpleOrchestrator')
logger.setLevel(logging.INFO)

class SimpleInteractiveOrchestrator:
    """
    간결한 대화형 Orchestrator
    """

    def __init__(self):
        # UserInputHandler 초기화
        self.input_handler = UserInputHandler(orchestrator=None, use_hybrid_models=True)
        logger.info("Interactive Orchestrator initialized")

    async def process_request(self, user_input: str) -> dict:
        """
        사용자 요청 처리 (간결한 출력)
        """
        print("\n" + "=" * 80)
        print(f"[User Request] {user_input}")
        print("=" * 80)

        # UserInputHandler를 통해 처리
        result = await self.input_handler.process_user_input(user_input)

        # 간결한 결과 출력
        self._display_simple_result(result)

        return result

    def _display_simple_result(self, result: dict):
        """간결한 결과 출력"""

        print("\n" + "-" * 80)
        print("[Execution Summary]")
        print("-" * 80)

        # Agent별 상호작용 표시
        for agent_name in result['agents_executed']:
            agent_result = result['results'].get(agent_name, {})
            status = agent_result.get('status', 'unknown')

            status_icon = "[OK]" if status == 'success' else "[FAIL]"
            print(f"{status_icon} {agent_name}: {status}")

            # 프롬프트와 응답 표시 (간결하게)
            if 'response' in agent_result:
                response = agent_result['response']

                # 응답이 너무 길면 요약
                if len(response) > 500:
                    # 코드 블록 제거
                    if '```' in response:
                        lines = []
                        in_code = False
                        for line in response.split('\n'):
                            if line.strip().startswith('```'):
                                in_code = not in_code
                                if in_code:
                                    lines.append("  [Code output - see logs for details]")
                                continue
                            if not in_code:
                                lines.append(line)
                        response_summary = '\n'.join(lines[:10])  # 첫 10줄만
                    else:
                        response_summary = response[:500] + "..."
                else:
                    response_summary = response

                print(f"  Response: {response_summary}")

        # 최종 요약
        print("\n" + "-" * 80)
        print(f"[OK] Success: {len(result['successful_agents'])}/{len(result['agents_executed'])} agents")
        if result['failed_agents']:
            print(f"[FAIL] Failed: {', '.join(result['failed_agents'])}")

        # 로그 파일 안내
        session_id = self.input_handler.interaction_logger.session_id
        print(f"\nDetailed logs: storage/agent_interactions/session_{session_id}.log")
        print("=" * 80)

    async def interactive_mode(self):
        """대화형 모드"""

        print("\n" + "=" * 80)
        print(" " * 20 + "Simple Interactive Orchestrator")
        print("=" * 80)

        print("\nCommands:")
        print("  - Enter your request in natural language")
        print("  - 'exit' or 'quit': Exit")
        print("  - 'help': Show help")

        print("\nExamples:")
        print("  - 'Generate trading signals for AAPL'")
        print("  - 'Load NASDAQ data from MongoDB'")
        print("  - 'Run backtest for 2024-01-01 to 2024-06-30'")

        print("\n" + "=" * 80)

        while True:
            try:
                # 사용자 입력 받기
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # 종료 명령
                if user_input.lower() in ['exit', 'quit', '종료']:
                    print("\n[EXIT] Goodbye!")
                    break

                # 도움말
                if user_input.lower() in ['help', '도움말']:
                    self._display_help()
                    continue

                # 일반 요청 처리
                await self.process_request(user_input)

            except KeyboardInterrupt:
                print("\n\n[EXIT] Interrupted")
                break

            except Exception as e:
                logger.error(f"[ERROR] {e}")
                print(f"\n[ERROR] {e}")

    def _display_help(self):
        """도움말 출력"""
        print("\n" + "=" * 80)
        print("[Help]")
        print("=" * 80)

        print("\nUsage:")
        print("  Just type your request in natural language")

        print("\nExamples:")
        print("  1. Generate signals:")
        print("     'Generate trading signals for AAPL, MSFT'")
        print("\n  2. Load data:")
        print("     'Load NASDAQ market data'")
        print("\n  3. Run backtest:")
        print("     'Run backtest from 2024-01-01 to 2024-06-30'")

        print("\nCommands:")
        print("  - exit/quit: Exit program")
        print("  - help: Show this help")

        print("\nLogs:")
        print("  All interactions are logged to:")
        print("  storage/agent_interactions/session_*.log")
        print("\n  View logs:")
        print("  python view_agent_logs.py")


async def main():
    """메인 실행 함수"""

    # SimpleInteractiveOrchestrator 생성
    orchestrator = SimpleInteractiveOrchestrator()

    # 대화형 모드 실행
    await orchestrator.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
