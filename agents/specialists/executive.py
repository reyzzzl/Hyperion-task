import asyncio
import json
from typing import List

from ..base import BaseAgent
from ..prompts import DECISION_PROMPT

class ExecutiveAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Executive Agent", expertise="strategy, leadership, decision making", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor
        self.sub_agents: List[BaseAgent] = []

    def set_sub_agents(self, agents: List[BaseAgent]):
        self.sub_agents = [a for a in agents if a.name != self.name]

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "decide")
        if action == "decide":
            return await self._strategic_decision(task.get("description", ""), context)
        if action == "delegate":
            return await self._delegate(task.get("params", {}), context)
        if action == "plan":
            return await self._plan(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _strategic_decision(self, situation: str, context: dict) -> dict:
        advices = []
        async def consult(agent):
            try:
                resp = await agent.process({"description": f"Advise on: {situation}", "action": "advise"}, context)
                advices.append({"agent": agent.name, "advice": resp})
            except Exception as e:
                advices.append({"agent": agent.name, "error": str(e)})
        await asyncio.gather(*[consult(a) for a in self.sub_agents])
        prompt = DECISION_PROMPT.format(situation=situation, advices=json.dumps(advices))
        decision = await self.think(prompt)
        self.remember("last_decision", decision, shared=True)
        return {"success": True, "data": {"decision": decision, "consulted": advices}}

    async def _delegate(self, params: dict, context: dict) -> dict:
        agent_name = params.get("agent", "").lower()
        for agent in self.sub_agents:
            if agent_name in agent.name.lower():
                result = await agent.process({"description": params.get("task"), "action": params.get("action", "execute")}, context)
                return {"success": True, "data": {"delegated_to": agent.name, "result": result}}
        return {"success": False, "error": f"Agent {agent_name} not found"}

    async def _plan(self, description: str, context: dict) -> dict:
        prompt = f"Create business plan: {description}"
        plan = await self.think(prompt)
        return {"success": True, "data": {"plan": plan}}