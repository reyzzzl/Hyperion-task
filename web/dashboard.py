import os
import asyncio
import json
import logging
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query, Response
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
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
_agent_orchestrator = None

security = HTTPBearer()

def set_workflow_manager(manager: WorkflowManager):
    global _workflow_manager
    _workflow_manager = manager

def set_agent_orchestrator(orchestrator):
    global _agent_orchestrator
    _agent_orchestrator = orchestrator

async def get_workflow_manager() -> WorkflowManager:
    if _workflow_manager is None:
        raise HTTPException(503, "Workflow manager not running")
    return _workflow_manager

async def get_agent_orchestrator():
    if _agent_orchestrator is None:
        raise HTTPException(503, "Agent orchestrator not initialized")
    return _agent_orchestrator

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return "admin"

def get_token_from_cookie(request: Request) -> str:
    return request.cookies.get("token", "")

async def get_current_user_from_cookie(request: Request):
    token = get_token_from_cookie(request)
    if not token or token != API_TOKEN:
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
async def dashboard(request: Request, response: Response):
    token = get_token_from_cookie(request)
    if not token or token != API_TOKEN:
        return HTMLResponse(content="<html><body><h1>Unauthorized</h1><p>Please login with token</p><form method='post' action='/api/login'><input name='token' placeholder='Token'><button type='submit'>Login</button></form></body></html>", status_code=401)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/api/login")
async def login(request: Request, response: Response):
    body = await request.json()
    token = body.get("token")
    if token == API_TOKEN:
        secure = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
        resp = JSONResponse({"success": True})
        resp.set_cookie(key="token", value=token, httponly=True, secure=secure, samesite="Lax")
        return resp
    raise HTTPException(401, "Invalid token")

@app.get("/api/tasks")
async def list_tasks(
    status: Optional[str] = None,
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user_from_cookie),
):
    return await manager.db.get_all_tasks(status)

@app.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    manager: WorkflowManager = Depends(get_workflow_manager),
    current_user: str = Depends(get_current_user_from_cookie),
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
    current_user: str = Depends(get_current_user_from_cookie),
):
    task = await manager.db.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "waiting_approval":
        raise HTTPException(400, "Task not waiting for approval")
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
    current_user: str = Depends(get_current_user_from_cookie),
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
    current_user: str = Depends(get_current_user_from_cookie),
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

@app.post("/api/agent/task")
async def agent_task(request: Request, current_user: str = Depends(get_current_user_from_cookie)):
    body = await request.json()
    orchestrator = await get_agent_orchestrator()
    result = await orchestrator.route_task(body.get("task", {}), body.get("context", {}))
    return result

@app.get("/api/agent/status")
async def agent_status(current_user: str = Depends(get_current_user_from_cookie)):
    orchestrator = await get_agent_orchestrator()
    return orchestrator.get_status()