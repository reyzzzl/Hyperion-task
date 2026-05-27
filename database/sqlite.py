import aiosqlite
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SQLiteDB")

DATABASE_PATH = "tasks.db"


class TaskDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                function TEXT,
                priority INTEGER,
                title TEXT,
                description TEXT,
                assigned_agent TEXT,
                status TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TEXT,
                deadline TEXT,
                metadata TEXT,
                result TEXT,
                human_decision TEXT
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TEXT
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                trigger TEXT,
                trigger_config TEXT,
                nodes TEXT,
                start_node TEXT,
                status TEXT
            )
        """)
        await self.db.commit()
        logger.info("SQLite database connected and tables ensured")

    async def close(self):
        await self.db.close()

    async def upsert_task(self, task: Dict[str, Any]):
        await self.db.execute("""
            INSERT INTO tasks (task_id, function, priority, title, description, assigned_agent, status, retry_count, max_retries, created_at, deadline, metadata, result, human_decision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                function=excluded.function,
                priority=excluded.priority,
                title=excluded.title,
                description=excluded.description,
                assigned_agent=excluded.assigned_agent,
                status=excluded.status,
                retry_count=excluded.retry_count,
                max_retries=excluded.max_retries,
                deadline=excluded.deadline,
                metadata=excluded.metadata,
                result=excluded.result,
                human_decision=excluded.human_decision
        """, (
            task["task_id"],
            task["function"],
            task.get("priority", 2),
            task["title"],
            task["description"],
            task.get("assigned_agent"),
            task["status"],
            task.get("retry_count", 0),
            task.get("max_retries", 3),
            task.get("created_at", datetime.now().isoformat()),
            task.get("deadline"),
            json.dumps(task.get("metadata", {})),
            json.dumps(task.get("result")),
            json.dumps(task.get("human_decision"))
        ))
        await self.db.commit()

    async def get_task(self, task_id: str) -> Optional[Dict]:
        cursor = await self.db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    async def get_all_tasks(self, status_filter: Optional[str] = None) -> List[Dict]:
        if status_filter:
            cursor = await self.db.execute("SELECT * FROM tasks WHERE status=?", (status_filter,))
        else:
            cursor = await self.db.execute("SELECT * FROM tasks")
        rows = await cursor.fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def update_task_status(self, task_id: str, status: str, result: Any = None, retry_count: Optional[int] = None):
        if retry_count is not None:
            await self.db.execute(
                "UPDATE tasks SET status=?, result=?, retry_count=? WHERE task_id=?",
                (status, json.dumps(result), retry_count, task_id)
            )
        else:
            await self.db.execute(
                "UPDATE tasks SET status=?, result=? WHERE task_id=?",
                (status, json.dumps(result), task_id)
            )
        await self.db.commit()

    async def increment_retry(self, task_id: str):
        await self.db.execute("UPDATE tasks SET retry_count = retry_count + 1 WHERE task_id=?", (task_id,))
        await self.db.commit()

    async def save_event(self, event_type: str, data: Dict):
        await self.db.execute(
            "INSERT INTO events (event_type, data, timestamp) VALUES (?, ?, ?)",
            (event_type, json.dumps(data), datetime.now().isoformat())
        )
        await self.db.commit()

    async def save_metric(self, metric_name: str, metric_value: float):
        await self.db.execute(
            "INSERT INTO metrics (metric_name, metric_value, timestamp) VALUES (?, ?, ?)",
            (metric_name, metric_value, datetime.now().isoformat())
        )
        await self.db.commit()

    async def save_workflow(self, workflow: Dict):
        await self.db.execute(
            "INSERT OR REPLACE INTO workflows (workflow_id, name, description, trigger, trigger_config, nodes, start_node, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                workflow["workflow_id"],
                workflow["name"],
                workflow.get("description", ""),
                workflow.get("trigger", "manual"),
                json.dumps(workflow.get("trigger_config", {})),
                json.dumps(workflow.get("nodes", [])),
                workflow.get("start_node"),
                workflow.get("status", "active")
            )
        )
        await self.db.commit()

    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        cursor = await self.db.execute("SELECT * FROM workflows WHERE workflow_id=?", (workflow_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "workflow_id": row["workflow_id"],
            "name": row["name"],
            "description": row["description"],
            "trigger": row["trigger"],
            "trigger_config": json.loads(row["trigger_config"]),
            "nodes": json.loads(row["nodes"]),
            "start_node": row["start_node"],
            "status": row["status"]
        }

    def _row_to_dict(self, row) -> Dict:
        return {
            "task_id": row["task_id"],
            "function": row["function"],
            "priority": row["priority"],
            "title": row["title"],
            "description": row["description"],
            "assigned_agent": row["assigned_agent"],
            "status": row["status"],
            "retry_count": row["retry_count"],
            "max_retries": row["max_retries"],
            "created_at": row["created_at"],
            "deadline": row["deadline"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "result": json.loads(row["result"]) if row["result"] else None,
            "human_decision": json.loads(row["human_decision"]) if row["human_decision"] else None,
        }