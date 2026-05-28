from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import (
    Workflow as WorkflowModel, WorkflowNode as WorkflowNodeModel,
    WorkflowExecution
)

DEFAULT_PRIORITY = 2
DEFAULT_MAX_RETRIES = 3

def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        dt_str = dt_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

class SQLAlchemyCursorWrapper:
    def __init__(self, result):
        self._result = result
    async def fetchall(self):
        rows = self._result.all()
        return rows
    def close(self):
        if hasattr(self._result, 'close'):
            self._result.close()

class WorkflowDatabase:
    def __init__(self, session: AsyncSession, org_id: Optional[str] = None):
        self.session = session
        self.org_id = UUID(org_id) if org_id else None

    async def close(self):
        await self.session.close()

    def _apply_org_filter(self, query, model):
        if self.org_id:
            return query.where(model.org_id == self.org_id)
        return query

    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        stmt = select(WorkflowModel).where(
            WorkflowModel.workflow_id == UUID(workflow_id),
            WorkflowModel.deleted_at.is_(None)
        )
        stmt = self._apply_org_filter(stmt, WorkflowModel)
        result = await self.session.execute(stmt)
        wf = result.scalar_one_or_none()
        if not wf:
            return None
        stmt_nodes = select(WorkflowNodeModel).where(WorkflowNodeModel.workflow_id == wf.workflow_id)
        nodes_result = await self.session.execute(stmt_nodes)
        nodes = nodes_result.scalars().all()
        return {
            "workflow_id": str(wf.workflow_id),
            "name": wf.name,
            "description": wf.description or "",
            "trigger": wf.trigger_type or "manual",
            "trigger_config": wf.trigger_config or {},
            "nodes": [
                {
                    "node_id": str(n.node_id),
                    "action_type": n.action_type,
                    "config": n.config or {},
                    "next_node": str(n.next_node) if n.next_node else None,
                    "on_error": str(n.on_error) if n.on_error else None,
                    "retry_count": n.retry_count,
                    "timeout_seconds": n.timeout_seconds,
                    "temp_id": n.temp_id,
                }
                for n in nodes
            ],
            "start_node": str(wf.start_node) if wf.start_node else None,
            "status": wf.status,
        }

    async def save_workflow(self, workflow: Dict, created_by: Optional[str] = None) -> None:
        wf_id = UUID(workflow["workflow_id"])
        try:
            stmt = select(WorkflowModel).where(
                WorkflowModel.workflow_id == wf_id,
                WorkflowModel.deleted_at.is_(None)
            ).with_for_update()
            stmt = self._apply_org_filter(stmt, WorkflowModel)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.name = workflow["name"]
                existing.description = workflow.get("description", "")
                existing.trigger_type = workflow.get("trigger", "manual")
                existing.trigger_config = workflow.get("trigger_config", {})
                existing.start_node = UUID(workflow["start_node"]) if workflow.get("start_node") else None
                existing.status = workflow.get("status", "active")
                existing.updated_at = datetime.now(timezone.utc)
                existing.created_by = UUID(created_by) if created_by else existing.created_by
                subq = select(WorkflowModel.workflow_id).where(
                    WorkflowModel.workflow_id == wf_id
                )
                if self.org_id:
                    subq = subq.where(WorkflowModel.org_id == self.org_id)
                await self.session.execute(
                    delete(WorkflowNodeModel).where(WorkflowNodeModel.workflow_id.in_(subq))
                )
            else:
                existing = WorkflowModel(
                    workflow_id=wf_id,
                    org_id=self.org_id,
                    name=workflow["name"],
                    description=workflow.get("description", ""),
                    trigger_type=workflow.get("trigger", "manual"),
                    trigger_config=workflow.get("trigger_config", {}),
                    start_node=UUID(workflow["start_node"]) if workflow.get("start_node") else None,
                    status=workflow.get("status", "active"),
                    created_by=UUID(created_by) if created_by else None,
                    created_at=datetime.now(timezone.utc),
                )
                self.session.add(existing)
            await self.session.flush()
            for node in workflow.get("nodes", []):
                node_obj = WorkflowNodeModel(
                    node_id=UUID(node["node_id"]),
                    workflow_id=wf_id,
                    action_type=node["action_type"],
                    config=node.get("config", {}),
                    next_node=UUID(node["next_node"]) if node.get("next_node") else None,
                    on_error=UUID(node["on_error"]) if node.get("on_error") else None,
                    retry_count=node.get("retry_count", 3),
                    timeout_seconds=node.get("timeout_seconds", 30),
                    temp_id=node.get("temp_id"),
                )
                self.session.add(node_obj)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def soft_delete_workflow(self, workflow_id: str) -> bool:
        try:
            stmt = select(WorkflowModel).where(
                WorkflowModel.workflow_id == UUID(workflow_id),
                WorkflowModel.deleted_at.is_(None)
            ).with_for_update()
            stmt = self._apply_org_filter(stmt, WorkflowModel)
            result = await self.session.execute(stmt)
            wf = result.scalar_one_or_none()
            if not wf:
                return False
            wf.deleted_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            raise

    async def execute(self, query: str, params: Dict = None) -> Any:
        if params is None:
            params = {}
        result = await self.session.execute(text(query), params)
        return SQLAlchemyCursorWrapper(result)

    async def save_event(self, event_type: str, data: Dict) -> None:
        pass

    async def save_metric(self, metric_name: str, metric_value: float) -> None:
        pass

    async def save_execution(self, context: Dict) -> None:
        execution = WorkflowExecution(
            execution_id=UUID(context["execution_id"]),
            workflow_id=UUID(context["workflow_id"]),
            status=context.get("status"),
            input_data=context.get("input"),
            output_data=context.get("output"),
            node_outputs=context.get("node_outputs"),
            errors=context.get("errors"),
            started_at=_parse_iso(context.get("started_at")),
            completed_at=_parse_iso(context.get("completed_at")),
            depth=context.get("depth", 0),
            triggered_by=UUID(context["triggered_by"]) if context.get("triggered_by") else None,
        )
        self.session.add(execution)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def get_all_tasks(self, status_filter: Optional[str] = None) -> List[Dict]:
        stmt = select(WorkflowExecution).select_from(WorkflowExecution).order_by(
            WorkflowExecution.started_at.desc()
        )
        if status_filter:
            stmt = stmt.where(WorkflowExecution.status == status_filter)
        if self.org_id:
            stmt = stmt.join(
                WorkflowModel, WorkflowExecution.workflow_id == WorkflowModel.workflow_id
            ).where(WorkflowModel.org_id == self.org_id)
        result = await self.session.execute(stmt)
        executions = result.scalars().all()
        return [
            {
                "task_id": str(e.execution_id),
                "function": str(e.workflow_id),
                "priority": DEFAULT_PRIORITY,
                "title": "",
                "description": "",
                "assigned_agent": None,
                "status": e.status,
                "retry_count": 0,
                "max_retries": DEFAULT_MAX_RETRIES,
                "created_at": e.started_at.isoformat() if e.started_at else "",
                "deadline": None,
                "metadata": {},
                "result": e.output_data,
                "human_decision": None,
            }
            for e in executions
        ]

    async def get_task(self, task_id: str) -> Optional[Dict]:
        stmt = select(WorkflowExecution).where(WorkflowExecution.execution_id == UUID(task_id))
        if self.org_id:
            stmt = stmt.select_from(WorkflowExecution).join(
                WorkflowModel, WorkflowExecution.workflow_id == WorkflowModel.workflow_id
            ).where(WorkflowModel.org_id == self.org_id)
        result = await self.session.execute(stmt)
        e = result.scalar_one_or_none()
        if not e:
            return None
        return {
            "task_id": str(e.execution_id),
            "function": str(e.workflow_id),
            "priority": DEFAULT_PRIORITY,
            "title": "",
            "description": "",
            "assigned_agent": None,
            "status": e.status,
            "retry_count": 0,
            "max_retries": DEFAULT_MAX_RETRIES,
            "created_at": e.started_at.isoformat() if e.started_at else "",
            "deadline": None,
            "metadata": {},
            "result": e.output_data,
            "human_decision": None,
        }

    async def update_task_status(self, task_id: str, status: str, result: Any = None) -> bool:
        values = {"status": status}
        if result is not None:
            values["output_data"] = result
        stmt = update(WorkflowExecution).where(WorkflowExecution.execution_id == UUID(task_id))
        if self.org_id:
            stmt = stmt.where(
                WorkflowExecution.workflow_id.in_(
                    select(WorkflowModel.workflow_id).where(WorkflowModel.org_id == self.org_id)
                )
            )
        stmt = stmt.values(**values)
        try:
            res = await self.session.execute(stmt)
            await self.session.commit()
            return res.rowcount > 0
        except Exception:
            await self.session.rollback()
            raise

    async def upsert_task(self, task: Dict) -> None:
        pass

    async def increment_retry(self, task_id: str) -> None:
        pass