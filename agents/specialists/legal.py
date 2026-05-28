from ..base import BaseAgent

class LegalAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Legal Agent", expertise="legal, compliance, contracts", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "review")
        if action == "review_contract":
            return await self._review(task.get("description", ""), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _review(self, contract: str, context: dict) -> dict:
        prompt = f"Review contract for risks: {contract}"
        review = await self.think(prompt)
        return {"success": True, "data": {"review": review}}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As a Legal expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}