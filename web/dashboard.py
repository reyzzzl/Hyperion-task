import os
import asyncio
import json
import logging
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from hyperion_task.core.workflow_manager import WorkflowManager
from .auth import API_TOKEN

logger = logging.getLogger("Dashboard")

app = FastAPI(title="Hyperion Task Dashboard")

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)
templates = Jinja2Templates(directory=templates_dir)

_workflow_manager: Optional[WorkflowManager] = None

security = HTTPBearer()


def set_workflow_manager(manager: WorkflowManager):
    global _workflow_manager
    _workflow_manager = manager


async def get_workflow_manager() -> WorkflowManager:
    if _workflow_manager is None:
        raise HTTPException(503, "Workflow manager not running")
    return _workflow_manager


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return "admin"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics(
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    return manager.executor.metrics


@app.get("/api/stream/tasks")
async def task_stream(
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    async def event_generator():
        previous_snapshot = None
        while True:
            tasks = await manager.db.get_all_tasks()
            current_snapshot = json.dumps(tasks, sort_keys=True, default=str)
            if current_snapshot != previous_snapshot:
                previous_snapshot = current_snapshot
                yield f"data: {current_snapshot}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: str = Depends(get_current_user)):
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "token": API_TOKEN}
    )


@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = None,
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    return await manager.db.get_all_tasks(status)


@app.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    task = await manager.db.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.post("/api/tasks/{task_id}/approve")
async def approve_task(
    task_id: str,
    decision: str = Form(...),
    notes: str = Form(""),
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    task = await manager.db.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "waiting_approval":
        raise HTTPException(400, "Task not waiting for approval")

    # Hanya proses jika approved (reject ditangani route terpisah)
    approved = decision.lower() in ("yes", "approve")
    if not approved:
        raise HTTPException(400, "Invalid decision for approval endpoint. Use /reject for rejection.")

    task["human_decision"] = {"approved": True, "notes": notes}
    task["status"] = "pending"
    await manager.db.upsert_task(task)

    workflow_id = task.get("metadata", {}).get("workflow_id")
    if workflow_id:
        workflow_data = await manager.db.get_workflow(workflow_id)
        if workflow_data:
            workflow = manager.create_workflow_from_json(workflow_data)
            await manager.workflow_queue.put(workflow)
            logger.info(f"Task {task_id} approved, workflow {workflow_id} re-queued")
        else:
            logger.warning(f"Task {task_id} approved but workflow {workflow_id} not found")
    else:
        logger.warning(f"Task {task_id} approved but no workflow_id in metadata, cannot re-queue")

    return {"message": "Task approved and re-queued"}


@app.post("/api/tasks/{task_id}/reject")
async def reject_task(
    task_id: str,
    reason: str = Form(...),
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    task = await manager.db.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "waiting_approval":
        raise HTTPException(400, "Task not waiting for approval")
    await manager.db.update_task_status(task_id, "cancelled", f"Rejected by human: {reason}")
    return {"message": "Task rejected"}


@app.get("/api/stats")
async def stats(
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user),
):
    all_tasks = await manager.db.get_all_tasks()
    status_counts = {}
    for t in all_tasks:
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
    return {
        "total_tasks": len(all_tasks),
        "by_status": status_counts,
        "metrics": manager.executor.metrics,
    }