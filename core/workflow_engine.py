import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import uuid
import httpx

from .template import template_engine

logger = logging.getLogger("WorkflowEngine")


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(Enum):
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EMAIL = "email"
    DATABASE = "database"
    MANUAL = "manual"


class ActionType(Enum):
    HTTP_REQUEST = "http_request"
    DATABASE_QUERY = "database_query"
    SEND_EMAIL = "send_email"
    TRANSFORM_DATA = "transform_data"
    CONDITION = "condition"
    LOOP = "loop"
    DELAY = "delay"


@dataclass
class WorkflowNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.HTTP_REQUEST
    config: Dict[str, Any] = field(default_factory=dict)
    next_node: Optional[str] = None
    on_error: Optional[str] = None
    retry_count: int = 3
    timeout_seconds: int = 30
    temp_id: Optional[str] = None


@dataclass
class Workflow:
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    trigger: Optional[TriggerType] = None
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    start_node: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    max_iterations: int = 100


class WorkflowExecutor:
    def __init__(self, db, integrations: Dict[str, Any], max_concurrent: int = 10):
        self.db = db
        self.integrations = integrations
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.metrics = {"executed": 0, "succeeded": 0, "failed": 0}
        self.registered_actions: Dict[str, Callable] = {
            "http_request": self._execute_http_request,
            "database_query": self._execute_database_query,
            "send_email": self._execute_send_email,
            "transform_data": self._execute_transform_data,
            "condition": self._execute_condition,
            "loop": self._execute_loop,
            "delay": self._execute_delay,
        }
        self.http_client = httpx.AsyncClient()

    async def close(self):
        await self.http_client.aclose()

    async def execute_workflow(self, workflow: Workflow, input_data: Dict) -> Dict:
        execution_id = str(uuid.uuid4())
        context = {
            "execution_id": execution_id,
            "workflow_id": workflow.workflow_id,
            "input": input_data,
            "output": {},
            "node_outputs": {},
            "errors": [],
            "started_at": datetime.now().isoformat(),
        }
        self.metrics["executed"] += 1
        try:
            async with self.semaphore:
                current_node_id = workflow.start_node
                max_iterations = getattr(workflow, 'max_iterations', 100)
                iteration = 0
                while current_node_id and iteration < max_iterations:
                    iteration += 1
                    node = workflow.nodes.get(current_node_id)
                    if not node:
                        context["errors"].append(f"Node {current_node_id} not found")
                        break
                    logger.info(f"Executing node {node.node_id} ({node.action_type.value})")
                    node_result = None
                    action_func = self.registered_actions.get(node.action_type.value)
                    if not action_func:
                        context["errors"].append(f"No handler for {node.action_type.value}")
                        current_node_id = node.on_error
                        continue

                    success = False
                    for attempt in range(node.retry_count + 1):
                        try:
                            node_result = await asyncio.wait_for(
                                action_func(node, context),
                                timeout=node.timeout_seconds
                            )
                            if node_result.get("success"):
                                self._store_node_output(context, node, node_result.get("data"))
                                if node.action_type == ActionType.CONDITION:
                                    decision = node_result.get("data")
                                    if isinstance(decision, dict):
                                        current_node_id = decision.get("next_node", node.next_node)
                                    elif decision:
                                        current_node_id = node.config.get("true_node", node.next_node)
                                    else:
                                        current_node_id = node.config.get("false_node", node.next_node)
                                else:
                                    current_node_id = node.next_node
                                success = True
                                break
                            else:
                                if attempt < node.retry_count:
                                    logger.warning(f"Retrying node {node.node_id} ({attempt+1}/{node.retry_count}) after failure: {node_result.get('error')}")
                                    await asyncio.sleep(2)
                        except asyncio.TimeoutError:
                            context["errors"].append(f"Node {current_node_id} timed out after {node.timeout_seconds}s")
                            current_node_id = node.on_error
                            break
                        except Exception as e:
                            context["errors"].append(f"Node {current_node_id} unexpected error: {str(e)}")
                            current_node_id = node.on_error
                            break
                    if not success and not context["errors"]:
                        context["errors"].append(node_result.get("error", "Unknown error"))
                        current_node_id = node.on_error
                if iteration >= max_iterations:
                    context["errors"].append("Max iterations reached, possible infinite loop")
            context["completed_at"] = datetime.now().isoformat()
            if not context["errors"]:
                self.metrics["succeeded"] += 1
                context["status"] = "completed"
            else:
                self.metrics["failed"] += 1
                context["status"] = "failed"
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            self.metrics["failed"] += 1
            context["status"] = "failed"
            context["errors"].append(str(e))
        return context

    def _store_node_output(self, context: Dict, node: WorkflowNode, data: Any):
        context["node_outputs"][node.node_id] = data
        if node.temp_id:
            context["node_outputs"][node.temp_id] = data

    async def _execute_http_request(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        method = config.get("method", "GET").upper()
        url = template_engine.render(config.get("url", ""), context)
        headers_raw = config.get("headers", {})
        headers = {k: template_engine.render(v, context) for k, v in headers_raw.items()}
        body_raw = config.get("body", {})

        try:
            if isinstance(body_raw, str):
                rendered_body = template_engine.render(body_raw, context)
                try:
                    body = json.loads(rendered_body)
                except json.JSONDecodeError:
                    body = rendered_body
            else:
                rendered = template_engine.render(json.dumps(body_raw), context)
                try:
                    body = json.loads(rendered)
                except json.JSONDecodeError:
                    body = rendered
        except Exception as e:
            return {"success": False, "error": f"Body rendering failed: {e}"}

        try:
            if method == "GET":
                resp = await self.http_client.get(url, headers=headers, timeout=node.timeout_seconds)
            elif method == "POST":
                if isinstance(body, dict):
                    resp = await self.http_client.post(url, headers=headers, json=body, timeout=node.timeout_seconds)
                else:
                    resp = await self.http_client.post(url, headers=headers, content=body, timeout=node.timeout_seconds)
            elif method == "PUT":
                if isinstance(body, dict):
                    resp = await self.http_client.put(url, headers=headers, json=body, timeout=node.timeout_seconds)
                else:
                    resp = await self.http_client.put(url, headers=headers, content=body, timeout=node.timeout_seconds)
            elif method == "DELETE":
                resp = await self.http_client.delete(url, headers=headers, timeout=node.timeout_seconds)
            else:
                return {"success": False, "error": f"Unsupported method {method}"}
            if resp.status_code in (200, 201, 204):
                return {"success": True, "data": resp.json() if resp.text else {}}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_database_query(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        query = template_engine.render(config.get("query", ""), context)
        params_raw = config.get("params", {})
        params = {k: template_engine.render(str(v), context) for k, v in params_raw.items()}
        try:
            cursor = await self.db.db.execute(query, params)
            rows = await cursor.fetchall()
            return {"success": True, "data": [dict(row) for row in rows]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_send_email(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        to = template_engine.render(config.get("to", ""), context)
        subject = template_engine.render(config.get("subject", ""), context)
        body = template_engine.render(config.get("body", ""), context)
        email_service = self.integrations.get("email")
        if email_service:
            result = await email_service.send_email(to, subject, body)
            if isinstance(result, dict) and result.get("success"):
                return {"success": True, "data": result}
            return {"success": False, "error": result.get("error", "Unknown email error")}
        return {"success": False, "error": "No email integration configured"}

    async def _execute_transform_data(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        template = config.get("template", {})
        if isinstance(template, str):
            rendered = template_engine.render(template, context)
            try:
                return {"success": True, "data": json.loads(rendered)}
            except json.JSONDecodeError:
                return {"success": True, "data": rendered}
        elif isinstance(template, dict):
            result = {}
            for key, value_expr in template.items():
                if isinstance(value_expr, str) and "{{" in value_expr:
                    result[key] = template_engine.render(value_expr, context)
                else:
                    result[key] = value_expr
            return {"success": True, "data": result}
        return {"success": False, "error": "Template must be string or dict"}

    async def _execute_condition(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        field = config.get("field")
        operator = config.get("operator", "equals")
        value = config.get("value")
        true_node = config.get("true_node")
        false_node = config.get("false_node")
        current_value = template_engine._evaluate_expression(field, context)
        condition_met = False
        if operator == "equals":
            condition_met = str(current_value) == str(value)
        elif operator == "not_equals":
            condition_met = str(current_value) != str(value)
        elif operator == "greater_than":
            condition_met = float(current_value) > float(value)
        elif operator == "less_than":
            condition_met = float(current_value) < float(value)
        elif operator == "contains":
            condition_met = str(value) in str(current_value)
        elif operator == "not_empty":
            condition_met = bool(current_value)
        elif operator == "empty":
            condition_met = not bool(current_value)
        next_node = true_node if condition_met else false_node
        return {"success": True, "data": {"condition_met": condition_met, "next_node": next_node}}

    async def _execute_loop(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        items_expr = config.get("items", "[]")
        sub_workflow_id = config.get("sub_workflow")
        items = []
        if isinstance(items_expr, str) and "{{" in items_expr:
            rendered = template_engine.render(items_expr, context)
            try:
                items = json.loads(rendered)
            except json.JSONDecodeError:
                items = []
        elif isinstance(items_expr, list):
            items = items_expr
        results = []
        if sub_workflow_id:
            sub_workflow_data = await self.db.get_workflow(sub_workflow_id)
            if sub_workflow_data:
                sub_workflow = Workflow(
                    workflow_id=sub_workflow_data["workflow_id"],
                    name=sub_workflow_data["name"],
                    description=sub_workflow_data.get("description", ""),
                    trigger=TriggerType(sub_workflow_data.get("trigger", "manual")),
                    trigger_config=sub_workflow_data.get("trigger_config", {}),
                    start_node=sub_workflow_data.get("start_node"),
                )
                for n_data in sub_workflow_data["nodes"]:
                    node_obj = WorkflowNode(
                        node_id=n_data.get("node_id", str(uuid.uuid4())),
                        action_type=ActionType(n_data["action_type"]),
                        config=n_data.get("config", {}),
                        next_node=n_data.get("next_node"),
                        on_error=n_data.get("on_error"),
                        retry_count=n_data.get("retry_count", 3),
                        timeout_seconds=n_data.get("timeout_seconds", 30),
                        temp_id=n_data.get("temp_id"),
                    )
                    sub_workflow.nodes[node_obj.node_id] = node_obj
                for item in items:
                    sub_context = {**context, "loop_item": item}
                    result = await self.execute_workflow(sub_workflow, sub_context)
                    results.append(result)
        return {"success": True, "data": results}

    async def _execute_delay(self, node: WorkflowNode, context: Dict) -> Dict:
        seconds = node.config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"success": True, "data": f"Delayed for {seconds}s"}