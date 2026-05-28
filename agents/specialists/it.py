from ..base import BaseAgent

class ITAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="IT Agent", expertise="it, infrastructure, security", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "diagnose")
        if action == "diagnose":
            return await self._diagnose(task.get("description", ""), context)
        if action == "automate":
            return await self._automate(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _diagnose(self, issue: str, context: dict) -> dict:
        prompt = f"Diagnose IT issue: {issue}"
        diag = await self.think(prompt)
        return {"success": True, "data": {"diagnosis": diag}}

    async def _automate(self, params: dict, context: dict) -> dict:
        return {"success": True, "data": {"plan": "Automation plan mock"}}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As an IT expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}