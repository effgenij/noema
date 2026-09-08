"""Shared SQLite helpers for the Cortex data core. Pure stdlib — no Hermes imports."""

import sqlite3
import threading
import time
from pathlib import Path


_seq = 0
_lock = threading.Lock()


def uuid7() -> str:
    """128-bit UUIDv7 as a 32-char hex string: 48-bit ms timestamp + version/variant + counter.

    Python 3.11 has no ``uuid.uuid7()`` (3.14+), so generate it manually. A global
    monotonic counter (62 bits) replaces the random field: ids are strictly ordered
    by creation time — within a millisecond by counter, across milliseconds by the
    timestamp prefix (2^80 per ms dwarfs the 2^62 counter). A lock keeps the counter
    race-free across gateway threads.
    """
    global _seq
    ms = (time.time_ns() // 1_000_000) & ((1 << 48) - 1)
    with _lock:
        _seq = (_seq + 1) & ((1 << 62) - 1)
        seq = _seq
    return f"{(ms << 80) | (0b0111 << 76) | (0b1000 << 72) | (0b10 << 62) | seq:032x}"


def connect(db_path) -> sqlite3.Connection:
    """Open (creating if needed) a WAL-mode SQLite database with dict-like rows."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
