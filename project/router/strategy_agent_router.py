"""
Strategy Agent Router Integration
Claude.md 규칙 준수: Strategy Agent의 LLM 라우터 통합

Author: Strategy Agent
Date: 2025-09-15
Layer: Strategy Layer
Rules: Claude.md 규칙 1, 4, 9, 11, 12 준수
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.llm_router_client import LLMRouterClient, RouterResponse
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class StrategyAgentRouter:
    """
    Strategy Agent LLM 라우터 통합

    Claude.md 규칙에 따른 Strategy Agent의 LLM 요청 처리:
    - 복잡한 전략: claude-3-opus (최고 품질)
    - 신호 생성: claude-3-sonnet (균형)
    - 매개변수 최적화: gemini-pro (효율성)
    """

    def __init__(self):
        """Strategy Agent 라우터 초기화"""
        self.router = LLMRouterClient()
        self.agent_name = "strategy_agent"

        # Strategy Agent 작업 유형별 모델 매핑
        self.task_model_mapping = {
            "strategy_development": "claude-3-opus-20240229",
            "signal_generation": "claude-3-sonnet-20240229",
            "parameter_optimization": "gemini-pro",
            "risk_analysis": "claude-3-opus-20240229",
            "portfolio_optimization": "claude-3-opus-20240229",
            "performance_analysis": "claude-3-sonnet-20240229"
        }

        logger.info("Strategy Agent Router initialized")

    def develop_trading_strategy(
        self,
        strategy_type: str,
        market_conditions: Dict[str, Any],
        constraints: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        거래 전략 개발 요청 처리

        Args:
            strategy_type: 전략 유형 (momentum, mean_reversion, etc.)
            market_conditions: 시장 조건
            constraints: 제약 조건

        Returns:
            RouterResponse: 개발된 전략
        """
        message = f"""
        Develop advanced trading strategy:
        - Strategy type: {strategy_type}
        - Market conditions: {market_conditions}
        - Constraints: {constraints or 'none'}

        Create detailed strategy with:
        1. Entry/exit conditions
        2. Position sizing rules
        3. Risk management parameters
        4. Expected performance metrics
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="strategy_development",
            message=message,
            context={
                "complexity": "high",
                "quality_critical": True,
                "strategy_type": strategy_type
            },
            preferences={
                "temperature": 0.3,  # 창의성과 정확성 균형
                "max_tokens": 3000
            }
        )

    def generate_trading_signals(
        self,
        market_data: Dict[str, Any],
        indicators: List[str],
        strategy_rules: Dict[str, Any]
    ) -> RouterResponse:
        """
        거래 신호 생성 요청 처리

        Args:
            market_data: 시장 데이터
            indicators: 기술지표 값들
            strategy_rules: 전략 규칙

        Returns:
            RouterResponse: 거래 신호
        """
        message = f"""
        Generate trading signals based on:
        - Market data: {market_data}
        - Technical indicators: {indicators}
        - Strategy rules: {strategy_rules}

        Provide clear BUY/SELL/HOLD signals with:
        1. Signal strength (1-10)
        2. Confidence level
        3. Supporting rationale
        4. Risk assessment
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="signal_generation",
            message=message,
            context={
                "real_time": True,
                "decision_critical": True
            },
            preferences={
                "temperature": 0.2,  # 일관성 있는 신호 생성
                "max_tokens": 1500
            }
        )

    def optimize_strategy_parameters(
        self,
        strategy_code: str,
        historical_data: Dict[str, Any],
        optimization_target: str = "sharpe_ratio"
    ) -> RouterResponse:
        """
        전략 매개변수 최적화 요청

        Args:
            strategy_code: 전략 코드
            historical_data: 역사적 데이터
            optimization_target: 최적화 목표

        Returns:
            RouterResponse: 최적화된 매개변수
        """
        message = f"""
        Optimize strategy parameters:
        - Strategy code: {strategy_code[:500]}...
        - Historical data period: {historical_data.get('period', 'unknown')}
        - Optimization target: {optimization_target}

        Find optimal parameters using:
        1. Grid search approach
        2. Backtesting validation
        3. Risk-adjusted returns
        4. Robustness testing
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="parameter_optimization",
            message=message,
            context={
                "optimization_intensive": True,
                "large_computation": True
            },
            preferences={
                "temperature": 0.1,  # 정확한 최적화
                "max_tokens": 2500
            }
        )

    def analyze_portfolio_risk(
        self,
        portfolio: Dict[str, Any],
        market_volatility: float,
        correlation_matrix: Dict[str, Any]
    ) -> RouterResponse:
        """
        포트폴리오 리스크 분석

        Args:
            portfolio: 포트폴리오 구성
            market_volatility: 시장 변동성
            correlation_matrix: 상관계수 행렬

        Returns:
            RouterResponse: 리스크 분석 결과
        """
        message = f"""
        Analyze portfolio risk:
        - Portfolio composition: {portfolio}
        - Market volatility: {market_volatility}
        - Asset correlations: {correlation_matrix}

        Provide comprehensive risk analysis:
        1. Value at Risk (VaR)
        2. Maximum drawdown estimation
        3. Concentration risk
        4. Stress test scenarios
        5. Risk mitigation recommendations
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="risk_analysis",
            message=message,
            context={
                "analysis_depth": "comprehensive",
                "quality_critical": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 2000
            }
        )

    def optimize_portfolio_allocation(
        self,
        assets: List[str],
        expected_returns: Dict[str, float],
        risk_tolerance: float,
        constraints: Dict[str, Any] = None
    ) -> RouterResponse:
        """
        포트폴리오 최적화

        Args:
            assets: 자산 목록
            expected_returns: 예상 수익률
            risk_tolerance: 리스크 허용도
            constraints: 제약 조건

        Returns:
            RouterResponse: 최적화된 포트폴리오
        """
        message = f"""
        Optimize portfolio allocation:
        - Assets: {assets}
        - Expected returns: {expected_returns}
        - Risk tolerance: {risk_tolerance}
        - Constraints: {constraints or 'none'}

        Apply modern portfolio theory:
        1. Efficient frontier calculation
        2. Risk-return optimization
        3. Constraint satisfaction
        4. Rebalancing recommendations
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="portfolio_optimization",
            message=message,
            context={
                "optimization_complex": True,
                "mathematical_intensive": True
            },
            preferences={
                "temperature": 0.1,  # 정확한 수학적 계산
                "max_tokens": 2500
            }
        )

    def analyze_strategy_performance(
        self,
        strategy_results: Dict[str, Any],
        benchmark_returns: List[float],
        time_period: str
    ) -> RouterResponse:
        """
        전략 성과 분석

        Args:
            strategy_results: 전략 결과
            benchmark_returns: 벤치마크 수익률
            time_period: 분석 기간

        Returns:
            RouterResponse: 성과 분석 보고서
        """
        message = f"""
        Analyze strategy performance:
        - Strategy results: {strategy_results}
        - Benchmark returns: {len(benchmark_returns)} data points
        - Analysis period: {time_period}

        Generate performance report:
        1. Risk-adjusted returns (Sharpe, Sortino, Calmar)
        2. Drawdown analysis
        3. Win/loss statistics
        4. Benchmark comparison
        5. Performance attribution
        """

        return self.router.route_request(
            agent_name=self.agent_name,
            task_type="performance_analysis",
            message=message,
            context={
                "analytical_depth": "detailed",
                "reporting": True
            },
            preferences={
                "temperature": 0.2,
                "max_tokens": 2000
            }
        )

    def get_model_recommendation(
        self,
        task_complexity: str,
        time_constraint: bool = False,
        cost_sensitive: bool = False
    ) -> str:
        """
        작업 복잡도에 따른 모델 추천

        Args:
            task_complexity: 작업 복잡도 (low, medium, high)
            time_constraint: 시간 제약 여부
            cost_sensitive: 비용 민감성

        Returns:
            str: 추천 모델명
        """
        if cost_sensitive and task_complexity == "low":
            return "claude-3-haiku-20240307"

        if time_constraint and task_complexity in ["low", "medium"]:
            return "gemini-pro"

        if task_complexity == "high":
            return "claude-3-opus-20240229"

        return "claude-3-sonnet-20240229"  # 기본값

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Strategy Agent 라우터 성능 지표"""
        return {
            **self.router.get_metrics(),
            "agent_name": self.agent_name,
            "specialized_tasks": list(self.task_model_mapping.keys()),
            "quality_focus": "high"
        }

# Example usage functions for Strategy Agent
def create_momentum_strategy(
    lookback_period: int = 20,
    threshold: float = 0.02
) -> RouterResponse:
    """모멘텀 전략 생성 예시"""
    router = StrategyAgentRouter()
    return router.develop_trading_strategy(
        strategy_type="momentum",
        market_conditions={
            "trend": "bullish",
            "volatility": "medium",
            "liquidity": "high"
        },
        constraints={
            "lookback_period": lookback_period,
            "threshold": threshold,
            "max_positions": 10
        }
    )

def generate_buy_sell_signals(
    current_price: float,
    rsi: float,
    macd_signal: float
) -> RouterResponse:
    """매매 신호 생성 예시"""
    router = StrategyAgentRouter()
    return router.generate_trading_signals(
        market_data={"current_price": current_price},
        indicators=["RSI", "MACD"],
        strategy_rules={
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "macd_threshold": 0
        }
    )