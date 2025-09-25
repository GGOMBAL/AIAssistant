"""
Data Agent Router Integration
Claude.md 규칙 준수: Data Agent의 LLM 라우터 통합

Author: Data Agent
Date: 2025-09-15
Layer: Indicator Layer
Rules: Claude.md 규칙 1, 4, 9, 11, 12 준수
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.llm_router_client import LLMRouterClient, RouterResponse
from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataAgentRouter:
    """
    Data Agent LLM 라우터 통합

    Claude.md 규칙에 따른 Data Agent의 LLM 요청 처리:
    - 기술지표 계산: claude-3-sonnet (기본)
    - 대용량 데이터: gemini-pro (효율성)
    - 간단한 계산: claude-3-haiku (비용 효율)
    """

    def __init__(self):
        """Data Agent 라우터 초기화"""
        self.router = LLMRouterClient()
        self.agent_name = "data_agent"

        # Data Agent 작업 유형별 모델 매핑
        self.task_model_mapping = {
            "technical_indicators": "claude-3-sonnet-20240229",
            "large_dataset_processing": "gemini-pro",
            "simple_calculation": "claude-3-haiku-20240307",
            "data_validation": "claude-3-sonnet-20240229",
            "database_operations": "claude-3-sonnet-20240229"
        }

        logger.info("Data Agent Router initialized")

    def process_technical_indicators(
        self,
        data: pd.DataFrame,
        indicators: List[str],
        parameters: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        기술지표 계산 요청 처리

        Args:
            data: 주가 데이터
            indicators: 계산할 지표 목록
            parameters: 지표별 매개변수

        Returns:
            RouterResponse: 계산 결과
        """
        # 데이터 크기에 따른 모델 선택
        if len(data) > 10000:
            task_type = "large_dataset_processing"
            context = {"dataset_size": "large", "rows": len(data)}
        else:
            task_type = "technical_indicators"
            context = {"dataset_size": "normal", "rows": len(data)}

        message = f"""
        Calculate technical indicators for stock data:
        - Indicators: {', '.join(indicators)}
        - Data points: {len(data)}
        - Columns: {list(data.columns)}
        - Parameters: {parameters or 'default'}

        Please calculate the requested indicators and return structured results.
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type=task_type,
            message=message,
            context=context,
            preferences={
                "temperature": 0.1,  # 정확한 계산을 위해 낮은 temperature
                "max_tokens": 2000
            }
        )

    def process_data_validation(
        self,
        data: pd.DataFrame,
        validation_rules: Dict[str, Any]
    ) -> RouterResponse:
        """
        데이터 검증 요청 처리

        Args:
            data: 검증할 데이터
            validation_rules: 검증 규칙

        Returns:
            RouterResponse: 검증 결과
        """
        message = f"""
        Validate market data according to rules:
        - Data shape: {data.shape}
        - Validation rules: {validation_rules}
        - Sample data: {data.head(3).to_dict()}

        Check data quality, missing values, outliers, and consistency.
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="data_validation",
            message=message,
            context={
                "data_quality_check": True,
                "validation_type": "market_data"
            }
        )

    def process_database_query(
        self,
        query_type: str,
        query_parameters: Dict[str, Any]
    ) -> RouterResponse:
        """
        데이터베이스 쿼리 최적화 요청

        Args:
            query_type: 쿼리 유형
            query_parameters: 쿼리 매개변수

        Returns:
            RouterResponse: 최적화된 쿼리
        """
        message = f"""
        Optimize database query for trading system:
        - Query type: {query_type}
        - Parameters: {query_parameters}
        - Target: MongoDB market data

        Generate efficient query and suggest indexing strategy.
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="database_operations",
            message=message,
            context={
                "database_type": "mongodb",
                "optimization_focus": "performance"
            }
        )

    def simple_calculation(
        self,
        calculation_type: str,
        values: List[float],
        formula: str = None
    ) -> RouterResponse:
        """
        간단한 계산 요청 (비용 효율적 모델 사용)

        Args:
            calculation_type: 계산 유형
            values: 계산할 값들
            formula: 사용자 정의 공식

        Returns:
            RouterResponse: 계산 결과
        """
        message = f"""
        Perform simple calculation:
        - Type: {calculation_type}
        - Values: {values[:10]}{'...' if len(values) > 10 else ''}
        - Formula: {formula or 'standard'}

        Return precise numerical result.
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="simple_calculation",
            message=message,
            context={
                "calculation_complexity": "simple",
                "cost_optimization": True
            },
            preferences={
                "temperature": 0.0,  # 정확한 계산
                "max_tokens": 500
            }
        )

    def get_optimal_model(self, task_type: str, context: Dict[str, Any] = None) -> str:
        """
        작업에 최적화된 모델 선택

        Args:
            task_type: 작업 유형
            context: 추가 컨텍스트

        Returns:
            str: 최적 모델명
        """
        # 기본 매핑에서 선택
        base_model = self.task_model_mapping.get(task_type, "claude-3-sonnet-20240229")

        # 컨텍스트 기반 조정
        if context:
            # 대용량 데이터의 경우 Gemini 선호
            if context.get("dataset_size") == "large":
                return "gemini-pro"

            # 비용 최적화가 필요한 경우
            if context.get("cost_optimization"):
                return "claude-3-haiku-20240307"

            # 고품질이 필요한 경우
            if context.get("quality_critical"):
                return "claude-3-opus-20240229"

        return base_model

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Data Agent 라우터 성능 지표"""
        return {
            **self.router.get_metrics(),
            "agent_name": self.agent_name,
            "specialized_tasks": list(self.task_model_mapping.keys())
        }

# Example usage functions for Data Agent
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> RouterResponse:
    """RSI 계산 예시"""
    router = DataAgentRouter()
    return router.process_technical_indicators(
        data=data,
        indicators=["RSI"],
        parameters={"period": period}
    )

def validate_market_data(data: pd.DataFrame) -> RouterResponse:
    """시장 데이터 검증 예시"""
    router = DataAgentRouter()
    return router.process_data_validation(
        data=data,
        validation_rules={
            "price_range": {"min": 0, "max": 1000000},
            "volume_check": {"min": 0},
            "timestamp_format": "ISO8601"
        }
    )

def optimize_query(symbol: str, start_date: str, end_date: str) -> RouterResponse:
    """쿼리 최적화 예시"""
    router = DataAgentRouter()
    return router.process_database_query(
        query_type="time_series_data",
        query_parameters={
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "fields": ["open", "high", "low", "close", "volume"]
        }
    )