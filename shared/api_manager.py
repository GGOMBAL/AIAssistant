import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from queue import PriorityQueue
import logging

logger = logging.getLogger(__name__)

class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class APIRequest:
    agent_name: str
    priority: Priority
    request_data: Dict[Any, Any]
    timestamp: float
    callback: Optional[callable] = None
    
    def __lt__(self, other):
        return (self.priority.value, self.timestamp) < (other.priority.value, other.timestamp)

class APIRateLimiter:
    def __init__(self, requests_per_minute: int = 30, requests_per_day: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_window = []
        self.daily_count = 0
        self.last_reset = time.time()
        
    def can_make_request(self) -> bool:
        current_time = time.time()
        
        if current_time - self.last_reset > 86400:
            self.daily_count = 0
            self.last_reset = current_time
            
        self.minute_window = [t for t in self.minute_window if current_time - t < 60]
        
        if len(self.minute_window) >= self.requests_per_minute:
            return False
        
        if self.daily_count >= self.requests_per_day:
            return False
            
        return True
    
    def record_request(self):
        current_time = time.time()
        self.minute_window.append(current_time)
        self.daily_count += 1

class SharedAPIManager:
    def __init__(self, api_key: str, rate_limiter: APIRateLimiter = None):
        self.api_key = api_key
        self.rate_limiter = rate_limiter or APIRateLimiter()
        self.request_queue = PriorityQueue()
        self.processing = False
        self.agent_stats = {}
        
    async def add_request(self, agent_name: str, request_data: Dict, 
                          priority: Priority = Priority.MEDIUM) -> Any:
        request = APIRequest(
            agent_name=agent_name,
            priority=priority,
            request_data=request_data,
            timestamp=time.time()
        )
        
        self.request_queue.put(request)
        
        if not self.processing:
            asyncio.create_task(self._process_queue())
            
        future = asyncio.Future()
        request.callback = lambda result: future.set_result(result)
        return await future
    
    async def _process_queue(self):
        self.processing = True
        
        while not self.request_queue.empty():
            if not self.rate_limiter.can_make_request():
                await asyncio.sleep(1)
                continue
                
            request = self.request_queue.get()
            
            try:
                result = await self._execute_api_call(request)
                self.rate_limiter.record_request()
                self._update_stats(request.agent_name, success=True)
                
                if request.callback:
                    request.callback(result)
                    
            except Exception as e:
                logger.error(f"API call failed for {request.agent_name}: {e}")
                self._update_stats(request.agent_name, success=False)
                
                if request.callback:
                    request.callback(None)
                    
        self.processing = False
    
    async def _execute_api_call(self, request: APIRequest) -> Any:
        await asyncio.sleep(0.1)
        
        return {
            "agent": request.agent_name,
            "data": request.request_data,
            "timestamp": time.time()
        }
    
    def _update_stats(self, agent_name: str, success: bool):
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {"success": 0, "failed": 0}
            
        if success:
            self.agent_stats[agent_name]["success"] += 1
        else:
            self.agent_stats[agent_name]["failed"] += 1
    
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        return self.agent_stats