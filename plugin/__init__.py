"""Cortex — Hermes plugin (agent half): task CRUD tools for the chat agent.

The data core (tasks_core) is pure stdlib; this module is a thin adapter that
resolves the DB path under the Hermes home and exposes CRUD as agent tools.
"""

import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

import tasks_core  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
from plugin_db import db_path  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
from tools.registry import tool_error, tool_result  # type: ignore[reportMissingImports]  # runtime: gateway process

TOOLSET = "cortex"

CREATE_SCHEMA = {
    "name": "tasks_create",
    "description": "Create a task in the Cortex task list.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title."},
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "done"],
                "description": "Initial status (default: todo).",
            },
            "due": {"type": "string", "description": "Optional due date, ISO-8601 (e.g. 2026-09-10)."},
        },
        "required": ["title"],
    },
}

LIST_SCHEMA = {
    "name": "tasks_list",
    "description": "List tasks from the Cortex task list, optionally filtered by status.",
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "done"],
                "description": "Only return tasks with this status.",
            },
        },
    },
}

UPDATE_SCHEMA = {
    "name": "tasks_update",
    "description": "Update a task in the Cortex task list (title, status, or due date).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Task id (from tasks_list)."},
            "title": {"type": "string", "description": "New title."},
            "status": {"type": "string", "enum": ["todo", "in_progress", "done"], "description": "New status."},
            "due": {"type": "string", "description": "New due date, ISO-8601."},
        },
        "required": ["id"],
    },
}

DELETE_SCHEMA = {
    "name": "tasks_delete",
    "description": "Delete a task from the Cortex task list.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Task id (from tasks_list)."},
        },
        "required": ["id"],
    },
}


def _handle_create(args: dict, **kw) -> str:
    conn = tasks_core.connect(db_path())
    try:
        task = tasks_core.create_task(
            conn,
            title=args.get("title", ""),
            status=args.get("status", "todo"),
            due=args.get("due"),
        )
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"id": task["id"], "title": task["title"], "status": task["status"]})


def _handle_list(args: dict, **kw) -> str:
    conn = tasks_core.connect(db_path())
    try:
        tasks = tasks_core.list_tasks(conn, status=args.get("status"))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"tasks": tasks})


def _handle_update(args: dict, **kw) -> str:
    conn = tasks_core.connect(db_path())
    try:
        task = tasks_core.update_task(
            conn,
            args.get("id", ""),
            title=args.get("title"),
            status=args.get("status"),
            due=args.get("due"),
        )
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    if task is None:
        return tool_error("task not found")
    return tool_result({"id": task["id"], "title": task["title"], "status": task["status"]})


def _handle_delete(args: dict, **kw) -> str:
    conn = tasks_core.connect(db_path())
    try:
        deleted = tasks_core.delete_task(conn, args.get("id", ""))
    finally:
        conn.close()
    if not deleted:
        return tool_error("task not found")
    return tool_result({"deleted": args.get("id")})


_TOOLS = (
    ("tasks_create", CREATE_SCHEMA, _handle_create, "➕"),
    ("tasks_list", LIST_SCHEMA, _handle_list, "📋"),
    ("tasks_update", UPDATE_SCHEMA, _handle_update, "✏️"),
    ("tasks_delete", DELETE_SCHEMA, _handle_delete, "🗑️"),
)


def register(ctx):
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(name=name, toolset=TOOLSET, schema=schema, handler=handler, emoji=emoji)
