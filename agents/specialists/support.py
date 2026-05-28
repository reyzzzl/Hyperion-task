from ..base import BaseAgent

class SupportAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Support Agent", expertise="customer support, tickets, faq", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "answer")
        if action == "answer":
            return await self._answer(task.get("description", ""), context)
        if action == "create_ticket":
            return await self._create_ticket(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _answer(self, query: str, context: dict) -> dict:
        prompt = f"As support agent, answer: {query}"
        ans = await self.think(prompt)
        return {"success": True, "data": {"answer": ans}}

    async def _create_ticket(self, params: dict, context: dict) -> dict:
        ticketing = self.integrations.get("ticketing")
        if ticketing:
            res = await ticketing.create_ticket(params.get("customer_email"), params.get("issue"))
            return {"success": True, "data": res}
        return {"success": True, "data": {"ticket_id": "mock", "status": "open"}}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As a Support expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}