"""
User Input Handler
사용자 입력을 받아서 Orchestrator를 통해 Sub-Agent에게 작업 할당

Version: 1.0
Created: 2025-10-09
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# 프로젝트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from orchestrator.prompt_generator import PromptGenerator, PromptContext, TaskType, RequestType, CodeModificationPhase
from orchestrator.hybrid_model_manager import HybridModelManager
from orchestrator.agent_interaction_logger import get_interaction_logger
from orchestrator.output_validator import OutputValidator, ValidationStatus
from orchestrator.run_agent_handler import RunAgentHandler
import yaml
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserInputHandler:
    """
    사용자 입력 처리기

    사용자의 자연어 입력을 받아서:
    1. 입력 분석
    2. 필요한 Agent 식별
    3. 프롬프트 생성
    4. Agent에게 작업 할당
    5. 결과 취합 및 반환
    """

    def __init__(self, orchestrator=None, use_hybrid_models=True, run_agent=None, verbose=True):
        self.orchestrator = orchestrator
        self.run_agent = run_agent  # RUN AGENT 추가
        self.prompt_generator = PromptGenerator()
        self.conversation_history = []
        self.verbose = verbose  # 로그 출력 여부

        # RunAgentHandler 초기화
        self.run_agent_handler = RunAgentHandler(run_agent=run_agent) if run_agent else None

        # verbose=False이면 로깅 레벨을 ERROR로 설정
        if not verbose:
            logging.getLogger('orchestrator.user_input_handler').setLevel(logging.ERROR)
            logging.getLogger('orchestrator.hybrid_model_manager').setLevel(logging.ERROR)
            logging.getLogger('orchestrator.agent_interaction_logger').setLevel(logging.ERROR)
            logging.getLogger('orchestrator.output_validator').setLevel(logging.ERROR)
            logging.getLogger('gemini_client').setLevel(logging.ERROR)

        # Hybrid Model Manager 초기화
        self.use_hybrid_models = use_hybrid_models
        if use_hybrid_models:
            self.model_manager = HybridModelManager()
            if verbose:
                logger.info("[OK] Hybrid Model Manager 활성화 (Claude 구독 + Gemini API)")
        else:
            self.model_manager = None
            if verbose:
                logger.info("[WARN] Hybrid Model 비활성화 (시뮬레이션 모드)")

        # Interaction Logger 초기화
        self.interaction_logger = get_interaction_logger()
        if verbose:
            logger.info("[OK] Agent Interaction Logger 활성화")

        # Orchestrator 설정 로드
        self.orchestrator_settings = self._load_orchestrator_settings()

        # Output Validator 초기화
        validation_criteria = self.orchestrator_settings.get('validation_criteria', {})
        self.output_validator = OutputValidator(validation_criteria)
        if verbose:
            logger.info(f"[OK] Output Validator 활성화 (max_iterations: {self.orchestrator_settings.get('max_iterations', 5)})")

    def _load_orchestrator_settings(self) -> Dict[str, Any]:
        """orchestrator_settings를 myStockInfo.yaml에서 로드"""
        try:
            config_path = PROJECT_ROOT / "myStockInfo.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            settings = config.get('orchestrator_settings', {
                'max_iterations': 5,
                'enable_output_validation': True,
                'validation_criteria': {
                    'min_confidence': 0.7,
                    'require_complete_data': True,
                    'check_error_presence': True
                },
                'iteration_strategy': 'adaptive',
                'stop_on_success': True
            })

            logger.info(f"[Config] Orchestrator 설정 로드 완료")
            return settings

        except Exception as e:
            logger.warning(f"[Config] 설정 로드 실패, 기본값 사용: {e}")
            return {
                'max_iterations': 5,
                'enable_output_validation': True,
                'validation_criteria': {
                    'min_confidence': 0.7,
                    'require_complete_data': True,
                    'check_error_presence': True
                },
                'iteration_strategy': 'adaptive',
                'stop_on_success': True
            }

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        사용자 입력 처리

        Args:
            user_input: 사용자의 자연어 입력

        Returns:
            처리 결과
        """
        logger.info("=" * 60)
        logger.info(f"사용자 입력: {user_input}")
        logger.info("=" * 60)

        # 1. LLM 기반 입력 분석 (use_hybrid_models가 활성화된 경우)
        if self.use_hybrid_models and self.model_manager:
            analysis = await self._analyze_user_request_with_llm(user_input)
        else:
            # Fallback: 규칙 기반 분석
            logger.info("[FALLBACK] 규칙 기반 요청 분석 사용")
            analysis = self.prompt_generator.parse_user_request(user_input)

        logger.info(f"\n[분석 결과]")
        logger.info(f"작업 타입: {analysis['task_type']}")
        logger.info(f"요청 타입: {analysis['request_type']}")
        logger.info(f"필요한 Agent: {analysis['agents_needed']}")
        logger.info(f"파라미터: {analysis['parameters']}")

        # CODE_MODIFICATION 요청 시 특별 워크플로우
        if analysis['request_type'] == RequestType.CODE_MODIFICATION:
            logger.info(f"\n[CODE_MODIFICATION 워크플로우 시작]")
            final_result = await self._execute_code_modification_workflow(user_input, analysis)
        # 백테스트 요청이면서 RUN AGENT를 사용하는 경우
        elif analysis.get('task_type') == TaskType.BACKTEST and 'run_agent' in analysis.get('agents_needed', []):
            logger.info(f"\n[RUN AGENT 백테스트 워크플로우 시작]")
            if self.run_agent_handler:
                result = await self.run_agent_handler.execute_backtest_with_feedback(
                    user_request=user_input,
                    analysis=analysis,
                    max_retries=3
                )
                # 결과를 표준 형식으로 변환
                final_result = {
                    "user_request": user_input,
                    "task_type": str(analysis['task_type']),
                    "agents_executed": ["run_agent"],
                    "successful_agents": ["run_agent"] if result.get("status") == "success" else [],
                    "failed_agents": ["run_agent"] if result.get("status") == "error" else [],
                    "results": {"run_agent": result},
                    "summary": self._generate_run_agent_summary(result),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                final_result = {
                    "user_request": user_input,
                    "task_type": str(analysis['task_type']),
                    "agents_executed": [],
                    "successful_agents": [],
                    "failed_agents": [],
                    "results": {},
                    "summary": "RUN AGENT가 초기화되지 않았습니다.",
                    "timestamp": datetime.now().isoformat()
                }
        else:
            # 기존 EXECUTION 워크플로우
            # 2. Workflow 실행 계획
            workflow_plan = self._create_workflow_plan(analysis, user_input)

            logger.info(f"\n[Workflow 계획]")
            for i, step in enumerate(workflow_plan, 1):
                logger.info(f"{i}. {step['agent']}: {step['description']}")

            # 3. Agent에게 작업 할당 및 실행
            results = await self._execute_workflow(workflow_plan, user_input, analysis)

            # 4. 결과 취합
            final_result = self._aggregate_results(results, user_input, analysis)

        # 5. 대화 히스토리 저장
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "analysis": analysis,
            "results": final_result
        })

        # 6. 세션 요약 저장 (모든 요청 처리 후)
        self.interaction_logger.save_session_summary()

        return final_result

    def _create_workflow_plan(
        self,
        analysis: Dict[str, Any],
        user_input: str
    ) -> List[Dict[str, Any]]:
        """Workflow 실행 계획 생성"""

        # 기본 workflow가 있으면 사용
        if analysis.get('workflow'):
            return [
                {
                    "agent": step["agent"],
                    "description": step["task"],
                    "dependencies": []
                }
                for step in analysis['workflow']
            ]

        # 없으면 Agent 순서에 따라 생성
        workflow = []
        prev_agents = []

        for agent in analysis['agents_needed']:
            workflow.append({
                "agent": agent,
                "description": f"{agent} task for: {user_input[:50]}...",
                "dependencies": prev_agents.copy()
            })
            prev_agents.append(agent)

        return workflow

    async def _execute_workflow(
        self,
        workflow_plan: List[Dict[str, Any]],
        user_input: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Workflow 실행 (반복 검증 포함)"""

        results = {}

        for step in workflow_plan:
            agent_name = step['agent']
            dependencies = step['dependencies']

            logger.info(f"\n[실행] {agent_name}")

            # Agent 반복 실행 (최대 max_iterations회)
            result = await self._execute_agent_with_iterations(
                agent_name=agent_name,
                user_input=user_input,
                analysis=analysis,
                dependencies=dependencies
            )

            results[agent_name] = result

            logger.info(f"[OK] {agent_name} 완료 (최종 신뢰도: {result.get('final_confidence', 0):.2f})")

            # 의존성 있는 Agent가 실패하면 중단
            if result.get('status') == 'error':
                logger.error(f"[ERROR] {agent_name} 실패: {result.get('error')}")
                break

        return results

    async def _execute_agent_with_iterations(
        self,
        agent_name: str,
        user_input: str,
        analysis: Dict[str, Any],
        dependencies: List[str]
    ) -> Dict[str, Any]:
        """
        Agent를 반복 실행하여 출력 품질을 개선

        Args:
            agent_name: Agent 이름
            user_input: 사용자 입력
            analysis: 요청 분석 결과
            dependencies: 의존성 Agent 목록

        Returns:
            최종 Agent 실행 결과 (iterations 정보 포함)
        """
        max_iterations = self.orchestrator_settings.get('max_iterations', 5)
        enable_validation = self.orchestrator_settings.get('enable_output_validation', True)
        stop_on_success = self.orchestrator_settings.get('stop_on_success', True)

        # 프롬프트 생성
        context = PromptContext(
            task_type=analysis['task_type'],
            request_type=analysis.get('request_type', RequestType.EXECUTION),  # 추가
            user_request=user_input,
            parameters=analysis.get('parameters', {}),
            dependencies=dependencies
        )

        prompt = self.prompt_generator.generate_prompt(agent_name, context)

        iteration = 0
        result = None
        all_iterations = []

        while iteration < max_iterations:
            iteration += 1

            logger.info(f"\n[Iteration {iteration}/{max_iterations}] {agent_name}")

            # Agent 실행
            if agent_name == "run_agent" and self.run_agent:
                # RUN AGENT 직접 실행
                current_result = await self._execute_run_agent(context.parameters)
            elif self.orchestrator or self.model_manager:
                current_result = await self._execute_agent_via_orchestrator(
                    agent_name,
                    prompt
                )
            else:
                current_result = await self._simulate_agent_execution(
                    agent_name,
                    prompt,
                    dependencies,
                    {}
                )

            # 검증 활성화 시
            if enable_validation:
                # 출력 검증
                validation_result = self.output_validator.validate_agent_output(
                    agent_name=agent_name,
                    agent_output=current_result,
                    task_type=str(analysis['task_type'])
                )

                # Iteration 정보 저장
                all_iterations.append({
                    'iteration': iteration,
                    'result': current_result,
                    'validation': {
                        'status': validation_result.status.value,
                        'confidence': validation_result.confidence,
                        'issues': validation_result.issues,
                        'suggestions': validation_result.suggestions
                    }
                })

                logger.info(f"  검증 상태: {validation_result.status.value}")
                logger.info(f"  신뢰도: {validation_result.confidence:.2f}")

                if validation_result.issues:
                    logger.warning(f"  발견된 이슈: {len(validation_result.issues)}개")
                    for issue in validation_result.issues[:3]:  # 최대 3개만 표시
                        logger.warning(f"    - {issue}")

                # 성공 시 중단 옵션
                if stop_on_success and not validation_result.needs_refinement:
                    logger.info(f"  [SUCCESS] 검증 통과! (iteration {iteration})")
                    result = current_result
                    result['final_confidence'] = validation_result.confidence
                    result['iterations_used'] = iteration
                    result['all_iterations'] = all_iterations
                    break

                # 재작업 필요 시
                if validation_result.needs_refinement and iteration < max_iterations:
                    logger.info(f"  [REFINE] 출력 개선 필요, 재시도 중...")

                    # 개선된 프롬프트 생성
                    prompt = self.output_validator.generate_refinement_prompt(
                        validation_result=validation_result,
                        original_prompt=prompt,
                        previous_output=current_result
                    )

                    # 다음 iteration으로
                    result = current_result
                    continue
                else:
                    # 마지막 iteration
                    result = current_result
                    result['final_confidence'] = validation_result.confidence
                    result['iterations_used'] = iteration
                    result['all_iterations'] = all_iterations

            else:
                # 검증 비활성화 시 바로 반환
                result = current_result
                result['final_confidence'] = 1.0
                result['iterations_used'] = 1
                break

        # 최종 결과에 메타데이터 추가
        if result:
            result['validation_enabled'] = enable_validation
            result['max_iterations_allowed'] = max_iterations

        return result

    async def _execute_agent_via_orchestrator(
        self,
        agent_name: str,
        prompt: str
    ) -> Dict[str, Any]:
        """
        Orchestrator(Claude)를 통해 프롬프트를 생성하고,
        그 프롬프트를 Sub-Agent(Gemini)에게 전달
        """
        import time

        # 1단계: Orchestrator가 이미 생성한 프롬프트를 그대로 사용
        # (Orchestrator의 추가 분석 단계를 건너뛰어 "no parts" 오류 방지)
        generated_prompt = prompt

        # Sub-Agent 프롬프트 로깅
        start_time = time.time()

        interaction_id = self.interaction_logger.log_prompt(
            from_agent="orchestrator",
            to_agent=agent_name,
            prompt=generated_prompt,
            metadata={"handler": "user_input_handler"}
        )

        try:

            if self.model_manager:
                # Agent별 시스템 프롬프트
                system_prompts = {
                    "helper_agent": "You are a Helper Agent specializing in external API integration.",
                    "database_agent": "You are a Database Agent specializing in MongoDB data management.",
                    "strategy_agent": "You are a Strategy Agent specializing in trading signal generation.",
                    "service_agent": "You are a Service Agent specializing in backtesting and portfolio management."
                }

                system_prompt = system_prompts.get(
                    agent_name,
                    f"You are a {agent_name.replace('_', ' ')} agent."
                )

                response = await self.model_manager.execute_agent_task(
                    agent_name=agent_name,
                    prompt=generated_prompt,
                    system_prompt=system_prompt
                )

            # 기존 Orchestrator 사용
            elif self.orchestrator:
                response = await self.orchestrator.process_agent_request(
                    agent_name=agent_name,
                    message=generated_prompt
                )

            else:
                response = "No execution method available"

            # 응답 시간 계산
            duration_ms = (time.time() - start_time) * 1000

            # 응답 로깅
            self.interaction_logger.log_response(
                interaction_id=interaction_id,
                from_agent=agent_name,
                to_agent="orchestrator",
                response=response,
                duration_ms=duration_ms,
                token_count=len(response.split()) if response else 0,
                model_used=self.model_manager.get_agent_model_info(agent_name).get('model_id') if self.model_manager else None,
                metadata={"status": "success"}
            )

            return {
                "status": "success",
                "agent": agent_name,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "interaction_id": interaction_id
            }

        except Exception as e:
            # 에러 로깅
            import traceback
            self.interaction_logger.log_error(
                interaction_id=interaction_id,
                from_agent=agent_name,
                to_agent="orchestrator",
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                metadata={"error_type": type(e).__name__}
            )

            logger.error(f"Agent {agent_name} 실행 오류: {e}")
            return {
                "status": "error",
                "agent": agent_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "interaction_id": interaction_id
            }

    async def _execute_run_agent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        RUN AGENT 직접 실행

        Args:
            parameters: 실행 파라미터 (file_path, args, timeout 등)

        Returns:
            실행 결과
        """
        try:
            file_path = parameters.get('file_path', '')
            args = parameters.get('args', [])
            timeout = parameters.get('timeout', 300)

            logger.info(f"[RUN_AGENT] Executing file: {file_path}")

            if not file_path:
                return {
                    "status": "error",
                    "error": "file_path parameter is required",
                    "timestamp": datetime.now().isoformat()
                }

            # RUN AGENT의 execute_python_file 메서드 호출
            result = await self.run_agent.execute_python_file(
                file_path=file_path,
                args=args,
                timeout=timeout
            )

            # 결과 포맷 변환 (status, response 포함)
            formatted_result = {
                "status": result.get("status", "error"),
                "response": f"File: {file_path}\nReturn Code: {result.get('return_code', -1)}\nDuration: {result.get('duration', 0):.2f}s",
                "file_path": result.get("file_path"),
                "return_code": result.get("return_code"),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "duration": result.get("duration", 0),
                "start_time": result.get("start_time"),
                "end_time": result.get("end_time"),
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"[RUN_AGENT] Execution completed: {formatted_result['status']}")

            return formatted_result

        except Exception as e:
            logger.error(f"[RUN_AGENT] Execution error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _simulate_agent_execution(
        self,
        agent_name: str,
        prompt: str,
        dependencies: List[str],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agent 실행 시뮬레이션 (테스트용)"""

        # 시뮬레이션 대기
        await asyncio.sleep(0.5)

        # Agent별 시뮬레이션 응답
        simulated_responses = {
            "helper_agent": {
                "status": "success",
                "data": {
                    "source": "KIS_API",
                    "records": 100,
                    "symbols": ["AAPL", "MSFT", "GOOGL"]
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "records_count": 100
                }
            },
            "database_agent": {
                "status": "success",
                "operation": "read",
                "affected_documents": 100,
                "data": {
                    "collections": ["NasDataBase_D", "NysDataBase_D"],
                    "total_symbols": 15113
                }
            },
            "strategy_agent": {
                "status": "success",
                "signals": [
                    {
                        "symbol": "AAPL",
                        "signal": "BUY",
                        "confidence": 0.85,
                        "entry_price": 175.50,
                        "target_price": 185.00,
                        "stop_loss": 170.00,
                        "reasoning": "Strong momentum + RS > 80"
                    }
                ],
                "metadata": {
                    "total_signals": 5,
                    "strategy": "momentum"
                }
            },
            "service_agent": {
                "status": "success",
                "backtest_result": {
                    "total_return": 0.15,
                    "sharpe_ratio": 1.23,
                    "max_drawdown": 0.08,
                    "win_rate": 0.58,
                    "total_trades": 45
                }
            }
        }

        return simulated_responses.get(agent_name, {
            "status": "success",
            "message": f"{agent_name} completed successfully",
            "timestamp": datetime.now().isoformat()
        })

    def _aggregate_results(
        self,
        results: Dict[str, Any],
        user_input: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """결과 취합"""

        # 성공한 Agent들
        successful_agents = [
            agent for agent, result in results.items()
            if result.get('status') == 'success'
        ]

        # 실패한 Agent들
        failed_agents = [
            agent for agent, result in results.items()
            if result.get('status') == 'error'
        ]

        # 최종 응답 생성
        final_response = {
            "user_request": user_input,
            "task_type": str(analysis['task_type']),
            "agents_executed": list(results.keys()),
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "results": results,
            "summary": self._generate_summary(results, analysis),
            "timestamp": datetime.now().isoformat()
        }

        return final_response

    def _generate_summary(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """결과 요약 생성"""

        task_type = analysis.get('task_type')

        # Backtest 결과 요약
        if task_type == TaskType.BACKTEST and 'service_agent' in results:
            service_result = results['service_agent']
            if 'backtest_result' in service_result:
                bt = service_result['backtest_result']
                return f"""
백테스트 완료:
- 총 수익률: {bt.get('total_return', 0)*100:.2f}%
- 샤프 비율: {bt.get('sharpe_ratio', 0):.2f}
- 최대 낙폭: {bt.get('max_drawdown', 0)*100:.2f}%
- 승률: {bt.get('win_rate', 0)*100:.1f}%
- 총 거래: {bt.get('total_trades', 0)}회
"""

        # 시그널 생성 요약
        elif task_type == TaskType.SIGNAL_GENERATION and 'strategy_agent' in results:
            strategy_result = results['strategy_agent']
            if 'signals' in strategy_result:
                signals = strategy_result['signals']
                buy_signals = len([s for s in signals if s.get('signal') == 'BUY'])
                return f"""
매매 시그널 생성 완료:
- 총 시그널: {len(signals)}개
- BUY 시그널: {buy_signals}개
- SELL 시그널: {len(signals) - buy_signals}개
"""

        # 기본 요약
        successful = len([r for r in results.values() if r.get('status') == 'success'])
        return f"{successful}/{len(results)} Agent(s) 성공적으로 실행됨"

    def _generate_run_agent_summary(self, result: Dict[str, Any]) -> str:
        """RUN AGENT 실행 결과 요약 생성"""
        if result.get("status") == "success":
            summary = result.get("summary", "")
            if summary:
                return f"백테스트 실행 완료:\n{summary}"
            else:
                return f"""
백테스트 실행 완료:
- 실행 파일: {result.get('file_path', 'N/A')}
- 실행 시간: {result.get('duration', 0):.2f}초
- 상태: 성공
"""
        else:
            return f"""
백테스트 실행 실패:
- 에러: {result.get('error', 'Unknown error')}
- 시도 횟수: {result.get('attempts', 1)}
- 마지막 에러: {result.get('last_error', 'N/A')}
"""

    def _get_agent_description(self, agent_name: str) -> str:
        """Agent별 역할 설명"""
        descriptions = {
            "helper_agent": """
- 외부 API 통합 (KIS API, Alpha Vantage, Yahoo Finance)
- 실시간 데이터 수집 및 검증
- API 인증 및 속도 제한 관리
- 구조화된 데이터 반환
""",
            "database_agent": """
- MongoDB CRUD 작업 수행
- 데이터 스키마 검증
- 데이터 무결성 보장
- 쿼리 최적화
- 사용 가능한 컬렉션: NasDataBase_D, NysDataBase_D
""",
            "strategy_agent": """
- 시장 데이터 및 기술 지표 분석
- BUY/SELL/HOLD 신호 생성
- 포지션 크기 및 리스크 레벨 계산
- 신호 신뢰도 및 근거 제공
- 전략 타입: Momentum, Mean Reversion, Breakout
""",
            "service_agent": """
- 백테스트 시뮬레이션 실행
- 포트폴리오 포지션 관리
- 성과 지표 계산 (수익률, 샤프비율, MDD, 승률)
- 상세 리포트 생성
- 거래 내역 및 포트폴리오 요약 제공
"""
        }
        return descriptions.get(agent_name, f"{agent_name}의 역할")

    async def _analyze_user_request_with_llm(self, user_input: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 사용자 요청을 분석

        Args:
            user_input: 사용자 요청

        Returns:
            분석 결과 (task_type, request_type, agents_needed, parameters 등)
        """
        logger.info("[LLM] 사용자 요청 분석 중...")

        system_prompt = """You are an Orchestrator Agent analyzing user requests for a multi-agent trading system.

Your job is to analyze the user's request and return a structured JSON response.

**Available Agents**:
- helper_agent: System configuration, MongoDB connection, external API integration
- database_agent: Data loading from MongoDB, technical indicator calculation
- strategy_agent: Trading signal generation, universe selection
- service_agent: Backtest execution, portfolio management, performance analysis
- run_agent: Execute existing Python scripts for backtest or trading (run_backtest.py, run_auto_trade.py, etc.)

**Request Types**:
1. EXECUTION: Running existing code, querying data, generating signals, backtesting
   - Keywords: run, execute, backtest, query, show, display, generate (signals/reports)

2. CODE_MODIFICATION: Modifying or adding code
   - Keywords: add (function/class), modify, fix, improve, create (new function), implement

**Task Types**:
- data_collection: Loading or fetching data
- data_analysis: Analyzing data, calculating indicators
- signal_generation: Generating trading signals
- backtest: Running backtest simulations
- trading: Executing trades
- reporting: Creating reports

**IMPORTANT**:
- "시그널 생성" (generate signal) = EXECUTION (calling existing functions)
- "함수 생성" (create function) = CODE_MODIFICATION (writing new code)
- Context matters! Analyze the full sentence to determine intent.
- For backtest requests with "RUN AGENT를 이용해서" or "RUN AGENT로", use run_agent
- When user explicitly mentions "RUN AGENT", always include "run_agent" in agents_needed

Return JSON in this format:
```json
{
    "task_type": "signal_generation",
    "request_type": "EXECUTION",
    "agents_needed": ["database_agent", "strategy_agent"],
    "parameters": {
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    },
    "reasoning": "User wants to generate trading signals for AAPL, which is an execution task"
}
```"""

        analysis_prompt = f"""Analyze this user request and return structured JSON:

User Request: "{user_input}"

Provide a JSON response following the format specified in the system prompt."""

        try:
            response = await self.model_manager.execute_orchestrator_task(
                prompt=analysis_prompt,
                system_prompt=system_prompt
            )

            # JSON 파싱
            analysis = self._parse_llm_analysis(response)

            logger.info(f"[LLM] 분석 완료 - Request Type: {analysis['request_type']}, Task Type: {analysis['task_type']}")
            return analysis

        except Exception as e:
            logger.error(f"[LLM] 요청 분석 실패: {e}")
            logger.info("[FALLBACK] 규칙 기반 분석으로 전환")
            return self.prompt_generator.parse_user_request(user_input)

    def _parse_llm_analysis(self, llm_response: str) -> Dict[str, Any]:
        """
        LLM 응답에서 JSON 분석 결과 추출

        Args:
            llm_response: LLM 응답 텍스트

        Returns:
            파싱된 분석 결과
        """
        try:
            # JSON 추출 (코드 블록 제거)
            response_text = llm_response.strip()

            # ```json ... ``` 형식 처리
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            analysis = json.loads(response_text)

            # RequestType enum 변환
            request_type_str = analysis.get('request_type', 'EXECUTION').upper()
            analysis['request_type'] = RequestType.EXECUTION if request_type_str == 'EXECUTION' else RequestType.CODE_MODIFICATION

            # TaskType enum 변환
            task_type_str = analysis.get('task_type', 'signal_generation').lower()
            try:
                analysis['task_type'] = TaskType(task_type_str)
            except ValueError:
                logger.warning(f"알 수 없는 task_type: {task_type_str}, 기본값 사용")
                analysis['task_type'] = TaskType.SIGNAL_GENERATION

            # 필수 필드 보장
            if 'agents_needed' not in analysis:
                analysis['agents_needed'] = ['database_agent', 'strategy_agent']
            if 'parameters' not in analysis:
                analysis['parameters'] = {}

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            logger.error(f"응답 내용: {llm_response[:500]}")
            raise
        except Exception as e:
            logger.error(f"분석 결과 파싱 중 오류: {e}")
            raise

    async def _generate_planning_prompt_with_llm(
        self,
        agent_name: str,
        user_request: str,
        analysis: Dict[str, Any]
    ) -> str:
        """
        LLM을 사용하여 PLANNING 단계 프롬프트 생성

        Args:
            agent_name: Sub-Agent 이름
            user_request: 사용자 요청
            analysis: 요청 분석 결과

        Returns:
            생성된 프롬프트
        """
        logger.info(f"[LLM] {agent_name}용 PLANNING 프롬프트 생성 중...")

        system_prompt = f"""You are an Orchestrator creating a PLANNING prompt for {agent_name}.

Your task is to create a detailed, structured prompt that instructs the {agent_name} to generate a comprehensive implementation plan.

**Context**:
- User Request: {user_request}
- Task Type: {analysis['task_type']}
- Request Type: CODE_MODIFICATION - PLANNING Phase
- Target Agent: {agent_name}

**The prompt you generate should**:
1. Clearly explain this is PLANNING phase (no code implementation yet)
2. Describe the modification target (layer, file, component)
3. Include project architecture context
4. Specify the JSON output format for the plan
5. Emphasize that the agent must return structured JSON

**Required JSON Plan Structure**:
```json
{{
    "phase": "planning",
    "analysis": {{
        "current_code_structure": "...",
        "identified_issues": ["..."],
        "modification_scope": "..."
    }},
    "function_specification": {{
        "name": "...",
        "parameters": [...],
        "return_type": "...",
        "purpose": "..."
    }},
    "implementation_plan": {{
        "steps": [...],
        "dependencies": [...],
        "risks": [...]
    }},
    "interface_impact": {{...}},
    "test_requirements": {{...}},
    "estimated_effort": {{...}}
}}
```

Generate a comprehensive prompt for {agent_name} following these guidelines."""

        meta_prompt = f"""Create a PLANNING prompt for {agent_name} that will:
1. Instruct the agent this is PLANNING phase (DO NOT implement code yet)
2. Ask the agent to analyze the user request: "{user_request}"
3. Request a detailed implementation plan in JSON format
4. Include architecture context and interface specifications

Return the complete prompt text that will be sent to {agent_name}."""

        try:
            prompt = await self.model_manager.execute_orchestrator_task(
                prompt=meta_prompt,
                system_prompt=system_prompt
            )
            logger.info(f"[LLM] PLANNING 프롬프트 생성 완료 ({len(prompt)} chars)")
            return prompt

        except Exception as e:
            logger.error(f"[LLM] 프롬프트 생성 실패: {e}")
            logger.info("[FALLBACK] 규칙 기반 프롬프트 생성으로 전환")

            # Fallback to rule-based prompt
            planning_context = PromptContext(
                task_type=analysis['task_type'],
                request_type=RequestType.CODE_MODIFICATION,
                user_request=user_request,
                parameters=analysis.get('parameters', {}),
                modification_target=analysis.get('modification_target'),
                code_modification_phase=CodeModificationPhase.PLANNING
            )
            return self.prompt_generator.generate_prompt(agent_name, planning_context)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """대화 히스토리 반환"""
        return self.conversation_history

    async def _execute_code_modification_workflow(
        self,
        user_input: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CODE_MODIFICATION 전용 워크플로우

        단계:
        1. PLANNING: Sub-Agent가 Plan 생성
        2. REVIEW: Orchestrator가 Plan 리뷰 및 승인
        3. IMPLEMENTATION: Sub-Agent가 승인된 Plan 기반으로 코드 작업

        Args:
            user_input: 사용자 요청
            analysis: 요청 분석 결과

        Returns:
            최종 결과
        """
        results = {}

        # 사용할 Agent 선택 (첫 번째 Agent)
        agent_name = analysis['agents_needed'][0] if analysis['agents_needed'] else 'database_agent'

        logger.info(f"\n[Phase 1] PLANNING - {agent_name}가 Plan을 생성합니다...")

        # ========== Phase 1: PLANNING ==========
        # LLM 기반 프롬프트 생성 (use_hybrid_models 활성화 시)
        if self.use_hybrid_models and self.model_manager:
            planning_prompt = await self._generate_planning_prompt_with_llm(
                agent_name=agent_name,
                user_request=user_input,
                analysis=analysis
            )
        else:
            # Fallback: 규칙 기반 프롬프트
            planning_context = PromptContext(
                task_type=analysis['task_type'],
                request_type=RequestType.CODE_MODIFICATION,
                user_request=user_input,
                parameters=analysis.get('parameters', {}),
                modification_target=analysis.get('modification_target'),
                code_modification_phase=CodeModificationPhase.PLANNING
            )
            planning_prompt = self.prompt_generator.generate_prompt(agent_name, planning_context)

        planning_result = await self._execute_agent_via_orchestrator(agent_name, planning_prompt)

        results['planning'] = planning_result

        # Plan 파싱
        plan_data = self._parse_plan_from_response(planning_result.get('response', ''))

        if not plan_data:
            logger.error("[Phase 1] Plan 생성 실패")
            return self._aggregate_results(results, user_input, analysis)

        logger.info(f"[Phase 1] Plan 생성 완료")
        logger.info(f"  - 함수명: {plan_data.get('function_specification', {}).get('name', 'N/A')}")
        logger.info(f"  - 구현 단계: {len(plan_data.get('implementation_plan', {}).get('steps', []))}개")
        logger.info(f"  - 예상 시간: {plan_data.get('estimated_effort', {}).get('hours', 0)}시간")

        # ========== Phase 2: REVIEW ==========
        logger.info(f"\n[Phase 2] REVIEW - Orchestrator가 Plan을 리뷰합니다...")

        review_result = await self._review_plan(plan_data, user_input)
        results['review'] = review_result

        if not review_result.get('approved', False):
            logger.warning(f"[Phase 2] Plan이 승인되지 않았습니다")
            logger.warning(f"  사유: {review_result.get('feedback', 'No feedback provided')}")
            return self._aggregate_results(results, user_input, analysis)

        logger.info(f"[Phase 2] Plan 승인 완료")
        logger.info(f"  - 승인 사유: {review_result.get('feedback', 'Approved')}")

        # ========== Phase 3: IMPLEMENTATION ==========
        logger.info(f"\n[Phase 3] IMPLEMENTATION - {agent_name}가 코드를 작성합니다...")

        implementation_context = PromptContext(
            task_type=analysis['task_type'],
            request_type=RequestType.CODE_MODIFICATION,
            user_request=user_input,
            parameters=analysis.get('parameters', {}),
            modification_target=analysis.get('modification_target'),
            code_modification_phase=CodeModificationPhase.IMPLEMENTATION,
            plan_data=plan_data
        )

        implementation_prompt = self.prompt_generator.generate_prompt(agent_name, implementation_context)
        implementation_result = await self._execute_agent_via_orchestrator(agent_name, implementation_prompt)

        results['implementation'] = implementation_result

        logger.info(f"[Phase 3] 구현 완료")

        # 최종 결과 반환
        return self._aggregate_results(results, user_input, analysis)

    def _parse_plan_from_response(self, response: str) -> Dict[str, Any]:
        """
        Agent 응답에서 Plan JSON 추출

        Args:
            response: Agent 응답 문자열

        Returns:
            파싱된 Plan 데이터 (Dict) 또는 None
        """
        try:
            # JSON 코드 블록 추출
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                # JSON 블록이 없으면 전체를 JSON으로 파싱 시도
                json_str = response.strip()

            plan_data = json.loads(json_str)

            # Plan 유효성 검증
            if plan_data.get('phase') == 'planning':
                return plan_data
            else:
                logger.warning(f"[Plan Parsing] Invalid phase: {plan_data.get('phase')}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"[Plan Parsing] JSON decode error: {e}")
            logger.debug(f"Response: {response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"[Plan Parsing] Unexpected error: {e}")
            return None

    async def _review_plan(
        self,
        plan_data: Dict[str, Any],
        user_request: str
    ) -> Dict[str, Any]:
        """
        Orchestrator가 Plan을 리뷰하고 승인 여부 결정

        Args:
            plan_data: Sub-Agent가 생성한 Plan
            user_request: 원본 사용자 요청

        Returns:
            리뷰 결과 {'approved': bool, 'feedback': str, 'suggestions': []}
        """
        logger.info("[Review] Orchestrator가 Plan을 분석 중...")

        # 리뷰 기준
        review_criteria = {
            'has_function_spec': bool(plan_data.get('function_specification')),
            'has_implementation_plan': bool(plan_data.get('implementation_plan', {}).get('steps')),
            'has_test_requirements': bool(plan_data.get('test_requirements')),
            'has_interface_impact': bool(plan_data.get('interface_impact')),
            'has_estimated_effort': bool(plan_data.get('estimated_effort'))
        }

        # 점수 계산
        score = sum(review_criteria.values()) / len(review_criteria)

        logger.info(f"[Review] Plan 품질 점수: {score:.1%}")
        for criterion, passed in review_criteria.items():
            status = "OK" if passed else "MISSING"
            logger.info(f"  - {criterion}: {status}")

        # 승인 기준: 80% 이상
        approved = score >= 0.8

        if approved:
            feedback = f"Plan이 승인되었습니다 (품질 점수: {score:.1%})"
            suggestions = []
        else:
            feedback = f"Plan이 기준을 충족하지 못했습니다 (품질 점수: {score:.1%})"
            suggestions = [
                criterion for criterion, passed in review_criteria.items()
                if not passed
            ]

        return {
            'approved': approved,
            'score': score,
            'feedback': feedback,
            'suggestions': suggestions,
            'criteria_results': review_criteria,
            'timestamp': datetime.now().isoformat()
        }


# 사용 예시
async def main():
    """테스트 메인 함수"""

    # UserInputHandler 생성 (Orchestrator 없이 시뮬레이션)
    handler = UserInputHandler()

    # 예시 1: 백테스트 요청
    print("\n" + "=" * 80)
    print("예시 1: 백테스트 요청")
    print("=" * 80)

    result1 = await handler.process_user_input(
        "NASDAQ 종목으로 2024-01-01부터 2024-06-30까지 백테스트 실행해줘"
    )

    print("\n[최종 결과]")
    print(f"Summary: {result1['summary']}")
    print(f"Successful Agents: {result1['successful_agents']}")

    # 예시 2: 시그널 생성 요청
    print("\n" + "=" * 80)
    print("예시 2: 시그널 생성 요청")
    print("=" * 80)

    result2 = await handler.process_user_input(
        "AAPL, MSFT, GOOGL 종목에 대한 매매 시그널 생성해줘"
    )

    print("\n[최종 결과]")
    print(f"Summary: {result2['summary']}")

    # 대화 히스토리
    print("\n" + "=" * 80)
    print("대화 히스토리")
    print("=" * 80)
    for i, conv in enumerate(handler.get_conversation_history(), 1):
        print(f"\n{i}. {conv['user_input']}")
        print(f"   실행된 Agent: {', '.join(conv['results']['agents_executed'])}")


if __name__ == "__main__":
    asyncio.run(main())
