"""Cortex backend routes. Mounted by the Hermes gateway at /api/plugins/cortex/.

Loaded as a top-level module by file location, so the plugin root is added to
sys.path to reach the shared data core (tasks_core).
"""

import sqlite3
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from fastapi import APIRouter, Depends, HTTPException  # type: ignore[reportMissingImports]  # runtime: Hermes venv

import tasks_core  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
from plugin_db import db_path  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above

router = APIRouter()


def get_conn():
    conn = tasks_core.connect(db_path())
    try:
        yield conn
    finally:
        conn.close()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "plugin": "cortex"}


@router.get("/tasks")
def list_tasks(status: str | None = None, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        return tasks_core.list_tasks(conn, status=status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tasks", status_code=201)
def create_task(body: dict, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        return tasks_core.create_task(
            conn,
            title=str(body.get("title") or ""),
            status=body.get("status", "todo"),
            due=body.get("due"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}")
def update_task(task_id: str, body: dict, conn: sqlite3.Connection = Depends(get_conn)):
    try:
        task = tasks_core.update_task(
            conn,
            task_id,
            title=body.get("title"),
            status=body.get("status"),
            due=body.get("due"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    if not tasks_core.delete_task(conn, task_id):
        raise HTTPException(status_code=404, detail="task not found")
