"""Cortex — Hermes plugin (agent half): task/note/habit tools for the chat agent.

The data cores (tasks_core, notes_core, habits_core) are pure stdlib; this module
is a thin adapter that resolves the DB path under the Hermes home and exposes
CRUD as agent tools.
"""

import json
import sys
from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

import tasks_core  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
import notes_core  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
import habits_core  # type: ignore[reportMissingImports]  # resolves via the sys.path bootstrap above
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


NOTES_CREATE_SCHEMA = {
    "name": "notes_create",
    "description": "Create a note in the Cortex notes base.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Note title."},
            "folder": {"type": "string", "description": "Optional folder for the tree (e.g. 'work')."},
            "text": {"type": "string", "description": "Optional initial body text."},
        },
        "required": ["title"],
    },
}

NOTES_LIST_SCHEMA = {
    "name": "notes_list",
    "description": "List notes from the Cortex notes base, optionally filtered by folder.",
    "parameters": {
        "type": "object",
        "properties": {
            "folder": {"type": "string", "description": "Only return notes in this folder."},
        },
    },
}

NOTES_GET_SCHEMA = {
    "name": "notes_get",
    "description": "Get a single note by id (title, body, folder).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Note id (from notes_list)."},
        },
        "required": ["id"],
    },
}

NOTES_UPDATE_SCHEMA = {
    "name": "notes_update",
    "description": "Update a note (title, body text, or folder).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Note id (from notes_list)."},
            "title": {"type": "string", "description": "New title."},
            "text": {"type": "string", "description": "New body text (replaces the whole body)."},
            "folder": {"type": "string", "description": "New folder."},
        },
        "required": ["id"],
    },
}

NOTES_APPEND_SCHEMA = {
    "name": "notes_append",
    "description": "Append a summary or text to a note's body (e.g. a meeting summary from chat).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Note id (from notes_list)."},
            "text": {"type": "string", "description": "Text to append."},
        },
        "required": ["id", "text"],
    },
}

NOTES_DELETE_SCHEMA = {
    "name": "notes_delete",
    "description": "Delete a note.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Note id (from notes_list)."},
        },
        "required": ["id"],
    },
}


def _note_body(note: dict) -> str:
    try:
        return json.loads(note["content"]).get("text", "")
    except (ValueError, AttributeError):
        return note["content"]


def _handle_note_create(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        note = notes_core.create_note(conn, args.get("title", ""), folder=args.get("folder", ""), text=args.get("text", ""))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"id": note["id"], "title": note["title"], "folder": note["folder"]})


def _handle_note_list(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        notes = notes_core.list_notes(conn, folder=args.get("folder"))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"notes": [{"id": n["id"], "title": n["title"], "folder": n["folder"]} for n in notes]})


def _handle_note_get(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        note = notes_core.get_note(conn, args.get("id", ""))
    finally:
        conn.close()
    if note is None:
        return tool_error("note not found")
    return tool_result({"id": note["id"], "title": note["title"], "folder": note["folder"], "text": notes_core._body(note["content"])})


def _handle_note_update(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        note = notes_core.update_note(conn, args.get("id", ""), title=args.get("title"), text=args.get("text"), folder=args.get("folder"))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    if note is None:
        return tool_error("note not found")
    return tool_result({"id": note["id"], "title": note["title"], "folder": note["folder"], "text": notes_core._body(note["content"])})


def _handle_note_append(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        note = notes_core.append_note(conn, args.get("id", ""), args.get("text", ""))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    if note is None:
        return tool_error("note not found")
    return tool_result({"id": note["id"], "title": note["title"]})


def _handle_note_delete(args: dict, **kw) -> str:
    conn = notes_core.connect(db_path())
    try:
        deleted = notes_core.delete_note(conn, args.get("id", ""))
    finally:
        conn.close()
    if not deleted:
        return tool_error("note not found")
    return tool_result({"deleted": args.get("id")})


HABITS_CREATE_SCHEMA = {
    "name": "habits_create",
    "description": "Create a habit to track daily.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Habit name."},
        },
        "required": ["name"],
    },
}

HABITS_LIST_SCHEMA = {
    "name": "habits_list",
    "description": "List habits with their current streak and 14-day sparkline.",
    "parameters": {"type": "object", "properties": {}},
}

HABITS_CHECKIN_SCHEMA = {
    "name": "habits_checkin",
    "description": "Record a daily check-in for a habit (default: today).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Habit id (from habits_list)."},
            "day": {"type": "string", "description": "Optional day, YYYY-MM-DD (default today)."},
        },
        "required": ["id"],
    },
}

HABITS_UNCHECK_SCHEMA = {
    "name": "habits_uncheck",
    "description": "Remove a daily check-in (e.g. a mistake).",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Habit id (from habits_list)."},
            "day": {"type": "string", "description": "Optional day, YYYY-MM-DD (default today)."},
        },
        "required": ["id"],
    },
}

HABITS_DELETE_SCHEMA = {
    "name": "habits_delete",
    "description": "Delete a habit.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Habit id (from habits_list)."},
        },
        "required": ["id"],
    },
}


def _handle_habit_create(args: dict, **kw) -> str:
    conn = habits_core.connect(db_path())
    try:
        habit = habits_core.create_habit(conn, args.get("name", ""))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"id": habit["id"], "name": habit["name"]})


def _handle_habit_list(args: dict, **kw) -> str:
    conn = habits_core.connect(db_path())
    try:
        habits = habits_core.list_habits(conn)
    finally:
        conn.close()
    return tool_result({"habits": habits})


def _handle_habit_checkin(args: dict, **kw) -> str:
    conn = habits_core.connect(db_path())
    try:
        if not habits_core.habit_exists(conn, args.get("id", "")):
            return tool_error("habit not found")
        habits_core.check_in(conn, args.get("id", ""), day=args.get("day"))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"checked": args.get("id"), "day": args.get("day") or "today"})


def _handle_habit_uncheck(args: dict, **kw) -> str:
    conn = habits_core.connect(db_path())
    try:
        if not habits_core.habit_exists(conn, args.get("id", "")):
            return tool_error("habit not found")
        habits_core.uncheck(conn, args.get("id", ""), day=args.get("day"))
    except ValueError as exc:
        return tool_error(str(exc))
    finally:
        conn.close()
    return tool_result({"unchecked": args.get("id"), "day": args.get("day") or "today"})


def _handle_habit_delete(args: dict, **kw) -> str:
    conn = habits_core.connect(db_path())
    try:
        deleted = habits_core.delete_habit(conn, args.get("id", ""))
    finally:
        conn.close()
    if not deleted:
        return tool_error("habit not found")
    return tool_result({"deleted": args.get("id")})


_TOOLS = (
    ("tasks_create", CREATE_SCHEMA, _handle_create, "➕"),
    ("tasks_list", LIST_SCHEMA, _handle_list, "📋"),
    ("tasks_update", UPDATE_SCHEMA, _handle_update, "✏️"),
    ("tasks_delete", DELETE_SCHEMA, _handle_delete, "🗑️"),
    ("notes_create", NOTES_CREATE_SCHEMA, _handle_note_create, "📝"),
    ("notes_list", NOTES_LIST_SCHEMA, _handle_note_list, "🗂️"),
    ("notes_get", NOTES_GET_SCHEMA, _handle_note_get, "📄"),
    ("notes_update", NOTES_UPDATE_SCHEMA, _handle_note_update, "🔧"),
    ("notes_append", NOTES_APPEND_SCHEMA, _handle_note_append, "📎"),
    ("notes_delete", NOTES_DELETE_SCHEMA, _handle_note_delete, "🚮"),
    ("habits_create", HABITS_CREATE_SCHEMA, _handle_habit_create, "🌱"),
    ("habits_list", HABITS_LIST_SCHEMA, _handle_habit_list, "📊"),
    ("habits_checkin", HABITS_CHECKIN_SCHEMA, _handle_habit_checkin, "✅"),
    ("habits_uncheck", HABITS_UNCHECK_SCHEMA, _handle_habit_uncheck, "↩️"),
    ("habits_delete", HABITS_DELETE_SCHEMA, _handle_habit_delete, "❌"),
)


def register(ctx):
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(name=name, toolset=TOOLSET, schema=schema, handler=handler, emoji=emoji)
