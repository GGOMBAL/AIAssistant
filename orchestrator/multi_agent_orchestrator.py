import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from shared.multi_agent_system import (
    MultiAgentOrchestrator, Agent, AgentMessage, MessageType
)
from shared.agent_collaboration import (
    CollaborationFramework, CollaborationType, CollaborationTask
)
from shared.claude_client import SharedClaudeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingMultiAgentSystem:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.claude_client = SharedClaudeClient(api_key)
        self.orchestrator = MultiAgentOrchestrator(api_key)
        self.collaboration_framework = CollaborationFramework()
        self.workflow_engine = WorkflowEngine()
        self._setup_agent_roles()
        
    def _setup_agent_roles(self):
        roles = {
            "strategy_agent": {
                "role": "chief_strategist",
                "responsibilities": ["signal_generation", "strategy_development", "risk_analysis"],
                "authority_level": 1,
                "can_delegate_to": ["model_agent", "backtest_agent"]
            },
            "data_agent": {
                "role": "data_coordinator",
                "responsibilities": ["data_management", "quality_assurance", "data_distribution"],
                "authority_level": 1,
                "can_delegate_to": ["getstockdata_agent", "api_agent"]
            },
            "trade_agent": {
                "role": "execution_manager",
                "responsibilities": ["order_execution", "position_management", "slippage_control"],
                "authority_level": 2,
                "can_delegate_to": ["api_agent"]
            },
            "model_agent": {
                "role": "ml_specialist",
                "responsibilities": ["model_development", "prediction", "feature_engineering"],
                "authority_level": 2,
                "can_delegate_to": []
            },
            "backtest_agent": {
                "role": "validation_specialist",
                "responsibilities": ["strategy_testing", "performance_validation", "optimization"],
                "authority_level": 2,
                "can_delegate_to": []
            },
            "evaluation_agent": {
                "role": "risk_analyst",
                "responsibilities": ["performance_analysis", "risk_metrics", "compliance"],
                "authority_level": 2,
                "can_delegate_to": []
            },
            "api_agent": {
                "role": "integration_specialist",
                "responsibilities": ["external_connectivity", "api_management", "data_routing"],
                "authority_level": 3,
                "can_delegate_to": []
            },
            "getstockdata_agent": {
                "role": "market_data_specialist",
                "responsibilities": ["real_time_data", "historical_data", "data_streaming"],
                "authority_level": 3,
                "can_delegate_to": []
            }
        }
        
        self.collaboration_framework.define_agent_roles(roles)
    
    async def execute_trading_workflow(self, symbols: List[str], strategy_params: Dict[str, Any]):
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting trading workflow {workflow_id} for symbols: {symbols}")
        
        workflow_steps = [
            {
                "name": "data_collection",
                "task": CollaborationTask(
                    id=f"{workflow_id}_data",
                    name="Collect Market Data",
                    description="Gather latest market data for analysis",
                    required_agents=["data_agent", "getstockdata_agent", "api_agent"],
                    collaboration_type=CollaborationType.HIERARCHICAL,
                    parameters={"symbols": symbols, "lead_agent": "data_agent"},
                    dependencies=[],
                    created_at=datetime.now()
                )
            },
            {
                "name": "signal_generation",
                "task": CollaborationTask(
                    id=f"{workflow_id}_signals",
                    name="Generate Trading Signals",
                    description="Analyze data and generate trading signals",
                    required_agents=["strategy_agent", "model_agent", "data_agent"],
                    collaboration_type=CollaborationType.PARALLEL,
                    parameters={"strategy": strategy_params, "symbols": symbols},
                    dependencies=["data_collection"],
                    created_at=datetime.now()
                )
            },
            {
                "name": "validation",
                "task": CollaborationTask(
                    id=f"{workflow_id}_validation",
                    name="Validate Signals",
                    description="Backtest and validate generated signals",
                    required_agents=["backtest_agent", "evaluation_agent", "strategy_agent"],
                    collaboration_type=CollaborationType.CONSENSUS,
                    parameters={"max_consensus_rounds": 2},
                    dependencies=["signal_generation"],
                    created_at=datetime.now()
                )
            },
            {
                "name": "execution",
                "task": CollaborationTask(
                    id=f"{workflow_id}_execution",
                    name="Execute Trades",
                    description="Execute validated trading signals",
                    required_agents=["trade_agent", "api_agent", "evaluation_agent"],
                    collaboration_type=CollaborationType.SEQUENTIAL,
                    parameters={"execution_mode": "paper"},
                    dependencies=["validation"],
                    created_at=datetime.now()
                )
            }
        ]
        
        results = {}
        for step in workflow_steps:
            logger.info(f"Executing step: {step['name']}")
            
            if step["task"].dependencies:
                await self._wait_for_dependencies(step["task"].dependencies, results)
            
            step_result = await self.collaboration_framework.initiate_collaboration(
                step["task"],
                self.orchestrator.agents
            )
            
            results[step["name"]] = step_result
            
            await self._process_step_result(step["name"], step_result)
        
        return {
            "workflow_id": workflow_id,
            "symbols": symbols,
            "strategy": strategy_params,
            "results": results,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _wait_for_dependencies(self, dependencies: List[str], results: Dict[str, Any]):
        for dep in dependencies:
            while dep not in results or results[dep].get("status") != "completed":
                await asyncio.sleep(0.1)
    
    async def _process_step_result(self, step_name: str, result: Dict[str, Any]):
        if step_name == "signal_generation":
            signals = result.get("aggregated_output", {})
            await self._broadcast_signals(signals)
        elif step_name == "execution":
            execution_result = result.get("final_output", {})
            await self._log_execution(execution_result)
    
    async def _broadcast_signals(self, signals: Dict[str, Any]):
        await self.orchestrator.broadcast_notification({
            "type": "trading_signals",
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _log_execution(self, execution_result: Dict[str, Any]):
        logger.info(f"Trade execution completed: {execution_result}")
    
    async def run_adaptive_strategy(self, market_conditions: Dict[str, Any]):
        task = CollaborationTask(
            id=str(uuid.uuid4()),
            name="Adaptive Strategy",
            description="Adapt trading strategy based on market conditions",
            required_agents=["strategy_agent", "model_agent", "evaluation_agent", "data_agent"],
            collaboration_type=CollaborationType.DELEGATION,
            parameters={
                "delegator": "strategy_agent",
                "market_conditions": market_conditions
            },
            dependencies=[],
            created_at=datetime.now()
        )
        
        result = await self.collaboration_framework.initiate_collaboration(
            task,
            self.orchestrator.agents
        )
        
        return result
    
    async def perform_risk_analysis(self, portfolio: Dict[str, Any]):
        task = CollaborationTask(
            id=str(uuid.uuid4()),
            name="Risk Analysis",
            description="Comprehensive portfolio risk analysis",
            required_agents=["evaluation_agent", "strategy_agent", "model_agent"],
            collaboration_type=CollaborationType.CONSENSUS,
            parameters={
                "portfolio": portfolio,
                "max_consensus_rounds": 3
            },
            dependencies=[],
            created_at=datetime.now()
        )
        
        result = await self.collaboration_framework.initiate_collaboration(
            task,
            self.orchestrator.agents
        )
        
        return result

class WorkflowEngine:
    def __init__(self):
        self.workflows = {}
        self.workflow_templates = self._load_workflow_templates()
        
    def _load_workflow_templates(self) -> Dict[str, Any]:
        return {
            "daily_trading": {
                "steps": ["market_open_check", "data_update", "signal_generation", 
                         "risk_check", "execution", "position_monitoring"],
                "schedule": "daily",
                "priority": "high"
            },
            "intraday_scalping": {
                "steps": ["real_time_data", "rapid_signals", "quick_execution", 
                         "stop_loss_monitoring"],
                "schedule": "continuous",
                "priority": "critical"
            },
            "portfolio_rebalance": {
                "steps": ["portfolio_analysis", "target_allocation", "rebalance_orders",
                         "execution", "verification"],
                "schedule": "weekly",
                "priority": "medium"
            },
            "risk_management": {
                "steps": ["position_analysis", "risk_metrics", "hedge_recommendations",
                         "alert_generation"],
                "schedule": "continuous",
                "priority": "high"
            }
        }
    
    def create_workflow(self, template_name: str, custom_params: Dict[str, Any] = None):
        template = self.workflow_templates.get(template_name)
        
        if not template:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        workflow_id = str(uuid.uuid4())
        workflow = {
            "id": workflow_id,
            "template": template_name,
            "steps": template["steps"],
            "parameters": custom_params or {},
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }
        
        self.workflows[workflow_id] = workflow
        return workflow

async def main():
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key-here")
    
    trading_system = TradingMultiAgentSystem(api_key)
    
    result = await trading_system.execute_trading_workflow(
        symbols=["AAPL", "GOOGL", "MSFT"],
        strategy_params={
            "type": "momentum",
            "timeframe": "1h",
            "risk_level": "moderate"
        }
    )
    
    print(json.dumps(result, indent=2))
    
    adaptive_result = await trading_system.run_adaptive_strategy({
        "volatility": "high",
        "trend": "bullish",
        "volume": "increasing"
    })
    
    print("\nAdaptive Strategy Result:")
    print(json.dumps(adaptive_result, indent=2))
    
    risk_result = await trading_system.perform_risk_analysis({
        "positions": ["AAPL", "GOOGL"],
        "total_value": 100000,
        "leverage": 1.5
    })
    
    print("\nRisk Analysis Result:")
    print(json.dumps(risk_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())