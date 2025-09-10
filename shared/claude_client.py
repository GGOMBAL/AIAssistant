import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ClaudeAPIClient:
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", 
                 max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.session = None
        self.connection_pool = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, messages: List[Dict[str, str]], 
                          system_prompt: Optional[str] = None,
                          temperature: float = 0.7) -> Dict[str, Any]:
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": temperature
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return {"error": error_text, "status": response.status}
                    
        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}

class SharedClaudeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.clients = {}
        self.request_history = []
        
    def get_client(self, agent_name: str, model: str = None) -> ClaudeAPIClient:
        if agent_name not in self.clients:
            model = model or self._get_agent_model(agent_name)
            self.clients[agent_name] = ClaudeAPIClient(
                api_key=self.api_key,
                model=model
            )
        return self.clients[agent_name]
    
    def _get_agent_model(self, agent_name: str) -> str:
        model_mapping = {
            "strategy_agent": "claude-3-opus-20240229",
            "data_agent": "claude-3-opus-20240229",
            "service_agent": "claude-3-5-sonnet-20241022",
            "helper_agent": "claude-3-5-sonnet-20241022"
        }
        return model_mapping.get(agent_name, "claude-3-5-sonnet-20241022")
    
    async def send_agent_message(self, agent_name: str, messages: List[Dict[str, str]], 
                                 system_prompt: Optional[str] = None) -> Dict[str, Any]:
        client = self.get_client(agent_name)
        
        request_info = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        async with client as active_client:
            result = await active_client.send_message(messages, system_prompt)
            
        request_info["response"] = result
        self.request_history.append(request_info)
        
        return result
    
    def get_usage_stats(self) -> Dict[str, Any]:
        agent_usage = {}
        for request in self.request_history:
            agent = request["agent"]
            if agent not in agent_usage:
                agent_usage[agent] = {"count": 0, "errors": 0}
            
            agent_usage[agent]["count"] += 1
            if "error" in request.get("response", {}):
                agent_usage[agent]["errors"] += 1
        
        return {
            "total_requests": len(self.request_history),
            "agent_usage": agent_usage,
            "active_clients": list(self.clients.keys())
        }