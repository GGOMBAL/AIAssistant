import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MessageType(Enum):
    TASK = "task"
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    COLLABORATION = "collaboration"
    STATUS = "status"

@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    message_type: MessageType = MessageType.TASK
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    correlation_id: Optional[str] = None

class Agent:
    def __init__(self, name: str, capabilities: List[str], claude_client=None):
        self.name = name
        self.capabilities = capabilities
        self.claude_client = claude_client
        self.message_queue = asyncio.Queue()
        self.collaborators = {}
        self.status = "idle"
        self.current_task = None
        self.knowledge_base = {}
        
    async def receive_message(self, message: AgentMessage):
        await self.message_queue.put(message)
        logger.info(f"{self.name} received message from {message.sender}: {message.message_type.value}")
    
    async def process_messages(self):
        while True:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"{self.name} error processing message: {e}")
    
    async def _handle_message(self, message: AgentMessage):
        self.status = "processing"
        self.current_task = message.id
        
        if message.message_type == MessageType.TASK:
            result = await self._execute_task(message.content)
            if message.requires_response:
                await self._send_response(message, result)
                
        elif message.message_type == MessageType.QUERY:
            response = await self._handle_query(message.content)
            await self._send_response(message, response)
            
        elif message.message_type == MessageType.COLLABORATION:
            await self._collaborate(message)
            
        self.status = "idle"
        self.current_task = None
    
    async def _execute_task(self, task_content: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_content.get("type")
        
        if self.claude_client:
            prompt = self._build_task_prompt(task_content)
            response = await self.claude_client.send_agent_message(
                agent_name=self.name,
                messages=[{"role": "user", "content": prompt}]
            )
            return {"result": response, "task_type": task_type}
        
        return {"result": f"{self.name} completed task: {task_type}"}
    
    async def _handle_query(self, query_content: Dict[str, Any]) -> Dict[str, Any]:
        query_type = query_content.get("type")
        
        if query_type == "capabilities":
            return {"capabilities": self.capabilities}
        elif query_type == "status":
            return {"status": self.status, "current_task": self.current_task}
        elif query_type == "knowledge":
            topic = query_content.get("topic")
            return {"knowledge": self.knowledge_base.get(topic, "No knowledge on this topic")}
        
        return {"response": f"{self.name} processed query: {query_type}"}
    
    async def _collaborate(self, message: AgentMessage):
        collab_type = message.content.get("type")
        
        if collab_type == "share_knowledge":
            topic = message.content.get("topic")
            knowledge = message.content.get("knowledge")
            self.knowledge_base[topic] = knowledge
            logger.info(f"{self.name} learned about {topic} from {message.sender}")
            
        elif collab_type == "request_assistance":
            task = message.content.get("task")
            if self._can_assist(task):
                result = await self._execute_task(task)
                await self._send_response(message, result)
    
    async def _send_response(self, original_message: AgentMessage, response: Dict[str, Any]):
        response_message = AgentMessage(
            sender=self.name,
            recipient=original_message.sender,
            message_type=MessageType.RESPONSE,
            content=response,
            correlation_id=original_message.id
        )
        
        if original_message.sender in self.collaborators:
            await self.collaborators[original_message.sender].receive_message(response_message)
    
    def _build_task_prompt(self, task_content: Dict[str, Any]) -> str:
        return f"""
Task Type: {task_content.get('type')}
Parameters: {json.dumps(task_content.get('parameters', {}), indent=2)}
Context: {task_content.get('context', 'No additional context')}

Please complete this task and provide a structured response.
"""
    
    def _can_assist(self, task: Dict[str, Any]) -> bool:
        required_capabilities = task.get("required_capabilities", [])
        return any(cap in self.capabilities for cap in required_capabilities)
    
    def add_collaborator(self, agent):
        self.collaborators[agent.name] = agent
        logger.info(f"{self.name} added collaborator: {agent.name}")

class MultiAgentOrchestrator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.agents = {}
        self.message_broker = MessageBroker()
        self.task_queue = asyncio.Queue()
        self._initialize_agents()
        
    def _initialize_agents(self):
        agent_configs = {
            "data_agent": {
                "capabilities": ["data_gathering", "indicator_calculation", "data_validation", "data_transformation", "market_scanning", "database_read_only"],
                "role": "Data gathering service and indicator management. Database read-only access for technical indicators."
            },
            "strategy_agent": {
                "capabilities": ["signal_generation", "position_sizing", "strategy_optimization", "risk_analysis", "portfolio_optimization"],
                "role": "Trading strategy development and signal generation"
            },
            "service_agent": {
                "capabilities": ["backtesting", "trade_execution", "position_management", "database_management", "risk_control"],
                "role": "Backtesting, trading, and database services"
            },
            "helper_agent": {
                "capabilities": ["broker_api", "external_data_api", "api_rate_limiting", "webhook_management"],
                "role": "External API and broker connections"
            }
        }
        
        for agent_name, config in agent_configs.items():
            agent = Agent(agent_name, config["capabilities"])
            self.agents[agent_name] = agent
            self.message_broker.register_agent(agent)
            
        self._establish_collaborations()
    
    def _establish_collaborations(self):
        collaborations = {
            "data_agent": ["strategy_agent", "service_agent", "helper_agent"],
            "strategy_agent": ["data_agent", "service_agent"],
            "service_agent": ["data_agent", "strategy_agent", "helper_agent"],
            "helper_agent": ["data_agent", "service_agent"]
        }
        
        for agent_name, collaborator_names in collaborations.items():
            agent = self.agents[agent_name]
            for collab_name in collaborator_names:
                if collab_name in self.agents:
                    agent.add_collaborator(self.agents[collab_name])
    
    async def delegate_task(self, task_description: str, context: Dict[str, Any] = None):
        best_agent = self._select_best_agent(task_description, context)
        
        if not best_agent:
            logger.error(f"No suitable agent found for task: {task_description}")
            return None
        
        message = AgentMessage(
            sender="orchestrator",
            recipient=best_agent.name,
            message_type=MessageType.TASK,
            content={
                "type": "delegated_task",
                "description": task_description,
                "context": context or {},
                "parameters": {}
            },
            requires_response=True
        )
        
        await best_agent.receive_message(message)
        return f"Task delegated to {best_agent.name}"
    
    def _select_best_agent(self, task_description: str, context: Dict[str, Any] = None) -> Optional[Agent]:
        task_keywords = {
            "strategy": ["strategy_agent"],
            "signal": ["strategy_agent"],
            "data": ["data_agent"],
            "indicator": ["data_agent"],
            "gather": ["data_agent"],
            "trade": ["service_agent"],
            "execute": ["service_agent"],
            "backtest": ["service_agent"],
            "test": ["service_agent"],
            "database": ["service_agent"],
            "api": ["helper_agent"],
            "broker": ["helper_agent"],
            "external": ["helper_agent"]
        }
        
        task_lower = task_description.lower()
        candidates = []
        
        for keyword, agent_names in task_keywords.items():
            if keyword in task_lower:
                for agent_name in agent_names:
                    if agent_name in self.agents:
                        candidates.append(self.agents[agent_name])
        
        if candidates:
            return candidates[0]
        
        return self.agents.get("data_agent")
    
    async def coordinate_workflow(self, workflow: Dict[str, Any]):
        workflow_type = workflow.get("type")
        steps = workflow.get("steps", [])
        
        results = []
        for step in steps:
            agent_name = step.get("agent")
            task = step.get("task")
            dependencies = step.get("dependencies", [])
            
            if dependencies:
                await self._wait_for_dependencies(dependencies, results)
            
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                message = AgentMessage(
                    sender="orchestrator",
                    recipient=agent_name,
                    message_type=MessageType.TASK,
                    content=task,
                    requires_response=True
                )
                
                await agent.receive_message(message)
                results.append({"step": step.get("name"), "agent": agent_name, "status": "initiated"})
        
        return results
    
    async def _wait_for_dependencies(self, dependencies: List[str], results: List[Dict]):
        for dep in dependencies:
            while not any(r.get("step") == dep and r.get("status") == "completed" for r in results):
                await asyncio.sleep(0.1)
    
    async def broadcast_notification(self, notification: Dict[str, Any]):
        message = AgentMessage(
            sender="orchestrator",
            recipient="all",
            message_type=MessageType.NOTIFICATION,
            content=notification
        )
        
        await self.message_broker.broadcast(message)
    
    async def start_agents(self):
        tasks = []
        for agent in self.agents.values():
            tasks.append(asyncio.create_task(agent.process_messages()))
        
        await asyncio.gather(*tasks)

class MessageBroker:
    def __init__(self):
        self.agents = []
        self.message_history = []
        self.topics = {}
        
    def register_agent(self, agent: Agent):
        self.agents.append(agent)
        logger.info(f"Registered agent: {agent.name}")
    
    async def broadcast(self, message: AgentMessage):
        self.message_history.append(message)
        
        for agent in self.agents:
            if agent.name != message.sender:
                await agent.receive_message(message)
    
    async def publish_to_topic(self, topic: str, message: AgentMessage):
        if topic not in self.topics:
            self.topics[topic] = []
        
        subscribers = self.topics[topic]
        for agent in subscribers:
            await agent.receive_message(message)
    
    def subscribe_to_topic(self, topic: str, agent: Agent):
        if topic not in self.topics:
            self.topics[topic] = []
        
        if agent not in self.topics[topic]:
            self.topics[topic].append(agent)
            logger.info(f"{agent.name} subscribed to topic: {topic}")