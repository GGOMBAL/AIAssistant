import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CollaborationType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel" 
    HIERARCHICAL = "hierarchical"
    CONSENSUS = "consensus"
    DELEGATION = "delegation"

@dataclass
class CollaborationTask:
    id: str
    name: str
    description: str
    required_agents: List[str]
    collaboration_type: CollaborationType
    parameters: Dict[str, Any]
    dependencies: List[str]
    created_at: datetime
    status: str = "pending"
    results: Dict[str, Any] = None

class CollaborationFramework:
    def __init__(self):
        self.active_collaborations = {}
        self.collaboration_history = []
        self.agent_roles = {}
        self.shared_memory = {}
        
    def define_agent_roles(self, roles: Dict[str, Dict[str, Any]]):
        self.agent_roles = roles
        logger.info(f"Defined roles for {len(roles)} agents")
    
    async def initiate_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Initiating {task.collaboration_type.value} collaboration: {task.name}")
        
        self.active_collaborations[task.id] = {
            "task": task,
            "agents": task.required_agents,
            "start_time": datetime.now(),
            "status": "active"
        }
        
        if task.collaboration_type == CollaborationType.SEQUENTIAL:
            result = await self._sequential_collaboration(task, agents)
        elif task.collaboration_type == CollaborationType.PARALLEL:
            result = await self._parallel_collaboration(task, agents)
        elif task.collaboration_type == CollaborationType.HIERARCHICAL:
            result = await self._hierarchical_collaboration(task, agents)
        elif task.collaboration_type == CollaborationType.CONSENSUS:
            result = await self._consensus_collaboration(task, agents)
        elif task.collaboration_type == CollaborationType.DELEGATION:
            result = await self._delegation_collaboration(task, agents)
        else:
            result = {"error": f"Unknown collaboration type: {task.collaboration_type}"}
        
        self.active_collaborations[task.id]["status"] = "completed"
        self.active_collaborations[task.id]["end_time"] = datetime.now()
        self.collaboration_history.append(self.active_collaborations[task.id])
        
        return result
    
    async def _sequential_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        previous_output = None
        
        for agent_name in task.required_agents:
            if agent_name not in agents:
                logger.error(f"Agent {agent_name} not found")
                continue
            
            agent = agents[agent_name]
            
            input_data = {
                "task": task.description,
                "parameters": task.parameters,
                "previous_output": previous_output
            }
            
            agent_result = await self._execute_agent_task(agent, input_data)
            results[agent_name] = agent_result
            previous_output = agent_result
            
            self._update_shared_memory(task.id, agent_name, agent_result)
        
        return {
            "collaboration_type": "sequential",
            "task_id": task.id,
            "results": results,
            "final_output": previous_output
        }
    
    async def _parallel_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        tasks = []
        
        for agent_name in task.required_agents:
            if agent_name not in agents:
                continue
            
            agent = agents[agent_name]
            input_data = {
                "task": task.description,
                "parameters": task.parameters
            }
            
            tasks.append(self._execute_agent_task(agent, input_data))
        
        results = await asyncio.gather(*tasks)
        
        agent_results = {
            task.required_agents[i]: results[i] 
            for i in range(len(results))
        }
        
        return {
            "collaboration_type": "parallel",
            "task_id": task.id,
            "results": agent_results,
            "aggregated_output": self._aggregate_results(results)
        }
    
    async def _hierarchical_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        lead_agent = task.parameters.get("lead_agent")
        subordinate_agents = [a for a in task.required_agents if a != lead_agent]
        
        subordinate_tasks = []
        for agent_name in subordinate_agents:
            if agent_name in agents:
                input_data = {
                    "task": task.description,
                    "role": "subordinate",
                    "parameters": task.parameters
                }
                subordinate_tasks.append(self._execute_agent_task(agents[agent_name], input_data))
        
        subordinate_results = await asyncio.gather(*subordinate_tasks)
        
        if lead_agent in agents:
            lead_input = {
                "task": task.description,
                "role": "lead",
                "subordinate_results": subordinate_results,
                "parameters": task.parameters
            }
            final_result = await self._execute_agent_task(agents[lead_agent], lead_input)
        else:
            final_result = {"error": "Lead agent not found"}
        
        return {
            "collaboration_type": "hierarchical",
            "task_id": task.id,
            "lead_agent": lead_agent,
            "subordinate_results": dict(zip(subordinate_agents, subordinate_results)),
            "final_result": final_result
        }
    
    async def _consensus_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        proposals = {}
        
        for agent_name in task.required_agents:
            if agent_name not in agents:
                continue
            
            agent = agents[agent_name]
            input_data = {
                "task": task.description,
                "parameters": task.parameters,
                "mode": "propose"
            }
            
            proposal = await self._execute_agent_task(agent, input_data)
            proposals[agent_name] = proposal
        
        consensus_round = 0
        max_rounds = task.parameters.get("max_consensus_rounds", 3)
        consensus_reached = False
        
        while consensus_round < max_rounds and not consensus_reached:
            votes = {}
            
            for agent_name in task.required_agents:
                if agent_name not in agents:
                    continue
                
                vote_input = {
                    "proposals": proposals,
                    "mode": "vote",
                    "round": consensus_round
                }
                
                vote = await self._execute_agent_task(agents[agent_name], vote_input)
                votes[agent_name] = vote
            
            consensus_reached = self._check_consensus(votes)
            consensus_round += 1
        
        return {
            "collaboration_type": "consensus",
            "task_id": task.id,
            "proposals": proposals,
            "final_votes": votes,
            "consensus_reached": consensus_reached,
            "rounds": consensus_round
        }
    
    async def _delegation_collaboration(self, task: CollaborationTask, agents: Dict[str, Any]) -> Dict[str, Any]:
        delegator = task.parameters.get("delegator")
        
        if delegator not in agents:
            return {"error": f"Delegator {delegator} not found"}
        
        delegation_plan = await self._execute_agent_task(
            agents[delegator],
            {
                "task": task.description,
                "available_agents": [a for a in task.required_agents if a != delegator],
                "mode": "plan_delegation"
            }
        )
        
        delegated_tasks = delegation_plan.get("delegated_tasks", [])
        delegation_results = {}
        
        for delegated_task in delegated_tasks:
            agent_name = delegated_task.get("agent")
            subtask = delegated_task.get("subtask")
            
            if agent_name in agents:
                result = await self._execute_agent_task(
                    agents[agent_name],
                    {"task": subtask, "delegated_by": delegator}
                )
                delegation_results[agent_name] = result
        
        final_integration = await self._execute_agent_task(
            agents[delegator],
            {
                "mode": "integrate_results",
                "delegation_results": delegation_results
            }
        )
        
        return {
            "collaboration_type": "delegation",
            "task_id": task.id,
            "delegator": delegator,
            "delegation_plan": delegation_plan,
            "delegation_results": delegation_results,
            "final_integration": final_integration
        }
    
    async def _execute_agent_task(self, agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from shared.multi_agent_system import AgentMessage, MessageType
        
        message = AgentMessage(
            sender="collaboration_framework",
            recipient=agent.name,
            message_type=MessageType.TASK,
            content=input_data,
            requires_response=True
        )
        
        await agent.receive_message(message)
        
        await asyncio.sleep(0.1)
        
        return {
            "agent": agent.name,
            "result": f"Processed: {input_data.get('task', 'Unknown task')}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _update_shared_memory(self, task_id: str, agent_name: str, result: Any):
        if task_id not in self.shared_memory:
            self.shared_memory[task_id] = {}
        
        self.shared_memory[task_id][agent_name] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "aggregated_at": datetime.now().isoformat(),
            "num_results": len(results),
            "results_summary": [r.get("result", "No result") for r in results]
        }
    
    def _check_consensus(self, votes: Dict[str, Any]) -> bool:
        if not votes:
            return False
        
        vote_values = list(votes.values())
        if all(v == vote_values[0] for v in vote_values):
            return True
        
        return False
    
    def get_collaboration_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.active_collaborations.get(task_id)
    
    def get_shared_memory(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.shared_memory.get(task_id)