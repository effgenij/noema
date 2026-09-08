"""Habits data core: strict table + per-day check-in log. Pure stdlib — the Hermes SDK never touches this module.

This is the pre-agreed test seam: REST routes, agent tools, and the UI are thin
adapters over this module. Streak = consecutive checked days ending today (or
yesterday if today is not yet checked); a missed day resets it. Sparkline = 0/1
per day for the last N days (rendered as SVG by the UI).
"""

import re
import sqlite3
from datetime import date, timedelta

from cortex_db import connect as _raw_connect  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin

SPARKLINE_DAYS = 14
_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the habits tables if missing."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS habits ("
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS habit_log ("
        "habit_id TEXT NOT NULL, day TEXT NOT NULL, "
        "PRIMARY KEY (habit_id, day), "
        "FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE)"
    )


def connect(db_path) -> sqlite3.Connection:
    """Open the habits database, creating the schema if needed."""
    conn = _raw_connect(db_path)
    ensure_schema(conn)
    conn.commit()
    return conn


def _today() -> str:
    return date.today().isoformat()


def create_habit(conn: sqlite3.Connection, name: str) -> dict:
    """Insert a habit and return it as a dict. ``name`` must be non-blank."""
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required")
    habit = {"id": uuid7(), "name": name, "created_at": _today()}
    conn.execute(
        "INSERT INTO habits (id, name, created_at) VALUES (?, ?, ?)",
        (habit["id"], habit["name"], habit["created_at"]),
    )
    conn.commit()
    return habit


def _checked_days(conn: sqlite3.Connection, habit_id: str) -> set[str]:
    rows = conn.execute("SELECT day FROM habit_log WHERE habit_id = ?", (habit_id,)).fetchall()
    return {r["day"] for r in rows}


def current_streak(conn: sqlite3.Connection, habit_id: str, today: str | None = None) -> int:
    """Consecutive checked days ending today (or yesterday if today is unchecked)."""
    today = date.fromisoformat(today or _today())
    checked = _checked_days(conn, habit_id)
    day = today
    if day.isoformat() not in checked:
        day -= timedelta(days=1)
    count = 0
    while day.isoformat() in checked:
        count += 1
        day -= timedelta(days=1)
    return count


def sparkline(conn: sqlite3.Connection, habit_id: str, days: int = SPARKLINE_DAYS, today: str | None = None) -> list[int]:
    """0/1 per day for the last ``days`` days, oldest first."""
    today = date.fromisoformat(today or _today())
    checked = _checked_days(conn, habit_id)
    return [1 if (today - timedelta(days=i)).isoformat() in checked else 0 for i in range(days - 1, -1, -1)]


def list_habits(conn: sqlite3.Connection, today: str | None = None) -> list[dict]:
    """All habits with their current streak and sparkline data."""
    rows = conn.execute("SELECT * FROM habits ORDER BY created_at, id").fetchall()
    return [
        {
            **dict(r),
            "streak": current_streak(conn, r["id"], today=today),
            "sparkline": sparkline(conn, r["id"], today=today),
        }
        for r in rows
    ]


def habit_exists(conn: sqlite3.Connection, habit_id: str) -> bool:
    """True if a habit with this id exists."""
    return conn.execute("SELECT 1 FROM habits WHERE id = ?", (habit_id,)).fetchone() is not None


def _validate_day(day: str) -> None:
    if not _DAY_RE.match(day):
        raise ValueError(f"invalid day: {day!r} (expected YYYY-MM-DD)")


def check_in(conn: sqlite3.Connection, habit_id: str, day: str | None = None) -> bool:
    """Record a check-in for ``day`` (default today). Idempotent; True if a row was added."""
    day = day or _today()
    _validate_day(day)
    cur = conn.execute(
        "INSERT OR IGNORE INTO habit_log (habit_id, day) VALUES (?, ?)",
        (habit_id, day),
    )
    conn.commit()
    return cur.rowcount > 0


def uncheck(conn: sqlite3.Connection, habit_id: str, day: str | None = None) -> bool:
    """Remove a check-in for ``day`` (default today); True if a row was removed."""
    day = day or _today()
    _validate_day(day)
    cur = conn.execute("DELETE FROM habit_log WHERE habit_id = ? AND day = ?", (habit_id, day))
    conn.commit()
    return cur.rowcount > 0


def delete_habit(conn: sqlite3.Connection, habit_id: str) -> bool:
    """Delete a habit (and its log via cascade); True if a row was removed."""
    cur = conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    return cur.rowcount > 0
