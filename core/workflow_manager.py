import asyncio
import logging
from typing import Any, Dict, Optional, Set

from .workflow_engine import Workflow, WorkflowNode, WorkflowExecutor, TriggerType, ActionType
from .nlu_engine import NLUEngine
from ..database.sqlite import TaskDatabase

logger = logging.getLogger("WorkflowManager")


class WorkflowManager:
    def __init__(self, db: TaskDatabase, integrations: Dict[str, Any]):
        self.db = db
        self.executor = WorkflowExecutor(db, integrations)
        self.nlu = NLUEngine()
        self.workflow_queue = asyncio.Queue()
        self.active_workflows: Dict[str, Workflow] = {}
        self.integrations = integrations
        self._running = True
        self._running_tasks: Set[asyncio.Task] = set()

    def create_workflow_from_json(self, definition: Dict) -> Workflow:
        workflow = Workflow(
            name=definition.get("name", "Unnamed Workflow"),
            description=definition.get("description", ""),
            trigger=TriggerType(definition.get("trigger", "manual")),
            trigger_config=definition.get("trigger_config", {})
        )
        nodes_list = definition.get("nodes", [])
        if not nodes_list:
            raise ValueError("Workflow definition must contain at least one node.")
        node_map = {}
        for node_data in nodes_list:
            node = WorkflowNode(
                action_type=ActionType(node_data["action_type"]),
                config=node_data.get("config", {}),
                next_node=node_data.get("next_node"),
                on_error=node_data.get("on_error"),
                retry_count=node_data.get("retry_count", 3),
                timeout_seconds=node_data.get("timeout_seconds", 30),
                temp_id=node_data.get("temp_id"),
            )
            workflow.nodes[node.node_id] = node
            node_map[node_data.get("temp_id", node.node_id)] = node.node_id
        for node_data in nodes_list:
            current_temp_id = node_data.get("temp_id")
            if current_temp_id and current_temp_id in node_map:
                current_id = node_map[current_temp_id]
                if node_data.get("next_node") and node_data["next_node"] in node_map:
                    workflow.nodes[current_id].next_node = node_map[node_data["next_node"]]
                if node_data.get("on_error") and node_data["on_error"] in node_map:
                    workflow.nodes[current_id].on_error = node_map[node_data["on_error"]]
        start_temp_id = definition.get("start_node")
        if not start_temp_id:
            raise ValueError("Workflow definition must include 'start_node'")
        if start_temp_id not in node_map:
            raise ValueError(f"Start node with temp_id '{start_temp_id}' not found in workflow definition.")
        workflow.start_node = node_map[start_temp_id]
        self.active_workflows[workflow.workflow_id] = workflow
        return workflow

    async def handle_event(self, event_type: str, data: Dict):
        if event_type == "customer_email":
            user_input = f"Email from {data.get('from')} with subject: {data.get('subject')}"
            intent = await self.nlu.parse_intent(user_input)
            if intent["intent"] == "check_status":
                order_id = intent["params"].get("order_id")
                if not order_id or not isinstance(order_id, str) or len(order_id) > 50 or not order_id.strip():
                    logger.warning(f"Invalid or missing order_id from email: {order_id}")
                    return
                workflow_def = {
                    "name": f"Auto-Reply to {data.get('from')}",
                    "description": "Automated status check workflow",
                    "trigger": "email",
                    "nodes": [
                        {
                            "temp_id": "query_node",
                            "action_type": "database_query",
                            "config": {
                                "query": "SELECT status FROM orders WHERE order_id = :order_id",
                                "params": {"order_id": order_id}
                            },
                            "next_node": "send_email_node"
                        },
                        {
                            "temp_id": "send_email_node",
                            "action_type": "send_email",
                            "config": {
                                "to": data.get("from"),
                                "subject": "Re: " + data.get("subject", ""),
                                "body": "Your order status is: {{node_outputs.query_node.0.status}}"
                            }
                        }
                    ],
                    "start_node": "query_node"
                }
                workflow = self.create_workflow_from_json(workflow_def)
                await self.workflow_queue.put(workflow)

    async def _email_polling_loop(self, interval: int = 30):
        email_service = self.integrations.get("email")
        if not email_service:
            logger.info("Email polling disabled: no email integration")
            return
        while self._running:
            try:
                emails = await email_service.read_emails(query="is:unread", max_results=5)
                for email in emails:
                    logger.info(f"Processing email from {email.get('from')}")
                    await self.handle_event("customer_email", email)
                    await email_service.mark_as_read(email["id"])
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Email polling error: {e}")
                await asyncio.sleep(interval)

    async def start(self):
        logger.info("Workflow Manager started")
        asyncio.create_task(self._email_polling_loop())
        while self._running:
            try:
                workflow = await asyncio.wait_for(self.workflow_queue.get(), timeout=1.0)
                task = asyncio.create_task(self._execute_workflow(workflow))
                self._running_tasks.add(task)
                task.add_done_callback(self._running_tasks.discard)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Workflow queue error: {e}")

    async def _execute_workflow(self, workflow: Workflow):
        try:
            result = await self.executor.execute_workflow(workflow, {})
            await self.db.save_event("workflow_execution", result)
            logger.info(f"Workflow {workflow.workflow_id} executed: {result.get('status')}")
        except Exception as e:
            logger.error(f"Workflow {workflow.workflow_id} failed: {e}")
        finally:
            self.active_workflows.pop(workflow.workflow_id, None)

    async def close(self):
        self._running = False
        for task in self._running_tasks:
            if not task.done():
                task.cancel()
        if self._running_tasks:
            await asyncio.wait(self._running_tasks, timeout=5.0)
        await self.executor.close()