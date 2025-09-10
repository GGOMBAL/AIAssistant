import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.api_manager import SharedAPIManager, Priority, APIRateLimiter
from shared.claude_client import SharedClaudeClient
from orchestrator.agent_scheduler import AgentScheduler, AgentTask, ExecutionMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainOrchestrator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.rate_limiter = APIRateLimiter(requests_per_minute=30, requests_per_day=1000)
        self.api_manager = SharedAPIManager(api_key, self.rate_limiter)
        self.claude_client = SharedClaudeClient(api_key)
        self.scheduler = AgentScheduler(self.api_manager, max_concurrent=3)
        self.agents_config = self._load_agents_config()
        self._initialize_agents()
        
    def _load_agents_config(self) -> Dict[str, Any]:
        return {
            "strategy_agent": {
                "priority": 1,
                "model": "claude-3-opus-20240229",
                "capabilities": ["signal_generation", "position_sizing", "strategy_optimization"]
            },
            "data_agent": {
                "priority": 1,
                "model": "claude-3-opus-20240229",
                "capabilities": ["data_collection", "database_management", "data_validation"]
            },
            "trade_agent": {
                "priority": 2,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["order_execution", "position_management", "risk_control"]
            },
            "model_agent": {
                "priority": 3,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["ml_training", "prediction", "feature_engineering"]
            },
            "backtest_agent": {
                "priority": 3,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["strategy_testing", "performance_analysis", "optimization"]
            },
            "evaluation_agent": {
                "priority": 3,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["risk_assessment", "performance_metrics", "reporting"]
            },
            "api_agent": {
                "priority": 2,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["external_api", "data_integration", "webhook_management"]
            },
            "getstockdata_agent": {
                "priority": 2,
                "model": "claude-3-5-sonnet-20241022",
                "capabilities": ["stock_data_retrieval", "market_data", "real_time_feeds"]
            }
        }
    
    def _initialize_agents(self):
        for agent_name, config in self.agents_config.items():
            self.scheduler.register_agent(agent_name, config)
            logger.info(f"Initialized {agent_name} with priority {config['priority']}")
    
    async def execute_workflow(self, workflow_type: str, params: Dict[str, Any]):
        logger.info(f"Executing workflow: {workflow_type}")
        
        if workflow_type == "daily_trading":
            await self._execute_daily_trading_workflow(params)
        elif workflow_type == "backtest":
            await self._execute_backtest_workflow(params)
        elif workflow_type == "data_update":
            await self._execute_data_update_workflow(params)
        else:
            logger.error(f"Unknown workflow type: {workflow_type}")
    
    async def _execute_daily_trading_workflow(self, params: Dict[str, Any]):
        self.scheduler.set_execution_mode(ExecutionMode.BATCH)
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="getstockdata_agent",
            task_type="fetch_market_data",
            payload={"symbols": params.get("symbols", [])},
            priority=1
        ))
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="data_agent",
            task_type="update_database",
            payload={"data_type": "market_data"},
            priority=1,
            dependencies=["getstockdata_agent"]
        ))
        
        strategy_tasks = []
        for symbol in params.get("symbols", []):
            task = AgentTask(
                agent_name="strategy_agent",
                task_type="generate_signals",
                payload={"symbol": symbol, "timeframe": params.get("timeframe", "1d")},
                priority=2,
                dependencies=["data_agent"]
            )
            await self.scheduler.schedule_task(task)
            strategy_tasks.append(task)
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="trade_agent",
            task_type="execute_trades",
            payload={"mode": params.get("mode", "paper")},
            priority=3,
            dependencies=["strategy_agent"]
        ))
        
        await self.scheduler.run_scheduler()
    
    async def _execute_backtest_workflow(self, params: Dict[str, Any]):
        self.scheduler.set_execution_mode(ExecutionMode.PARALLEL)
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="data_agent",
            task_type="load_historical_data",
            payload={
                "symbols": params.get("symbols", []),
                "start_date": params.get("start_date"),
                "end_date": params.get("end_date")
            },
            priority=1
        ))
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="backtest_agent",
            task_type="run_backtest",
            payload={
                "strategy": params.get("strategy"),
                "parameters": params.get("parameters", {})
            },
            priority=2,
            dependencies=["data_agent"]
        ))
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="evaluation_agent",
            task_type="analyze_results",
            payload={"metrics": ["sharpe", "max_drawdown", "win_rate"]},
            priority=3,
            dependencies=["backtest_agent"]
        ))
        
        await self.scheduler.run_scheduler()
    
    async def _execute_data_update_workflow(self, params: Dict[str, Any]):
        self.scheduler.set_execution_mode(ExecutionMode.ROUND_ROBIN)
        
        data_sources = params.get("sources", ["stock", "forex", "crypto"])
        
        for source in data_sources:
            await self.scheduler.schedule_task(AgentTask(
                agent_name="api_agent",
                task_type="fetch_data",
                payload={"source": source},
                priority=1
            ))
        
        await self.scheduler.schedule_task(AgentTask(
            agent_name="data_agent",
            task_type="consolidate_data",
            payload={"sources": data_sources},
            priority=2,
            dependencies=["api_agent"]
        ))
        
        await self.scheduler.run_scheduler()
    
    async def process_agent_request(self, agent_name: str, message: str) -> str:
        messages = [{"role": "user", "content": message}]
        
        system_prompt = self._get_agent_system_prompt(agent_name)
        
        result = await self.claude_client.send_agent_message(
            agent_name=agent_name,
            messages=messages,
            system_prompt=system_prompt
        )
        
        if "error" in result:
            logger.error(f"Error from {agent_name}: {result['error']}")
            return f"Error: {result['error']}"
        
        return result.get("content", [{}])[0].get("text", "No response")
    
    def _get_agent_system_prompt(self, agent_name: str) -> str:
        prompts = {
            "strategy_agent": "You are a trading strategy specialist. Generate trading signals and optimize position sizing.",
            "data_agent": "You are a data management specialist. Handle data collection, validation, and database operations.",
            "trade_agent": "You are a trade execution specialist. Manage order execution and position management.",
            "model_agent": "You are a machine learning specialist. Develop and deploy predictive models.",
            "backtest_agent": "You are a backtesting specialist. Test and validate trading strategies.",
            "evaluation_agent": "You are a performance evaluation specialist. Analyze trading results and risk metrics.",
            "api_agent": "You are an API integration specialist. Handle external data sources and webhooks.",
            "getstockdata_agent": "You are a market data specialist. Retrieve and process real-time market data."
        }
        return prompts.get(agent_name, "You are a specialized trading system agent.")
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "api_stats": self.api_manager.get_stats(),
            "agent_stats": self.scheduler.get_agent_stats(),
            "usage_stats": self.claude_client.get_usage_stats(),
            "rate_limit": {
                "minute_remaining": self.rate_limiter.requests_per_minute - len(self.rate_limiter.minute_window),
                "daily_remaining": self.rate_limiter.requests_per_day - self.rate_limiter.daily_count
            }
        }

async def main():
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key-here")
    
    orchestrator = MainOrchestrator(api_key)
    
    await orchestrator.execute_workflow("daily_trading", {
        "symbols": ["AAPL", "GOOGL", "MSFT"],
        "timeframe": "1d",
        "mode": "paper"
    })
    
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    asyncio.run(main())