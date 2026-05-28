from ..base import BaseAgent

class HRAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="HR Agent", expertise="human resources, recruitment, onboarding", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "advise")
        if action == "recruit":
            return await self._recruit(task.get("description", ""), context)
        if action == "onboard":
            return await self._onboard(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _recruit(self, desc: str, context: dict) -> dict:
        prompt = f"Create recruitment plan for: {desc}"
        plan = await self.think(prompt)
        return {"success": True, "data": {"plan": plan}}

    async def _onboard(self, params: dict, context: dict) -> dict:
        prompt = f"Create onboarding checklist for {params.get('name')} as {params.get('role')}"
        checklist = await self.think(prompt)
        return {"success": True, "data": {"checklist": checklist}}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As an HR expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}