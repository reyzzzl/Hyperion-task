from ..base import BaseAgent

class FinanceAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Finance Agent", expertise="finance, accounting, budgeting", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "analyze")
        if action == "create_invoice":
            return await self._create_invoice(task.get("params", {}), context)
        if action == "forecast":
            return await self._forecast(task.get("description", ""), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _create_invoice(self, params: dict, context: dict) -> dict:
        accounting = self.integrations.get("accounting")
        if accounting:
            res = await accounting.create_invoice(params.get("customer"), params.get("amount"), params.get("items", []))
            return {"success": True, "data": res}
        return {"success": True, "data": {"invoice_id": "mock", "amount": params.get("amount")}}

    async def _forecast(self, desc: str, context: dict) -> dict:
        prompt = f"Create budget forecast: {desc}"
        res = await self.think(prompt)
        return {"success": True, "data": {"forecast": res}}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As a Finance expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}