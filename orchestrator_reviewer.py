#!/usr/bin/env python3
"""
Orchestrator Review System
오케스트레이터가 서브 에이전트의 작업 결과를 리뷰하고 교정하는 시스템
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add project root path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_client import GeminiClient
from orchestrator.main_orchestrator import MainOrchestrator

@dataclass
class AgentInteraction:
    """에이전트 상호작용 기록"""
    interaction_id: str
    timestamp: str
    user_prompt: str
    orchestrator_analysis: Dict[str, Any]
    agent_name: str
    agent_prompt: str
    agent_response: str
    orchestrator_review: Optional[str] = None
    quality_score: Optional[float] = None
    corrections: Optional[List[str]] = None
    final_output: Optional[str] = None
    status: str = "pending_review"

class AgentStorageManager:
    """에이전트 상호작용 저장 관리자"""

    def __init__(self):
        self.storage_dir = Path("storage/agent_interactions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_interaction(self, interaction: AgentInteraction) -> str:
        """상호작용 기록 저장"""
        file_path = self.storage_dir / f"{interaction.interaction_id}.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(interaction), f, ensure_ascii=False, indent=2)

        return str(file_path)

    def load_interaction(self, interaction_id: str) -> Optional[AgentInteraction]:
        """상호작용 기록 로드"""
        file_path = self.storage_dir / f"{interaction_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return AgentInteraction(**data)

    def get_pending_reviews(self) -> List[str]:
        """리뷰 대기 중인 상호작용 ID 목록"""
        pending = []
        for file_path in self.storage_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('status') == 'pending_review':
                    pending.append(data['interaction_id'])
        return pending

class OrchestratorReviewer:
    """오케스트레이터 리뷰어"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "test-google-key")
        self.orchestrator = None
        self.gemini_client = GeminiClient()
        self.storage_manager = AgentStorageManager()

    async def initialize_orchestrator(self):
        """오케스트레이터 초기화"""
        try:
            self.orchestrator = MainOrchestrator(self.api_key)
            return True
        except Exception as e:
            print(f"[ERROR] Orchestrator initialization failed: {e}")
            return False

    def generate_interaction_id(self) -> str:
        """고유한 상호작용 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"interaction_{timestamp}"

    async def process_user_request(self, user_prompt: str) -> Dict[str, Any]:
        """사용자 요청 처리 및 서브 에이전트 응답 수집"""
        interaction_id = self.generate_interaction_id()
        timestamp = datetime.now().isoformat()

        print(f"[ORCHESTRATOR] Processing user request: {interaction_id}")
        print(f"[USER_PROMPT] {user_prompt}")

        # 1. 오케스트레이터 분석
        orchestrator_analysis = await self._analyze_user_prompt(user_prompt)
        print(f"[ANALYSIS] Required agents: {orchestrator_analysis['required_agents']}")

        # 2. 각 에이전트별 작업 실행 및 저장
        interactions = []

        for agent_name in orchestrator_analysis['execution_order']:
            if agent_name in orchestrator_analysis['tasks']:
                task = orchestrator_analysis['tasks'][agent_name]

                print(f"[DELEGATING] Task to {agent_name}: {task}")

                # 에이전트 응답 수집
                agent_response = await self._get_agent_response(agent_name, task)

                # 상호작용 기록 생성
                interaction = AgentInteraction(
                    interaction_id=f"{interaction_id}_{agent_name}",
                    timestamp=timestamp,
                    user_prompt=user_prompt,
                    orchestrator_analysis=orchestrator_analysis,
                    agent_name=agent_name,
                    agent_prompt=task,
                    agent_response=agent_response
                )

                # 저장
                file_path = self.storage_manager.save_interaction(interaction)
                print(f"[SAVED] Interaction saved to: {file_path}")

                interactions.append(interaction)

        return {
            'interaction_id': interaction_id,
            'interactions': interactions,
            'total_agents': len(interactions)
        }

    async def _analyze_user_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """사용자 프롬프트 분석"""
        # 키워드 기반 분석 (기존 로직 활용)
        agent_keywords = {
            'data_agent': ['data', 'collect', 'database', 'historical', 'price', '데이터', '수집', '저장'],
            'strategy_agent': ['strategy', 'signal', 'trading', 'analysis', 'buy', 'sell', '전략', '신호', '분석'],
            'service_agent': ['backtest', 'execution', 'order', 'performance', 'run', '백테스팅', '실행', '성능'],
            'helper_agent': ['api', 'notification', 'alert', 'integration', 'connect', '알림', '연동', '외부']
        }

        required_agents = []
        prompt_lower = user_prompt.lower()

        for agent, keywords in agent_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                required_agents.append(agent)

        if not required_agents:
            required_agents = ['data_agent', 'strategy_agent']

        # 작업 생성
        tasks = {}
        for agent in required_agents:
            if agent == 'data_agent':
                tasks[agent] = f"데이터 관련 작업: {user_prompt}"
            elif agent == 'strategy_agent':
                tasks[agent] = f"전략 관련 작업: {user_prompt}"
            elif agent == 'service_agent':
                tasks[agent] = f"서비스 관련 작업: {user_prompt}"
            elif agent == 'helper_agent':
                tasks[agent] = f"보조 서비스 작업: {user_prompt}"

        execution_order = ['data_agent', 'strategy_agent', 'service_agent', 'helper_agent']
        final_order = [agent for agent in execution_order if agent in required_agents]

        return {
            'required_agents': required_agents,
            'tasks': tasks,
            'execution_order': final_order
        }

    async def _get_agent_response(self, agent_name: str, task: str) -> str:
        """에이전트 응답 수집"""
        try:
            system_prompt = self.orchestrator._get_agent_system_prompt(agent_name)
            response = await self.gemini_client.agent_response(agent_name, task, system_prompt)
            return response
        except Exception as e:
            return f"Error getting response from {agent_name}: {str(e)}"

    async def review_agent_output(self, interaction_id: str) -> Dict[str, Any]:
        """오케스트레이터가 에이전트 출력을 리뷰"""
        interaction = self.storage_manager.load_interaction(interaction_id)

        if not interaction:
            return {"error": f"Interaction {interaction_id} not found"}

        print(f"[REVIEWING] {interaction.agent_name} output for {interaction_id}")

        # 오케스트레이터 리뷰 프롬프트 생성
        review_prompt = f"""
You are an expert orchestrator reviewing the work of a sub-agent in a multi-agent trading system.

ORIGINAL USER REQUEST: {interaction.user_prompt}

TASK GIVEN TO {interaction.agent_name.upper()}: {interaction.agent_prompt}

AGENT'S RESPONSE: {interaction.agent_response}

Please review this response and provide:

1. QUALITY ASSESSMENT (1-10 scale):
   - Relevance to the original request
   - Completeness of the answer
   - Technical accuracy
   - Clarity and structure

2. IDENTIFIED ISSUES:
   - Any missing information
   - Potential inaccuracies
   - Areas that need improvement

3. SPECIFIC CORRECTIONS:
   - Suggest specific improvements
   - Provide corrected or additional content if needed

4. FINAL RECOMMENDATION:
   - APPROVE: Response is satisfactory
   - REVISE: Needs minor corrections
   - REDO: Needs major rework

Please respond in Korean if the original request was in Korean.
Provide your review in a structured format.
"""

        try:
            # Claude Opus를 사용하여 리뷰 (오케스트레이터는 claude_opus 모델 사용)
            review_response = await self._get_orchestrator_review(review_prompt)

            # 품질 점수 추출 (간단한 패턴 매칭)
            quality_score = self._extract_quality_score(review_response)

            # 교정사항 추출
            corrections = self._extract_corrections(review_response)

            # 상호작용 업데이트
            interaction.orchestrator_review = review_response
            interaction.quality_score = quality_score
            interaction.corrections = corrections
            interaction.status = "reviewed"

            # 저장
            self.storage_manager.save_interaction(interaction)

            print(f"[REVIEW_COMPLETE] Quality Score: {quality_score}/10")
            print(f"[CORRECTIONS] {len(corrections) if corrections else 0} corrections identified")

            return {
                "interaction_id": interaction_id,
                "agent_name": interaction.agent_name,
                "quality_score": quality_score,
                "review": review_response,
                "corrections": corrections,
                "status": "reviewed"
            }

        except Exception as e:
            print(f"[ERROR] Review failed: {e}")
            return {"error": f"Review failed: {str(e)}"}

    async def _get_orchestrator_review(self, review_prompt: str) -> str:
        """오케스트레이터(Claude Opus) 리뷰 받기"""
        # 실제 환경에서는 Claude Opus API 사용
        # 현재는 Gemini로 대체 (실제 프로젝트에서는 Claude 사용)
        return await self.gemini_client.generate_response(review_prompt)

    def _extract_quality_score(self, review_text: str) -> Optional[float]:
        """리뷰 텍스트에서 품질 점수 추출"""
        import re

        # 1-10 점수 패턴 찾기
        patterns = [
            r'품질.*?(\d+(?:\.\d+)?)\s*[/점]',
            r'점수.*?(\d+(?:\.\d+)?)\s*[/점]',
            r'(\d+(?:\.\d+)?)\s*[/점].*?10',
            r'QUALITY.*?(\d+(?:\.\d+)?)'
        ]

        for pattern in patterns:
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(max(score, 0), 10)  # 0-10 범위로 제한
                except ValueError:
                    continue

        return None

    def _extract_corrections(self, review_text: str) -> List[str]:
        """리뷰 텍스트에서 교정사항 추출"""
        corrections = []

        # 교정, 개선, 수정 관련 섹션 찾기
        lines = review_text.split('\n')
        in_corrections_section = False

        for line in lines:
            line = line.strip()

            # 교정사항 섹션 시작 감지
            if any(keyword in line.lower() for keyword in
                   ['correction', '교정', '개선', '수정', 'improvement', '보완']):
                in_corrections_section = True
                continue

            # 다른 섹션 시작되면 종료
            if line.startswith('#') or line.startswith('**') or line.startswith('##'):
                if 'correction' not in line.lower() and '교정' not in line and '개선' not in line:
                    in_corrections_section = False
                    continue

            # 교정사항 수집
            if in_corrections_section and line:
                if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    corrections.append(line[1:].strip())
                elif line and not line.startswith('#'):
                    corrections.append(line)

        return corrections[:10]  # 최대 10개로 제한

    async def apply_corrections(self, interaction_id: str) -> Dict[str, Any]:
        """교정사항을 적용하여 개선된 응답 생성"""
        interaction = self.storage_manager.load_interaction(interaction_id)

        if not interaction or interaction.status != "reviewed":
            return {"error": "Interaction not found or not reviewed"}

        if not interaction.corrections or interaction.quality_score >= 8.0:
            # 교정사항이 없거나 품질이 이미 높으면 원본 유지
            interaction.final_output = interaction.agent_response
            interaction.status = "completed"
            self.storage_manager.save_interaction(interaction)

            return {
                "interaction_id": interaction_id,
                "action": "no_corrections_needed",
                "final_output": interaction.agent_response
            }

        # 교정사항을 반영한 새로운 프롬프트 생성
        correction_prompt = f"""
Based on the following review and corrections, please provide an improved response:

ORIGINAL TASK: {interaction.agent_prompt}
ORIGINAL RESPONSE: {interaction.agent_response}

ORCHESTRATOR REVIEW: {interaction.orchestrator_review}

SPECIFIC CORRECTIONS TO APPLY:
{chr(10).join(f"- {correction}" for correction in interaction.corrections)}

Please provide an improved response that addresses all the identified issues and incorporates the suggested corrections.
Maintain the same language (Korean/English) as the original response.
"""

        try:
            # 개선된 응답 생성
            improved_response = await self.gemini_client.agent_response(
                interaction.agent_name,
                correction_prompt,
                self.orchestrator._get_agent_system_prompt(interaction.agent_name)
            )

            # 최종 출력 저장
            interaction.final_output = improved_response
            interaction.status = "completed"
            self.storage_manager.save_interaction(interaction)

            print(f"[IMPROVED] Generated improved response for {interaction_id}")

            return {
                "interaction_id": interaction_id,
                "action": "corrections_applied",
                "original_length": len(interaction.agent_response),
                "improved_length": len(improved_response),
                "final_output": improved_response
            }

        except Exception as e:
            print(f"[ERROR] Failed to apply corrections: {e}")
            return {"error": f"Failed to apply corrections: {str(e)}"}

    async def get_interaction_summary(self, interaction_id: str) -> Dict[str, Any]:
        """상호작용 요약 정보 반환"""
        interaction = self.storage_manager.load_interaction(interaction_id)

        if not interaction:
            return {"error": "Interaction not found"}

        return {
            "interaction_id": interaction.interaction_id,
            "timestamp": interaction.timestamp,
            "user_prompt": interaction.user_prompt,
            "agent_name": interaction.agent_name,
            "status": interaction.status,
            "quality_score": interaction.quality_score,
            "has_corrections": bool(interaction.corrections),
            "correction_count": len(interaction.corrections) if interaction.corrections else 0,
            "response_length": len(interaction.agent_response),
            "has_final_output": bool(interaction.final_output)
        }

class WorkflowOrchestrator:
    """전체 워크플로우 오케스트레이터"""

    def __init__(self):
        self.reviewer = OrchestratorReviewer()

    async def process_complete_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """완전한 워크플로우 처리: 요청 → 실행 → 리뷰 → 교정 → 완료"""

        print("="*80)
        print("COMPLETE WORKFLOW EXECUTION")
        print("="*80)

        # 1. 오케스트레이터 초기화
        if not await self.reviewer.initialize_orchestrator():
            return {"error": "Failed to initialize orchestrator"}

        # 2. 사용자 요청 처리
        print("\n[PHASE 1] Processing user request...")
        result = await self.reviewer.process_user_request(user_prompt)

        if 'error' in result:
            return result

        # 3. 각 에이전트 응답 리뷰
        print(f"\n[PHASE 2] Reviewing {result['total_agents']} agent responses...")
        review_results = []

        for interaction in result['interactions']:
            review_result = await self.reviewer.review_agent_output(interaction.interaction_id)
            review_results.append(review_result)

        # 4. 필요시 교정 적용
        print("\n[PHASE 3] Applying corrections...")
        final_results = []

        for interaction in result['interactions']:
            correction_result = await self.reviewer.apply_corrections(interaction.interaction_id)
            final_results.append(correction_result)

        # 5. 최종 요약
        print("\n[PHASE 4] Generating summary...")
        summary = {
            "workflow_id": result['interaction_id'],
            "user_prompt": user_prompt,
            "total_agents": result['total_agents'],
            "agent_summaries": []
        }

        for interaction in result['interactions']:
            agent_summary = await self.reviewer.get_interaction_summary(interaction.interaction_id)
            summary["agent_summaries"].append(agent_summary)

        print("\n" + "="*80)
        print("WORKFLOW COMPLETED")
        print("="*80)

        return summary

# 메인 실행 함수
async def main():
    """메인 실행 함수"""
    workflow = WorkflowOrchestrator()

    # 예시 실행
    test_prompt = "AAPL 주식의 기술적 분석을 수행하고 매매 신호를 생성해주세요"

    result = await workflow.process_complete_workflow(test_prompt)

    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())