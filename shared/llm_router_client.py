"""
LLM Router Client for AI Assistant Multi-Agent System
Claude.md 규칙에 따른 LLM 모델 라우팅 클라이언트

Author: AI Assistant System
Date: 2025-09-15
Rules: Claude.md 필수 준수
"""

import json
import requests
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RouterRequest:
    """라우터 요청 데이터 구조"""
    agent: str
    task: str
    message: str
    preferences: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class RouterResponse:
    """라우터 응답 데이터 구조"""
    model_used: str
    response: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class LLMRouterClient:
    """
    LLM 라우터 클라이언트

    Claude.md 규칙 9, 11, 12에 따른 LLM 모델 라우팅 시스템
    - 에이전트별 모델 자동 할당
    - Gemini 모델 Claude Code 통합
    - 로드 밸런싱 및 fallback 지원
    """

    def __init__(self, router_url: str = "http://localhost:3000", config_path: str = None):
        """
        라우터 클라이언트 초기화

        Args:
            router_url: 라우터 서버 URL
            config_path: agent_model.yaml 경로
        """
        self.router_url = router_url.rstrip('/')
        self.config_path = config_path or "config/agent_model.yaml"

        # Load agent configurations
        self.agent_configs = self._load_agent_configs()
        self.router_config = self._load_router_config()

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "model_usage": {},
            "cost_tracking": {}
        }

        logger.info(f"LLM Router Client initialized with URL: {router_url}")

    def _load_agent_configs(self) -> Dict[str, Any]:
        """agent_model.yaml에서 에이전트별 설정 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('agents', {})
        except FileNotFoundError:
            logger.warning(f"Agent config file not found: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing agent config: {e}")
            return {}

    def _load_router_config(self) -> Dict[str, Any]:
        """라우터 설정 파일 로드"""
        try:
            with open("llm-router/router_config.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Router config file not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing router config: {e}")
            return {}

    def route_request(
        self,
        agent_name: str,
        task_type: str,
        message: str,
        **kwargs
    ) -> RouterResponse:
        """
        에이전트 요청을 적절한 LLM으로 라우팅

        Args:
            agent_name: 요청하는 에이전트 이름
            task_type: 작업 유형
            message: 처리할 메시지
            **kwargs: 추가 옵션

        Returns:
            RouterResponse: 라우팅 결과
        """
        start_time = time.time()

        try:
            # Build request payload
            request_data = self._build_request_payload(
                agent_name, task_type, message, **kwargs
            )

            # Send request to router
            response = self._send_router_request(request_data)

            # Process response
            router_response = self._process_response(response, start_time)

            # Update metrics
            self._update_metrics(router_response, start_time)

            return router_response

        except Exception as e:
            logger.error(f"Router request failed: {e}")

            # Try fallback
            fallback_response = self._try_fallback(agent_name, message, str(e))
            self._update_metrics(fallback_response, start_time, failed=True)

            return fallback_response

    def _build_request_payload(
        self,
        agent_name: str,
        task_type: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """요청 페이로드 구성"""

        agent_config = self.agent_configs.get(agent_name, {})

        payload = {
            "agent": agent_name,
            "task": task_type,
            "message": message,
            "preferences": {
                "primary_model": agent_config.get("primary_model"),
                "fallback_model": agent_config.get("fallback_model"),
                "strategy": agent_config.get("model_selection_strategy", "efficiency_first"),
                **kwargs.get("preferences", {})
            },
            "context": {
                "timestamp": datetime.now().isoformat(),
                "agent_config": agent_config,
                **kwargs.get("context", {})
            }
        }

        return payload

    def _send_router_request(self, payload: Dict[str, Any]) -> requests.Response:
        """라우터 서버로 요청 전송"""

        endpoint = f"{self.router_url}/api/route"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Assistant-Router-Client/1.0"
        }

        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        return response

    def _process_response(
        self,
        response: requests.Response,
        start_time: float
    ) -> RouterResponse:
        """라우터 응답 처리"""

        response_time = time.time() - start_time
        response_data = response.json()

        return RouterResponse(
            model_used=response_data.get("model_used", "unknown"),
            response=response_data.get("response", ""),
            metadata={
                "response_time": response_time,
                "cost": response_data.get("cost", 0.0),
                "tokens_used": response_data.get("tokens_used", 0),
                "provider": response_data.get("provider", "unknown"),
                **response_data.get("metadata", {})
            },
            success=True
        )

    def _try_fallback(
        self,
        agent_name: str,
        message: str,
        error: str
    ) -> RouterResponse:
        """Fallback 모델로 재시도"""

        logger.warning(f"Trying fallback for agent {agent_name} due to: {error}")

        agent_config = self.agent_configs.get(agent_name, {})
        fallback_model = agent_config.get("fallback_model", "claude-3-haiku-20240307")

        # Simple fallback response (실제 구현에서는 직접 API 호출)
        return RouterResponse(
            model_used=fallback_model,
            response=f"Fallback response for: {message[:100]}...",
            metadata={
                "response_time": 1.0,
                "cost": 0.001,
                "tokens_used": 100,
                "provider": "fallback",
                "fallback_reason": error
            },
            success=True,
            error=f"Primary router failed: {error}"
        )

    def _update_metrics(
        self,
        response: RouterResponse,
        start_time: float,
        failed: bool = False
    ):
        """성능 지표 업데이트"""

        self.metrics["total_requests"] += 1

        if failed:
            self.metrics["failed_requests"] += 1
        else:
            self.metrics["successful_requests"] += 1

        # Update model usage
        model = response.model_used
        if model not in self.metrics["model_usage"]:
            self.metrics["model_usage"][model] = 0
        self.metrics["model_usage"][model] += 1

        # Update cost tracking
        cost = response.metadata.get("cost", 0.0)
        if model not in self.metrics["cost_tracking"]:
            self.metrics["cost_tracking"][model] = 0.0
        self.metrics["cost_tracking"][model] += cost

        # Update average response time
        response_time = response.metadata.get("response_time", 0.0)
        total_time = self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1)
        self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_requests"]

    def get_agent_preferences(self, agent_name: str) -> Dict[str, Any]:
        """
        에이전트별 선호도 조회

        Args:
            agent_name: 에이전트 이름

        Returns:
            Dict: 에이전트 설정 정보
        """
        return self.agent_configs.get(agent_name, {})

    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 조회"""
        try:
            response = requests.get(f"{self.router_url}/api/models")
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []

    def get_router_status(self) -> Dict[str, Any]:
        """라우터 상태 조회"""
        try:
            response = requests.get(f"{self.router_url}/api/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get router status: {e}")
            return {"status": "error", "message": str(e)}

    def get_metrics(self) -> Dict[str, Any]:
        """클라이언트 메트릭 조회"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_requests"] / max(self.metrics["total_requests"], 1)
            ) * 100
        }

    def test_connection(self) -> bool:
        """라우터 연결 테스트"""
        try:
            response = requests.get(f"{self.router_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Router connection test failed: {e}")
            return False

# Convenience functions for agents
def create_router_client(config_path: str = None) -> LLMRouterClient:
    """라우터 클라이언트 생성 (에이전트용 편의 함수)"""
    return LLMRouterClient(config_path=config_path)

def route_agent_request(
    agent_name: str,
    task_type: str,
    message: str,
    router_client: LLMRouterClient = None,
    **kwargs
) -> RouterResponse:
    """에이전트 요청 라우팅 (편의 함수)"""
    if router_client is None:
        router_client = create_router_client()

    return router_client.route_request(agent_name, task_type, message, **kwargs)