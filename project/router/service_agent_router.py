"""
Service Agent Router Integration
Claude.md 규칙 준수: Service Agent의 LLM 라우터 통합

Author: Service Agent
Date: 2025-09-15
Layer: Service Layer
Rules: Claude.md 규칙 1, 4, 9, 11, 12 준수
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.llm_router_client import LLMRouterClient, RouterResponse
from typing import Dict, Any, List
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class ServiceAgentRouter:
    """
    Service Agent LLM 라우터 통합

    Claude.md 규칙에 따른 Service Agent의 LLM 요청 처리:
    - 백테스팅: claude-3-sonnet (균형)
    - 주문 실행: claude-3-haiku (빠른 응답)
    - 리스크 모니터링: claude-3-sonnet (신뢰성)
    - 성과 분석: claude-3-sonnet (상세 분석)
    """

    def __init__(self):
        """Service Agent 라우터 초기화"""
        self.router = LLMRouterClient()
        self.agent_name = "service_agent"

        # Service Agent 작업 유형별 모델 매핑
        self.task_model_mapping = {
            "backtesting": "claude-3-sonnet-20240229",
            "order_execution": "claude-3-haiku-20240307",
            "risk_monitoring": "claude-3-sonnet-20240229",
            "performance_analysis": "claude-3-sonnet-20240229",
            "position_management": "claude-3-haiku-20240307",
            "trade_validation": "claude-3-sonnet-20240229",
            "service_monitoring": "claude-3-haiku-20240307",
            "database_management": "claude-3-sonnet-20240229"
        }

        logger.info("Service Agent Router initialized")

    def process_backtesting_request(
        self,
        strategy_code: str,
        historical_data: Dict[str, Any],
        parameters: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        백테스팅 실행 요청 처리

        Args:
            strategy_code: 전략 코드
            historical_data: 역사적 데이터
            parameters: 백테스팅 매개변수

        Returns:
            RouterResponse: 백테스팅 결과
        """
        # 데이터 크기에 따른 모델 선택
        data_size = historical_data.get('data_points', 0)
        if data_size > 50000:
            task_type = "large_backtesting"
            context = {"data_size": "large", "computation_intensive": True}
        else:
            task_type = "backtesting"
            context = {"data_size": "normal", "computation_intensive": False}

        message = f"""
        Execute comprehensive backtesting:
        - Strategy: {strategy_code[:200]}...
        - Data period: {historical_data.get('period', 'unknown')}
        - Data points: {data_size}
        - Parameters: {parameters or 'default'}

        Perform backtesting analysis:
        1. Execute strategy on historical data
        2. Calculate performance metrics
        3. Risk analysis and drawdown
        4. Trade statistics
        5. Benchmark comparison
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type=task_type,
            message=message,
            context=context,
            preferences={
                "temperature": 0.2,  # 일관된 분석
                "max_tokens": 3000
            }
        )

    def process_order_execution(
        self,
        order_details: Dict[str, Any],
        market_conditions: Dict[str, Any],
        risk_checks: Dict[str, Any]
    ) -> RouterResponse:
        """
        주문 실행 요청 처리

        Args:
            order_details: 주문 상세정보
            market_conditions: 시장 조건
            risk_checks: 리스크 체크 결과

        Returns:
            RouterResponse: 주문 실행 결과
        """
        message = f"""
        Execute trading order with real-time validation:
        - Order: {order_details}
        - Market conditions: {market_conditions}
        - Risk validation: {risk_checks}

        Execute order processing:
        1. Final risk validation
        2. Market timing optimization
        3. Order size adjustment
        4. Execution monitoring
        5. Fill confirmation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="order_execution",
            message=message,
            context={
                "time_critical": True,
                "low_latency_required": True,
                "real_time": True
            },
            preferences={
                "temperature": 0.1,  # 정확한 실행
                "max_tokens": 1000   # 빠른 응답
            }
        )

    def monitor_portfolio_risk(
        self,
        current_positions: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        risk_limits: Dict[str, Any]
    ) -> RouterResponse:
        """
        포트폴리오 리스크 모니터링

        Args:
            current_positions: 현재 포지션
            market_data: 시장 데이터
            risk_limits: 리스크 한도

        Returns:
            RouterResponse: 리스크 모니터링 결과
        """
        message = f"""
        Monitor real-time portfolio risk:
        - Positions: {len(current_positions)} active positions
        - Market data: {market_data}
        - Risk limits: {risk_limits}

        Perform risk monitoring:
        1. Position-level risk assessment
        2. Portfolio correlation analysis
        3. Exposure limit validation
        4. Stress test scenarios
        5. Alert generation for violations
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="risk_monitoring",
            message=message,
            context={
                "real_time_monitoring": True,
                "critical_system": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 2000
            }
        )

    def analyze_trading_performance(
        self,
        trade_history: List[Dict[str, Any]],
        benchmark_data: Dict[str, Any],
        analysis_period: str
    ) -> RouterResponse:
        """
        거래 성과 분석

        Args:
            trade_history: 거래 이력
            benchmark_data: 벤치마크 데이터
            analysis_period: 분석 기간

        Returns:
            RouterResponse: 성과 분석 보고서
        """
        message = f"""
        Analyze comprehensive trading performance:
        - Trades: {len(trade_history)} transactions
        - Period: {analysis_period}
        - Benchmark: {benchmark_data.get('name', 'unknown')}

        Generate performance analysis:
        1. Return and risk metrics
        2. Trade-level analysis
        3. Strategy attribution
        4. Risk-adjusted performance
        5. Improvement recommendations
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="performance_analysis",
            message=message,
            context={
                "analytical_depth": "comprehensive",
                "reporting_required": True
            },
            preferences={
                "temperature": 0.3,
                "max_tokens": 2500
            }
        )

    def manage_position_updates(
        self,
        position_changes: List[Dict[str, Any]],
        account_balance: float,
        margin_requirements: Dict[str, Any]
    ) -> RouterResponse:
        """
        포지션 관리 및 업데이트

        Args:
            position_changes: 포지션 변경사항
            account_balance: 계좌 잔고
            margin_requirements: 마진 요구사항

        Returns:
            RouterResponse: 포지션 관리 결과
        """
        message = f"""
        Manage position updates and account reconciliation:
        - Position changes: {len(position_changes)} updates
        - Account balance: {account_balance}
        - Margin requirements: {margin_requirements}

        Execute position management:
        1. Position reconciliation
        2. Margin calculation
        3. Account balance update
        4. Risk exposure recalculation
        5. Notification generation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="position_management",
            message=message,
            context={
                "account_critical": True,
                "accuracy_required": True
            },
            preferences={
                "temperature": 0.1,  # 정확한 계산
                "max_tokens": 1500
            }
        )

    def validate_trade_execution(
        self,
        executed_trades: List[Dict[str, Any]],
        expected_results: Dict[str, Any],
        tolerance_levels: Dict[str, Any]
    ) -> RouterResponse:
        """
        거래 실행 검증

        Args:
            executed_trades: 실행된 거래
            expected_results: 예상 결과
            tolerance_levels: 허용 오차

        Returns:
            RouterResponse: 거래 검증 결과
        """
        message = f"""
        Validate trade execution accuracy:
        - Executed trades: {len(executed_trades)} transactions
        - Expected results: {expected_results}
        - Tolerance levels: {tolerance_levels}

        Perform execution validation:
        1. Price execution analysis
        2. Timing accuracy check
        3. Quantity verification
        4. Slippage calculation
        5. Exception identification
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="trade_validation",
            message=message,
            context={
                "quality_control": True,
                "accuracy_critical": True
            },
            preferences={
                "temperature": 0.1,
                "max_tokens": 2000
            }
        )

    def monitor_service_health(
        self,
        service_metrics: Dict[str, Any],
        system_status: Dict[str, Any],
        alert_thresholds: Dict[str, Any]
    ) -> RouterResponse:
        """
        서비스 상태 모니터링

        Args:
            service_metrics: 서비스 지표
            system_status: 시스템 상태
            alert_thresholds: 알림 임계값

        Returns:
            RouterResponse: 서비스 상태 보고
        """
        message = f"""
        Monitor trading service health:
        - Service metrics: {service_metrics}
        - System status: {system_status}
        - Alert thresholds: {alert_thresholds}

        Perform health monitoring:
        1. Service availability check
        2. Performance metrics analysis
        3. Error rate monitoring
        4. Resource utilization review
        5. Alert generation
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="service_monitoring",
            message=message,
            context={
                "monitoring": True,
                "operations_critical": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 1500
            }
        )

    def manage_database_operations(
        self,
        operation_type: str,
        database_config: Dict[str, Any],
        data_specifications: Dict[str, Any]
    ) -> RouterResponse:
        """
        데이터베이스 운영 관리

        Args:
            operation_type: 작업 유형
            database_config: 데이터베이스 설정
            data_specifications: 데이터 명세

        Returns:
            RouterResponse: 데이터베이스 작업 결과
        """
        message = f"""
        Manage database operations:
        - Operation: {operation_type}
        - Database config: {database_config}
        - Data specs: {data_specifications}

        Execute database management:
        1. Operation planning
        2. Data integrity validation
        3. Performance optimization
        4. Backup verification
        5. Recovery procedures
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="database_management",
            message=message,
            context={
                "database_operations": True,
                "data_integrity_critical": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 2000
            }
        )

    def get_model_for_urgency(self, urgency_level: str) -> str:
        """
        긴급도에 따른 모델 선택

        Args:
            urgency_level: 긴급도 (low, medium, high, critical)

        Returns:
            str: 추천 모델명
        """
        if urgency_level == "critical":
            return "claude-3-haiku-20240307"  # 가장 빠른 응답
        elif urgency_level == "high":
            return "claude-3-haiku-20240307"
        elif urgency_level == "medium":
            return "claude-3-sonnet-20240229"
        else:  # low
            return "claude-3-sonnet-20240229"

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Service Agent 라우터 성능 지표"""
        return {
            **self.router.get_metrics(),
            "agent_name": self.agent_name,
            "specialized_tasks": list(self.task_model_mapping.keys()),
            "focus": "reliability_and_speed"
        }

# Example usage functions for Service Agent
def run_strategy_backtest(
    strategy_name: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000
) -> RouterResponse:
    """전략 백테스팅 실행 예시"""
    router = ServiceAgentRouter()
    return router.process_backtesting_request(
        strategy_code=f"def {strategy_name}_strategy(): pass",
        historical_data={
            "period": f"{start_date} to {end_date}",
            "data_points": 252,  # 1년 데이터
            "initial_capital": initial_capital
        },
        parameters={
            "commission": 0.001,
            "slippage": 0.0005,
            "benchmark": "SPY"
        }
    )

def execute_market_order(
    symbol: str,
    quantity: int,
    side: str,
    current_price: float
) -> RouterResponse:
    """시장가 주문 실행 예시"""
    router = ServiceAgentRouter()
    return router.process_order_execution(
        order_details={
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "order_type": "market"
        },
        market_conditions={
            "current_price": current_price,
            "bid_ask_spread": 0.01,
            "volume": 1000000
        },
        risk_checks={
            "position_limit_ok": True,
            "margin_available": True,
            "risk_within_limits": True
        }
    )