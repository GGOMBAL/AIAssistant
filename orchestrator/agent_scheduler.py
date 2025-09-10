import asyncio
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BATCH = "batch"
    ROUND_ROBIN = "round_robin"

class AgentTask:
    def __init__(self, agent_name: str, task_type: str, payload: Dict[str, Any], 
                 priority: int = 5, dependencies: List[str] = None):
        self.agent_name = agent_name
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = "pending"
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None

class AgentScheduler:
    def __init__(self, api_manager, max_concurrent: int = 3):
        self.api_manager = api_manager
        self.max_concurrent = max_concurrent
        self.agents = {}
        self.task_queue = asyncio.Queue()
        self.running_tasks = []
        self.completed_tasks = []
        self.execution_mode = ExecutionMode.BATCH
        
    def register_agent(self, agent_name: str, config: Dict[str, Any]):
        self.agents[agent_name] = {
            "config": config,
            "status": "idle",
            "last_run": None,
            "task_count": 0
        }
        logger.info(f"Registered agent: {agent_name}")
    
    async def schedule_task(self, task: AgentTask):
        await self.task_queue.put(task)
        logger.info(f"Scheduled task for {task.agent_name}: {task.task_type}")
    
    async def run_scheduler(self):
        logger.info(f"Starting scheduler in {self.execution_mode.value} mode")
        
        if self.execution_mode == ExecutionMode.PARALLEL:
            await self._run_parallel()
        elif self.execution_mode == ExecutionMode.BATCH:
            await self._run_batch()
        elif self.execution_mode == ExecutionMode.ROUND_ROBIN:
            await self._run_round_robin()
        else:
            await self._run_sequential()
    
    async def _run_parallel(self):
        tasks = []
        while not self.task_queue.empty() or tasks:
            while len(tasks) < self.max_concurrent and not self.task_queue.empty():
                task = await self.task_queue.get()
                if self._can_execute(task):
                    tasks.append(asyncio.create_task(self._execute_task(task)))
            
            if tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for completed in done:
                    result = await completed
                    logger.info(f"Task completed: {result}")
            else:
                await asyncio.sleep(0.1)
    
    async def _run_batch(self):
        batch_size = self.max_concurrent
        while not self.task_queue.empty():
            batch = []
            for _ in range(min(batch_size, self.task_queue.qsize())):
                task = await self.task_queue.get()
                if self._can_execute(task):
                    batch.append(task)
            
            if batch:
                results = await asyncio.gather(
                    *[self._execute_task(task) for task in batch]
                )
                logger.info(f"Batch completed: {len(results)} tasks")
            
            await asyncio.sleep(0.5)
    
    async def _run_round_robin(self):
        agent_queues = {name: [] for name in self.agents.keys()}
        
        while not self.task_queue.empty():
            task = await self.task_queue.get()
            agent_queues[task.agent_name].append(task)
        
        while any(agent_queues.values()):
            for agent_name, queue in agent_queues.items():
                if queue and self.agents[agent_name]["status"] == "idle":
                    task = queue.pop(0)
                    if self._can_execute(task):
                        asyncio.create_task(self._execute_task(task))
                        await asyncio.sleep(0.1)
    
    async def _run_sequential(self):
        while not self.task_queue.empty():
            task = await self.task_queue.get()
            if self._can_execute(task):
                await self._execute_task(task)
    
    def _can_execute(self, task: AgentTask) -> bool:
        for dep in task.dependencies:
            if not any(t.agent_name == dep and t.status == "completed" 
                      for t in self.completed_tasks):
                return False
        return True
    
    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        agent = self.agents[task.agent_name]
        agent["status"] = "running"
        agent["last_run"] = datetime.now()
        task.status = "running"
        
        try:
            result = await self.api_manager.add_request(
                agent_name=task.agent_name,
                request_data={
                    "task_type": task.task_type,
                    "payload": task.payload
                },
                priority=self._get_priority(task.priority)
            )
            
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
            agent["task_count"] += 1
            
        except Exception as e:
            logger.error(f"Task failed for {task.agent_name}: {e}")
            task.status = "failed"
            task.result = {"error": str(e)}
            
        finally:
            agent["status"] = "idle"
            
        return {
            "agent": task.agent_name,
            "task": task.task_type,
            "status": task.status,
            "duration": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None
        }
    
    def _get_priority(self, priority_value: int):
        from shared.api_manager import Priority
        if priority_value <= 3:
            return Priority.HIGH
        elif priority_value <= 6:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def get_agent_stats(self) -> Dict[str, Any]:
        return {
            agent_name: {
                "status": agent["status"],
                "task_count": agent["task_count"],
                "last_run": agent["last_run"].isoformat() if agent["last_run"] else None
            }
            for agent_name, agent in self.agents.items()
        }
    
    def set_execution_mode(self, mode: ExecutionMode):
        self.execution_mode = mode
        logger.info(f"Execution mode set to: {mode.value}")