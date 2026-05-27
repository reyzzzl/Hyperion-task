import asyncio
import os
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.metrics import metrics
from ..utils.rate_limiter import RateLimiter
from ..utils.circuit_breaker import CircuitBreaker, CircuitOpenError
from ..utils.retry import retry
from ..utils.exceptions import RateLimitExceeded, LLMTimeoutError

_shared_client = None

def get_shared_client():
    global _shared_client
    if _shared_client is None:
        import ollama
        _shared_client = ollama.AsyncClient()
    return _shared_client

class BaseAgent(ABC):
    def __init__(self, name: str, expertise: str, model: str = None, shared_memory: Dict = None):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.expertise = expertise
        self.model = model or os.environ.get("OLLAMA_MODEL", "mistral")
        self.memory: List[Dict] = []
        self.tools: Dict[str, Any] = {}
        self.status = "idle"
        self._client = get_shared_client()
        self._shared_memory = shared_memory if shared_memory is not None else {}
        self._rate_limiter = RateLimiter(default_rate=5, default_capacity=10)
        self._circuit_breaker = CircuitBreaker(name=f"llm_{name}", failure_threshold=3, recovery_timeout=60)
        self._credential_scope = set()
        self._logger = get_logger(f"Agent.{name}")

    def grant_credential(self, credential_name: str):
        self._credential_scope.add(credential_name)

    def has_credential(self, credential_name: str) -> bool:
        return credential_name in self._credential_scope

    @retry(exceptions=(LLMTimeoutError,), max_attempts=2, delay=1.0)
    async def think(self, prompt: str, timeout: int = 30) -> str:
        start = time.monotonic()
        async def _call():
            try:
                return await asyncio.wait_for(
                    self._client.generate(model=self.model, prompt=prompt),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise LLMTimeoutError(f"LLM timeout after {timeout}s")
        try:
            if not await self._rate_limiter.wait_and_acquire(f"agent_{self.name}", max_wait=2):
                metrics.counter_inc(f"agent_{self.name}_rate_limited")
                raise RateLimitExceeded(f"Rate limit exceeded for {self.name}")
            response = await self._circuit_breaker.call(_call)
            duration_ms = (time.monotonic() - start) * 1000
            metrics.timing(f"agent_{self.name}_llm", duration_ms)
            self._logger.debug(f"LLM call completed in {duration_ms:.2f}ms")
            if hasattr(response, 'response'):
                return response.response
            return response.get('response', '')
        except CircuitOpenError as e:
            self._logger.error(f"Circuit breaker open for {self.name}: {e}")
            metrics.counter_inc(f"agent_{self.name}_circuit_open")
            return ""
        except Exception as e:
            self._logger.error(f"LLM error: {e}", exc_info=True)
            metrics.counter_inc(f"agent_{self.name}_llm_error")
            raise

    def remember(self, key: str, value: Any, shared: bool = False):
        if shared:
            self._shared_memory[key] = value
        else:
            self.memory.append({"key": key, "value": value, "timestamp": datetime.now().isoformat()})

    def recall(self, key: str, from_shared: bool = False) -> Optional[Any]:
        if from_shared:
            return self._shared_memory.get(key)
        for item in reversed(self.memory):
            if item["key"] == key:
                return item["value"]
        return None

    async def use_tool(self, name: str, params: Dict) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in agent {self.name}")
        return await self.tools[name](params)

    def register_tool(self, name: str, handler: Any):
        self.tools[name] = handler

    async def _fallback(self, task: Dict, context: Dict) -> Dict:
        prompt = f"As a {self.name} expert, handle: {task.get('description', '')}\nReturn JSON with 'response'."
        result = await self.think(prompt)
        return {"success": True, "data": {"response": result}}

    @abstractmethod
    async def process(self, task: Dict, context: Dict) -> Dict:
        pass

    async def close(self):
        pass

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "expertise": self.expertise,
            "status": self.status,
            "tools": list(self.tools.keys())
        }