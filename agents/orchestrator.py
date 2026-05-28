import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseAgent, get_shared_client
from .registry import AgentRegistry
from ..utils.logging import get_logger, get_correlation_id
from ..utils.metrics import metrics
from ..utils.shared_memory import SharedMemory
from ..utils.exceptions import HyperionException

try:
    from .prompts import CLASSIFICATION_PROMPT
except ImportError:
    CLASSIFICATION_PROMPT = """Classify the user request into one of these agent categories: {agents}
User request: {text}
Respond with ONLY the agent name (one word: {keys}).
If unsure, respond with 'executive'."""

logger = get_logger("AgentOrchestrator")

class AgentOrchestrator:
    def __init__(self, integrations: Dict[str, Any], workflow_executor=None):
        self.integrations = integrations
        self.workflow_executor = workflow_executor
        self.agents: Dict[str, BaseAgent] = {}
        self._shared_memory = SharedMemory()
        self._client = get_shared_client()
        self._running = True
        self._init_agents()
        self.routing_history: List[Dict] = []
        self._max_history = 1000

    def _init_agents(self):
        for name, agent_class in AgentRegistry.list().items():
            self.agents[name] = agent_class(self.integrations, workflow_executor=self.workflow_executor, shared_memory=self._shared_memory)
        exec_agent = self.agents.get("executive")
        if exec_agent and hasattr(exec_agent, "set_sub_agents"):
            exec_agent.set_sub_agents(list(self.agents.values()))

    async def route_task(self, task: Dict, context: Optional[Dict] = None) -> Dict:
        start = time.monotonic()
        correlation_id = get_correlation_id()
        if context is None:
            context = {}
        task_type = task.get("type", "")
        if task_type and task_type in self.agents:
            selected = self.agents[task_type]
        else:
            selected = await self._classify_intent(task.get("description", ""))
        if not selected:
            selected = self.agents.get("executive")
        logger.info(f"Routing to {selected.name}")
        selected.status = "working"
        result = None
        try:
            result = await selected.process(task, context)
            duration_ms = (time.monotonic() - start) * 1000
            metrics.timing("orchestrator_routing", duration_ms)
            metrics.counter_inc(f"orchestrator_routed_to_{selected.name}")
            return result
        except HyperionException as e:
            logger.error(f"Agent {selected.name} failed: {e}")
            metrics.counter_inc("orchestrator_errors")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.exception(f"Unexpected error in {selected.name}: {e}")
            metrics.counter_inc("orchestrator_errors")
            return {"success": False, "error": "Internal server error"}
        finally:
            selected.status = "idle"
            self.routing_history.append({
                "task": task,
                "agent": selected.name,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "correlation_id": correlation_id
            })
            if len(self.routing_history) > self._max_history:
                self.routing_history = self.routing_history[-self._max_history:]

    async def _classify_intent(self, text: str) -> Optional[BaseAgent]:
        if not text:
            return self.agents.get("executive")
        agent_keys = list(self.agents.keys())
        agent_names = [{"name": k, "expertise": self.agents[k].expertise} for k in agent_keys]
        prompt = CLASSIFICATION_PROMPT.format(
            agents=json.dumps(agent_names),
            text=text,
            keys=", ".join(agent_keys)
        )
        try:
            response = await self._client.generate(model=self._get_model(), prompt=prompt)
            result = (response.response if hasattr(response, 'response') else response.get('response', '')).strip().lower()
            for key in agent_keys:
                if key in result:
                    return self.agents.get(key)
        except Exception as e:
            logger.error(f"Classification error: {e}")
        return self.agents.get("executive")

    def _get_model(self) -> str:
        return os.environ.get("OLLAMA_MODEL", "mistral")

    async def broadcast(self, message: str, sender: str) -> List[Dict]:
        tasks = []
        for name, agent in self.agents.items():
            if name != sender:
                tasks.append(self._safe_process(agent, message, sender))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [{"agent": name, "result": r if not isinstance(r, Exception) else {"error": str(r)}}
                for name, r in zip([n for n in self.agents if n != sender], results)]

    async def _safe_process(self, agent: BaseAgent, message: str, sender: str):
        return await agent.process({"description": message, "type": "broadcast"}, {"sender": sender})

    async def health_check(self) -> Dict:
        agent_status = {}
        for name, agent in self.agents.items():
            agent_status[name] = {
                "status": agent.status,
                "tools": list(agent.tools.keys()),
                "credential_scope": list(agent._credential_scope)
            }
        return {
            "status": "healthy" if self._running else "shutting_down",
            "agents": agent_status,
            "total_agents": len(self.agents),
            "routing_history_count": len(self.routing_history)
        }

    def get_status(self) -> Dict:
        return {name: agent.to_dict() for name, agent in self.agents.items()}

    async def shutdown(self, timeout: float = 30.0):
        self._running = False
        logger.info("Shutting down orchestrator")
        await asyncio.gather(*[agent.close() for agent in self.agents.values()], return_exceptions=True)