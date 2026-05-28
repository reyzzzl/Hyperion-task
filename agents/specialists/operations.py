from ..base import BaseAgent

class OperationsAgent(BaseAgent):
    def __init__(self, integrations: dict, workflow_executor=None, shared_memory: dict = None):
        super().__init__(name="Operations Agent", expertise="operations, logistics, inventory", shared_memory=shared_memory)
        self.integrations = integrations
        self.workflow_executor = workflow_executor

    async def process(self, task: dict, context: dict) -> dict:
        action = task.get("action", "check")
        if action == "check_inventory":
            return await self._check_inventory(task.get("params", {}), context)
        if action == "update_inventory":
            return await self._update_inventory(task.get("params", {}), context)
        if action == "advise":
            return await self._advise(task.get("description", ""), context)
        return await self._fallback(task, context)

    async def _check_inventory(self, params: dict, context: dict) -> dict:
        erp = self.integrations.get("erp")
        if not erp:
            return {"success": False, "error": "ERP integration not configured"}
        item_id = params.get("item_id")
        if not item_id:
            return {"success": False, "error": "Missing item_id"}
        try:
            result = await erp.get_inventory(item_id)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_inventory(self, params: dict, context: dict) -> dict:
        erp = self.integrations.get("erp")
        if not erp:
            return {"success": False, "error": "ERP integration not configured"}
        item_id = params.get("item_id")
        change = params.get("change", 0)
        if not item_id:
            return {"success": False, "error": "Missing item_id"}
        try:
            result = await erp.manage_inventory(item_id, change)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _advise(self, topic: str, context: dict) -> dict:
        prompt = f"As an Operations expert, provide strategic advice on: {topic}"
        advice = await self.think(prompt)
        return {"success": True, "data": {"advice": advice}}