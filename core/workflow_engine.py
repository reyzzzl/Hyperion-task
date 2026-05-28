import asyncio
import json
import logging
import os
import base64
import gzip
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import uuid
import httpx

from hyperion_task.core.template import template_engine

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

    GOOGLE_SHEETS_READ = "google_sheets_read"
    GOOGLE_SHEETS_WRITE = "google_sheets_write"
    GOOGLE_DRIVE_UPLOAD = "google_drive_upload"
    GOOGLE_DOCS_CREATE = "google_docs_create"
    GOOGLE_CALENDAR_EVENT = "google_calendar_event"

    MS365_SEND_EMAIL = "ms365_send_email"
    MS365_TEAMS_MEETING = "ms365_teams_meeting"
    MS365_ONEDRIVE_UPLOAD = "ms365_onedrive_upload"
    MS365_EXCEL_WRITE = "ms365_excel_write"

    SLACK_SEND_MESSAGE = "slack_send_message"
    TELEGRAM_SEND_MESSAGE = "telegram_send_message"
    DISCORD_WEBHOOK = "discord_webhook"
    WHATSAPP_BUSINESS = "whatsapp_business"

    HUBSPOT_CREATE_CONTACT = "hubspot_create_contact"
    HUBSPOT_UPDATE_DEAL = "hubspot_update_deal"
    SALESFORCE_CREATE_LEAD = "salesforce_create_lead"
    MAILCHIMP_ADD_SUBSCRIBER = "mailchimp_add_subscriber"
    SENDGRID_SEND_EMAIL = "sendgrid_send_email"

    S3_UPLOAD = "s3_upload"
    S3_DOWNLOAD = "s3_download"
    FTP_UPLOAD = "ftp_upload"
    LOCAL_FILE_READ = "local_file_read"
    LOCAL_FILE_WRITE = "local_file_write"
    PDF_GENERATE = "pdf_generate"
    EXCEL_GENERATE = "excel_generate"

    WEB_SCRAPE = "web_scrape"
    RSS_FEED = "rss_feed"
    WEBHOOK_SEND = "webhook_send"

    LLM_TEXT_GENERATE = "llm_text_generate"
    LLM_SUMMARIZE = "llm_summarize"
    LLM_CLASSIFY = "llm_classify"
    OCR_IMAGE = "ocr_image"

    TWITTER_POST = "twitter_post"
    LINKEDIN_POST = "linkedin_post"

    POSTGRES_QUERY = "postgres_query"
    MYSQL_QUERY = "mysql_query"
    MONGO_FIND = "mongo_find"

    COMPRESS_GZIP = "compress_gzip"
    DECOMPRESS_GZIP = "decompress_gzip"
    ENCRYPT_AES = "encrypt_aes"
    DECRYPT_AES = "decrypt_aes"
    WAIT = "wait"
    STOP = "stop"
    THROW_ERROR = "throw_error"


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
        self.http_client = httpx.AsyncClient()
        depth_limit = os.environ.get("WORKFLOW_DEPTH_LIMIT", "5")
        self._loop_depth_limit = int(depth_limit) if depth_limit.isdigit() else 5

        self.registered_actions: Dict[str, Callable] = {
            "http_request": self._execute_http_request,
            "database_query": self._execute_database_query,
            "send_email": self._execute_send_email,
            "transform_data": self._execute_transform_data,
            "condition": self._execute_condition,
            "loop": self._execute_loop,
            "delay": self._execute_delay,

            "google_sheets_read": self._execute_google_sheets_read,
            "google_sheets_write": self._execute_google_sheets_write,
            "google_drive_upload": self._execute_google_drive_upload,
            "google_docs_create": self._execute_google_docs_create,
            "google_calendar_event": self._execute_google_calendar_event,

            "ms365_send_email": self._execute_ms365_send_email,
            "ms365_teams_meeting": self._execute_ms365_teams_meeting,
            "ms365_onedrive_upload": self._execute_ms365_onedrive_upload,
            "ms365_excel_write": self._execute_ms365_excel_write,

            "slack_send_message": self._execute_slack_send_message,
            "telegram_send_message": self._execute_telegram_send_message,
            "discord_webhook": self._execute_discord_webhook,
            "whatsapp_business": self._execute_whatsapp_business,

            "hubspot_create_contact": self._execute_hubspot_create_contact,
            "hubspot_update_deal": self._execute_hubspot_update_deal,
            "salesforce_create_lead": self._execute_salesforce_create_lead,
            "mailchimp_add_subscriber": self._execute_mailchimp_add_subscriber,
            "sendgrid_send_email": self._execute_sendgrid_send_email,

            "s3_upload": self._execute_s3_upload,
            "s3_download": self._execute_s3_download,
            "ftp_upload": self._execute_ftp_upload,
            "local_file_read": self._execute_local_file_read,
            "local_file_write": self._execute_local_file_write,
            "pdf_generate": self._execute_pdf_generate,
            "excel_generate": self._execute_excel_generate,

            "web_scrape": self._execute_web_scrape,
            "rss_feed": self._execute_rss_feed,
            "webhook_send": self._execute_webhook_send,

            "llm_text_generate": self._execute_llm_text_generate,
            "llm_summarize": self._execute_llm_summarize,
            "llm_classify": self._execute_llm_classify,
            "ocr_image": self._execute_ocr_image,

            "twitter_post": self._execute_twitter_post,
            "linkedin_post": self._execute_linkedin_post,

            "postgres_query": self._execute_postgres_query,
            "mysql_query": self._execute_mysql_query,
            "mongo_find": self._execute_mongo_find,

            "compress_gzip": self._execute_compress_gzip,
            "decompress_gzip": self._execute_decompress_gzip,
            "encrypt_aes": self._execute_encrypt_aes,
            "decrypt_aes": self._execute_decrypt_aes,
            "wait": self._execute_wait,
            "stop": self._execute_stop,
            "throw_error": self._execute_throw_error,
        }

    async def close(self):
        await self.http_client.aclose()

    async def _load_workflow_from_db(self, workflow_id: str) -> Optional[Workflow]:
        data = await self.db.get_workflow(workflow_id)
        if not data:
            return None
        try:
            workflow = Workflow(
                workflow_id=data["workflow_id"],
                name=data["name"],
                description=data.get("description", ""),
                trigger=TriggerType(data.get("trigger", "manual")),
                trigger_config=data.get("trigger_config", {}),
                start_node=data.get("start_node"),
            )
            nodes_list = data.get("nodes", [])
            if not isinstance(nodes_list, list):
                logger.error(f"Invalid nodes format for workflow {workflow_id}")
                return None
            for n_data in nodes_list:
                try:
                    action_type = ActionType(n_data["action_type"])
                except ValueError:
                    logger.error(f"Invalid action_type in workflow {workflow_id}: {n_data.get('action_type')}")
                    continue
                node_obj = WorkflowNode(
                    node_id=n_data.get("node_id", str(uuid.uuid4())),
                    action_type=action_type,
                    config=n_data.get("config", {}),
                    next_node=n_data.get("next_node"),
                    on_error=n_data.get("on_error"),
                    retry_count=n_data.get("retry_count", 3),
                    timeout_seconds=n_data.get("timeout_seconds", 30),
                    temp_id=n_data.get("temp_id"),
                )
                workflow.nodes[node_obj.node_id] = node_obj
            return workflow
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_id}: {e}")
            return None

    async def execute_workflow(self, workflow: Workflow, input_data: Dict, depth: int = 0) -> Dict:
        if depth > self._loop_depth_limit:
            logger.warning(f"Workflow recursion depth {depth} exceeded limit {self._loop_depth_limit}")
            return {
                "status": "failed",
                "errors": [f"Workflow recursion depth exceeded limit {self._loop_depth_limit}"],
                "workflow_id": workflow.workflow_id
            }
        execution_id = str(uuid.uuid4())
        context = {
            "execution_id": execution_id,
            "workflow_id": workflow.workflow_id,
            "input": input_data,
            "output": {},
            "node_outputs": {},
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "_depth": depth,
        }
        self.metrics["executed"] += 1
        try:
            async with self.semaphore:
                current_node_id = workflow.start_node
                if not current_node_id:
                    context["errors"].append("Workflow has no start_node")
                    raise ValueError("No start node")
                max_iterations = getattr(workflow, 'max_iterations', 100)
                iteration = 0
                while current_node_id and iteration < max_iterations:
                    iteration += 1
                    node = workflow.nodes.get(current_node_id)
                    if not node:
                        context["errors"].append(f"Node {current_node_id} not found")
                        break
                    logger.debug(f"Executing node {node.node_id} ({node.action_type.value})")
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
                                if node.action_type.value == "condition":
                                    decision = node_result.get("data")
                                    if isinstance(decision, dict):
                                        current_node_id = decision.get("next_node", node.next_node)
                                    elif decision:
                                        current_node_id = node.config.get("true_node", node.next_node)
                                    else:
                                        current_node_id = node.config.get("false_node", node.next_node)
                                elif node.action_type.value == "stop":
                                    current_node_id = None
                                    break
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
                    if not success:
                        if not context["errors"]:
                            context["errors"].append(node_result.get("error", "Unknown error") if node_result else "Node execution failed")
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

    async def execute_workflow_by_id(self, workflow_id: str, input_data: Dict) -> Dict:
        workflow = await self._load_workflow_from_db(workflow_id)
        if not workflow:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}
        return await self.execute_workflow(workflow, input_data)

    def _store_node_output(self, context: Dict, node: WorkflowNode, data: Any):
        context["node_outputs"][node.node_id] = data
        if node.temp_id:
            context["node_outputs"][node.temp_id] = data

    def _evaluate_expression(self, expr: str, context: Dict) -> Any:
        try:
            return template_engine.render(expr, context)
        except Exception:
            try:
                return template_engine._evaluate_expression(expr, context)
            except Exception:
                return None

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
                rendered_json = json.dumps(body_raw)
                rendered = template_engine.render(rendered_json, context)
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
            if 200 <= resp.status_code <= 299:
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
            if not hasattr(self.db, 'db') or self.db.db is None:
                return {"success": False, "error": "Database connection not available"}
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
        field_expr = config.get("field")
        operator = config.get("operator", "equals")
        value = config.get("value")
        true_node = config.get("true_node")
        false_node = config.get("false_node")
        if not field_expr:
            return {"success": False, "error": "Condition missing 'field'"}
        try:
            current_value = self._evaluate_expression(field_expr, context)
        except Exception as e:
            return {"success": False, "error": f"Failed to evaluate field expression: {e}"}
        condition_met = False
        try:
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
            else:
                return {"success": False, "error": f"Unknown operator: {operator}"}
        except (ValueError, TypeError) as e:
            return {"success": False, "error": f"Type error in condition: {e}"}
        next_node = true_node if condition_met else false_node
        return {"success": True, "data": {"condition_met": condition_met, "next_node": next_node}}

    async def _execute_loop(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        items_expr = config.get("items", "[]")
        sub_workflow_id = config.get("sub_workflow")
        if not sub_workflow_id:
            return {"success": False, "error": "Loop node requires sub_workflow_id"}
        try:
            if isinstance(items_expr, str):
                rendered = template_engine.render(items_expr, context)
                try:
                    items = json.loads(rendered) if isinstance(rendered, str) else rendered
                except json.JSONDecodeError:
                    items = []
            elif isinstance(items_expr, list):
                items = items_expr
            else:
                items = []
            if not isinstance(items, list):
                items = []
        except Exception as e:
            return {"success": False, "error": f"Failed to parse loop items: {e}"}
        sub_workflow = await self._load_workflow_from_db(sub_workflow_id)
        if not sub_workflow:
            return {"success": False, "error": f"Sub-workflow {sub_workflow_id} not found or invalid"}
        results = []
        max_loop_iterations = node.config.get("max_iterations", 100)
        sub_workflow.max_iterations = node.config.get("sub_workflow_max_iterations", 10)
        depth = context.get("_depth", 0) + 1
        if depth > self._loop_depth_limit:
            return {"success": False, "error": f"Loop depth exceeded limit {self._loop_depth_limit}"}
        clean_context = {k: v for k, v in context.items() if k != "_depth"}
        for idx, item in enumerate(items):
            if idx >= max_loop_iterations:
                break
            sub_context = {**clean_context, "loop_item": item, "loop_index": idx}
            try:
                result = await self.execute_workflow(sub_workflow, sub_context, depth=depth)
                results.append(result)
            except Exception as e:
                logger.error(f"Loop iteration {idx} failed: {e}")
                results.append({"error": str(e), "status": "failed"})
        return {"success": True, "data": results}

    async def _execute_delay(self, node: WorkflowNode, context: Dict) -> Dict:
        seconds = node.config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"success": True, "data": f"Delayed for {seconds}s"}

    async def _execute_google_sheets_read(self, node: WorkflowNode, context: Dict) -> Dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration not configured"}
        spreadsheet_id = template_engine.render(node.config.get("spreadsheet_id", ""), context)
        range_name = template_engine.render(node.config.get("range", "Sheet1!A1:Z"), context)
        result = await gs.sheets_operation(spreadsheet_id, range_name, operation="read")
        if "values" in result:
            return {"success": True, "data": result["values"]}
        return {"success": False, "error": result.get("error", "Read failed")}

    async def _execute_google_sheets_write(self, node: WorkflowNode, context: Dict) -> Dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration not configured"}
        spreadsheet_id = template_engine.render(node.config.get("spreadsheet_id", ""), context)
        range_name = template_engine.render(node.config.get("range", "Sheet1!A1"), context)
        values = node.config.get("values", [])
        rendered_values = []
        for row in values:
            new_row = []
            for cell in row:
                if isinstance(cell, str) and "{{" in cell:
                    cell = template_engine.render(cell, context)
                new_row.append(cell)
            rendered_values.append(new_row)
        result = await gs.sheets_operation(spreadsheet_id, range_name, values=rendered_values, operation="write")
        if result.get("success"):
            return {"success": True, "data": result}
        return {"success": False, "error": result.get("error", "Write failed")}

    async def _execute_google_drive_upload(self, node: WorkflowNode, context: Dict) -> Dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration not configured"}
        if hasattr(gs, "drive_upload"):
            file_path = template_engine.render(node.config.get("file_path", ""), context)
            mime_type = node.config.get("mime_type", "application/octet-stream")
            result = await gs.drive_upload(file_path, mime_type)
            return result
        return {"success": False, "error": "Drive upload not implemented in integration"}

    async def _execute_google_docs_create(self, node: WorkflowNode, context: Dict) -> Dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration not configured"}
        title = template_engine.render(node.config.get("title", "New Doc"), context)
        content = template_engine.render(node.config.get("content", ""), context)
        result = await gs.create_doc(title, content)
        return result

    async def _execute_google_calendar_event(self, node: WorkflowNode, context: Dict) -> Dict:
        gs = self.integrations.get("google")
        if not gs:
            return {"success": False, "error": "Google integration not configured"}
        summary = template_engine.render(node.config.get("summary", ""), context)
        start_time = template_engine.render(node.config.get("start_time", ""), context)
        end_time = template_engine.render(node.config.get("end_time", ""), context)
        attendees = node.config.get("attendees", [])
        timezone = node.config.get("timezone", os.environ.get("TIMEZONE", "UTC"))
        result = await gs.schedule_meeting(summary, start_time, end_time, attendees, timezone)
        return result

    async def _execute_ms365_send_email(self, node: WorkflowNode, context: Dict) -> Dict:
        ms = self.integrations.get("microsoft")
        if not ms:
            return {"success": False, "error": "Microsoft 365 integration not configured"}
        to = template_engine.render(node.config.get("to", ""), context)
        subject = template_engine.render(node.config.get("subject", ""), context)
        body = template_engine.render(node.config.get("body", ""), context)
        result = await ms.send_email(to, subject, body)
        return result

    async def _execute_ms365_teams_meeting(self, node: WorkflowNode, context: Dict) -> Dict:
        ms = self.integrations.get("microsoft")
        if not ms:
            return {"success": False, "error": "Microsoft 365 integration not configured"}
        subject = template_engine.render(node.config.get("subject", ""), context)
        start_time = template_engine.render(node.config.get("start_time", ""), context)
        end_time = template_engine.render(node.config.get("end_time", ""), context)
        attendees = node.config.get("attendees", [])
        result = await ms.create_teams_meeting(subject, start_time, end_time, attendees)
        return result

    async def _execute_ms365_onedrive_upload(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "OneDrive upload not implemented yet"}

    async def _execute_ms365_excel_write(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "Excel write not implemented yet"}

    async def _execute_slack_send_message(self, node: WorkflowNode, context: Dict) -> Dict:
        webhook_url = node.config.get("webhook_url")
        if not webhook_url:
            return {"success": False, "error": "Slack webhook URL required"}
        webhook_url = template_engine.render(webhook_url, context)
        text = template_engine.render(node.config.get("text", ""), context)
        try:
            resp = await self.http_client.post(webhook_url, json={"text": text})
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except json.JSONDecodeError:
                    data = resp.text
                return {"success": True, "data": data}
            return {"success": False, "error": f"Slack error: {resp.status_code} - {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_telegram_send_message(self, node: WorkflowNode, context: Dict) -> Dict:
        bot_token = node.config.get("bot_token")
        chat_id = node.config.get("chat_id")
        if not bot_token or not chat_id:
            return {"success": False, "error": "Telegram bot_token and chat_id required"}
        bot_token = template_engine.render(bot_token, context)
        chat_id = template_engine.render(str(chat_id), context)
        text = template_engine.render(node.config.get("text", ""), context)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            resp = await self.http_client.post(url, json={"chat_id": chat_id, "text": text})
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": f"Telegram error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_discord_webhook(self, node: WorkflowNode, context: Dict) -> Dict:
        webhook_url = template_engine.render(node.config.get("webhook_url", ""), context)
        content = template_engine.render(node.config.get("content", ""), context)
        try:
            resp = await self.http_client.post(webhook_url, json={"content": content})
            success = resp.status_code in (200, 204)
            return {"success": success, "data": {"status": resp.status_code}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_whatsapp_business(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "WhatsApp Business not implemented yet"}

    async def _execute_hubspot_create_contact(self, node: WorkflowNode, context: Dict) -> Dict:
        api_key = self.integrations.get("hubspot_api_key") or os.environ.get("HUBSPOT_API_KEY")
        if not api_key:
            return {"success": False, "error": "HubSpot API key not configured in environment"}
        email = template_engine.render(node.config.get("email", ""), context)
        firstname = template_engine.render(node.config.get("firstname", ""), context)
        lastname = template_engine.render(node.config.get("lastname", ""), context)
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        body = {"properties": {"email": email, "firstname": firstname, "lastname": lastname}}
        try:
            resp = await self.http_client.post(url, headers=headers, json=body)
            if resp.status_code in (200, 201):
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": f"HubSpot error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_hubspot_update_deal(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "HubSpot update deal not implemented"}

    async def _execute_salesforce_create_lead(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "Salesforce not implemented"}

    async def _execute_mailchimp_add_subscriber(self, node: WorkflowNode, context: Dict) -> Dict:
        api_key = self.integrations.get("mailchimp_api_key") or os.environ.get("MAILCHIMP_API_KEY")
        if not api_key:
            return {"success": False, "error": "Mailchimp API key not configured"}
        list_id = node.config.get("list_id")
        email = template_engine.render(node.config.get("email", ""), context)
        if not list_id:
            return {"success": False, "error": "Mailchimp list_id required"}
        dc = api_key.split('-')[-1]
        url = f"https://{dc}.api.mailchimp.com/3.0/lists/{list_id}/members"
        auth = httpx.BasicAuth("anystring", api_key)
        data = {"email_address": email, "status": "subscribed"}
        try:
            resp = await self.http_client.post(url, json=data, auth=auth)
            if resp.status_code in (200, 201):
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": f"Mailchimp error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_sendgrid_send_email(self, node: WorkflowNode, context: Dict) -> Dict:
        api_key = self.integrations.get("sendgrid_api_key") or os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            return {"success": False, "error": "SendGrid API key not configured"}
        from_email = template_engine.render(node.config.get("from_email", ""), context)
        to_email = template_engine.render(node.config.get("to_email", ""), context)
        subject = template_engine.render(node.config.get("subject", ""), context)
        content = template_engine.render(node.config.get("content", ""), context)
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": content}]
        }
        try:
            resp = await self.http_client.post(url, headers=headers, json=data)
            if resp.status_code == 202:
                return {"success": True, "data": {"message": "Sent"}}
            return {"success": False, "error": f"SendGrid error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_s3_upload(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "S3 upload not implemented yet"}

    async def _execute_s3_download(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "S3 download not implemented"}

    async def _execute_ftp_upload(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "FTP upload not implemented"}

    async def _execute_local_file_read(self, node: WorkflowNode, context: Dict) -> Dict:
        file_path = template_engine.render(node.config.get("file_path", ""), context)
        try:
            normalized = os.path.normpath(file_path)
            if normalized.startswith('..') or os.path.isabs(normalized):
                return {"success": False, "error": "Path traversal not allowed"}
            allowed_dir = os.environ.get("WORKFLOW_DATA_DIR", "./workflow_data")
            allowed_dir_real = os.path.realpath(allowed_dir)
            full_path = os.path.realpath(os.path.join(allowed_dir, normalized))
            if not full_path.startswith(allowed_dir_real):
                return {"success": False, "error": "Path outside allowed directory"}
            import aiofiles
            async with aiofiles.open(full_path, mode='r') as f:
                content = await f.read()
            return {"success": True, "data": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_local_file_write(self, node: WorkflowNode, context: Dict) -> Dict:
        file_path = template_engine.render(node.config.get("file_path", ""), context)
        content = template_engine.render(node.config.get("content", ""), context)
        try:
            normalized = os.path.normpath(file_path)
            if normalized.startswith('..') or os.path.isabs(normalized):
                return {"success": False, "error": "Path traversal not allowed"}
            allowed_dir = os.environ.get("WORKFLOW_DATA_DIR", "./workflow_data")
            allowed_dir_real = os.path.realpath(allowed_dir)
            full_path = os.path.realpath(os.path.join(allowed_dir, normalized))
            if not full_path.startswith(allowed_dir_real):
                return {"success": False, "error": "Path outside allowed directory"}
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not parent_dir.startswith(allowed_dir_real):
                return {"success": False, "error": "Parent directory outside allowed scope"}
            os.makedirs(parent_dir, exist_ok=True)
            import aiofiles
            async with aiofiles.open(full_path, mode='w') as f:
                await f.write(content)
            return {"success": True, "data": {"path": full_path}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_pdf_generate(self, node: WorkflowNode, context: Dict) -> Dict:
        try:
            from reportlab.pdfgen import canvas
            file_path = template_engine.render(node.config.get("file_path", "output.pdf"), context)
            text = template_engine.render(node.config.get("text", ""), context)
            allowed_dir = os.environ.get("WORKFLOW_DATA_DIR", "./workflow_data")
            allowed_dir_real = os.path.realpath(allowed_dir)
            full_path = os.path.realpath(os.path.join(allowed_dir, os.path.basename(file_path)))
            if not full_path.startswith(allowed_dir_real):
                return {"success": False, "error": "Path outside allowed directory"}
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            c = canvas.Canvas(full_path)
            c.drawString(100, 750, text)
            c.save()
            return {"success": True, "data": {"path": full_path}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_excel_generate(self, node: WorkflowNode, context: Dict) -> Dict:
        try:
            import openpyxl
            file_path = template_engine.render(node.config.get("file_path", "output.xlsx"), context)
            data = node.config.get("data", [])
            allowed_dir = os.environ.get("WORKFLOW_DATA_DIR", "./workflow_data")
            allowed_dir_real = os.path.realpath(allowed_dir)
            full_path = os.path.realpath(os.path.join(allowed_dir, os.path.basename(file_path)))
            if not full_path.startswith(allowed_dir_real):
                return {"success": False, "error": "Path outside allowed directory"}
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            wb = openpyxl.Workbook()
            ws = wb.active
            for row in data:
                ws.append(row)
            wb.save(full_path)
            return {"success": True, "data": {"path": full_path}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_web_scrape(self, node: WorkflowNode, context: Dict) -> Dict:
        url = template_engine.render(node.config.get("url", ""), context)
        selector = node.config.get("selector", "body")
        max_size = 10 * 1024 * 1024
        try:
            from bs4 import BeautifulSoup
            async with self.http_client.stream("GET", url) as response:
                if response.status_code != 200:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_size:
                    return {"success": False, "error": f"Response too large: {content_length} bytes (max {max_size})"}
                body = b""
                async for chunk in response.aiter_bytes():
                    body += chunk
                    if len(body) > max_size:
                        return {"success": False, "error": f"Response exceeded max size {max_size}"}
                html = body.decode("utf-8", errors="replace")
                soup = BeautifulSoup(html, 'html.parser')
                elements = soup.select(selector)
                texts = [el.get_text(strip=True) for el in elements]
                return {"success": True, "data": texts}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_rss_feed(self, node: WorkflowNode, context: Dict) -> Dict:
        feed_url = template_engine.render(node.config.get("feed_url", ""), context)
        try:
            import feedparser
            loop = asyncio.get_running_loop()
            parsed = await loop.run_in_executor(None, feedparser.parse, feed_url)
            entries = []
            for entry in parsed.entries[:node.config.get("limit", 10)]:
                entries.append({
                    "title": entry.get("title"),
                    "link": entry.get("link"),
                    "published": entry.get("published"),
                    "summary": entry.get("summary")
                })
            return {"success": True, "data": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_webhook_send(self, node: WorkflowNode, context: Dict) -> Dict:
        config = node.config
        url = template_engine.render(config.get("url", ""), context)
        payload = config.get("payload", {})
        if isinstance(payload, dict):
            rendered = {}
            for k, v in payload.items():
                if isinstance(v, str) and "{{" in v:
                    rendered[k] = template_engine.render(v, context)
                else:
                    rendered[k] = v
        else:
            rendered = payload
        try:
            resp = await self.http_client.post(url, json=rendered, timeout=node.timeout_seconds)
            if resp.status_code in (200, 201, 202, 204):
                return {"success": True, "data": resp.json() if resp.text else {}}
            return {"success": False, "error": f"Webhook failed: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_llm_text_generate(self, node: WorkflowNode, context: Dict) -> Dict:
        prompt = template_engine.render(node.config.get("prompt", ""), context)
        model = node.config.get("model") or os.environ.get("OLLAMA_MODEL", "mistral")
        try:
            from hyperion_task.agents.base import get_shared_client
            client = get_shared_client()
            response = await client.generate(model=model, prompt=prompt)
            if hasattr(response, 'response'):
                text = response.response
            elif isinstance(response, dict):
                text = response.get('response', '')
            else:
                text = str(response)
            return {"success": True, "data": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_llm_summarize(self, node: WorkflowNode, context: Dict) -> Dict:
        text = template_engine.render(node.config.get("text", ""), context)
        model = node.config.get("model") or os.environ.get("OLLAMA_MODEL", "mistral")
        prompt = f"Summarize the following text concisely:\n\n{text}"
        temp_node = WorkflowNode(action_type=ActionType.LLM_TEXT_GENERATE, config={"prompt": prompt, "model": model})
        return await self._execute_llm_text_generate(temp_node, context)

    async def _execute_llm_classify(self, node: WorkflowNode, context: Dict) -> Dict:
        text = template_engine.render(node.config.get("text", ""), context)
        categories = node.config.get("categories", ["positive", "negative", "neutral"])
        model = node.config.get("model") or os.environ.get("OLLAMA_MODEL", "mistral")
        prompt = f"Classify the following text into one of {categories}. Return only the category name.\n\nText: {text}"
        temp_node = WorkflowNode(action_type=ActionType.LLM_TEXT_GENERATE, config={"prompt": prompt, "model": model})
        return await self._execute_llm_text_generate(temp_node, context)

    async def _execute_ocr_image(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "OCR not implemented yet"}

    async def _execute_twitter_post(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "Twitter post not implemented yet"}

    async def _execute_linkedin_post(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "LinkedIn post not implemented yet"}

    async def _execute_postgres_query(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "PostgreSQL query not implemented yet"}

    async def _execute_mysql_query(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "MySQL query not implemented yet"}

    async def _execute_mongo_find(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "MongoDB find not implemented yet"}

    async def _execute_compress_gzip(self, node: WorkflowNode, context: Dict) -> Dict:
        data = template_engine.render(node.config.get("data", ""), context).encode()
        compressed = gzip.compress(data)
        return {"success": True, "data": base64.b64encode(compressed).decode()}

    async def _execute_decompress_gzip(self, node: WorkflowNode, context: Dict) -> Dict:
        b64_data = template_engine.render(node.config.get("data", ""), context)
        try:
            compressed = base64.b64decode(b64_data)
            decompressed = gzip.decompress(compressed).decode()
            return {"success": True, "data": decompressed}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_encrypt_aes(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "AES encrypt not implemented"}

    async def _execute_decrypt_aes(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": False, "error": "AES decrypt not implemented"}

    async def _execute_wait(self, node: WorkflowNode, context: Dict) -> Dict:
        seconds = node.config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"success": True, "data": f"Waited {seconds}s"}

    async def _execute_stop(self, node: WorkflowNode, context: Dict) -> Dict:
        return {"success": True, "data": {"stopped": True, "message": node.config.get("message", "Workflow stopped")}}

    async def _execute_throw_error(self, node: WorkflowNode, context: Dict) -> Dict:
        error_msg = template_engine.render(node.config.get("error_message", "Manual error"), context)
        return {"success": False, "error": error_msg}