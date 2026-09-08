"""Notes data core: JSON documents (hybrid model) + CRUD. Pure stdlib — the Hermes SDK never touches this module.

This is the pre-agreed test seam: REST routes, agent tools, and the UI are thin
adapters over this module. Notes are JSON documents: the content column stores a
JSON object with a ``text`` body; folders group notes for the tree (folders
inside bases).
"""

import json
import sqlite3
from datetime import datetime, timezone

from cortex_db import connect as _raw_connect  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the notes table if missing."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, "
        "folder TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )


def connect(db_path) -> sqlite3.Connection:
    """Open the notes database, creating the schema if needed."""
    conn = _raw_connect(db_path)
    ensure_schema(conn)
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _doc(text: str) -> str:
    return json.dumps({"text": text}, ensure_ascii=False)


def _body(content: str) -> str:
    try:
        return json.loads(content).get("text", "")
    except (ValueError, AttributeError):
        return content  # tolerate legacy plain-text content


def create_note(conn: sqlite3.Connection, title: str, folder: str = "", text: str = "") -> dict:
    """Insert a note and return it as a dict. ``title`` must be non-blank."""
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    now = _now()
    note = {
        "id": uuid7(),
        "title": title,
        "content": _doc(text),
        "folder": (folder or "").strip(),
        "created_at": now,
        "updated_at": now,
    }
    conn.execute(
        "INSERT INTO notes (id, title, content, folder, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (note["id"], note["title"], note["content"], note["folder"], note["created_at"], note["updated_at"]),
    )
    conn.commit()
    return note


def list_notes(conn: sqlite3.Connection, folder: str | None = None) -> list[dict]:
    """All notes (optionally filtered by folder), oldest first."""
    if folder is None:
        rows = conn.execute("SELECT * FROM notes ORDER BY created_at, id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes WHERE folder = ? ORDER BY created_at, id", (folder,)).fetchall()
    return [dict(r) for r in rows]


def folders(conn: sqlite3.Connection) -> list[str]:
    """Distinct non-empty folders, sorted — the tree's folder level."""
    rows = conn.execute("SELECT DISTINCT folder FROM notes WHERE folder != '' ORDER BY folder").fetchall()
    return [r["folder"] for r in rows]


def get_note(conn: sqlite3.Connection, note_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row) if row else None


def update_note(
    conn: sqlite3.Connection,
    note_id: str,
    *,
    title: str | None = None,
    text: str | None = None,
    folder: str | None = None,
) -> dict | None:
    """Update the given fields of a note; returns the updated row, or None if the id is unknown.

    Static SQL: COALESCE keeps the stored value for any field passed as None.
    """
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("title cannot be blank")
    if title is None and text is None and folder is None:
        return get_note(conn, note_id)  # no-op PATCH: don't bump updated_at
    content = _doc(text) if text is not None else None
    conn.execute(
        "UPDATE notes SET title = COALESCE(?, title), content = COALESCE(?, content), "
        "folder = COALESCE(?, folder), updated_at = ? WHERE id = ?",
        (title, content, folder, _now(), note_id),
    )
    conn.commit()
    return get_note(conn, note_id)


def append_note(conn: sqlite3.Connection, note_id: str, text: str) -> dict | None:
    """Append ``text`` to the note's body (the agent adds a summary from chat)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("text is required")
    note = get_note(conn, note_id)
    if note is None:
        return None
    body = _body(note["content"])
    updated = _doc(f"{body}\n\n{text}" if body else text)
    conn.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
        (updated, _now(), note_id),
    )
    conn.commit()
    return get_note(conn, note_id)


def delete_note(conn: sqlite3.Connection, note_id: str) -> bool:
    """Delete a note; True if a row was removed."""
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return cur.rowcount > 0
