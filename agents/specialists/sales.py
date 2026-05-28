from ..base import BaseAgent

class SalesAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Sales Agent", expertise="sales, crm, lead management, pipeline", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor
        self._register_tools()

    def _register_tools(self):
        if self.integrations.get("hubspot"):
            self.register_tool("hubspot_create_contact", self._hubspot_create_contact)

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "qualify")
        if action == "qualify_lead":
            return await self._qualify_lead(task.get("description", ""), context)
        if action == "create_lead":
            return await self._create_lead(task.get("params", {}), context)
        if action == "update_pipeline":
            return await self._update_pipeline(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _qualify_lead(self, desc: str, context: dict) -> dict:
        prompt = f"Qualify lead using BANT: {desc}\nReturn JSON: score, qualification, next_steps."
        result = await self.think(prompt)
        return {"success": True, "data": {"qualification": result}}

    async def _create_lead(self, params: dict, context: dict) -> dict:
        hubspot = self.integrations.get("hubspot")
        if hubspot:
            res = await hubspot.create_contact(params.get("email"), params.get("name"), params.get("company"))
            return {"success": True, "data": res}
        return {"success": True, "data": {"lead_id": "mock", "status": "created"}}

    async def _update_pipeline(self, params: dict, context: dict) -> dict:
        return {"success": True, "data": {"updated": True}}

    async def _hubspot_create_contact(self, params: dict) -> dict:
        hubspot = self.integrations.get("hubspot")
        if not hubspot:
            return {"success": False, "error": "HubSpot integration missing"}
        return await hubspot.create_contact(params["email"], params.get("name"), params.get("company"))

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As a Sales expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}