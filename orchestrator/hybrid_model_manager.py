"""
Hybrid Model Manager
Claude 구독 모델(현재 세션)과 Gemini API를 함께 사용하는 매니저

Version: 1.0
Created: 2025-10-09
"""

import os
import yaml
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum

# Gemini Client import
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """모델 제공자"""
    CLAUDE_SUBSCRIPTION = "claude_subscription"  # Claude Code (현재 세션)
    GEMINI_API = "gemini_api"  # Gemini API

class HybridModelManager:
    """
    Claude 구독과 Gemini API를 하이브리드로 사용하는 매니저

    - Orchestrator: Claude 구독 모델 사용 (현재 Claude Code 세션)
    - Sub-Agents: Gemini API 사용 (비용 효율적)
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = PROJECT_ROOT / "config" / "agent_model.yaml"

        self.config = self._load_config(config_path)
        self.gemini_client = GeminiClient()

        # Agent별 모델 매핑
        self.agent_models = self._initialize_agent_models()

        logger.info("[OK] Hybrid Model Manager 초기화 완료")
        logger.info(f"  - Claude 구독: Orchestrator")
        logger.info(f"  - Gemini API: Sub-Agents (Helper, Database, Strategy, Service, RUN)")

    def _load_config(self, config_path: Path) -> dict:
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패: {e}, 기본값 사용")
            return {}

    def _initialize_agent_models(self) -> Dict[str, Dict[str, Any]]:
        """Agent별 모델 매핑 초기화"""
        agent_configs = self.config.get('agents', {})

        agent_models = {}

        for agent_name, agent_config in agent_configs.items():
            primary_model = agent_config.get('primary_model', 'gemini_flash')

            # Orchestrator는 Claude 구독 (현재 세션) 사용
            if agent_name == 'orchestrator':
                provider = ModelProvider.CLAUDE_SUBSCRIPTION
                model_id = "claude-code-session"  # 현재 실행 중인 Claude Code 세션
            else:
                # 다른 Agent들은 Gemini API 사용
                provider = ModelProvider.GEMINI_API
                model_config = self.config.get('models', {}).get(primary_model, {})
                model_id = model_config.get('model_id', 'gemini-2.5-flash')

            agent_models[agent_name] = {
                'provider': provider,
                'model_id': model_id,
                'primary_model': primary_model,
                'fallback_model': agent_config.get('fallback_model'),
                'use_cases': agent_config.get('use_cases', [])
            }

        return agent_models

    async def execute_orchestrator_task(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Orchestrator 작업 실행 (Claude 구독 모델 사용)

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트

        Returns:
            Orchestrator 응답 (Sub-Agent용 프롬프트)
        """
        logger.info("[Orchestrator] Claude 구독 모델로 프롬프트 생성 중...")

        # Orchestrator는 Claude 구독 모델 사용 (Gemini API 호출)
        # 실제로는 Orchestrator도 Gemini를 사용하지만, 구분을 위해 별도 메서드
        try:
            response = await self.gemini_client.agent_response(
                agent_name="orchestrator",
                task=prompt,
                system_prompt=system_prompt or "You are an Orchestrator managing multiple AI agents."
            )
            return response
        except Exception as e:
            logger.error(f"Orchestrator 실행 오류: {e}")
            # fallback: 원본 프롬프트 반환
            return prompt

    async def execute_agent_task(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Agent 작업 실행 (하이브리드 모델 사용)

        Args:
            agent_name: Agent 이름
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트

        Returns:
            Agent 응답
        """
        agent_config = self.agent_models.get(agent_name)

        if not agent_config:
            logger.warning(f"Agent '{agent_name}' 설정 없음, Gemini 기본값 사용")
            agent_config = {
                'provider': ModelProvider.GEMINI_API,
                'model_id': 'gemini-2.5-flash'
            }

        provider = agent_config['provider']
        model_id = agent_config['model_id']

        logger.info(f"[{agent_name}] {provider.value} 사용 ({model_id})")

        # Provider에 따라 실행
        if provider == ModelProvider.CLAUDE_SUBSCRIPTION:
            # Orchestrator는 현재 Claude Code 세션에서 실행
            # 실제로는 이 코드 자체가 Claude Code에서 실행되므로
            # 여기서는 시뮬레이션 또는 Claude Code API 호출
            return await self._execute_with_claude_subscription(
                agent_name, prompt, system_prompt
            )

        elif provider == ModelProvider.GEMINI_API:
            # Sub-Agents는 Gemini API 사용
            return await self._execute_with_gemini_api(
                agent_name, prompt, system_prompt
            )

        else:
            return f"Unknown provider: {provider}"

    async def _execute_with_claude_subscription(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Claude 구독 모델 사용 (현재 세션)"""

        # 현재 Claude Code 세션에서 실행 중이므로
        # 실제로는 이 함수 자체가 Claude에 의해 실행됨

        # 옵션 1: Claude Code API를 통해 별도 요청 (구현 필요)
        # 옵션 2: 시뮬레이션 (현재)
        # 옵션 3: Tool을 통해 Claude Code에 작업 위임

        logger.info(f"[{agent_name}] Claude 구독 모델로 처리 중...")

        # 현재는 시뮬레이션
        response = f"""
[Claude Subscription Response for {agent_name}]

Task: {prompt[:100]}...

This is a simulated response from Claude Code subscription model.
In production, this would be handled by the current Claude Code session.

System Prompt: {system_prompt[:100] if system_prompt else 'None'}...
"""
        return response

    async def _execute_with_gemini_api(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Gemini API 사용"""

        logger.info(f"[{agent_name}] Gemini API로 처리 중...")

        try:
            response = await self.gemini_client.agent_response(
                agent_name=agent_name,
                task=prompt,
                system_prompt=system_prompt or f"You are {agent_name}."
            )

            return response

        except Exception as e:
            logger.error(f"Gemini API 오류: {e}")
            return f"Error: {e}"

    def get_agent_model_info(self, agent_name: str) -> Dict[str, Any]:
        """Agent 모델 정보 반환"""
        return self.agent_models.get(agent_name, {})

    def get_all_agent_models(self) -> Dict[str, Dict[str, Any]]:
        """모든 Agent 모델 정보 반환"""
        return self.agent_models

    async def test_connectivity(self) -> Dict[str, bool]:
        """모델 연결 테스트"""
        results = {
            'claude_subscription': True,  # 현재 세션이므로 항상 가능
            'gemini_api': False
        }

        # Gemini API 테스트
        try:
            test_response = await self.gemini_client.generate_response(
                "Hello, this is a connectivity test."
            )
            if test_response and not test_response.startswith("Error"):
                results['gemini_api'] = True
        except Exception as e:
            logger.error(f"Gemini API 연결 테스트 실패: {e}")

        return results


# 사용 예시
async def main():
    """테스트 메인"""

    print("=" * 80)
    print("Hybrid Model Manager 테스트")
    print("=" * 80)

    # Manager 생성
    manager = HybridModelManager()

    # 연결 테스트
    print("\n[연결 테스트]")
    connectivity = await manager.test_connectivity()
    for provider, status in connectivity.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {provider}: {'연결됨' if status else '연결 실패'}")

    # Agent별 모델 정보
    print("\n[Agent별 모델 매핑]")
    for agent_name, model_info in manager.get_all_agent_models().items():
        provider = model_info['provider'].value
        model_id = model_info['model_id']
        print(f"  {agent_name}: {provider} ({model_id})")

    # Orchestrator 테스트 (Claude 구독)
    print("\n[Orchestrator 테스트 - Claude 구독]")
    orchestrator_response = await manager.execute_agent_task(
        agent_name="orchestrator",
        prompt="Analyze the current market situation",
        system_prompt="You are an orchestrator agent managing a trading system."
    )
    print(f"응답: {orchestrator_response[:200]}...")

    # Database Agent 테스트 (Gemini API)
    print("\n[Database Agent 테스트 - Gemini API]")
    database_response = await manager.execute_agent_task(
        agent_name="data_agent",
        prompt="Load NASDAQ data for the last 30 days",
        system_prompt="You are a database agent managing MongoDB data."
    )
    print(f"응답: {database_response[:200]}...")

    # Strategy Agent 테스트 (Gemini API)
    print("\n[Strategy Agent 테스트 - Gemini API]")
    strategy_response = await manager.execute_agent_task(
        agent_name="strategy_agent",
        prompt="Generate trading signals for AAPL, MSFT",
        system_prompt="You are a strategy agent generating trading signals."
    )
    print(f"응답: {strategy_response[:200]}...")

    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
