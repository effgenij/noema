"""Tasks data core: schema + CRUD. Pure stdlib — the Hermes SDK never touches this module.

This is the pre-agreed test seam: REST routes, agent tools, and the UI are thin
adapters over this module.
"""

import sqlite3
from datetime import datetime, timezone

from cortex_db import connect as _raw_connect  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin

STATUSES = ("todo", "in_progress", "done")


def connect(db_path) -> sqlite3.Connection:
    """Open the tasks database, creating the schema if needed."""
    conn = _raw_connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'todo', "
        "due TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _validate_status(status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"invalid status: {status!r} (expected one of {STATUSES})")


def create_task(conn: sqlite3.Connection, title: str, status: str = "todo", due: str | None = None) -> dict:
    """Insert a task and return it as a dict. ``title`` must be non-blank, ``status`` valid."""
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    _validate_status(status)
    now = _now()
    task = {
        "id": uuid7(),
        "title": title,
        "status": status,
        "due": due,
        "created_at": now,
        "updated_at": now,
    }
    conn.execute(
        "INSERT INTO tasks (id, title, status, due, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (task["id"], task["title"], task["status"], task["due"], task["created_at"], task["updated_at"]),
    )
    conn.commit()
    return task


def list_tasks(conn: sqlite3.Connection, status: str | None = None) -> list[dict]:
    """All tasks (optionally filtered by status), oldest first."""
    if status is not None:
        _validate_status(status)
    if status is None:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at, id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at, id", (status,)).fetchall()
    return [dict(row) for row in rows]


def update_task(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    title: str | None = None,
    status: str | None = None,
    due: str | None = None,
) -> dict | None:
    """Update the given fields of a task; returns the updated row, or None if the id is unknown.

    Static SQL: COALESCE keeps the stored value for any field passed as None.
    """
    if status is not None:
        _validate_status(status)
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("title cannot be blank")
    if title is None and status is None and due is None:
        return get_task(conn, task_id)  # no-op PATCH: don't bump updated_at
    conn.execute(
        "UPDATE tasks SET title = COALESCE(?, title), status = COALESCE(?, status), "
        "due = COALESCE(?, due), updated_at = ? WHERE id = ?",
        (title, status, due, _now(), task_id),
    )
    conn.commit()
    return get_task(conn, task_id)


def get_task(conn: sqlite3.Connection, task_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def delete_task(conn: sqlite3.Connection, task_id: str) -> bool:
    """Delete a task; True if a row was removed."""
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return cur.rowcount > 0
