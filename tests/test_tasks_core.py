"""Tests for the tasks data core (the pre-agreed seam: pure Python, no Hermes SDK)."""

import time

import pytest

from cortex_db import uuid7  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
from tasks_core import (  # type: ignore[reportMissingImports]  # resolves via pytest pythonpath=plugin
    connect,
    create_task,
    delete_task,
    list_tasks,
    update_task,
)


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    yield c
    c.close()


def test_connect_creates_wal_db(tmp_path):
    db = tmp_path / "t.db"
    c = connect(db)
    assert db.exists()
    assert c.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    c.close()


def test_uuid7_unique_and_time_ordered():
    a, b = uuid7(), uuid7()
    assert a != b
    assert len(a) == 32
    assert a < b


def test_uuid7_rfc_layout():
    u = uuid7()
    assert int(u[12], 16) == 7  # version nibble (bits 76-79)
    assert int(u[16], 16) & 0xC == 0x8  # variant 10 (bits 62-63)
    assert int(u[13], 16) & 0x8 == 0x8  # RFC var field 10xx (bits 72-75)
    ms = int(u[:12], 16)  # top 48 bits = unix ms
    now = int(time.time() * 1000)
    assert abs(ms - now) < 5000



def test_create_task_returns_row(conn):
    t = create_task(conn, "Buy milk")
    assert t["title"] == "Buy milk"
    assert t["status"] == "todo"
    assert t["id"]
    rows = list_tasks(conn)
    assert len(rows) == 1
    assert rows[0]["id"] == t["id"]


def test_create_task_requires_title(conn):
    with pytest.raises(ValueError):
        create_task(conn, "   ")


def test_create_task_validates_status(conn):
    with pytest.raises(ValueError):
        create_task(conn, "x", status="bogus")


def test_list_tasks_filters_by_status(conn):
    create_task(conn, "a", status="todo")
    create_task(conn, "b", status="done")
    assert len(list_tasks(conn, status="todo")) == 1
    assert len(list_tasks(conn, status="done")) == 1
    assert len(list_tasks(conn)) == 2


def test_update_task_changes_fields(conn):
    t = create_task(conn, "a")
    updated = update_task(conn, t["id"], status="done", title="A!")
    assert updated["status"] == "done"
    assert updated["title"] == "A!"
    assert updated["updated_at"] >= t["updated_at"]
    assert list_tasks(conn)[0]["status"] == "done"


def test_update_task_missing_returns_none(conn):
    assert update_task(conn, "nope", status="done") is None


def test_update_task_validates_status(conn):
    t = create_task(conn, "a")
    with pytest.raises(ValueError):
        update_task(conn, t["id"], status="bogus")


def test_delete_task(conn):
    t = create_task(conn, "a")
    assert delete_task(conn, t["id"]) is True
    assert list_tasks(conn) == []
    assert delete_task(conn, t["id"]) is False


def test_persistence_across_reconnect(tmp_path):
    db = tmp_path / "p.db"
    c1 = connect(db)
    create_task(c1, "persist me")
    c1.close()
    c2 = connect(db)
    assert len(list_tasks(c2)) == 1
    c2.close()
