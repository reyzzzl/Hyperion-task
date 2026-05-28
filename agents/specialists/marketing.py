from ..base import BaseAgent

class MarketingAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Marketing Agent", expertise="marketing, campaigns, social media, email, seo, content", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor
        self._register_tools()

    def _register_tools(self):
        if self.integrations.get("google"):
            self.register_tool("google_sheets_write", self._sheets_write)
        if self.integrations.get("email"):
            self.register_tool("send_email", self._send_email)

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "analyze")
        if action == "create_campaign":
            return await self._create_campaign(task.get("description", ""), context)
        if action == "send_newsletter":
            return await self._send_newsletter(task.get("params", {}), context)
        if action == "run_workflow":
            return await self._run_workflow(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _create_campaign(self, description: str, context: dict) -> dict:
        prompt = f"Create a marketing campaign plan for: {description}\nReturn JSON with: name, audience, channels, budget, timeline, kpis."
        plan = await self.think(prompt)
        return {"success": True, "data": {"campaign_plan": plan}}

    async def _send_newsletter(self, params: dict, context: dict) -> dict:
        email = self.integrations.get("email")
        if not email:
            return {"success": False, "error": "No email integration"}
        result = await email.send_email(params.get("to"), params.get("subject"), params.get("content"))
        if isinstance(result, dict) and result.get("success"):
            return {"success": True, "data": result}
        return {"success": False, "error": result.get("error", "Email send failed")}

    async def _sheets_write(self, params: dict) -> dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration missing"}
        return await gs.sheets_operation(params["spreadsheet_id"], params["range"], params.get("values"), "write")

    async def _send_email(self, params: dict) -> dict:
        email = self.integrations.get("email")
        if not email:
            return {"success": False, "error": "No email integration"}
        return await email.send_email(params["to"], params["subject"], params["body"])

    async def _run_workflow(self, params: dict, context: dict) -> dict:
        if not self.workflow_executor:
            return {"success": False, "error": "Workflow executor not available"}
        workflow_id = params.get("workflow_id")
        input_data = params.get("input", {})
        if not workflow_id:
            return {"success": False, "error": "Missing workflow_id"}
        try:
            result = await self.workflow_executor.execute_workflow_by_id(workflow_id, input_data)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As a Marketing expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}